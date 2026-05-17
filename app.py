import streamlit as st
import sqlite3
from datetime import datetime
import pytz
import hashlib
import os
from streamlit_autorefresh import st_autorefresh

# 🔐 تشفير الباسورد
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ⚙️ إعدادات التطبيق
st.set_page_config(page_title="WhatsApp Pro", page_icon="💬", layout="wide")
egypt_tz = pytz.timezone('Africa/Cairo')

# 🔄 تحديث تلقائي صامت كل ثانيتين
st_autorefresh(interval=2000, key="whatsapp_refresh_counter")

# 💾 قاعدة بيانات جديدة v7 تدعم نظام علامات الصح
conn = sqlite3.connect("whatsapp_v7.db", check_same_thread=False)
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)")

# إضافة عمود is_read (0 = لم تقرأ، 1 = قرأت)
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

if "user" not in st.session_state:
    st.session_state.user = None

if "chat" not in st.session_state:
    st.session_state.chat = None

# 🔑 تسجيل الدخول / إنشاء حساب
if st.session_state.user is None:
    st.title("💬 WhatsApp Pro")
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            data = c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
            if data and data[1] == hash_password(password):
                st.session_state.user = username
                st.rerun()
            else:
                st.error("Wrong username or password")

    with tab2:
        new_user = st.text_input("New Username", key="reg_user")
        new_pass = st.text_input("New Password", type="password", key="reg_pass")
        if st.button("Create Account"):
            try:
                c.execute("INSERT INTO users VALUES (?,?)", (new_user, hash_password(new_pass)))
                conn.commit()
                st.success("Account created")
            except:
                st.error("Username already exists")

# 💬 الشات
else:
    me = st.session_state.user
    st.sidebar.title(f"👤 {me}")

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.chat = None
        st.rerun()

    users = c.execute("SELECT username FROM users WHERE username!=?", (me,)).fetchall()
    for u in users:
        if st.sidebar.button(u[0], key=f"user_{u[0]}"):
            st.session_state.chat = u[0]
            st.rerun()

    chat = st.session_state.chat
    if chat:
        st.header(f"💬 Chat with {chat}")

        # 🔥 بمجرد فتح الشات: تحديث كل الرسائل القادمة من الطرف الآخر لتصبح "مقروءة"
        c.execute("UPDATE messages SET is_read = 1 WHERE sender = ? AND receiver = ?", (chat, me))
        conn.commit()

        # جلب الرسائل مع حالة القراءة
        msgs = c.execute("""
        SELECT sender, message, file_path, file_type, time, is_read
        FROM messages
        WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
        ORDER BY id ASC
        """, (me, chat, chat, me)).fetchall()

        for sender, text, f_path, f_type, t, is_read in msgs:
            
            # تحديد شكل ولون علامة الصح للرسائل التي أرسلتها أنا فقط
            if sender == me:
                # لون أزرق (#53bdeb) لو مقروءة، رمادي (#8696a0) لو وصلت ولم تقرأ بعد
                ticks_color = "#53bdeb" if is_read == 1 else "#8696a0"
                ticks_html = f" <span style='color:{ticks_color}; font-size:14px; font-weight:bold;'>✔✔</span>"
                st.markdown(f"🟢 **You:** {text} ({t}){ticks_html}", unsafe_allow_html=True)
            else:
                st.markdown(f"⚪ **{sender}:** {text} ({t})")

            if f_path and os.path.exists(f_path):
                if f_type and "image" in f_type:
                    st.image(f_path, width=200)
                else:
                    with open(f_path, "rb") as f:
                        st.download_button("Download file", f, file_name=f_path, key=f"file_{f_path}")

        st.divider()

        file = st.file_uploader("Send file", label_visibility="collapsed")
        msg = st.chat_input("اكتب رسالة هنا...", key="chat_message_input")

        if msg or file:
            now = datetime.now(egypt_tz).strftime("%H:%M")
            file_path = None
            file_type = None

            if file:
                file_path = f"media/{file.name}"
                with open(file_path, "wb") as f:
                    f.write(file.getbuffer())
                file_type = file.type

            # إدخال الرسالة وتعيين الحالة الافتراضية كـ غير مقروءة (0)
            c.execute("""
            INSERT INTO messages (sender, receiver, message, file_path, file_type, time, is_read)
            VALUES (?, ?, ?, ?, ?, ?, 0)
            """, (me, chat, msg if msg else "", file_path, file_type, now))
            
            conn.commit()
            st.rerun()
    else:
        st.write("👈 اختار شخص تبدأ معاه الشات")
