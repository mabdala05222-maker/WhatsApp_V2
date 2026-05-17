import streamlit as st
import sqlite3
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh
import os

# 1. إعدادات الصفحة والمنطقة الزمنية
st.set_page_config(page_title="WhatsApp Ultimate V2", page_icon="💬", layout="wide")
egypt_tz = pytz.timezone('Africa/Cairo')

# تحديث تلقائي كل ثانيتين لتلقي الرسائل الجديدة
st_autorefresh(interval=2000, key="chat_refresh")

# حقن CSS لتصغير الرسائل وتنسيق قائمة المستخدمين الثابتة
st.markdown("""
    <style>
    [data-testid="stMainBlockContainer"] { background-color: #efeae2 !important; }
    [data-testid="stSidebar"] { background-color: #111b21 !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label { color: white !important; }
    
    /* تصميم رأس المحادثة */
    .main-header {
        background-color: #008069; padding: 10px; color: white !important;
        font-size: 18px; font-weight: bold; border-radius: 8px; text-align: center; margin-bottom: 15px;
    }
    
    /* تنسيق فقاعات الرسائل (تصغير الحجم) */
    .msg-container { display: flex; flex-direction: column; margin: 4px 0; }
    .msg-box-sent {
        background-color: #d9fdd3; color: #111b21 !important; align-self: flex-end;
        padding: 6px 10px; border-radius: 8px 0px 8px 8px; max-width: 45%;
        font-size: 14px; box-shadow: 0 1px 1px rgba(0,0,0,0.1); word-wrap: break-word;
    }
    .msg-box-recv {
        background-color: #ffffff; color: #111b21 !important; align-self: flex-start;
        padding: 6px 10px; border-radius: 0px 8px 8px 8px; max-width: 45%;
        font-size: 14px; box-shadow: 0 1px 1px rgba(0,0,0,0.1); word-wrap: break-word;
    }
    .time-text { font-size: 9px; color: #667781 !important; text-align: right; margin-top: 2px; }
    
    /* أزرار الشات الثابتة في السايدبار لتصبح مثل الـ Contacts */
    .stSidebar div.stButton > button {
        background-color: #202c33 !important; color: white !important;
        border: none !important; width: 100% !important; text-align: right !important;
        padding: 10px !important; border-radius: 0px !important;
        border-bottom: 1px solid #222c32 !important; transition: 0.2s;
    }
    .stSidebar div.stButton > button:hover {
        background-color: #2a3942 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 2. إعداد قاعدة البيانات
conn = sqlite3.connect("whatsapp_v3.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

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

# إعداد المتغيرات في السيرفر لحفظ حالة تسجيل الدخول والشات النشط
if 'logged_in_user' not in st.session_state:
    st.session_state['logged_in_user'] = None
if 'active_chat' not in st.session_state:
    st.session_state['active_chat'] = None

# ==========================================
# 3. نظام الدخول في الصفحة الرئيسية (Main Page)
# ==========================================
if st.session_state['logged_in_user'] is None:
    st.markdown("<h2 style='text-align: center; color: #008069;'>💬 أهلاً بك في WhatsApp V2</h2>", unsafe_allow_html=True)
    
    # عمل بوكس في منتصف الصفحة للدخول والتسجيل
    col_space1, col_main, col_space2 = st.columns([1, 2, 1])
    
    with col_main:
        tab1, tab2 = st.tabs(["🔐 تسجيل الدخول", "✨ إنشاء حساب جديد"])
        
        with tab1:
            login_user = st.text_input("اسم المستخدم:", key="main_login_u").
