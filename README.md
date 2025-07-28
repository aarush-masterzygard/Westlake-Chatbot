# 🌊 Beachside High School AI Chatbot

An intelligent chatbot built with Streamlit and LangChain that provides comprehensive information about Beachside High School using RAG (Retrieval-Augmented Generation) technology.

## 🚀 Features

- **Smart Content Search**: Uses FAISS vector database for semantic search across web pages and PDFs
- **Conversational AI**: Maintains chat history and context for natural conversations
- **Real-time Responses**: Streaming responses with typing indicators for better user experience
- **Multi-Source Content**: Processes both website content and PDF documents automatically
- **Theme Support**: Toggle between dark/light modes with custom Beachside themes
- **Comprehensive Coverage**: Scrapes and indexes 110+ school website pages plus PDF documents
- **Error Recovery**: Robust error handling with automatic retries and graceful fallbacks
- **Mobile Responsive**: Optimized for all device sizes

## 📋 Content Coverage

The chatbot scrapes and indexes content from **110+ pages** of the Beachside High School website plus **PDF documents** including:

### 📄 PDF Documents

- Scholarship applications and information
- Course catalogs and academic guides
- Athletic forms and schedules
- Student handbooks and policies
- Dual enrollment materials
- Testing information and schedules
- _And many more educational resources_

### 🌐 Website Pages

### 🏠 Main Pages (Depth 0-1)

1. **Homepage** - https://www-bhs.stjohns.k12.fl.us/
2. **Calendar** - https://www-bhs.stjohns.k12.fl.us/calendar/
3. **Payments** - https://www-bhs.stjohns.k12.fl.us/payments/
4. **Academies** - https://www-bhs.stjohns.k12.fl.us/academics/academies/
5. **AICE Program** - https://www-bhs.stjohns.k12.fl.us/aice/
6. **Athletics** - https://www-bhs.stjohns.k12.fl.us/athletics/
7. **National Honor Society (NHS)** - https://www-bhs.stjohns.k12.fl.us/nhs/
8. **Cafeteria** - https://www-bhs.stjohns.k12.fl.us/cafeteria/
9. **Performing Arts** - https://www-bhs.stjohns.k12.fl.us/performing-arts/
10. **SAC** - https://www-bhs.stjohns.k12.fl.us/sac/
11. **Staff Directory** - https://www-bhs.stjohns.k12.fl.us/staff-directory/
12. **Student Clubs & Organizations** - https://www-bhs.stjohns.k12.fl.us/student-clubs-organizations/
13. **Attendance** - https://www-bhs.stjohns.k12.fl.us/attendance/
14. **Barracuda Beat** - https://www-bhs.stjohns.k12.fl.us/barracuda-beat/
15. **Health Clinic** - https://www-bhs.stjohns.k12.fl.us/clinic/
16. **Media Center** - https://www-bhs.stjohns.k12.fl.us/media/
17. **Registration** - https://www-bhs.stjohns.k12.fl.us/registration/
18. **Parent Information** - https://www-bhs.stjohns.k12.fl.us/parent-information/
19. **Yearbook** - https://www-bhs.stjohns.k12.fl.us/parent-information/yearbook/
20. **Parking Pass Information** - https://www-bhs.stjohns.k12.fl.us/parking-pass-information/
21. **School Counseling** - https://www-bhs.stjohns.k12.fl.us/guidance/
22. **Seniors** - https://www-bhs.stjohns.k12.fl.us/seniors/
23. **Testing Information** - https://www-bhs.stjohns.k12.fl.us/testing/
24. **Facility Requests** - https://www-bhs.stjohns.k12.fl.us/facility-requests/
25. **Transcript Requests** - https://www-bhs.stjohns.k12.fl.us/guidance/transcript-requests/
26. **School Accreditation** - https://www-bhs.stjohns.k12.fl.us/accreditation

### 🏃‍♂️ Athletics Pages (Depth 2)

