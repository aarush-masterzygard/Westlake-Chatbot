import streamlit as st
import time

# Configure the page title and settings
st.set_page_config(
    page_title="📚 Chat History", 
    page_icon="📚",
    layout="wide"
)

def initialize_session_state():
    # Theme preferences
    if "dark_mode" not in st.session_state:
        st.session_state["dark_mode"] = True
    if "beachside_theme" not in st.session_state:
        st.session_state["beachside_theme"] = False
    # Chat history for display
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

def get_theme_css(dark_mode, beachside_theme):
    """
    Generate theme-specific CSS based on dark mode and beachside theme settings.
    """
    if beachside_theme:
        # Beachside Theme Colors
        if dark_mode:
            # Beachside Dark Theme
            return """
            body {
                background-color: #0A1A2A;
                color: #E8F4F8;
            }
            .main-header {
                background: linear-gradient(90deg, #1E3A5F 0%, #2C5F7F 100%);
            }
            .chat-container {
                background: #1A2F3F;
                color: #E8F4F8;
            }
            .user-message {
                background: linear-gradient(135deg, #2C5F7F 0%, #1E3A5F 100%);
            }
            .ai-message {
                background: linear-gradient(135deg, #3F7F9F 0%, #5F9FBF 100%);
            }
            .timestamp {
                color: #B0D4E8;
            }
            .stats-container {
                background: #1A2F3F;
                border: 1px solid #2C5F7F;
                color: #E8F4F8;
            }
            .no-history-container {
                background: #1A2F3F;
                border: 1px solid #2C5F7F;
                color: #E8F4F8;
            }
            /* Beachside dark mode sidebar styling */
            .stSidebar > div {
                background: linear-gradient(180deg, #1E3A5F 0%, #2C5F7F 100%) !important;
            }
            """
        else:
            # Beachside Light Theme - Forest Green & Dark Teal
            return """
            body {
                background-color: #FFFFFF !important;
                color: #000000 !important;
            }
            .stApp {
                background-color: #FFFFFF !important;
            }
            .main-header {
                background: linear-gradient(90deg, #1FB25C 0%, #13635F 100%);
                /* Previous green: background: linear-gradient(90deg, #25CF6D 0%, #13635F 100%); */
            }
            .chat-container {
                background: #FFFFFF;
            }
            .user-message {
                background: linear-gradient(135deg, #1FB25C 0%, #13635F 100%);
                /* Previous green: background: linear-gradient(135deg, #25CF6D 0%, #13635F 100%); */
            }
            .ai-message {
                background: linear-gradient(135deg, #13635F 0%, #22B3AB 100%);
            }
            .timestamp {
                color: #2F4F4F;
            }
            .stats-container {
                background: #FFFFFF;
                border: 1px solid #13635F;
                color: #000000;
            }
            .no-history-container {
                background: #FFFFFF;
                border: 1px solid #13635F;
                color: #000000;
            }
            /* Beachside light mode sidebar styling */
            .stSidebar > div {
                background: linear-gradient(180deg, #1FB25C 0%, #13635F 100%) !important;
                /* Previous green: background: linear-gradient(180deg, #25CF6D 0%, #13635F 100%) !important; */
            }
            .stSidebar .stMarkdown {
                color: #FFFFFF !important;
            }
            """
    else:
        # Original Theme Colors
        if dark_mode:
            # Original Dark Theme
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
            .stats-container {
                background: #2D2D2D;
                border: 1px solid #3D3D3D;
                color: #E0E0E0;
            }
            .no-history-container {
                background: #2D2D2D;
                border: 1px solid #3D3D3D;
                color: #E0E0E0;
            }
            /* Original dark mode sidebar styling */
            .stSidebar > div {
                background: linear-gradient(180deg, #4B6CB7 0%, #182848 100%) !important;
            }
            """
        else:
            # Original Light Theme (with white background)
            return """
            body {
                background-color: #FFFFFF !important;
                color: #000000 !important;
            }
            .stApp {
                background-color: #FFFFFF !important;
            }
            .main-header {
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            }
            .chat-container {
                background: #FFFFFF;
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
            .stats-container {
                background: #FFFFFF;
                border: 1px solid #e9ecef;
                color: #000000;
            }
            .no-history-container {
                background: #FFFFFF;
                border: 1px solid #e9ecef;
                color: #000000;
            }
            /* Original light mode sidebar styling */
            .stSidebar > div {
                background: linear-gradient(180deg, #667eea 0%, #764ba2 100%) !important;
            }
            .stSidebar .stMarkdown {
                color: #FFFFFF !important;
            }
            """

def add_custom_css():
    # Get theme CSS based on current mode
    theme_css = get_theme_css(st.session_state["dark_mode"], st.session_state["beachside_theme"])
    
    st.markdown(f"""
    <style>
    /* Base styles that apply to both themes */
    .main-header {{
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }}
    
    .stats-container {{
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
    
    .no-history-container {{
        padding: 3rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        margin: 2rem 0;
    }}
    
    /* Theme-specific styles */
    {theme_css}
    </style>
    """, unsafe_allow_html=True)

def display_chat_message(message, is_user=True, timestamp=None):
    # Generate timestamp if not provided
    if timestamp is None:
        timestamp = time.strftime("%I:%M %p")
        
    if is_user:
        st.markdown(f"""
        <div class="user-message">
            <strong>🧑 You:</strong><br>
            {message}
            <div class="timestamp">{timestamp}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="ai-message">
            {message}
            <div class="timestamp">{timestamp}</div>
        </div>
        """, unsafe_allow_html=True)

def main():
    initialize_session_state()
    add_custom_css()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📚 Chat History</h1>
        <p>Review your previous conversations with the AI assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        # Theme toggle
        st.markdown("""
        <div class="sidebar-info">
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
        
        # Beachside Theme Toggle
        col3, col4 = st.columns([1.2, 1.8])
        with col3:
            st.markdown("**Style:**")
        with col4:
            # Beachside theme toggle
            beachside_theme = st.toggle("Beachside Theme", value=st.session_state["beachside_theme"], key="beachside_theme_toggle")
            # Update session state if toggle changed
            if beachside_theme != st.session_state["beachside_theme"]:
                st.session_state["beachside_theme"] = beachside_theme
                st.rerun()  # Immediately refresh to apply theme changes
        
        st.markdown("""
        <div class="sidebar-info">
            <h3>🔧 Actions</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Refresh History"):
            st.rerun()
        
        if st.button("🗑️ Clear All History"):
            st.session_state["chat_history"] = []
            if "messages" in st.session_state:
                st.session_state["messages"] = []
            st.success("Chat history cleared!")
            st.rerun()
        
        if st.button("⬅️ Back to Chat"):
            st.switch_page("2_Chatbot.py")
    
    # Display chat history
    if "chat_history" in st.session_state and st.session_state["chat_history"]:
        # Calculate statistics
        total_messages = len(st.session_state["chat_history"])
        user_messages = sum(1 for i in range(0, total_messages, 2) if i < total_messages)
        ai_messages = sum(1 for i in range(1, total_messages, 2) if i < total_messages)
        
        # Display statistics
        st.markdown(f"""
        <div class="stats-container">
            <h3>📊 Conversation Statistics</h3>
            <div style="display: flex; justify-content: space-around; margin-top: 1rem;">
                <div>
                    <h4 style="margin: 0; color: #667eea;">{total_messages}</h4>
                    <p style="margin: 0; font-size: 0.9rem;">Total Messages</p>
                </div>
                <div>
                    <h4 style="margin: 0; color: #667eea;">{user_messages}</h4>
                    <p style="margin: 0; font-size: 0.9rem;">Your Questions</p>
                </div>
                <div>
                    <h4 style="margin: 0; color: #667eea;">{ai_messages}</h4>
                    <p style="margin: 0; font-size: 0.9rem;">AI Responses</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 💬 Conversation History")
        
        # Display messages in reverse order (newest first)
        for i in range(len(st.session_state["chat_history"]) - 1, -1, -2):
            if i-1 >= 0:
                # Display AI message first (since we're going backwards)
                ai_content = st.session_state["chat_history"][i]
                if hasattr(ai_content, 'content'):
                    ai_content = ai_content.content
                display_chat_message(ai_content, is_user=False)
                
                # Display user message
                user_content = st.session_state["chat_history"][i-1]
                if hasattr(user_content, 'content'):
                    user_content = user_content.content
                display_chat_message(user_content, is_user=True)
                
                # Add separator between conversations
                st.markdown("<hr style='margin: 2rem 0; opacity: 0.3;'>", unsafe_allow_html=True)
    
    else:
        # No chat history available
        st.markdown("""
        <div class="no-history-container">
            <div class="no-history-icon">💬</div>
            <h3>No Chat History Yet</h3>
            <p>Start a conversation with the AI assistant to see your chat history here.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🚀 Start Chatting", use_container_width=True):
                st.switch_page("2_Chatbot.py")

if __name__ == "__main__":
    main()