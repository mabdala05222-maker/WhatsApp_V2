import streamlit as st
import sqlite3
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh
import os

# 1. إعدادات الصفحة والمنطقة الزمنية
st.set_page_config(page_title="WhatsApp", page_icon="💬", layout="wide", initial_sidebar_state="expanded")
egypt_tz = pytz.timezone('Africa/Cairo')

# تحديث تلقائي كل ثانيتين لجلب الرسائل فوراً
st_autorefresh(interval=2000, key="chat_refresh")

# 2. حقن CSS لتحويل الواجهة لنسخة طبق الأصل من واتساب ويب
st.markdown("""
    <style>
    [data-testid="stMainBlockContainer"] {
        background-color: #efeae2 !important;
        background-image: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png') !important;
        background-repeat: repeat !important;
        padding: 0rem 1rem 1rem 1rem !important;
    }
    [data-testid="stSidebar"] {
        background-color: #111b21 !important;
        border-right: 1px solid #222c32 !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label { color: #e9edef !important; }
    
    .whatsapp-header {
        background-color: #202c33; padding: 12px 20px; color: #e9edef !important;
        font-size: 16px; font-weight: bold; border-bottom: 1px solid #222c32;
        display: flex; align-items: center; margin-left: -4rem; margin-right: -4rem;
        margin-top: -3.5rem; margin-bottom: 20px;
    }
    
    .msg-container { display: flex; flex-direction: column; margin: 4px 0; width: 100%; }
    .msg-box-sent {
        background-color: #d9fdd3 !important; color: #111b21 !important; align-self: flex-end;
        padding: 6px 12px; border-radius: 8px 0px 8px 8px; max-width: 50%;
        font-size: 14.2px; box-shadow: 0 1px 0.5px rgba(11,20,26,.13); word-wrap: break-word;
    }
    .msg-box-recv {
        background-color: #ffffff !important; color: #111b21 !important; align-self: flex-start;
        padding: 6px 12px; border-radius: 0px 8px 8px 8px; max-width: 50%;
        font-size: 14.2px; box-shadow: 0 1px 0.5px rgba(11,20,26,.13); word-wrap: break-word;
    }
    .time-text { font-size: 10px; color: #667781 !important; text-align: left; margin-top: 4px; display: flex; justify-content: flex-end; align-items: center; }
    
    .stSidebar div.stButton > button {
        background-color: #111b21 !important; color: #e9edef !important; border: none !important;
        width: 100% !important; text-align: right !important; padding: 15px 10px !important;
        border-radius: 0px !important; border-bottom: 1px solid #222c32 !important; font-size: 15px !important;
    }
    .stSidebar div.stButton > button:hover { background-color: #202c33 !important; }
    .login-card { background-color: #202c33; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); color: white; }
    </style>
""", unsafe_allow_html=True)

# 3. إعداد قاعدة البيانات
conn = sqlite3.connect("whatsapp_v3.db", check_same_thread=False)
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)")
c.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    receiver TEXT,
    message TEXT,
    file_path TEXT,
    file_type TEXT,
    time TEXT,
    is_read INTEGER DEFAULT 0
)
""")
conn.commit()

if not os.path.exists("media"):
    os.makedirs("media")

if 'logged_in_user' not in st.session_state:
    st.session_state['logged_in_user'] = None
if 'active_chat' not in st.session_state:
    st.session_state['active_chat'] = None

# ==========================================
# الشاشة الأولى: صفحة الدخول والتسجيل
# ==========================================
if st.session_state['logged_in_user'] is None:
    st.markdown("<div style='background-color: #00a884; height: 220px; position: absolute; top:0; left:0; right:0; z-index:-1;'></div>", unsafe_allow_html=True)
    st.markdown("<br><br>
