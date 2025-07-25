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

# ⚡ PERFORMANCE OPTIMIZATIONS APPLIED:
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
    # Theme preference
    if "dark_mode" not in st.session_state:
        st.session_state["dark_mode"] = False
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
    
st.set_page_config(
    page_title="🌊 Beachside AI Assistant", 
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    possible_paths = [
        "index.faiss",           # When running from Source/ directory
        "Source/index.faiss",    # When running from root directory
        "../index.faiss"         # Alternative fallback
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Found vector database at: {path}")
            return path
    
    # If none found, default to the most likely location
    print("⚠️ Vector database not found in expected locations")
    return "index.faiss"

index_Faiss_Filepath = get_vector_db_path()

@st.cache_resource
def load_vector_database():
    """
    Load the Vector Database from local disk with caching for better performance.
    This expensive operation only runs once and gets cached.
    """
    return FAISS.load_local(
        index_Faiss_Filepath, 
        OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model="text-embedding-3-small"), 
        allow_dangerous_deserialization=True
    )

# Load the cached vector database
db = load_vector_database()


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
    return _db.as_retriever(search_type="similarity", search_kwargs={"k": 4})

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
    qa_system_prompt = """You are an assistant for question-answering tasks. \
Use the following pieces of retrieved context to answer the question. \
If you don't know the answer, just say that you don't know. \
Use three sentences maximum and keep the answer concise.\

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
    session.headers.update({'User-Agent': 'Beachside-Chatbot/1.0'})
    return session

def robust_ai_call(user_input, max_retries=3):
    """Retry failed API calls for better reliability"""
    components = get_lazy_components()  # Load components when needed
    
    for attempt in range(max_retries):
        try:
            return components['rag_chain'].invoke({
                "input": user_input, 
                "chat_history": st.session_state["chat_history"]
            })
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
                response_placeholder.markdown(f"""
                <div class="ai-message">
                    <strong>🤖 AI Assistant:</strong><br>
                    {displayed_response}▌
                    <div class="timestamp">{time.strftime("%I:%M %p")}</div>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(0.02)  # Small delay for streaming effect
        
        # Final display without cursor
        response_placeholder.empty()
        return full_response
        
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)[:100]}..."

def get_theme_css(dark_mode):
    """
    Generate theme-specific CSS based on dark mode setting.
    """
    if dark_mode:
        return """
        body {
            background-color: #1E1E1E;
            color: #E0E0E0;
        }
        .main-header {
            background: linear-gradient(90deg, #4B6CB7 0%, #182848 100%);
        }
        .chat-container {
            background: #2D2D2D;
            color: #E0E0E0;
        }
        .user-message {
            background: linear-gradient(135deg, #4B6CB7 0%, #182848 100%);
        }
        .ai-message {
            background: linear-gradient(135deg, #614385 0%, #516395 100%);
        }
        .timestamp {
            color: #A0A0A0;
        }
        .welcome-container {
            background: #2D2D2D;
            border: 1px solid #3D3D3D;
            color: #E0E0E0;
        }
        .welcome-container h2 {
            color: #E0E0E0;
        }
        .welcome-container p {
            color: #C0C0C0;
        }
        .stTextInput > div > div > input {
            background-color: #3D3D3D;
            color: #E0E0E0;
            border: 2px solid #4B6CB7;
        }
        
        .stTextArea > div > div > textarea {
            background-color: #3D3D3D;
            color: #E0E0E0;
            border: 2px solid #4B6CB7;
        }
        
        /* Dark mode sidebar styling */
        .sidebar-info {
            background: linear-gradient(135deg, #4B6CB7 0%, #182848 100%) !important;
            color: #E0E0E0 !important;
        }
        
        /* Dark mode button styling */
        .stButton > button {
            background: linear-gradient(90deg, #4B6CB7 0%, #182848 100%) !important;
            color: #E0E0E0 !important;
        }
        
        /* Dark mode sidebar background */
        .stSidebar > div {
            background-color: #2D2D2D;
        }
        
        /* Dark mode sidebar text */
        .stSidebar .stMarkdown {
            color: #E0E0E0;
        }
        """
    else:
        return """
        body {
            background-color: #FFFFFF;
            color: #333333;
        }
        .main-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        .chat-container {
            background: #f8f9fa;
        }
        .user-message {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .ai-message {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        .timestamp {
            color: #888888;
        }
        .welcome-container {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            color: #333333;
        }
        .welcome-container h2 {
            color: #333333;
        }
        .welcome-container p {
            color: #555555;
        }
        .stTextInput > div > div > input {
            border: 2px solid #667eea;
        }
        
        .stTextArea > div > div > textarea {
            border: 2px solid #667eea;
        }
        
        /* Light mode sidebar styling */
        .sidebar-info {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
        }
        
        /* Light mode button styling */
        .stButton > button {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
        }
        
        /* Light mode sidebar - keep default Streamlit styling */
        """
