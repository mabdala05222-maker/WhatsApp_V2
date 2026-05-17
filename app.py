import streamlit as st
import sqlite3
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh
import os

# 1. إعدادات الصفحة والمنطقة الزمنية
st.set_page_config(page_title="WhatsApp Ultimate V2", page_icon="💬", layout="wide")
egypt_tz = pytz.timezone('Africa/Cairo')

# تحديث تلقائي كل ثانيتين لتلقي الرسائل
st_autorefresh(interval=2000, key="chat_refresh")

# حقن CSS مطور لتصغير الرسائل وتظبيط الواجهة
st.markdown("""
    <style>
    [data-testid="stMainBlockContainer"] { background-color: #efeae2 !important; }
    [data-testid="stSidebar"] { background-color: #111b21 !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label { color: white !important; }
    .main-header {
        background-color: #008069; padding: 10px; color: white !important;
        font-size: 18px; font-weight: bold; border-radius: 8px; text-align: center; margin-bottom: 15px;
    }
    .msg-container { display: flex; flex-direction: column; margin: 4px 0; }
    /* تصغير حجم الرسائل وجعلها مرنة حسب النص */
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
    </style>
""", unsafe_allow_html=True)

# 2. إعداد قاعدة البيانات الجديدة
conn = sqlite3.connect("whatsapp_v3.db", check_same_thread=False)
c = conn.cursor()

# جدول المستخدمين
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

# جدول الرسائل المطور لدعم أنواع المرفقات
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

# مجلد لحفظ المرفقات محلياً
if not os.path.exists("media"):
    os.makedirs("media")

# 3. نظام تسجيل الدخول وإنشاء الحساب في السايدبار
if 'logged_in_user' not in st.session_state:
    st.session_state['logged_in_user'] = None

st.sidebar.markdown("<h3 style='center'>🔑 نظام الحسابات</h3>", unsafe_allow_html=True)

if st.session_state['logged_in_user'] is None:
    tab1, tab2 = st.sidebar.tabs(["تسجيل دخول", "إنشاء حساب جديد"])
    
    with tab1:
        login_user = st.text_input("اسم المستخدم:", key="login_u").strip()
        login_pass = st.text_input("كلمة السر:", type="password", key="login_p")
        if st.button("دخول"):
            user_data = c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (login_user, login_pass)).fetchone()
            if user_data:
                st.session_state['logged_in_user'] = login_user
                st.success(f"مرحباً {login_user}")
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة السر غلط!")
                
    with tab2:
        reg_user = st.text_input("اختر اسم مستخدم فريد:", key="reg_u").strip()
        reg_pass = st.text_input("اختر كلمة سر قوية:", type="password", key="reg_p")
        if st.button("تسجيل الحساب"):
            if reg_user and reg_pass:
                try:
                    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (reg_use
