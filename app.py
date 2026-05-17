import streamlit as st import sqlite3 from datetime import datetime import pytz import hashlib import os

=============================

'🔐' Security - Hash Password

=============================

def hash_password(password): return hashlib.sha256(password.encode()).hexdigest()

=============================

'⚙️' App Config

=============================

st.set_page_config(page_title="WhatsApp Pro", page_icon="💬", layout="wide")

egypt_tz = pytz.timezone('Africa/Cairo')

=============================

💾 Database

=============================

conn = sqlite3.connect("whatsapp_pro.db", check_same_thread=False) c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)")

c.execute(""" CREATE TABLE IF NOT EXISTS messages ( id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, receiver TEXT, message TEXT, file_path TEXT, file_type TEXT, time TEXT, is_read INTEGER DEFAULT 0 ) """) conn.commit()

if not os.path.exists("media"): os.makedirs("media")

=============================

🧠 Session State

=============================

if "user" not in st.session_state: st.session_state.user = None

if "chat" not in st.session_state: st.session_state.chat = None

=============================

🔑 Login / Register

=============================

if st.session_state.user is None: st.title("💬 WhatsApp Pro")

tab1, tab2 = st.tabs(["Login", "Register"])

with tab1:
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        data = c.execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()
        if data and data[1] == hash_password(p):
            st.session_state.user = u
            st.rerun()
        else:
            st.error("Wrong credentials")

with tab2:
    u = st.text_input("New Username")
    p = st.text_input("New Password", type="password")

    if st.button("Create Account"):
        try:
            c.execute("INSERT INTO users VALUES (?,?)", (u, hash_password(p)))
            conn.commit()
            st.success("Account created")
        except:
            st.error("Username exists")

=============================

💬 Chat System

=============================

else: me = st.session_state.user

# Sidebar users
st.sidebar.title(f"👤 {me}")

if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()

users = c.execute("SELECT username FROM users WHERE username!=?", (me,)).fetchall()

for u in users:
    if st.sidebar.button(u[0]):
        st.session_state.chat = u[0]

chat = st.session_state.chat

if chat:
    st.header(f"💬 Chat with {chat}")

    # Load messages (last 50)
    msgs = c.execute("""
    SELECT sender, message, file_path, file_type, time
    FROM messages
    WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
    ORDER BY id DESC LIMIT 50
    """, (me, chat, chat, me)).fetchall()

    msgs.reverse()

    for m in msgs:
        sender, text, f_path, f_type, t = m

        if sender == me:
            st.markdown(f"**🟢 You:** {text} ({t})")
        else:
            st.markdown(f"**⚪ {sender}:** {text} ({t})")

        if f_path:
            if "image" in str(f_type):
                st.image(f_path, width=200)
            else:
                with open(f_path, "rb") as f:
                    st.download_button("Download file", f, file_name=f_path)

    # Send message
    msg = st.text_input("Message")
    file = st.file_uploader("Send file")

    if st.button("Send"):
        now = datetime.now(egypt_tz).strftime("%H:%M")

        file_path = None
        file_type = None

        if file:
            file_path = f"media/{file.name}"
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
            file_type = file.type

        c.execute("""
        INSERT INTO messages (sender, receiver, message, file_path, file_type, time)
        VALUES (?,?,?,?,?,?)
        """, (me, chat, msg, file_path, file_type, now))

        conn.commit()
        st.rerun()

else:
    st.write("Select a user to start chatting")
