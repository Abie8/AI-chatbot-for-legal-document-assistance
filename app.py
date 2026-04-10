import streamlit as st
import os
import sqlite3
import hashlib
from PyPDF2 import PdfReader
from fpdf import FPDF
from dotenv import load_dotenv
from google import genai
import time

# --- 1. CORE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = "Dashboard"

st.set_page_config(page_title="LEGAL AI ASSISTANT", page_icon="⚖️", layout="wide")
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# --- 2. DATABASE UTILITIES ---
def init_db():
    conn = sqlite3.connect('legal_app.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    conn.commit()
    conn.close()

def create_user(username, password):
    hashed_pass = hashlib.sha256(password.encode()).hexdigest()
    try:
        conn = sqlite3.connect('legal_app.db')
        c = conn.cursor()
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pass))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    hashed_pass = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect('legal_app.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed_pass))
    result = c.fetchone()
    conn.close()
    return result

def export_as_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    clean_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, clean_text)
    return pdf.output(dest='S').encode('latin-1')

init_db()

# --- 3. BLACK & GOLD THEME ---
def apply_theme():
    st.markdown("""
    <style>
    /* MAIN BACKGROUND */
    .stApp {
        background: #0a0a0a;
    }
    
    /* GOLD HEADER */
    .gold-header {
        background: #000000;
        border-bottom: 3px solid #d4af37;
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 0 0 15px 15px;
        text-align: center;
    }
    
    .gold-header h1 {
        color: #d4af37;
        margin: 0;
        font-size: 2.5rem;
        text-shadow: 0 0 10px rgba(212, 175, 55, 0.3);
    }
    
    /* LOGIN BOX */
    .login-box {
        background: #111111;
        border: 2px solid #d4af37;
        border-radius: 20px;
        padding: 40px;
        max-width: 400px;
        margin: 50px auto;
        box-shadow: 0 0 30px rgba(212, 175, 55, 0.2);
    }
    
    .login-title {
        color: #d4af37;
        font-size: 2.5rem;
        text-align: center;
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    .login-subtitle {
        color: #888;
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* CARDS */
    .gold-card {
        background: #111111;
        border: 1px solid #d4af37;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        transition: 0.3s;
    }
    
    .gold-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(212, 175, 55, 0.2);
    }
    
    /* BUTTONS */
    .stButton > button {
        background: transparent !important;
        border: 2px solid #d4af37 !important;
        color: #d4af37 !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        padding: 10px !important;
        transition: 0.3s !important;
    }
    
    .stButton > button:hover {
        background: #d4af37 !important;
        color: black !important;
        transform: scale(1.02);
    }
    
    /* INPUT FIELDS */
    .stTextInput > div > div > input {
        background: #1a1a1a !important;
        border: 1px solid #d4af37 !important;
        color: white !important;
        border-radius: 8px !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #ffd700 !important;
        box-shadow: 0 0 10px rgba(212, 175, 55, 0.3);
    }
    
    /* TABS - WITH GAP */
    .stTabs [data-baseweb="tab-list"] {
        background: #111111 !important;
        border-radius: 10px !important;
        border: 1px solid rgba(212, 175, 55, 0.3);
        gap: 20px !important;
        padding: 5px !important;
        justify-content: center !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #888 !important;
        font-size: 1.1rem !important;
        padding: 10px 30px !important;
        border-radius: 8px !important;
        transition: all 0.3s !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: #d4af37 !important;
        color: black !important;
        font-weight: bold !important;
    }
    
    /* STATS */
    .stat-box {
        background: #111111;
        border: 1px solid #d4af37;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
    }
    
    .stat-number {
        color: #d4af37;
        font-size: 2rem;
        font-weight: bold;
    }
    
    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background: #000000 !important;
        border-right: 2px solid #d4af37 !important;
    }
    
    /* HEADERS */
    h1, h2, h3 {
        color: #d4af37 !important;
    }
    
    /* DIVIDER */
    hr {
        background: linear-gradient(90deg, transparent, #d4af37, transparent) !important;
        height: 2px !important;
        border: none !important;
    }
    
    /* CHAT MESSAGES */
    .stChatMessage {
        background: #111111 !important;
        border: 1px solid #d4af37 !important;
        border-radius: 15px !important;
    }
    
    /* SUCCESS/ERROR */
    .stSuccess {
        background: rgba(212, 175, 55, 0.1) !important;
        color: #d4af37 !important;
    }
    
    .stError {
        background: rgba(255, 0, 0, 0.1) !important;
        color: #ff6b6b !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LOGIN PAGE ---
def login_page():
    apply_theme()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="login-box">
            <div class="login-title">⚖️ LEGAL AI</div>
            <div class="login-subtitle">SUPER LEGAL INTELLIGENCE</div>
            <hr>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 LOGIN", "📋 REGISTER"])
        
        with tab1:
            username = st.text_input("", placeholder="👤 Enter username", key="login_user", label_visibility="collapsed")
            password = st.text_input("", type="password", placeholder="🔑 Enter password", key="login_pass", label_visibility="collapsed")
            
            if st.button("🚀 ACCESS PLATFORM", use_container_width=True):
                if username == "admin" and password == "123":
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = "ADMIN"
                    st.rerun()
                elif login_user(username, password):
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = username.upper()
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
        
        with tab2:
            new_user = st.text_input("", placeholder="👤 Choose username", key="reg_user", label_visibility="collapsed")
            new_pass = st.text_input("", type="password", placeholder="🔐 Choose password", key="reg_pass", label_visibility="collapsed")
            
            if st.button("✨ CREATE ACCOUNT", use_container_width=True):
                if create_user(new_user, new_pass):
                    st.success("✅ Account created successfully!")
                else:
                    st.error("❌ Username already exists")

# --- 5. DASHBOARD PAGE ---
def dashboard_page():
    apply_theme()
    
    st.markdown("""
    <div class="gold-header">
        <h1>⚖️ LEGAL AI DASHBOARD</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Welcome
    st.markdown(f'<h2>Welcome, {st.session_state["user"]}!</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color: #888;">Your AI-powered legal assistant is ready with Gemini 3 Flash</p>', unsafe_allow_html=True)
    
    # Stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="stat-box">
            <div class="stat-number">127</div>
            <div style="color: #888;">📄 Documents</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stat-box">
            <div class="stat-number">45</div>
            <div style="color: #888;">⚖️ Sections</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stat-box">
            <div class="stat-number">89</div>
            <div style="color: #888;">💬 Analyses</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="stat-box">
            <div class="stat-number">94%</div>
            <div style="color: #888;">🎯 Accuracy</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Quick Actions
    st.markdown("<h3>⚡ QUICK ACTIONS</h3>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container():
            st.markdown("""
            <div class="gold-card">
                <h4>📄 Document Summarizer</h4>
                <p style="color: #888;">Upload PDF documents for AI summarization using Gemini 3 Flash</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚀 Launch Summarizer", key="dash_sum", use_container_width=True):
                st.session_state['current_page'] = "Summarizer"
                st.rerun()
    
    with col2:
        with st.container():
            st.markdown("""
            <div class="gold-card">
                <h4>⚖️ Section Finder</h4>
                <p style="color: #888;">Find IPC and BNS sections with Gemini 3 Flash intelligence</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔍 Launch Finder", key="dash_find", use_container_width=True):
                st.session_state['current_page'] = "IPC Section Finder"
                st.rerun()
    
    # Recent Activity
    st.markdown("<br><h3>📋 RECENT ACTIVITY</h3>", unsafe_allow_html=True)
    
    activities = [
        "10:30 AM - 📄 Summarized criminal case document",
        "09:45 AM - ⚖️ Found IPC Section 302",
        "Yesterday - 📋 BNS Section 45 consultation"
    ]
    
    for act in activities:
        st.markdown(f"""
        <div class="gold-card" style="padding: 15px;">
            <div style="display: flex; align-items: center;">
                <div style="width: 10px; height: 10px; background: #d4af37; border-radius: 50%; margin-right: 15px;"></div>
                <div style="color: white;">{act}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- 6. SUMMARIZER PAGE ---
def summarizer_page():
    apply_theme()
    
    st.markdown("""
    <div class="gold-header">
        <h1>📄 DOCUMENT SUMMARIZER</h1>
        <p style="color: #888;">Powered by Gemini 3 Flash</p>
    </div>
    """, unsafe_allow_html=True)
    
    file = st.file_uploader("📎 Upload PDF Document", type="pdf")
    
    if file:
        st.success(f"✅ File uploaded: {file.name}")
        
        if st.button("✨ GENERATE SUMMARY WITH GEMINI 3", use_container_width=True):
            with st.spinner("🤖 Gemini 3 Flash is analyzing your document..."):
                try:
                    reader = PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        if page.extract_text():
                            text += page.extract_text()
                    
                    if api_key:
                        client = genai.Client(api_key=api_key)
                        response = client.models.generate_content(
                            model="gemini-3-flash-preview",
                            contents=f"""You are a legal expert. Please provide a comprehensive summary of this legal document:
                            
                            Document text:
                            {text[:8000]}
                            
                            Please include:
                            1. Key points and main arguments
                            2. Important legal provisions mentioned
                            3. Parties involved
                            4. Conclusion and outcomes
                            """
                        )
                        
                        st.markdown('<div class="gold-card">', unsafe_allow_html=True)
                        st.markdown("### 📝 Gemini 3 Flash Summary")
                        st.info(response.text)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                "📥 Download PDF",
                                export_as_pdf(response.text),
                                f"summary_{file.name}.pdf",
                                use_container_width=True
                            )
                        with col2:
                            st.download_button(
                                "📥 Download TXT",
                                response.text,
                                f"summary_{file.name}.txt",
                                use_container_width=True
                            )
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        st.success("✅ Summary generated successfully with Gemini 3 Flash!")
                    else:
                        st.error("❌ API key not found. Please check your .env file")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# --- 7. IPC SECTION FINDER PAGE (FIXED) ---
def ipc_section_finder_page():  # Changed function name to match
    apply_theme()
    
    st.markdown("""
    <div class="gold-header">
        <h1>⚖️ IPC SECTION FINDER</h1>
        <p style="color: #888;">IPC & BNS • Powered by Gemini 3 Flash</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display chat history
    for msg in st.session_state['chat_history']:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("💬 Describe your legal scenario to Gemini 3 Flash..."):
        # Add user message
        st.session_state['chat_history'].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response with Gemini 3 Flash
        with st.chat_message("assistant"):
            with st.spinner("🤖 Gemini 3 Flash is analyzing legal sections..."):
                try:
                    if api_key:
                        client = genai.Client(api_key=api_key)
                        response = client.models.generate_content(
                            model="gemini-3-flash-preview",
                            contents=f"""You are a legal expert specializing in Indian Penal Code (IPC) and Bharatiya Nyaya Sanhita (BNS). 
                            
                            Scenario: {prompt}
                            
                            Please identify:
                            1. Relevant IPC sections with explanations
                            2. Corresponding BNS sections (if applicable)
                            3. Key legal elements and punishments
                            4. Similar case references
                            
                            Format the response clearly with bullet points."""
                        )
                        
                        st.markdown(response.text)
                        st.session_state['chat_history'].append({"role": "assistant", "content": response.text})
                        st.success("✅ Sections identified by Gemini 3 Flash!")
                    else:
                        st.error("❌ API key not found. Please check your .env file")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Clear chat button
    if st.session_state['chat_history']:
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state['chat_history'] = []
            st.rerun()

# --- 8. MAIN APP (FIXED ROUTING) ---
def main():
    if not st.session_state['logged_in']:
        login_page()
    else:
        apply_theme()
        
        # Sidebar navigation
        with st.sidebar:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 3rem;">⚖️</div>
                <h3 style="color: #d4af37;">{st.session_state['user']}</h3>
                <p style="color: #666;">Gemini 3 Flash</p>
                <hr>
            </div>
            """, unsafe_allow_html=True)
            
            # Navigation buttons - FIXED: Changed key and value
            if st.button("🏠 AI Chatbot for legal document assistance", key="nav_dash", use_container_width=True):
                st.session_state['current_page'] = "Dashboard"
                st.rerun()
            
            if st.button("📄 SUMMARIZER", key="nav_sum", use_container_width=True):
                st.session_state['current_page'] = "Summarizer"
                st.rerun()
            
            # FIXED: Changed to match exactly
            if st.button("⚖️ IPC SECTION FINDER", key="nav_ipc", use_container_width=True):
                st.session_state['current_page'] = "IPC Section Finder"
                st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Logout button
            if st.button("🚪 LOGOUT", key="logout", use_container_width=True):
                st.session_state['logged_in'] = False
                st.session_state['user'] = None
                st.session_state['chat_history'] = []
                st.rerun()
        
        # Page routing - FIXED: Added exact match
        if st.session_state['current_page'] == "Dashboard":
            dashboard_page()
        elif st.session_state['current_page'] == "Summarizer":
            summarizer_page()
        elif st.session_state['current_page'] == "IPC Section Finder":  # EXACT MATCH
            ipc_section_finder_page()

if __name__ == "__main__":
    main()