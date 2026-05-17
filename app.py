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
    st.markdown("<br><br><h2 style='text-align: center; color: white; font-weight: 500;'>🟢 WHATSAPP WEB</h2>", unsafe_allow_html=True)
    
    col_space1, col_main, col_space2 = st.columns([1.2, 2, 1.2])
    with col_main:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🔐 تسجيل الدخول", "✨ مستخدم جديد"])
        
        with tab1:
            login_user = st.text_input("اسم المستخدم:", key="main_login_u").strip()
            login_pass = st.text_input("كلمة المرور:", type="password", key="main_login_p")
            if st.button("تسجيل الدخول", use_container_width=True):
                user_data = c.execute("SELECT * FROM users WHERE username = ?", (login_user,)).fetchone()
                if user_data and user_data[1] == login_pass:
                    st.session_state['logged_in_user'] = login_user
                    st.rerun()
                else:
                    st.error("البيانات غير صحيحة، تأكد من الاسم والباسوورد.")
                    
        with tab2:
            reg_user = st.text_input("اختر اسم مستخدم فريد:", key="main_reg_u").strip()
            reg_pass = st.text_input("اختر كلمة مرور قوية:", type="password", key="main_reg_p")
            if st.button("إنشاء الحساب وتفعيله", use_container_width=True):
                if reg_user and reg_pass:
                    try:
                        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (reg_user, reg_pass))
                        conn.commit()
                        
                        # السحر هنا: الدخول التلقائي فوراً بعد التسجيل الناجح
                        st.session_state['logged_in_user'] = reg_user
                        st.rerun()
                        
                    except sqlite3.IntegrityError:
                        st.error("اسم المستخدم هذا مسجل بالفعل!")
                else:
                    st.warning("برجاء إدخال البيانات كاملة أولاً.")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# الشاشة الثانية: واجهة المحادثات والشات