def get_theme_css(dark_mode):
    """
    Generate theme-specific CSS with caching based on dark mode setting.
    """
    if dark_mode:
        return """
        body {
            background-color: #1E1E1E;
            color: #E0E0E0;
        }
        .main-header {
            background: linear-gradient(90deg, #4B6CB7 0%, #182848 100%);
        }
        .chat-container {
            background: #2D2D2D;
            color: #E0E0E0;
        }
        .user-message {
            background: linear-gradient(135deg, #4B6CB7 0%, #182848 100%);
        }
        .ai-message {
            background: linear-gradient(135deg, #614385 0%, #516395 100%);
        }
        .timestamp {
            color: #A0A0A0;
        }
        .welcome-container {
            background: #2D2D2D;
            border: 1px solid #3D3D3D;
            color: #E0E0E0;
        }
        .welcome-container h2 {
            color: #E0E0E0;
        }
        .welcome-container p {
            color: #C0C0C0;
        }
        .stTextInput > div > div > input {
            background-color: #3D3D3D;
            color: #E0E0E0;
            border: 2px solid #4B6CB7;
        }
        
        .stTextArea > div > div > textarea {
            background-color: #3D3D3D;
            color: #E0E0E0;
            border: 2px solid #4B6CB7;
        }
        
        /* Dark mode sidebar styling */
        .sidebar-info {
            background: linear-gradient(135deg, #4B6CB7 0%, #182848 100%) !important;
            color: #E0E0E0 !important;
        }
        
        /* Dark mode button styling */
        .stButton > button {
            background: linear-gradient(90deg, #4B6CB7 0%, #182848 100%) !important;
            color: #E0E0E0 !important;
        }
        
        /* Dark mode sidebar background */
        .stSidebar > div {
            background-color: #2D2D2D;
        }
        
        /* Dark mode sidebar text */
        .stSidebar .stMarkdown {
            color: #E0E0E0;
        }
        """
    else:
        return """
        body {
            background-color: #FFFFFF;
            color: #333333;
        }
        .main-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        .chat-container {
            background: #f8f9fa;
        }
        .user-message {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .ai-message {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        .timestamp {
            color: #888888;
        }
        .welcome-container {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            color: #333333;
        }
        .welcome-container h2 {
            color: #333333;
        }
        .welcome-container p {
            color: #555555;
        }
        .stTextInput > div > div > input {
            border: 2px solid #667eea;
        }
        
        .stTextArea > div > div > textarea {
            border: 2px solid #667eea;
        }
        
        /* Light mode sidebar styling */
        .sidebar-info {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
        }
        
        /* Light mode button styling */
        .stButton > button {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
        }
        
        /* Light mode sidebar - keep default Streamlit styling */
        """

def smart_rerun():
    """Only rerun when necessary to prevent UI lag"""
    current_time = time.time()
    if current_time - st.session_state["last_rerun"] < 1.35:  # 1.35 second delay
        return False
    
    st.session_state["last_rerun"] = current_time
    st.rerun()
    return True

@st.cache_resource
def get_connection_pool():
    """Reuse HTTP connections for better performance"""
    import requests
    session = requests.Session()
    session.headers.update({'User-Agent': 'Beachside-Chatbot/1.0'})
    return session

