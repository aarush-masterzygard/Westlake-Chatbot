# 🏔️ Westlake High School AI Chatbot

## Developed by Aarush Rajkumar

An intelligent chatbot built with Streamlit and LangChain that provides comprehensive information about Westlake High School using RAG (Retrieval-Augmented Generation) technology.

## 🚀 Features

- **Smart Content Search**: Uses FAISS vector database for semantic search across web pages and PDFs
- **Conversational AI**: Maintains chat history and context for natural conversations
- **Real-time Responses**: Streaming responses with typing indicators for better user experience
- **Multi-Source Content**: Processes both website content and PDF documents automatically
- **Theme Support**: Toggle between dark/light modes with custom Westlake themes
- **Comprehensive Coverage**: Scrapes and indexes 120+ school website pages plus PDF documents
- **Error Recovery**: Robust error handling with automatic retries and graceful fallbacks
- **Mobile Responsive**: Optimized for all device sizes

## 📋 Content Coverage

The chatbot scrapes and indexes content from **120+ pages** of the Westlake High School website plus **PDF documents** including:

### 📄 PDF Documents

- Scholarship applications and information
- Course catalogs and academic guides
- Athletic forms and schedules
- Student handbooks and policies
- Dual enrollment materials
- Testing information and schedules
- _And many more educational resources_

### 🌐 Website Pages

The chatbot automatically discovers and indexes all accessible pages from the Westlake High School website (https://whs.conejousd.org/), including:

- **Homepage and Main Pages**
- **Academic Programs and Courses**
- **Athletics and Sports Teams**
- **Student Services and Counseling**
- **Performing Arts Programs**
- **Student Clubs and Organizations**
- **Administrative Information**
- **Calendar and Events**
- **Staff Directory**
- **And many more...**

## 📊 Technical Specifications

- **Total Web Pages Indexed**: 120+ pages
- **PDF Documents**: 150+ documents processed automatically
- **Embedding Model**: OpenAI text-embedding-3-small (1,536 dimensions)
- **Vector Database**: FAISS with optimized indexing
- **Web Content Chunks**: 600 characters with 100 character overlap
- **PDF Content Chunks**: 1,000 characters with 150 character overlap
- **Safety Limits**: 15MB per PDF, 100MB total PDF content, 100 pages per PDF
- **Processing Features**: Automatic retry logic, timeout handling, server-friendly delays

## 📁 Project Structure

```
WestlakeChatbot/
├── Source/
│   ├── 1_LoadWebsiteData.py    # Enhanced website + PDF scraper and vector DB creator
│   ├── 2_AI_Assistant.py       # Main Streamlit application with improved UI
│   ├── pages/
│   │   └── Chat_History.py     # Chat history page
│   ├── .streamlit/
│   │   └── secrets.toml        # Streamlit secrets (not in git)
│   └── index.faiss/            # Vector database files (web + PDF content)
│       ├── index.faiss         # FAISS vector index
│       └── index.pkl           # Document metadata
├── Environment/
│   └── API-Key.env            # Local environment variables (not in git)
├── requirements.txt           # Python dependencies
├── deploy.py                  # Deployment checker and launcher script
├── test_api_key.py           # API key testing utility
├── .gitignore                # Git ignore rules (excludes secrets and temp files)
└── README.md                 # This file
```

## 🔧 Configuration

### Content Scraper Settings

In `Source/1_LoadWebsiteData.py`, you can adjust:

- `max_pages`: Number of web pages to scrape (default: 120)
- `max_pdfs`: Number of PDF documents to process (default: 150)
- `PDF_SIZE_LIMIT`: Maximum PDF file size (default: 15MB)
- `MAX_PAGES_PER_PDF`: Maximum pages per PDF (default: 100)
- Web chunk size: 600 characters with 100 character overlap
- PDF chunk size: 1,000 characters with 150 character overlap
- Request delays: 2s between web pages, 5s between PDFs

### AI Assistant Settings

In `Source/2_AI_Assistant.py`:

- OpenAI model: `gpt-3.5-turbo-0125`
- Embedding model: `text-embedding-3-small`
- Search results: 4 most relevant chunks
- Streaming responses with HTML escaping for security
- Multiple theme options with dark/light mode support

## 🤖 Usage Examples

Ask the chatbot questions like:

- "What are the graduation requirements?"
- "Tell me about the academic programs"
- "What sports does Westlake offer?"
- "How do I apply for scholarships?"
- "What are the testing dates?"
- "Tell me about dual enrollment options"
- "What clubs and organizations are available?"

## 🎨 Westlake Theme Colors

### Light Mode
- **Blue**: #003D73 (Headers, text, borders)
- **Orange**: #FF6A13 (Buttons, accents, user messages)

### Dark Mode
- **Deep Navy Blue**: #001F3D (Backgrounds, headers)
- **Muted Orange**: #FF8C42 (Buttons, accents, user messages)
- **Soft Gray**: #B0B0B0 (Text, secondary elements)

## 🔒 Security

- API keys are excluded from version control via `.gitignore`
- Secrets are managed through Streamlit's secure secrets system
- Environment variables are used for local development

## 📈 Performance Features

- **Cached Components**: Vector database, LLM, and retriever caching with `@st.cache_resource`
- **Lazy Loading**: Heavy components loaded only when needed
- **Session State Optimization**: Efficient memory management with automatic cleanup
- **Connection Pooling**: Reused HTTP connections for better performance
- **Streaming Responses**: Real-time response generation with typing indicators
- **Smart Rerun Control**: Prevents unnecessary UI refreshes
- **Batch Processing**: PDF processing in optimized batches
- **Error Recovery**: Automatic retries with exponential backoff
- **HTML Security**: Proper escaping to prevent injection attacks

## 🎨 Features

- **Dark/Light Mode Toggle**: Switch between themes
- **Westlake Theme**: Custom colors matching school branding
- **Chat History**: Maintains conversation context
- **Streaming Responses**: Real-time response generation
- **Error Recovery**: Robust error handling with retries
- **Mobile Responsive**: Works on all device sizes

## 📄 License

This project is for educational purposes. Please respect the school's website terms of use.

## 📊 Content Analytics

The chatbot can answer questions about:

- **Academic Programs**: Course offerings, graduation requirements, academic support
- **Athletics**: Sports teams, tryouts, schedules, and athletic programs
- **Student Services**: Counseling, testing, health services, academic support
- **Administrative**: Registration, attendance, transcripts, policies
- **College Prep**: Scholarships, college planning, financial aid, career guidance
- **Extracurricular**: Student clubs, performing arts, leadership opportunities
- **PDF Resources**: Detailed information from handbooks, forms, catalogs, and applications

### 🔍 Enhanced Search Capabilities

- **Multi-Source Search**: Searches both web content and PDF documents simultaneously
- **Semantic Understanding**: Finds relevant information even with different wording
- **Context Awareness**: Maintains conversation history for follow-up questions
- **Document Attribution**: Shows whether information comes from web pages or PDF documents

---

_Built for Westlake High School students, parents, and staff_