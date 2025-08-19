from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import CharacterTextSplitter
from dotenv import load_dotenv, find_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import HumanMessage
import streamlit as st
import os
import time
import html
import re
import random

# 📚 ABBREVIATION DICTIONARY FOR QUERY EXPANSION
ABBREVIATIONS = {
    # General High School Abbreviations
    "PE": "Physical Education",
    "AP": "Advanced Placement",
    "IB": "International Baccalaureate",
    "GPA": "Grade Point Average",
    "SAT": "Scholastic Assessment Test",
    "ACT": "American College Testing",
    "NHS": "National Honor Society",
    "FFA": "Future Farmers of America",
    "STEM": "Science, Technology, Engineering, and Mathematics",
    "ESL": "English as a Second Language",
    "IEP": "Individualized Education Program",
    "TA": "Teaching Assistant",
    "CP": "College Prep",
    "DE": "Dual Enrollment",
    "GT": "Gifted and Talented",
    "IBDP": "International Baccalaureate Diploma Program",
    "PSAT": "Preliminary SAT",
    
    # Westlake High School / Conejo USD Specific
    "SAGE": "Students Achieving Greater Excellence",
    "CTE": "Career and Technical Education",
    "ASB": "Associated Student Body",
    "AVID": "Advancement Via Individual Determination",
    "RSP": "Resource Specialist Program",
    "ELAC": "English Learner Advisory Committee",
    "CVUSD": "Conejo Valley Unified School District",
    "WHS": "Westlake High School",
    
    # Clubs / Sports / Extracurriculars
    "FBLA": "Future Business Leaders of America",
    "DECA": "Distributive Education Clubs of America",
    "MUN": "Model United Nations",
    "NJHS": "National Junior Honor Society",
    "JV": "Junior Varsity",
    "VARSITY": "Varsity Team",
    "ORCHESTRA": "Orchestra Program",
    "BAND": "Band Program",
    "CHOIR": "Choir Program",
    "DRAMA": "Drama Club",
    "ROBOTICS": "Robotics Club",
    "SCIENCE_OLYMPIAD": "Science Olympiad",
    "STUDENT_COUNCIL": "Student Council",
    "YEARBOOK": "Yearbook Club",
    "ART_CLUB": "Art Club",
    
    # Common IT/Technology Terms
    "IT": "Information Technology",
    "CS": "Computer Science",
    "AI": "Artificial Intelligence",
    "VR": "Virtual Reality",
    "AR": "Augmented Reality"
}

def expand_abbreviations(query):
    """
    Expand abbreviations in the user query to improve semantic search.
    Returns both original and expanded query for better matching.
    """
    expanded_query = query
    found_abbreviations = []
    
    # Find abbreviations in the query (case-insensitive)
    for abbrev, full_form in ABBREVIATIONS.items():
        # Use word boundaries to match whole words only
        pattern = r'\b' + re.escape(abbrev) + r'\b'
        if re.search(pattern, query, re.IGNORECASE):
            # Replace the abbreviation with both forms for better matching
            expanded_query = re.sub(pattern, f"{abbrev} {full_form}", expanded_query, flags=re.IGNORECASE)
            found_abbreviations.append((abbrev, full_form))
    
    return expanded_query, found_abbreviations

def get_clarification_message(unknown_terms):
    """
    Generate a natural clarification message for unknown terms.
    """
    if not unknown_terms:
        return None
    
    # Different message templates for variety
    templates = [
        "Sorry, I don't recognize '{term}'. Can you clarify what it means?",
        "I'm not sure what '{term}' refers to. Could you explain it?",
        "I haven't seen '{term}' before. What does it mean?",
        "Could you help me understand what '{term}' stands for?",
        "I'm not familiar with '{term}'. Can you provide more details?"
    ]
    
    if len(unknown_terms) == 1:
        template = random.choice(templates)
        return template.format(term=unknown_terms[0])
    else:
        terms_str = "', '".join(unknown_terms[:-1]) + f"', and '{unknown_terms[-1]}"
        return f"I'm not familiar with some terms: '{terms_str}'. Could you clarify what they mean?"

def detect_unknown_abbreviations(query):
    """
    Detect potential abbreviations that aren't in our dictionary.
    Returns list of unknown uppercase terms that might be abbreviations.
    """
    # Find uppercase words that might be abbreviations
    potential_abbrevs = re.findall(r'\b[A-Z]{2,}\b', query)
    
    # Filter out known abbreviations
    unknown_abbrevs = [abbrev for abbrev in potential_abbrevs 
                      if abbrev.upper() not in [k.upper() for k in ABBREVIATIONS.keys()]]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_unknown = []
    for abbrev in unknown_abbrevs:
        if abbrev.upper() not in seen:
            seen.add(abbrev.upper())
            unique_unknown.append(abbrev)
    
    return unique_unknown

# ⚡ PERFORMANCE OPTIMIZATIONS:
# 1. @st.cache_resource for vector database loading (expensive I/O operation)
# 2. @st.cache_resource for LLM initialization (model loading)
# 3. @st.cache_resource for retriever creation (chain setup)
# 4. @st.cache_resource for RAG chain creation (complex pipeline)
# 5. @st.cache_resource for prompt loading from hub (network call)
# 6. @st.cache_data for document formatting (text processing)
# 7. @st.cache_data for theme CSS generation (string processing)
# These optimizations prevent expensive operations from running on every page refresh!

def optimize_session_state():
    """Keep only essential data in session state for better performance"""
    # Limit chat history to last 20 exchanges (10 user + 10 AI messages)
    if len(st.session_state["chat_history"]) > 20:
        st.session_state["chat_history"] = st.session_state["chat_history"][-20:]
    
    # Limit display messages to last 30
    if len(st.session_state["messages"]) > 30:
        st.session_state["messages"] = st.session_state["messages"][-30:]