27. **Cross Country** - https://www-bhs.stjohns.k12.fl.us/athletics/cross-country/
28. **Girls Golf** - https://www-bhs.stjohns.k12.fl.us/athletics/girls-golf/
29. **Boys Golf** - https://www-bhs.stjohns.k12.fl.us/athletics/boys-golf/
30. **Swimming & Diving** - https://www-bhs.stjohns.k12.fl.us/athletics/swim/
31. **Boys Basketball** - https://www-bhs.stjohns.k12.fl.us/athletics/boys-basketball/
32. **Girls Basketball** - https://www-bhs.stjohns.k12.fl.us/athletics/girls-basketball/
33. **Boys Soccer** - https://www-bhs.stjohns.k12.fl.us/athletics/boys-soccer/
34. **Girls Soccer** - https://www-bhs.stjohns.k12.fl.us/athletics/girls-soccer/
35. **Wrestling** - https://www-bhs.stjohns.k12.fl.us/athletics/wrestling/
36. **Girls Weightlifting** - https://www-bhs.stjohns.k12.fl.us/athletics/girls-weightlifting/
37. **Cheerleading** - https://www-bhs.stjohns.k12.fl.us/athletics/cheerleading/
38. **Dance** - https://www-bhs.stjohns.k12.fl.us/athletics/dance/
39. **Baseball** - https://www-bhs.stjohns.k12.fl.us/athletics/baseball/
40. **Boys Lacrosse** - https://www-bhs.stjohns.k12.fl.us/athletics/boys-lacrosse/
41. **Girls Lacrosse** - https://www-bhs.stjohns.k12.fl.us/athletics/girls-lacrosse/
42. **Softball** - https://www-bhs.stjohns.k12.fl.us/athletics/softball/
43. **Boys Tennis** - https://www-bhs.stjohns.k12.fl.us/athletics/boys-tennis/
44. **Girls Tennis** - https://www-bhs.stjohns.k12.fl.us/athletics/girls-tennis/
45. **Track & Field** - https://www-bhs.stjohns.k12.fl.us/athletics/track/
46. **Boys Volleyball** - https://www-bhs.stjohns.k12.fl.us/athletics/boys-volleyball/
47. **Beach Volleyball** - https://www-bhs.stjohns.k12.fl.us/athletics/beach-volleyball/
48. **Summer Camps** - https://www-bhs.stjohns.k12.fl.us/athletics/summer-camps/
49. **Baseball Summer Camp** - https://www-bhs.stjohns.k12.fl.us/athletics/baseball-summer-camp/
50. **Tennis Summer Camp** - https://www-bhs.stjohns.k12.fl.us/athletics/tennis-camp/
51. **Wrestling Summer Camp** - https://www-bhs.stjohns.k12.fl.us/athletics/wrestling-camp/
52. **Tickets** - https://www-bhs.stjohns.k12.fl.us/athletics/tickets/
53. **Tryouts** - https://www-bhs.stjohns.k12.fl.us/athletics/tryouts/
54. **Letter Jacket Ordering** - https://www-bhs.stjohns.k12.fl.us/athletics/ordering/

### 🎭 Performing Arts Pages (Depth 2)

55. **Band** - https://www-bhs.stjohns.k12.fl.us/performing-arts/band/
56. **Beachside Honors Chorus** - https://www-bhs.stjohns.k12.fl.us/performing-arts/chorus/
57. **Dance** - https://www-bhs.stjohns.k12.fl.us/performing-arts/dance/
58. **Theatre** - https://www-bhs.stjohns.k12.fl.us/performing-arts/theatre/

### 🎓 Academic & Counseling Pages (Depth 2)