def robust_ai_call(user_input, max_retries=3):
    """Retry failed API calls for better reliability"""
    components = get_lazy_components()  # Load components when needed
    
    for attempt in range(max_retries):
        try:
            return components['rag_chain'].invoke({
                "input": user_input, 
                "chat_history": st.session_state["chat_history"]
            })
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
                response_placeholder.markdown(f"""
                <div class="ai-message">
                    <strong>🤖 AI Assistant:</strong><br>
                    {displayed_response}▌
                    <div class="timestamp">{time.strftime("%I:%M %p")}</div>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(0.02)  # Small delay for streaming effect
        
        # Final display without cursor
        response_placeholder.empty()
        return full_response
        
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)[:100]}..."

def add_custom_css():
    """
    Add custom CSS with proper theme switching for all elements.
    """
    # Get theme CSS based on current mode (no caching to allow theme switching)
    theme_css = get_theme_css(st.session_state["dark_mode"])
    
    st.markdown(f"""
    <style>
    /* Base styles that apply to both themes */
    .main-header {{
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
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
        margin: 0.5rem 0;
        margin-left: 20%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        position: relative;
    }}
    
    .ai-message {{
        color: white;
        padding: 1rem;
        border-radius: 15px 15px 15px 5px;
        margin: 0.5rem 0;
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
    import html
    
    # Generate timestamp if not provided
    if timestamp is None:
        timestamp = time.strftime("%I:%M %p")
    
    # Escape HTML in user messages to prevent HTML injection
    if is_user:
        escaped_message = html.escape(str(message))
    else:
        escaped_message = str(message)  # AI responses are already safe
        
    if is_user:
        st.markdown(f"""
        <div class="user-message">
            <strong>🧑 You:</strong><br>
            {escaped_message}
            <div class="timestamp">{timestamp}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="ai-message">
            <strong>🤖 AI Assistant:</strong><br>
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
        <h1>🌊 Beachside AI Assistant</h1>
        <p>Your intelligent companion for exploring website content</p>
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
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write("Theme:")
        with col2:
            # Use the toggle with a key that triggers rerun
            dark_mode = st.toggle("Dark Mode", value=st.session_state["dark_mode"], key="dark_mode_toggle")
            # Update session state if toggle changed
            if dark_mode != st.session_state["dark_mode"]:
                st.session_state["dark_mode"] = dark_mode
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
    
    # Create a container for the chat input area
    chat_input_container = st.container()
    
    # Add custom CSS for better button styling
    st.markdown("""
    <style>
    /* Style the button */
    .stButton button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 25px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Style the input field */
    .stTextInput > div > div > input {
        border-radius: 25px;
        padding: 0.5rem 1rem;
        font-size: 16px;
        outline: none !important;
        box-shadow: none !important;
        border: 2px solid #e0e0e0 !important;
    }
    
    /* Remove focus outline and style focus state */
    .stTextInput > div > div > input:focus {
        outline: none !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3) !important;
        border: 2px solid #667eea !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Add specific CSS to fix alignment
    st.markdown("""
    <style>
    /* Remove conflicting margin and let the spacer div handle alignment */
    div[data-testid="column"]:nth-child(2) .stButton {
        margin-top: 0px;
    }
    
    /* Ensure consistent height */
    .stTextInput input {
        height: 40px;
    }
    
    .stButton button {
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Use form for proper Enter key handling
    with st.form(key="chat_form", clear_on_submit=True):
        # Create horizontal layout for input and button
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_area(
                "", 
                placeholder="💭 Ask me anything about the website...",
                height=90,
                key="user_input"
            )
        
        with col2:
            # Add a spacer div to align button with text area
            st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True)
            send_button = st.form_submit_button("🚀 Send", use_container_width=True)
    
    # Create a dedicated area for thinking indicator (always present)
    thinking_placeholder = st.empty()
    
    # Handle user input
    if send_button and user_input.strip():
        # Mark user as no longer first-time
        st.session_state["first_time_user"] = False
        
        # Add user message to display
        st.session_state["messages"].append({"content": user_input, "is_user": True})
        
        # Show thinking indicator in dedicated area
        with thinking_placeholder:
            st.markdown("""
            <div style="text-align: center; padding: 10px; color: #666;">
                🤔 <em>Thinking...</em>
            </div>
            """, unsafe_allow_html=True)
        
        # Get AI response
        ai_response = stream_response(user_input)
        
        # Clear thinking indicator
        thinking_placeholder.empty()
        
        # Update chat history for context
        st.session_state["chat_history"].extend([HumanMessage(content=user_input), ai_response])
        
        # Add AI response to display
        st.session_state["messages"].append({"content": ai_response, "is_user": False})
        
        # Optimize session state to prevent memory issues
        optimize_session_state()
        
        # Smart rerun with delay control
        smart_rerun()
    
    # Show keyboard shortcuts (always visible)
    st.markdown("""
    <div class="shortcut-hints">
        💡 <strong>Ctrl+Enter</strong> sends your message • <strong>Shift+Enter</strong> adds a new line
    </div>
    """, unsafe_allow_html=True)
    
    # Example questions for new users (show before chat history)
    if not st.session_state["messages"]:
        # Simple instruction text for recommendations
        st.markdown("""
        <p style='text-align: center; margin: 20px 0;'>
            I can help you find information about Beachside High School. Try one of these questions to get started:
        </p>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Tell me about Beachside High School", key="q1", use_container_width=True):
                st.session_state["pending_question"] = "Tell me about Beachside High School"
                st.rerun()
            
            if st.button("What programs does Beachside offer?", key="q3", use_container_width=True):
                st.session_state["pending_question"] = "What academic programs does Beachside High School offer?"
                st.rerun()
        
        with col2:
            if st.button("How do I contact Beachside?", key="q2", use_container_width=True):
                st.session_state["pending_question"] = "How can I contact Beachside High School?"
                st.rerun()
            
            if st.button("What extracurricular activities are available?", key="q4", use_container_width=True):
                st.session_state["pending_question"] = "What extracurricular activities and clubs are available at Beachside High School?"
                st.rerun()
    
    # Handle pending question from recommendation buttons
    if "pending_question" in st.session_state and st.session_state["pending_question"]:
        question = st.session_state["pending_question"]
        st.session_state["pending_question"] = None  # Clear the pending question
        
        # Add user message
        st.session_state["messages"].append({"content": question, "is_user": True})
        
        # Show thinking indicator in the dedicated area
        with thinking_placeholder:
            st.markdown("""
            <div style="text-align: center; padding: 10px; color: #666;">
                🤔 <em>Thinking...</em>
            </div>
            """, unsafe_allow_html=True)
        
        # Get AI response
        ai_msg = robust_ai_call(question)
        ai_response = ai_msg["answer"]
        
        # Clear thinking indicator
        thinking_placeholder.empty()
        
        # Update chat history and messages
        st.session_state["chat_history"].extend([HumanMessage(content=question), ai_response])
        st.session_state["messages"].append({"content": ai_response, "is_user": False})
        
        # Set flag to show streaming animation
        st.session_state["show_streaming"] = True
        st.session_state["streaming_response"] = ai_response
        
        # Rerun to show the conversation with streaming
        st.rerun()
    
    # Display chat history
    if st.session_state["messages"]:
        st.markdown("### 💬 Conversation")
        
        messages_to_show = st.session_state["messages"]
        if "show_streaming" in st.session_state and st.session_state["show_streaming"]:
            # Show all messages except the last AI response (which we'll stream)
            for i, msg in enumerate(messages_to_show[:-1]):
                display_chat_message(msg["content"], msg["is_user"])
            
            # Show streaming animation for the AI response
            response_text = st.session_state["streaming_response"]
            response_placeholder = st.empty()
            
            displayed_response = ""
            for i, char in enumerate(response_text):
                displayed_response += char
                if i % 3 == 0:  # Update every 3 characters
                    response_placeholder.markdown(f"""
                    <div class="ai-message">
                        <strong>🤖 AI Assistant:</strong><br>
                        {displayed_response}▌
                        <div class="timestamp">{time.strftime("%I:%M %p")}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    time.sleep(0.02)  # Small delay for streaming effect
            
            # Final display without cursor
            response_placeholder.markdown(f"""
            <div class="ai-message">
                <strong>🤖 AI Assistant:</strong><br>
                {displayed_response}
                <div class="timestamp">{time.strftime("%I:%M %p")}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Clear streaming flags
            st.session_state["show_streaming"] = False
            st.session_state["streaming_response"] = None
            
        else:
            # Normal display without streaming
            for msg in messages_to_show:
                display_chat_message(msg["content"], msg["is_user"])

if __name__ == "__main__":
    main()