def initialize_session_state():
    # Chat history for RAG context (langchain format)
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    # Display messages (our custom format for UI)
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    # Track processed messages to avoid duplicates
    if "processed_messages" not in st.session_state:
        st.session_state["processed_messages"] = set()
    # Generate a unique session ID
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = str(time.time())
    # Theme preferences - Default to Westlake Light Mode
    if "dark_mode" not in st.session_state:
        st.session_state["dark_mode"] = False
    if "westlake_theme" not in st.session_state:
        st.session_state["westlake_theme"] = True
    # Smart rerun control
    if "last_rerun" not in st.session_state:
        st.session_state["last_rerun"] = 0
    # First time user flag for shortcuts
    if "first_time_user" not in st.session_state:
        st.session_state["first_time_user"] = True
    # Pending question from recommendation buttons
    if "pending_question" not in st.session_state:
        st.session_state["pending_question"] = None
    # Streaming animation flags
    if "show_streaming" not in st.session_state:
        st.session_state["show_streaming"] = False
    if "streaming_response" not in st.session_state:
        st.session_state["streaming_response"] = None
    # Processing flags
    if "processing_message" not in st.session_state:
        st.session_state["processing_message"] = False
    # Hide recommendations flag
    if "hide_recommendations" not in st.session_state:
        st.session_state["hide_recommendations"] = False
    # Form submission flag to prevent duplication
    if "form_submitted" not in st.session_state:
        st.session_state["form_submitted"] = False
    