59. **Mu Alpha Theta** - https://www-bhs.stjohns.k12.fl.us/mu-alpha-theta/
60. **2025-26 Course Selection** - https://www-bhs.stjohns.k12.fl.us/guidance/course-selections/
61. **Career Planning** - https://www-bhs.stjohns.k12.fl.us/guidance/career-planning/
62. **Community Service/Paid Work Hours** - https://www-bhs.stjohns.k12.fl.us/guidance/community-service/
63. **Financial Aid** - https://www-bhs.stjohns.k12.fl.us/guidance/financial-aid/
64. **Florida Bright Futures Scholarship** - https://www-bhs.stjohns.k12.fl.us/guidance/florida-bright-futures/
65. **GPA Information** - https://www-bhs.stjohns.k12.fl.us/guidance/gpa/
66. **Graduation and Promotion Requirements** - https://www-bhs.stjohns.k12.fl.us/guidance/graduation-requirements/
67. **Mental Health Resources** - https://www-bhs.stjohns.k12.fl.us/guidance/mental-health-resources/
68. **NCAA Information** - https://www-bhs.stjohns.k12.fl.us/guidance/ncaa/
69. **Post-Secondary Options** - https://www-bhs.stjohns.k12.fl.us/guidance/post-secondary-options/
70. **Post-Secondary Visits and College Fairs** - https://www-bhs.stjohns.k12.fl.us/guidance/post-secondary-visits/
71. **Presentations and Resources** - https://www-bhs.stjohns.k12.fl.us/guidance/presentations-and-resources/
72. **State University System of Florida** - https://www-bhs.stjohns.k12.fl.us/guidance/state-university-system-of-florida/
73. **Testing Information** - https://www-bhs.stjohns.k12.fl.us/guidance/testing-information/
74. **Virtual School** - https://www-bhs.stjohns.k12.fl.us/guidance/virtual-school/
75. **Dual Enrollment at FCTC** - https://www-bhs.stjohns.k12.fl.us/guidance/dual-enrollment-fctc/
76. **Dual Enrollment at SJRSC** - https://www-bhs.stjohns.k12.fl.us/guidance/dual-enrollment-sjrsc/

### 💰 Scholarship Pages (Depth 2-3)

77. **Scholarship Tips and Information** - https://www-bhs.stjohns.k12.fl.us/guidance/scholarships/
78. **August Scholarships** - https://www-bhs.stjohns.k12.fl.us/guidance/scholarships/august-scholarships/
79. **September Scholarships** - https://www-bhs.stjohns.k12.fl.us/guidance/scholarships/september-scholarships/
80. **October Scholarships** - https://www-bhs.stjohns.k12.fl.us/guidance/scholarships/october-scholarships/
81. **November Scholarships** - https://www-bhs.stjohns.k12.fl.us/guidance/scholarships/november-scholarships/
82. **December Scholarships** - https://www-bhs.stjohns.k12.fl.us/guidance/scholarships/december-scholarships/
83. **January Scholarships** - https://www-bhs.stjohns.k12.fl.us/guidance/scholarships/january-scholarships/
84. **February Scholarships** - https://www-bhs.stjohns.k12.fl.us/guidance/scholarships/february-scholarships/
85. **March Scholarships** - https://www-bhs.stjohns.k12.fl.us/guidance/scholarships/march-scholarships/
86. **April Scholarships** - https://www-bhs.stjohns.k12.fl.us/guidance/scholarships/april-scholarships/
87. **May Scholarships** - https://www-bhs.stjohns.k12.fl.us/guidance/scholarships/may-scholarships/
88. **Summer Scholarships** - https://www-bhs.stjohns.k12.fl.us/guidance/scholarships/june-july-scholarships/

### 📝 Testing Pages (Depth 2-3)

89. **Beachside Testing Calendar** - https://www-bhs.stjohns.k12.fl.us/testing/beachside-testing-calendar/
90. **SJCSD Assessment Calendar** - https://www-bhs.stjohns.k12.fl.us/testing/home/beachside-testing-calendar/
91. **FAST & EOCs (State Exams)** - https://www-bhs.stjohns.k12.fl.us/testing/fast-eocs-state-exams/
92. **PSAT Information** - https://www-bhs.stjohns.k12.fl.us/testing/home/psat/
93. **SAT Information** - https://www-bhs.stjohns.k12.fl.us/testing/home/sat/
94. **ACT Information** - https://www-bhs.stjohns.k12.fl.us/testing/home/act/
95. **ACT Test Dates and Deadlines 25-26** - https://www-bhs.stjohns.k12.fl.us/testing/act-test-dates-and-deadlines-25-26/
96. **AP Testing Information** - https://www-bhs.stjohns.k12.fl.us/testing/ap-testing-information/

### 🔧 System Pages (Depth 2)

97. **Events Feed** - https://www-bhs.stjohns.k12.fl.us/feed/eo-events/
98. **Email Protection** - https://www-bhs.stjohns.k12.fl.us/cdn-cgi/l/email-protection
99. **WordPress Login** - https://www-bhs.stjohns.k12.fl.us/wp-login.php