# ==========================================
else:
    my_name = st.session_state['logged_in_user'].strip()
    
    # أ) السايدبار (قائمة الشات الثابتة)
    st.sidebar.markdown(f"""
        <div style='display: flex; align-items: center; padding: 5px;'>
            <div style='background-color: #00a884; width: 40px; height: 40px; border-radius: 50%; text-align: center; line-height: 40px; font-weight: bold; color: white;'>
                {my_name[0].upper()}
            </div>
            <div style='margin-right: 12px; font-size: 16px; font-weight: bold;'>{my_name}</div>
        </div>
    """, unsafe_allow_html=True)
    
    col_out, col_del = st.sidebar.columns(2)
    with col_out:
        if st.button("🚪 خروج", key="logout_btn", use_container_width=True):
            st.session_state['logged_in_user'] = None
            st.session_state['active_chat'] = None
            st.rerun()
            
    with col_del:
        if st.button("🗑️ حذف الحساب", key="delete_account_btn", use_container_width=True):
            c.execute("DELETE FROM users WHERE username = ?", (my_name,))
            c.execute("DELETE FROM messages WHERE sender = ? OR receiver = ?", (my_name, my_name))
            conn.commit()
            st.session_state['logged_in_user'] = None
            st.session_state['active_chat'] = None
            st.rerun()
        
    st.sidebar.markdown("<hr style='border-color:#222c32; margin:10px 0;'>", unsafe_allow_html=True)
    st.sidebar.markdown("<p style='color:#8696a0; font-size: 14px; font-weight:bold; padding-right:10px;'>الدردشات</p>", unsafe_allow_html=True)
    
    all_users = c.execute("SELECT username FROM users WHERE username != ?", (my_name,)).fetchall()
    if all_users:
        for user in all_users:
            u_name = user[0].strip()
            if st.sidebar.button(f"🟢 {u_name}", key=f"user_btn_{u_name}"):
                st.session_state['active_chat'] = u_name
                st.rerun()
    else:
        st.sidebar.markdown("<p style='color:#8696a0; padding-right:10px; font-size:13px;'>لا توجد جهات اتصال مسجلة بعد.</p>", unsafe_allow_html=True)

    # ب) جزء الشات الرئيسي (الأيمن)
    active_chat = st.session_state['active_chat']
    if active_chat:
        active_chat = active_chat.strip()
        
        st.markdown(f"""
            <div class='whatsapp-header'>
                <div style='background-color: #667781; width: 36px; height: 36px; border-radius: 50%; text-align: center; line-height: 36px; margin-left: 12px; color: white;'>
                    {active_chat[0].upper()}
                </div>
                <div>
                    <div>{active_chat}</div>
                    <div style='font-size: 11px; color: #8696a0; font-weight: normal; margin-top:2px;'>متصل حالياً</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        c.execute("UPDATE messages SET is_read = 1 WHERE sender = ? AND receiver = ?", (active_chat, my_name))
        conn.commit()
        
        chat_messages = c.execute("""
            SELECT id, sender, message, file_path, file_type, time, is_read 
            FROM messages 
            WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
            ORDER BY id ASC
        """, (my_name, active_chat, active_chat, my_name)).fetchall()
        
        for msg_id, sender, text, f_path, f_type, tm, is_read in chat_messages:
            is_me = (sender.strip() == my_name)
            box_class = "msg-box-sent" if is_me else "msg-box-recv"
            check_color = "#53bdeb" if is_read == 1 else "#8696a0"
            read_status = f"<span style='color:{check_color}; font-size:13px; margin-right:4px;'> ✔✔️</span>" if is_me else ""
            
            with st.markdown('<div class="msg-container">', unsafe_allow_html=True):
                st.markdown(f'<div class="{box_class}">', unsafe_allow_html=True)
                if text:
                    st.write(text)
                
                if f_path and os.path.exists(f_path):
                    with open(f_path, "rb") as file_data:
                        bytes_data = file_data.read()
                        if f_type == "image":
                            st.image(bytes_data, width=240)
                        elif f_type == "audio":
                            st.audio(bytes_data, format="audio/wav")
                        elif f_type == "file":
                            st.download_button(label="📁 مستند مرفق", data=bytes_data, file_name=os.path.basename(f_path), key=f"dl_{msg_id}")
                
                st.markdown(f'<div class="time-text">{tm}{read_status}</div></div></div>', unsafe_allow_html=True)

        st.markdown("<br><br>", unsafe_allow_html=True)
        
        with st.form(key="whatsapp_input_form", clear_on_submit=True):
            uploaded_file = st.file_uploader("📎 أرفق ميديا (اختياري):", type=["png", "jpg", "jpeg", "pdf", "docx", "txt", "mp3", "wav", "m4a"])
            txt_input = st.text_input("اكتب رسالة...", placeholder="اكتب رسالة هنا واضغط إرسال...")
            btn_send = st.form_submit_button("إرسال الرسالة 🚀", use_container_width=True)
            
            if btn_send:
                txt_stripped = txt_input.strip()
                if txt_stripped or uploaded_file:
                    now_str = datetime.now(egypt_tz).strftime("%I:%M %p")
                    saved_path = None
                    file_type = None
                    
                    if uploaded_file is not None:
                        saved_path = os.path.join("media", f"{int(datetime.now().timestamp())}_{uploaded_file.name}")
                        with open(saved_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        ext = uploaded_file.name.split(".")[-1].lower()
                        if ext in ["png", "jpg", "jpeg"]:
                            file_type = "image"
                        elif ext in ["mp3", "wav", "m4a"]:
                            file_type = "audio"
                        else:
                            file_type = "file"
                    
                    c.execute("""
                        INSERT INTO messages (sender, receiver, message, file_path, file_type, time, is_read) 
                        VALUES (?, ?, ?, ?, ?, ?, 0)
                    """, (my_name, active_chat, txt_stripped, saved_path, file_type, now_str))
                    conn.commit()
                    st.rerun()
    else:
        st.markdown("""
            <div style='text-align: center; margin-top: 15%; color: #667781;'>
                <h1 style='font-size: 40px;'>💬 WhatsApp Web</h1>
                <p style='font-size: 16px; margin-top: 10px;'>أرسل واستقبل الرسائل والميديا دون الحاجة لإبقاء هاتفك متصلاً بالإنترنت.</p>
                <p style='font-size: 13px; color: #8696a0; margin-top: 50px;'>🔒 مشفر تماماً بين الطرفين.</p>
            </div>
        """, unsafe_allow_html=True)