st.set_page_config(
    page_title="🏔️ Westlake AI Assistant", 
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set custom page name for sidebar navigation
if hasattr(st, '_main_script_path'):
    st._main_script_path = "AI Assistant"

# what is this line for?
os.environ["USER_AGENT"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


# Load environment variables (works for both local and deployed)
load_dotenv(dotenv_path="Environment/API-Key.env")

# Get API key - prioritize Streamlit secrets over environment variables
try:
    # First try to get from Streamlit secrets (for cloud deployment)
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
    if OPENAI_API_KEY:
        print("✅ Using API key from Streamlit secrets")
    else:
        # Fallback to environment variable (for local development)
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if OPENAI_API_KEY:
            print("✅ Using API key from environment variable")
        else:
            print("❌ No API key found in secrets or environment")
except Exception:
    # If secrets are not available (local development), use environment
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if OPENAI_API_KEY:
        print("✅ Using API key from environment variable (secrets not available)")
    else:
        print("❌ No API key found")

# Validate API key is properly set
if not OPENAI_API_KEY or OPENAI_API_KEY == "your-openai-api-key-here":
    st.error("🚨 OpenAI API key not configured! Please check your secrets or environment variables.")
    st.stop()

# Path to the prebuilt FAISS index - handle both running from root and Source directory
import os

def get_vector_db_path():
    """Get the correct path to the vector database regardless of working directory"""
    print(f"🔍 Current working directory: {os.getcwd()}")
    print(f"🔍 Files in current directory: {os.listdir('.')}")
    
    possible_paths = [
        "index.faiss",           # Primary: Root directory (preferred)
        "./index.faiss",         # Explicit current directory
        "../index.faiss",        # When running from subdirectory
        "Source/index.faiss",    # Legacy: Source directory (fallback)
        os.path.join("Source", "index.faiss")  # Explicit join fallback
    ]
    
    for path in possible_paths:
        print(f"🔍 Checking path: {path}")
        if os.path.exists(path):
            abs_path = os.path.abspath(path)
            print(f"✅ Found vector database at: {path} (absolute: {abs_path})")
            
            # Check if the required files exist
            faiss_file = os.path.join(path, "index.faiss")
            pkl_file = os.path.join(path, "index.pkl")
            print(f"🔍 FAISS file exists: {os.path.exists(faiss_file)} ({faiss_file})")
            print(f"🔍 PKL file exists: {os.path.exists(pkl_file)} ({pkl_file})")
            
            if os.path.exists(faiss_file) and os.path.exists(pkl_file):
                print(f"✅ Both database files found!")
                return path
            else:
                print(f"⚠️ Database directory found but missing files")
    
    # If none found, show detailed error
    print("❌ Vector database not found in any expected locations")
    print("🔍 Searched paths:")
    for path in possible_paths:
        print(f"   - {path} (exists: {os.path.exists(path)})")
    
    return "index.faiss"  # Default fallback

index_Faiss_Filepath = get_vector_db_path()

@st.cache_resource
def load_vector_database():
    """
    Load the Vector Database from local disk with caching for better performance.
    This expensive operation only runs once and gets cached.
    """
    try:
        print(f"🔄 Attempting to load vector database from: {index_Faiss_Filepath}")
        
        db = FAISS.load_local(
            index_Faiss_Filepath, 
            OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model="text-embedding-3-small"), 
            allow_dangerous_deserialization=True
        )
        
        # Verify the database loaded correctly
        vector_count = db.index.ntotal if hasattr(db, 'index') else 0
        print(f"✅ Vector database loaded successfully!")
        print(f"📊 Vector count: {vector_count}")
        
        # Test a simple search to verify functionality
        if vector_count > 0:
            test_results = db.similarity_search("Westlake High School", k=1)
            print(f"🔍 Test search returned {len(test_results)} results")
            if test_results:
                print(f"📄 Sample result length: {len(test_results[0].page_content)} characters")
        
        return db
        
    except Exception as e:
        print(f"❌ Error loading vector database: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
        
        # Show Streamlit error for user visibility
        st.error(f"🚨 Failed to load vector database: {str(e)}")
        st.error("This may cause the chatbot to give generic responses instead of school-specific information.")
        
        # Return None or raise the error
        raise e

# Load the cached vector database
try:
    db = load_vector_database()
    vector_count = db.index.ntotal if hasattr(db, 'index') else 0
    print(f"🎉 Database loaded with {vector_count} vectors")
except Exception as e:
    print(f"💥 Database loading failed: {e}")
    db = None


#Perform Sementic Search Of the Embeddings inside with the database you loaded --^
#docs = db.similarity_search("What is Aetherfloris Ventus")

#print_output(docs)

@st.cache_resource
def initialize_llm():
    """
    Initialize the LLM with caching for better performance.
    """
    return ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-3.5-turbo-0125")

@st.cache_resource
def get_retriever(_db):
    """
    Create retriever from the vector database with caching.
    The underscore prefix in _db tells Streamlit not to hash this parameter.
    """
    return _db.as_retriever(search_type="similarity", search_kwargs={"k": 6})

@st.cache_resource
def get_lazy_components():
    """Lazy load heavy components only when needed for better startup performance"""
    llm = initialize_llm()
    retriever = get_retriever(db)
    prompt = get_rag_prompt()
    rag_chain = create_rag_chain(llm, retriever, prompt)
    return {
        'llm': llm,
        'retriever': retriever, 
        'prompt': prompt,
        'rag_chain': rag_chain
    }

# Components will be loaded lazily when first question is asked

@st.cache_resource
def get_rag_prompt():
    """
    Get the RAG prompt with caching to avoid repeated hub calls.
    """
    system_prompt = """Given the chat history and a recent user question \
generate a new standalone question \
that can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed or otherwise return it as is."""
    
    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

@st.cache_data
def format_docs(docs):
    """
    Format documents with caching for repeated document sets.
    """
    return "\n\n".join(doc.page_content for doc in docs)

# All components are now loaded lazily in get_lazy_components() function
# This eliminates the startup delay and improves performance

#for chunk in rag_chain.stream("What's the most important part of the Voynich manuscript?"):
#   print(chunk, end="", flush=True)




# Conversation history is now handled in get_rag_prompt() function




@st.cache_resource
def create_rag_chain(_llm, _retriever, _prompt):
    """
    Create the complete RAG chain with caching for better performance.
    The underscore prefix tells Streamlit not to hash these parameters.
    """
    # Create history-aware retriever
    retriever_with_history = create_history_aware_retriever(_llm, _retriever, _prompt)
    
    # QA system prompt
    qa_system_prompt = """You are an AI assistant designed to answer questions 
    using information retrieved from the Westlake High School website and PDF documents. 
    Your goal is to provide clear, helpful, and accurate answers based 
    only on the provided context. If the context does not contain the answer, 
    respond politely by saying: 'This chatbot is still in its development phase 
    and may not have information on that topic yet.' 
    
    ABBREVIATION HANDLING:
    - Common abbreviations like IT (Information Technology), AP (Advanced Placement), 
      NHS (National Honor Society), JV (Junior Varsity), etc. should be understood automatically
    - When you encounter abbreviations, consider both the abbreviated and full forms
    - If you're unsure about an abbreviation, ask for clarification naturally
    
    When referencing information from PDF documents, mention the source like: 
    "According to the [filename] document..." or "As stated in the [filename] PDF..."
    
    Use simple and easy-to-understand language. Provide detailed and informative answers, 
    but only include information that is relevant and necessary. Limit responses to a 
    maximum of 10 to 15 sentences, but do not extend the response unless the question 
    requires it. Keep answers as short as possible while still being clear and helpful. 
    Do not repeat the user's question or add unnecessary filler phrases. Focus on 
    delivering the most useful information in a straightforward way.

{context}"""

    
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    # Create the chains
    question_answer_chain = create_stuff_documents_chain(_llm, qa_prompt)
    return create_retrieval_chain(retriever_with_history, question_answer_chain)

# RAG chain is now created lazily in get_lazy_components() function

def smart_rerun():
    """Only rerun when necessary to prevent UI lag"""
    current_time = time.time()
    if current_time - st.session_state["last_rerun"] < 1.0:  # 1 second delay
        return False
    
    st.session_state["last_rerun"] = current_time
    st.rerun()
    return True

@st.cache_resource
def get_connection_pool():
    """Reuse HTTP connections for better performance"""
    import requests
    session = requests.Session()
    session.headers.update({'User-Agent': 'Westlake-Chatbot/1.0'})
    return session

def robust_ai_call(user_input, max_retries=3):
    """Enhanced AI call with abbreviation expansion and unknown term detection"""
    components = get_lazy_components()  # Load components when needed
    
    # Step 1: Check for unknown abbreviations first
    unknown_abbrevs = detect_unknown_abbreviations(user_input)
    if unknown_abbrevs:
        clarification_msg = get_clarification_message(unknown_abbrevs)
        return {"answer": clarification_msg}
    
    # Step 2: Expand known abbreviations for better semantic search
    expanded_input, found_abbreviations = expand_abbreviations(user_input)
    
    # Use expanded input for better retrieval
    search_input = expanded_input if found_abbreviations else user_input
    
    for attempt in range(max_retries):
        try:
            result = components['rag_chain'].invoke({
                "input": search_input, 
                "chat_history": st.session_state["chat_history"]
            })
            
            # If we expanded abbreviations, add a note about what we found
            if found_abbreviations and result.get("answer"):
                expanded_terms = ", ".join([f"{abbrev} ({full})" for abbrev, full in found_abbreviations])
                # Only add note if the response seems successful (not the "development phase" message)
                if "development phase" not in result["answer"].lower():
                    result["answer"] = f"{result['answer']}\n\n*Note: I interpreted {expanded_terms} in your question.*"
            
            return result
            
        except Exception as e:
            if attempt == max_retries - 1:
                return {"answer": f"Sorry, I'm having trouble right now. Please try again. (Error: {str(e)[:50]}...)"}
            time.sleep(1)  # Brief delay before retry

def stream_response(user_input):
    """Stream AI response for better perceived performance"""
    response_placeholder = st.empty()
    
    try:
        # Get AI response with error recovery
        ai_msg = robust_ai_call(user_input)
        full_response = ai_msg["answer"]
        
        # Simulate streaming effect
        displayed_response = ""
        for i, char in enumerate(full_response):
            displayed_response += char
            if i % 3 == 0:  # Update every 3 characters for smooth effect
                escaped_response = html.escape(displayed_response)
                response_placeholder.markdown(f"""
                <div class="ai-message">
                    
                    {escaped_response}▌
                    <div class="timestamp">{time.strftime("%I:%M %p")}</div>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(0.02)  # Small delay for streaming effect
        
        # Final display without cursor
        response_placeholder.empty()
        return full_response
        
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)[:100]}..."

def get_theme_css(dark_mode, westlake_theme):
    """
    Generate theme-specific CSS based on dark mode and westlake theme settings.
    """
    if westlake_theme:
        # Westlake Theme Colors
        if dark_mode:
            # Westlake Dark Theme - Deep Navy Blue, Muted Orange, Soft Gray
            return """
            body {
                background-color: #001F3D;
                color: #FFFFFF;
            }
            .main-header {
                background: #001F3D;
            }
            .chat-container {
                background: #001F3D;
                color: #FFFFFF;
            }
            .user-message {
                background: #FF8C42;
                color: #FFFFFF;
            }
            .ai-message {
                background: #001F3D;
                color: #FFFFFF;
                border: 1px solid #FF8C42;
            }
            .timestamp {
                color: #FFFFFF;
            }
            .welcome-container {
                background: #001F3D;
                border: 1px solid #FF8C42;
                color: #FFFFFF;
            }
            .welcome-container h2 {
                color: #FFFFFF;
            }
            .welcome-container p {
                color: #FFFFFF;
            }
            .stTextInput > div > div > input {
                background-color: #001F3D !important;
                color: #FFFFFF !important;
                border: 2px solid #FF8C42;
                caret-color: #FFFFFF !important;
            }
            
            .stTextArea > div > div > textarea {
                background-color: #001F3D !important;
                color: #FFFFFF !important;
                border: 2px solid #FF8C42;
                caret-color: #FFFFFF !important;
            }
            
            /* Westlake dark mode placeholder text */
            .stTextInput > div > div > input::placeholder {
                color: #FFFFFF !important;
                opacity: 0.7 !important;
            }
            
            .stTextArea > div > div > textarea::placeholder {
                color: #FFFFFF !important;
                opacity: 0.7 !important;
            }
            
            /* Westlake dark mode sidebar styling */
            .sidebar-info {
                background: #FF8C42 !important;
                color: #FFFFFF !important;
            }
            
            /* Westlake dark mode button styling */
            .stButton > button {
                background: #FF8C42 !important;
                color: #FFFFFF !important;
                border: none !important;
            }
            
            /* Force button text color */
            .stButton > button span {
                color: #FFFFFF !important;
            }
            
            /* Westlake dark mode sidebar background */
            .stSidebar > div {
                background: #001F3D !important;
            }
            
            /* Westlake dark mode sidebar text */
            .stSidebar .stMarkdown {
                color: #FFFFFF;
            }
            """
        else:
            # Westlake Light Theme - Blue & Orange
            return """
            body {
                background-color: #FFFFFF !important;
                color: #000000 !important;
            }
            .stApp {
                background-color: #FFFFFF !important;
            }
            .main-header {
                background: #003D73;
            }
            .chat-container {
                background: #FFFFFF;
            }
            .user-message {
                background: #FF6A13;
                color: #FFFFFF;
            }
            .ai-message {
                background: #003D73;
                color: #FFFFFF;
            }
            .timestamp {
                color: #003D73;
            }
            .welcome-container {
                background: #FFFFFF;
                border: 1px solid #003D73;
                color: #000000;
            }
            .welcome-container h2 {
                color: #000000;
            }
            .welcome-container p {
                color: #000000;
            }
            .stTextInput > div > div > input {
                border: 2px solid #FF6A13;
                background-color: #FFF4F0 !important;
                color: #003D73 !important;
                caret-color: #003D73 !important;
            }
            
            .stTextArea > div > div > textarea {
                border: 2px solid #FF6A13;
                background-color: #FFF4F0 !important;
                color: #003D73 !important;
                caret-color: #003D73 !important;
            }
            
            /* Westlake light mode placeholder text */
            .stTextInput > div > div > input::placeholder {
                color: #003D73 !important;
                opacity: 0.7 !important;
            }
            
            .stTextArea > div > div > textarea::placeholder {
                color: #003D73 !important;
                opacity: 0.7 !important;
            }
            
            /* Westlake light mode sidebar styling */
            .stSidebar > div {
                background: #003D73 !important;
            }
            .stSidebar .stMarkdown {
                color: #FFFFFF !important;
            }
            .sidebar-info {
                background: #003D73 !important;
                color: white !important;
            }
            
            /* Westlake light mode button styling */
            .stButton > button {
                background: #FF6A13 !important;
                color: #FFFFFF !important;
                border: none !important;
            }
            
            /* Force button text color */
            .stButton > button span {
                color: #FFFFFF !important;
            }
            """
    else:
        # Original Theme Colors
        if dark_mode:
            # Original Dark Theme - Deep Purples, Dark Blues, Violets, Dark Reds
            return """
            body {
                background-color: #1a0d2e;
                color: #e8e3f0;
            }
            .main-header {
                /* ORIGINAL GRADIENT (commented for easy restoration): linear-gradient(90deg, #2d1b69 0%, #0f0c29 50%, #2d1b69 100%); */
                background: #0f0c29;
            }
            .chat-container {
                background: #2a1f3d;
                color: #e8e3f0;
            }
            .user-message {
                background: linear-gradient(135deg, #4a148c 0%, #6a1b9a 50%, #8e24aa 100%);
            }
            .ai-message {
                background: linear-gradient(135deg, #1a237e 0%, #283593 50%, #3949ab 100%);
            }
            .timestamp {
                color: #b39ddb;
            }
            .welcome-container {
                background: #2a1f3d;
                border: 1px solid #4a148c;
                color: #e8e3f0;
            }
            .welcome-container h2 {
                color: #e8e3f0;
            }
            .welcome-container p {
                color: #d1c4e9;
            }
            .stTextInput > div > div > input {
                background-color: #3d2352 !important;
                color: #e8e3f0 !important;
                border: 2px solid #6a1b9a;
            }
            
            .stTextArea > div > div > textarea {
                background-color: #3d2352 !important;
                color: #e8e3f0 !important;
                border: 2px solid #6a1b9a;
            }
            
            /* Dark mode sidebar styling */
            .sidebar-info {
                background: linear-gradient(135deg, #4a148c 0%, #6a1b9a 50%, #8e24aa 100%) !important;
                color: #e8e3f0 !important;
            }
            
            /* Dark mode button styling */
            .stButton > button {
                background: linear-gradient(90deg, #4a148c 0%, #6a1b9a 50%, #8e24aa 100%) !important;
                color: #FFFFFF !important;
                border: none !important;
            }
            
            /* Force button text color */
            .stButton > button span {
                color: #FFFFFF !important;
            }
            
            /* Original dark mode sidebar background */
            .stSidebar > div {
                background: linear-gradient(180deg, #2d1b69 0%, #4a148c 50%, #6a1b9a 100%) !important;
            }
            
            /* Dark mode sidebar text */
            .stSidebar .stMarkdown {
                color: #e8e3f0;
            }
            """
            
            # COMMENTED OUT - Original Dark Theme (for easy restoration)
            # return """
            # body {
            #     background-color: #1E1E1E;
            #     color: #E0E0E0;
            # }
            # .main-header {
            #     background: linear-gradient(90deg, #4B6CB7 0%, #182848 100%);
            # }
            # .chat-container {
            #     background: #2D2D2D;
            #     color: #E0E0E0;
            # }
            # .user-message {
            #     background: linear-gradient(135deg, #4B6CB7 0%, #182848 100%);
            # }
            # .ai-message {
            #     background: linear-gradient(135deg, #614385 0%, #516395 100%);
            # }
            # .timestamp {
            #     color: #A0A0A0;
            # }
            # .welcome-container {
            #     background: #2D2D2D;
            #     border: 1px solid #3D3D3D;
            #     color: #E0E0E0;
            # }
            # .welcome-container h2 {
            #     color: #E0E0E0;
            # }
            # .welcome-container p {
            #     color: #C0C0C0;
            # }
            # .stTextInput > div > div > input {
            #     background-color: #4A4A4A !important;
            #     color: #FFFFFF !important;
            #     border: 2px solid #4B6CB7;
            # }
            # 
            # .stTextArea > div > div > textarea {
            #     background-color: #4A4A4A !important;
            #     color: #FFFFFF !important;
            #     border: 2px solid #4B6CB7;
            # }
            # 
            # /* Dark mode sidebar styling */
            # .sidebar-info {
            #     background: linear-gradient(135deg, #4B6CB7 0%, #182848 100%) !important;
            #     color: #E0E0E0 !important;
            # }
            # 
            # /* Dark mode button styling */
            # .stButton > button {
            #     background: linear-gradient(90deg, #4B6CB7 0%, #182848 100%) !important;
            #     color: #FFFFFF !important;
            #     border: none !important;
            # }
            # 
            # /* Force button text color */
            # .stButton > button span {
            #     color: #FFFFFF !important;
            # }
            # 
            # /* Original dark mode sidebar background */
            # .stSidebar > div {
            #     background: linear-gradient(180deg, #4B6CB7 0%, #182848 100%) !important;
            # }
            # 
            # /* Dark mode sidebar text */
            # .stSidebar .stMarkdown {
            #     color: #E0E0E0;
            # }
            # """
        else:
            # Original Light Theme - Vibrant Orange to Red Gradients
            return """
            body {
                background-color: #FFFFFF !important;
                color: #000000 !important;
            }
            .stApp {
                background-color: #FFFFFF !important;
            }
            .main-header {
                background: linear-gradient(90deg, #5dd4b8 0%, #0b556e 100%);
            }
            .chat-container {
                background: #FFFFFF;
            }
            .user-message {
                background: linear-gradient(135deg, #5dd4b8 0%, #0b556e 100%);
            }
            .ai-message {
                background: linear-gradient(135deg, #4db89e 0%, #1a6b7a 100%);
            }
            .timestamp {
                color: #0b556e;
            }
            .welcome-container {
                background: #FFFFFF;
                border: 1px solid #0b556e;
                color: #000000;
            }
            .welcome-container h2 {
                color: #000000;
            }
            .welcome-container p {
                color: #000000;
            }
            .stTextInput > div > div > input {
                border: 2px solid #0b556e; 
                background-color: #d4f4f0 !important;
                color: #000000 !important;
                caret-color: #000000 !important;
            }
            
            .stTextArea > div > div > textarea {
                border: 2px solid #0b556e;
                background-color: #d4f4f0 !important;
                color: #000000 !important;
                caret-color: #000000 !important;
            }
            
            /* Make placeholder text black for better visibility */
            .stTextInput > div > div > input::placeholder {
                color: #000000 !important;
                opacity: 0.7 !important;
            }
            
            .stTextArea > div > div > textarea::placeholder {
                color: #000000 !important;
                opacity: 0.7 !important;
            }
            
            /* Original light mode sidebar styling */
            .stSidebar > div {
                background: linear-gradient(180deg, #5dd4b8 0%, #0b556e 100%) !important;
            }
            .stSidebar .stMarkdown {
                color: #FFFFFF !important;
            }
            
            /* Force sidebar navigation text to be white - comprehensive approach */
            .stSidebar * {
                color: #FFFFFF !important;
            }
            
            /* Specific targeting for navigation elements */
            .stSidebar .stTabs button,
            .stSidebar .stTabs button *,
            .stSidebar [data-baseweb="tab-list"] button,
            .stSidebar [data-baseweb="tab-list"] button *,
            .stSidebar [data-baseweb="tab-list"] [role="tab"],
            .stSidebar [data-baseweb="tab-list"] [role="tab"] *,
            .stSidebar nav,
            .stSidebar nav *,
            .stSidebar .stSelectbox,
            .stSidebar .stSelectbox *,
            .stSidebar .stRadio,
            .stSidebar .stRadio *,
            .stSidebar .stCheckbox,
            .stSidebar .stCheckbox *,
            .stSidebar .stToggle,
            .stSidebar .stToggle *,
            .stSidebar label,
            .stSidebar label *,
            .stSidebar p,
            .stSidebar span,
            .stSidebar div {
                color: #FFFFFF !important;
            }
            
            /* Override any specific text color that might be set */
            .stSidebar [data-testid="stSidebar"] * {
                color: #FFFFFF !important;
            }
            .sidebar-info {
                background: linear-gradient(135deg, #5dd4b8 0%, #0b556e 100%) !important;
                color: white !important;
            }
            
            /* Light mode button styling */
            .stButton > button {
                background: linear-gradient(90deg, #5dd4b8 0%, #0b556e 100%) !important;
                color: #FFFFFF !important;
                border: none !important;
            }
            
            /* Force button text color */
            .stButton > button span {
                color: #FFFFFF !important;
            }
            """




def add_custom_css():
    """
    Add custom CSS with proper theme switching for all elements.
    """
    # Get theme CSS based on current mode (no caching to allow theme switching)
    theme_css = get_theme_css(st.session_state["dark_mode"], st.session_state["westlake_theme"])
    
    st.markdown(f"""
    <style>
    /* Base styles that apply to both themes */
    .main-header {{
        padding: 1.2rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        text-align: center;
        color: white;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }}
    
    .chat-container {{
        border-radius: 15px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    
    .user-message {{
        color: white;
        padding: 1rem;
        border-radius: 15px 15px 5px 15px;
        margin: 0.5rem 0 2rem 0;
        margin-left: 20%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        position: relative;
    }}
    
    .ai-message {{
        color: white;
        padding: 1rem;
        border-radius: 15px 15px 15px 5px;
        margin: 0.5rem 0 2.5rem 0;
        margin-left: 0;
        margin-right: 20%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        position: relative;
    }}
    
    .timestamp {{
        font-size: 0.7rem;
        position: absolute;
        bottom: 5px;
        right: 10px;
        opacity: 0.8;
    }}
    
    .stTextInput > div > div > input {{
        border-radius: 25px;
        padding: 0.5rem 1rem;
        font-size: 16px;
    }}
    
    .stTextArea > div > div > textarea {{
        border-radius: 15px;
        padding: 0.75rem 1rem;
        font-size: 16px;
        resize: none;
        font-family: inherit;
    }}
    
    .stButton > button {{
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 25px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }}
    
    .sidebar-info {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }}
    
    .typing-indicator {{
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #667eea;
        animation: typing 1.4s infinite ease-in-out;
        margin: 0 2px;
    }}
    
    .typing-indicator:nth-child(1) {{ animation-delay: -0.32s; }}
    .typing-indicator:nth-child(2) {{ animation-delay: -0.16s; }}
    
    @keyframes typing {{
        0%, 80%, 100% {{ transform: scale(0); opacity: 0.5; }}
        40% {{ transform: scale(1); opacity: 1; }}
    }}
    
    .welcome-container {{
        border-radius: 15px;
        padding: 2rem;
        margin-top: 2rem;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        animation: fadeIn 1s ease-in-out;
    }}
    
    .welcome-icon {{
        font-size: 4rem;
        margin-bottom: 1rem;
        animation: pulse 2s infinite;
    }}
    
    .example-question {{
        display: inline-block;
        margin: 0.3rem;
        padding: 0.5rem 1rem;
        background: rgba(102, 126, 234, 0.1);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 20px;
        cursor: pointer;
        transition: all 0.3s ease;
    }}
    
    .example-question:hover {{
        background: rgba(102, 126, 234, 0.2);
        transform: translateY(-2px);
    }}
    
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    @keyframes pulse {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.1); }}
        100% {{ transform: scale(1); }}
    }}
    
    .theme-toggle {{
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 1rem;
    }}
    
    .theme-toggle span {{
        margin: 0 0.5rem;
    }}
    
    /* Keyboard shortcut hints */
    .shortcut-hints {{
        font-size: 0.75rem;
        color: #888;
        margin-top: 0.25rem;
        text-align: center;
        opacity: 0.7;
    }}
    
    /* Theme-specific styles */
    {theme_css}
    </style>
    

    """, unsafe_allow_html=True)

def display_chat_message(message, is_user=True, timestamp=None):
    
    # Generate timestamp if not provided
    if timestamp is None:
        timestamp = time.strftime("%I:%M %p")
    
    # Escape HTML in user messages to prevent HTML injection
    if is_user:
        escaped_message = html.escape(str(message))
    else:
        escaped_message = html.escape(str(message))  # Escape AI responses to prevent HTML interference
        
    if is_user:
        st.markdown(f"""
        <div class="user-message">
            {escaped_message}
            <div class="timestamp">{timestamp}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="ai-message">
            {escaped_message}
            <div class="timestamp">{timestamp}</div>
        </div>
        """, unsafe_allow_html=True)

def main():
    initialize_session_state()
    add_custom_css()
    
    # Initialize connection pool for better performance
    connection_pool = get_connection_pool()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1 style="margin-bottom: 8px; text-align: center; width: 100%; display: block; color: white;">⛰️ Westlake AI Assistant</h1>
        <h2 style="font-size: 1.4rem; margin: 8px 0 8px 0; text-align: center; width: 100%; display: block; color: white;">Developed by Aarush Rajkumar</h2>
        <p style="margin-top: 8px; text-align: center; width: 100%; display: block; line-height: 1.4; max-width: 600px; margin-left: auto; margin-right: auto; color: white;">Your intelligent companion for exploring website content</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        # Theme toggle
        st.markdown("""
        <div class="theme-toggle">
            <h3>🎨 Appearance</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Dark Mode Toggle
        col1, col2 = st.columns([1.2, 1.8])
        with col1:
            st.markdown("**Mode:**")
        with col2:
            # Use the toggle with a key that triggers rerun
            dark_mode = st.toggle("Dark Mode", value=st.session_state["dark_mode"], key="dark_mode_toggle")
            # Update session state if toggle changed
            if dark_mode != st.session_state["dark_mode"]:
                st.session_state["dark_mode"] = dark_mode
                st.rerun()  # Immediately refresh to apply theme changes
        
        # Westlake Theme Toggle
        col3, col4 = st.columns([1.2, 1.8])
        with col3:
            st.markdown("**Style:**")
        with col4:
            # Westlake theme toggle
            westlake_theme = st.toggle("Westlake Theme", value=st.session_state["westlake_theme"], key="westlake_theme_toggle")
            # Update session state if toggle changed
            if westlake_theme != st.session_state["westlake_theme"]:
                st.session_state["westlake_theme"] = westlake_theme
                st.rerun()  # Immediately refresh to apply theme changes
        
        st.markdown("""
        <div class="sidebar-info">
            <h3>🚀 Features</h3>
            <ul>
                <li>🔍 Smart content search</li>
                <li>💬 Conversational AI</li>
                <li>📚 Context-aware responses</li>
                <li>🧠 Memory of chat history</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Database status indicator
        if db is not None:
            try:
                vector_count = db.index.ntotal if hasattr(db, 'index') else 0
                st.markdown(f"""
                <div class="sidebar-info">
                    <h3>📊 Database Status</h3>
                    <p>✅ Loaded: {vector_count:,} vectors</p>
                    <p>📄 School data ready</p>
                </div>
                """, unsafe_allow_html=True)
            except:
                st.markdown("""
                <div class="sidebar-info">
                    <h3>📊 Database Status</h3>
                    <p>⚠️ Database loaded but status unclear</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="sidebar-info">
                <h3>📊 Database Status</h3>
                <p>❌ Database not loaded</p>
                <p>⚠️ Responses may be generic</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Add specific styling for clear chat history button in Westlake theme
        if st.session_state.get("westlake_theme", False) and not st.session_state.get("dark_mode", True):
            st.markdown("""
            <style>
            /* Clear chat history button - solid orange for Westlake light theme */
            div[data-testid="stSidebar"] .stButton > button {
                background: #FF6A13 !important;
                border: none !important;
                color: white !important;
            }
            div[data-testid="stSidebar"] .stButton > button:hover {
                background: #E55A0F !important;
                transform: translateY(-1px) !important;
            }
            </style>
            """, unsafe_allow_html=True)
        
        if st.button("🗑️ Clear Chat History"):
            st.session_state["chat_history"] = []
            st.session_state["messages"] = []
            st.session_state["processed_messages"] = set()
            st.rerun()
        
        st.markdown("---")
        st.markdown("**💡 Tips:**")
        st.markdown("• Ask specific questions about the website")
        st.markdown("• Reference previous messages in conversation")
        st.markdown("• Try asking for summaries or explanations")
    
    # Add CSS for chat layout with fixed input at bottom
    st.markdown("""
    <style>
    /* Chat container styling */
    .chat-messages-container {
        max-height: 60vh;
        overflow-y: auto;
        padding: 1rem;
        margin-bottom: 0;
        border-radius: 10px;
        background: rgba(0,0,0,0.02);
    }
    
    /* Input area directly in flow */
    .input-container {
        background: white;
        padding: 0.5rem 0;
        border-top: 1px solid #e0e0e0;
        margin-top: 0;
    }
    
    /* Style the button */
    .stButton button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 25px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: bold;
        font-size: 18px;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Style the input field */
    .stTextArea > div > div > textarea {
        border-radius: 15px;
        padding: 0.75rem 1rem;
        font-size: 16px;
        resize: none;
        font-family: inherit;
        border: 2px solid #e0e0e0;
    }
    
    .stTextArea > div > div > textarea:focus {
        outline: none !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3) !important;
        border: 2px solid #667eea !important;
    }
    
    /* Normal padding since input is in flow */
    .main .block-container {
        padding-bottom: 20px;
    }
    
    /* Auto-scroll to bottom */
    .chat-messages-container {
        scroll-behavior: smooth;
    }
    
    /* ORIGINAL WORKING BUTTON APPROACH - RESTORED */
    
    /* Ensure consistent height and alignment */
    .stButton button {
        height: 68px !important;  /* Match text area height */
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 18px !important;  /* Force larger font size */
        color: #FFFFFF !important;
        border: none !important;
    }
    
    /* Force button text to be white */
    .stButton button span {
        color: #FFFFFF !important;
    }
    
    /* Align button with text area */
    div[data-testid="column"]:nth-child(2) .stButton {
        margin-top: 0px;
    }
    
    /* Force larger font size for all buttons with more specific selectors */
    .stButton > button {
        font-size: 18px !important;
    }
    
    button[kind="primary"] {
        font-size: 18px !important;
    }
    
    button[data-testid="baseButton-primary"] {
        font-size: 18px !important;
    }
    
    /* Target recommendation buttons specifically */
    div[data-testid="column"] .stButton button {
        font-size: 18px !important;
        font-weight: bold !important;
    }
    
    /* Remove button fade animation and make them disappear immediately */
    .stButton button {
        transition: none !important;
        animation: none !important;
    }
    
    /* Ensure buttons are fully clickable */
    .stButton {
        width: 100% !important;
    }
    
    .stButton button {
        width: 100% !important;
        height: auto !important;
        min-height: 50px !important;
        padding: 12px 16px !important;
        white-space: normal !important;
        word-wrap: break-word !important;
        text-align: center !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    /* Better header text alignment */
    .main-header h1, .main-header h2, .main-header p {
        text-align: center !important;
        width: 100% !important;
        margin-left: auto !important;
        margin-right: auto !important;
        display: block !important;
        clear: both !important;
    }
    
    .main-header {
        text-align: center !important;
        width: 100% !important;
        display: block !important;
        overflow: hidden !important;
    }
    
    .main-header p {
        max-width: 600px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding: 0 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create main chat area container
    chat_container = st.container()
    
    # Create thinking indicator area (define early so it can be used anywhere)
    thinking_placeholder = st.empty()
    
    with chat_container:
        # Example questions for new users (show at top)
        show_recommendations = (
            len(st.session_state.get("messages", [])) == 0 and 
            not st.session_state.get("hide_recommendations", False) and
            not st.session_state.get("pending_question")
        )
        
        if show_recommendations:
            # Create a container for recommendations that can be cleared
            recommendations_container = st.container()
            
            with recommendations_container:
                st.markdown("""
                <p style='text-align: center; margin: 20px 0;'>
                    I can help you find information about Westlake High School. Try one of these questions to get started:
                </p>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Use direct button text instead of overlay approach
                    if st.button("Tell me about Westlake High School", key="q1", use_container_width=True):
                        st.session_state["pending_question"] = "Tell me about Westlake High School"
                        st.rerun()
                    
                    if st.button("What programs does Westlake offer?", key="q3", use_container_width=True):
                        st.session_state["pending_question"] = "What academic programs does Westlake High School offer?"
                        st.rerun()
                
                with col2:
                    if st.button("How do I contact Westlake?", key="q2", use_container_width=True):
                        st.session_state["pending_question"] = "How can I contact Westlake High School?"
                        st.rerun()
                    
                    if st.button("What extracurricular activities are available?", key="q4", use_container_width=True):
                        st.session_state["pending_question"] = "What extracurricular activities and clubs are available at Westlake High School?"
                        st.rerun()
        
        # Display chat messages in scrollable container
        if st.session_state["messages"]:
            # Create scrollable messages container
            with st.container():
                st.markdown('<div class="chat-messages-container">', unsafe_allow_html=True)
                
                messages_to_show = st.session_state["messages"]
                
                # Display all messages including streaming ones in their final position
                for i, msg in enumerate(messages_to_show):
                    if (i == len(messages_to_show) - 1 and 
                        not msg["is_user"] and 
                        "show_streaming" in st.session_state and 
                        st.session_state["show_streaming"]):
                        
                        # This is the last AI message and we should stream it
                        response_text = st.session_state["streaming_response"]
                        response_placeholder = st.empty()
                        
                        displayed_response = ""
                        for j, char in enumerate(response_text):
                            displayed_response += char
                            if j % 3 == 0:  # Update every 3 characters
                                escaped_response = html.escape(displayed_response)
                                response_placeholder.markdown(f"""
                                <div class="ai-message">
                                    {escaped_response}▌
                                    <div class="timestamp">{time.strftime("%I:%M %p")}</div>
                                </div>
                                """, unsafe_allow_html=True)
                                time.sleep(0.02)  # Small delay for streaming effect
                        
                        # Final display without cursor
                        escaped_final_response = html.escape(displayed_response)
                        response_placeholder.markdown(f"""
                        <div class="ai-message">
                            {escaped_final_response}
                            <div class="timestamp">{time.strftime("%I:%M %p")}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Clear streaming flags
                        st.session_state["show_streaming"] = False
                        st.session_state["streaming_response"] = None
                        
                    else:
                        # Normal message display
                        display_chat_message(msg["content"], msg["is_user"])
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Handle pending question from recommendation buttons
    if "pending_question" in st.session_state and st.session_state["pending_question"]:
        question = st.session_state["pending_question"]
        st.session_state["pending_question"] = None  # Clear the pending question immediately
        
        # Process the question directly without additional reruns
        # Add user message
        st.session_state["messages"].append({"content": question, "is_user": True})
        
        # Hide recommendations now that we have a conversation
        st.session_state["hide_recommendations"] = True
        
        # Process AI response immediately
        with st.spinner("Thinking..."):
            ai_msg = robust_ai_call(question)
            full_response = ai_msg["answer"]
            
            # Add AI response
            st.session_state["messages"].append({"content": full_response, "is_user": False})
            
            # Update chat history for context
            st.session_state["chat_history"].append(HumanMessage(content=question))
            st.session_state["chat_history"].append(ai_msg["answer"])
            
            # Optimize session state
            optimize_session_state()
        
        # Single rerun to show the complete conversation
        st.rerun()
    
    # Create input container that stays visible (minimal spacing)
    with st.container():
        # Check if we're currently processing
        is_processing = st.session_state.get("show_streaming", False)
        
        # Add CSS to reduce spacing above text input
        st.markdown("""
        <style>
        /* Reduce spacing above text input */
        .stForm {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        
        .stTextArea {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        
        /* Reduce container spacing */
        .stContainer {
            padding-top: 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Input form with stable key to prevent duplication
        with st.form(key="chat_form", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            
            with col1:
                if is_processing:
                    # Show disabled input during processing
                    st.text_area(
                        "", 
                        value="Processing your message...",
                        height=68,
                        key="user_input_disabled",
                        disabled=True
                    )
                    user_input = ""
                else:
                    # Show normal input when ready
                    user_input = st.text_area(
                        "", 
                        placeholder="💭 Ask me anything about the website...",
                        height=68,  # Minimum allowed height
                        key="user_input"
                    )
            
            with col2:
                # Better alignment for send button (RESTORED)
                st.markdown('<div style="height: 28px;"></div>', unsafe_allow_html=True)
                if is_processing:
                    # Show disabled button during processing
                    st.form_submit_button("⏳ Processing...", use_container_width=True, disabled=True)
                    send_button = False
                else:
                    # Show normal button when ready
                    send_button = st.form_submit_button("🚀 Send", use_container_width=True)
    
    # Handle user input from text box
    if send_button and user_input.strip() and not is_processing:
        # Mark user as no longer first-time
        st.session_state["first_time_user"] = False
        
        # Clean input
        clean_input = str(user_input).strip()
        
        # Add user message to display FIRST (like real messaging)
        st.session_state["messages"].append({"content": clean_input, "is_user": True})
        
        # Hide recommendations now that we have a conversation
        st.session_state["hide_recommendations"] = True
        
        # Clear any form-related flags to prevent duplication
        st.session_state["form_submitted"] = True
        
        # Process AI response immediately
        with st.spinner("Thinking..."):
            ai_msg = robust_ai_call(clean_input)
            full_response = ai_msg["answer"]
            
            # Add AI response
            st.session_state["messages"].append({"content": full_response, "is_user": False})
            
            # Update chat history for context
            st.session_state["chat_history"].append(HumanMessage(content=clean_input))
            st.session_state["chat_history"].append(ai_msg["answer"])
            
            # Optimize session state
            optimize_session_state()
        
        # Single rerun to show the complete conversation
        st.rerun()
        
        # Update chat history for context
        st.session_state["chat_history"].extend([HumanMessage(content=user_question), ai_response])
        
        # Set flag to show streaming animation for the last message
        st.session_state["show_streaming"] = True
        st.session_state["streaming_response"] = ai_response
        
        # Optimize session state to prevent memory issues
        optimize_session_state()
        
        # Rerun to show AI response with streaming
        st.rerun()
    
    # Show keyboard shortcuts
    st.markdown("""
    <div style="text-align: center; margin-top: 10px; color: #666; font-size: 0.8rem;">
        💡 <strong>Ctrl+Enter</strong> sends your message • <strong>Shift+Enter</strong> adds a new line
    </div>
    """, unsafe_allow_html=True)
    
    # Force button styling and immediate hiding behavior
    st.markdown("""
    <script>
    function forceButtonStyling() {
        // Try multiple selectors
        var selectors = [
            '.stButton button',
            'button[kind="primary"]',
            'button[data-testid="baseButton-primary"]',
            'button',
            '.stButton > button'
        ];
        
        selectors.forEach(function(selector) {
            var buttons = document.querySelectorAll(selector);
            buttons.forEach(function(button) {
                button.style.fontSize = '18px !important';
                button.style.fontWeight = 'bold !important';
                button.style.setProperty('font-size', '18px', 'important');
                
                // Remove any transition/animation effects
                button.style.transition = 'none !important';
                button.style.animation = 'none !important';
                
                // Make buttons fully clickable
                button.style.width = '100%';
                button.style.height = 'auto';
                button.style.minHeight = '50px';
                button.style.padding = '12px 16px';
                button.style.whiteSpace = 'normal';
                button.style.wordWrap = 'break-word';
                button.style.textAlign = 'center';
                button.style.display = 'flex';
                button.style.alignItems = 'center';
                button.style.justifyContent = 'center';
            });
        });
    }
    
    function hideRecommendationButtons() {
        // Find recommendation buttons and hide their container immediately
        var buttons = document.querySelectorAll('button');
        buttons.forEach(function(button) {
            if (button.textContent.includes('Tell me about Westlake') || 
                button.textContent.includes('What programs') ||
                button.textContent.includes('How do I contact') ||
                button.textContent.includes('What extracurricular')) {
                
                button.addEventListener('click', function() {
                    // Hide the entire recommendations section immediately
                    var container = button.closest('.stContainer');
                    if (container) {
                        container.style.display = 'none';
                    }
                    
                    // Also try to hide parent containers
                    var parent = button.closest('div[data-testid="column"]');
                    if (parent) {
                        var grandParent = parent.closest('.row-widget');
                        if (grandParent) {
                            grandParent.style.display = 'none';
                        }
                    }
                });
            }
        });
    }
    
    // Run immediately
    forceButtonStyling();
    hideRecommendationButtons();
    
    // Run after delays
    setTimeout(function() {
        forceButtonStyling();
        hideRecommendationButtons();
    }, 100);
    setTimeout(function() {
        forceButtonStyling();
        hideRecommendationButtons();
    }, 500);
    setTimeout(function() {
        forceButtonStyling();
        hideRecommendationButtons();
    }, 1000);
    
    // Run on any DOM changes
    var observer = new MutationObserver(function() {
        forceButtonStyling();
        hideRecommendationButtons();
    });
    observer.observe(document.body, { childList: true, subtree: true });
    
    // Auto-scroll for messages
    setTimeout(function() {
        var chatContainer = document.querySelector('.chat-messages-container');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }, 100);
    </script>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()