## 📊 Technical Specifications

- **Total Web Pages Indexed**: 110+ pages
- **PDF Documents**: 50+ documents processed automatically
- **Embedding Model**: OpenAI text-embedding-3-small (1,536 dimensions)
- **Vector Database**: FAISS with optimized indexing
- **Web Content Chunks**: 600 characters with 100 character overlap
- **PDF Content Chunks**: 1,000 characters with 150 character overlap
- **Safety Limits**: 15MB per PDF, 100MB total PDF content, 100 pages per PDF
- **Processing Features**: Automatic retry logic, timeout handling, server-friendly delays

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+
- OpenAI API Key

### Installation Steps

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd BeachsideChatbot
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API Key**

   For local development, create `Environment/API-Key.env`:

   ```
   OPENAI_API_KEY=your-openai-api-key-here
   ```

   For deployment, add to `Source/.streamlit/secrets.toml`:

   ```toml
   OPENAI_API_KEY = "your-openai-api-key-here"
   ```

4. **Create Vector Database**

   ```bash
   python Source/1_LoadWebsiteData.py
   ```

5. **Run the Application**

   ```bash
   python deploy.py
   ```

   Or directly:

   ```bash
   streamlit run Source/2_AI_Assistant.py
   ```

## 🚀 Deployment

### Streamlit Cloud

1. Push code to GitHub (API keys are excluded via .gitignore)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Set main file path: `Source/2_AI_Assistant.py`
5. Add your OpenAI API key in Streamlit Cloud secrets

### Local Development

Use the included `deploy.py` script which checks all requirements and starts the app.

## 📁 Project Structure

```
BeachsideChatbot/
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
├── count_links.py             # Utility script for link analysis
├── test_api_key.py           # API key testing utility
├── .gitignore                # Git ignore rules (excludes secrets and temp files)
└── README.md                 # This file
```

## 🔧 Configuration

### Content Scraper Settings

In `Source/1_LoadWebsiteData.py`, you can adjust:

- `max_pages`: Number of web pages to scrape (default: 110)
- `max_pdfs`: Number of PDF documents to process (default: 50)
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
- "Tell me about the AICE program"
- "What sports does Beachside offer?"
- "How do I apply for scholarships?"
- "What are the testing dates?"
- "Tell me about dual enrollment options"

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
- **Chat History**: Maintains conversation context
- **Streaming Responses**: Real-time response generation
- **Error Recovery**: Robust error handling with retries
- **Mobile Responsive**: Works on all device sizes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is for educational purposes. Please respect the school's website terms of use.

## 🆘 Troubleshooting

### Common Issues

1. **"No API key found"**

   - Check that your API key is properly set in the appropriate file
   - Ensure the API key starts with "sk-"

2. **"Vector database not found"**

   - Run `python Source/1_LoadWebsiteData.py` to create the database

3. **Import errors**

   - Run `pip install -r requirements.txt`

4. **Streamlit secrets not working**
   - Ensure secrets file is at `Source/.streamlit/secrets.toml`
   - Check that the file is not in `.gitignore` for local testing

### Getting Help

Run the deployment checker for diagnostics:

```bash
python deploy.py
```

## 📊 Content Analytics

The chatbot can answer questions about:

- **Academic Programs**: AICE, dual enrollment, course selection, graduation requirements
- **Athletics**: All 20+ sports teams, tryouts, camps, and schedules
- **Student Services**: Counseling, testing, health clinic, mental health resources
- **Administrative**: Registration, attendance, parking, transcripts, facility requests
- **College Prep**: Scholarships, NCAA eligibility, financial aid, college visits
- **Extracurricular**: Student clubs, performing arts, NHS, community service
- **PDF Resources**: Detailed information from scholarship applications, course catalogs, handbooks, and forms

### 🔍 Enhanced Search Capabilities

- **Multi-Source Search**: Searches both web content and PDF documents simultaneously
- **Semantic Understanding**: Finds relevant information even with different wording
- **Context Awareness**: Maintains conversation history for follow-up questions
- **Document Attribution**: Shows whether information comes from web pages or PDF documents

---

_Built for Beachside High School students, parents, and staff_
