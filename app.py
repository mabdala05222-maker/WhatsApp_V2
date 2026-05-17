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

# حقن CSS لتصغير حجم الرسائل وتنسيق الواجهة
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

# 2. إعداد قاعدة البيانات
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

st.sidebar.markdown("<h3>🔑 نظام الحسابات</h3>", unsafe_allow_html=True)

if st.session_state['logged_in_user'] is None:
    tab1, tab2 = st.sidebar.tabs(["تسجيل دخول", "إنشاء حساب جديد"])
    
    with tab1:
        login_user = st.text_input("اسم المستخدم:", key="login_u").strip()
        login_pass = st.text_input("كلمة السر:", type="password", key="login_p")
        if st.button("دخول"):
            user_data = c.execute(
                "SELECT * FROM users WHERE username = ? AND password = ?", 
                (login_user, login_pass)
            ).fetchone()
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
                    # تقسيم السطر المسبب للمشكلة لسطور قصيرة ومقفولة صح
                    c.execute(
                        "INSERT INTO users (username, password) VALUES (?, ?)", 
                        (reg_user, reg_pass)
                    )
                    conn.commit()
                    st.success("تم إنشاء الحساب بنجاح! يمكنك الدخول الآن.")
                except sqlite3.IntegrityError:
                    st.error("الاسم ده محجوز لمستخدم تاني، اختر اسم غيره!")
            else:
                st.warning("يرجى ملء البيانات أولاً.")
else:
    my_name = st.session_state['logged_in_user']
    st.sidebar.markdown(f"🟢 مسجل كـ: **{my_name}**")
    if st.sidebar.button("تسجيل الخروج 🚪"):
        st.session_state['logged_in_user'] = None
        st.rerun()

    st.sidebar.markdown("<hr style='border-color:#222c32;'>", unsafe_allow_html=True)
    
    # 4. بدء محادثة جديدة عن طريق البحث عن الاسم
    st.sidebar.markdown("<p style='color:#8696a0;'>🔍 ابدأ محادثة جديدة:</p>", unsafe_allow_html=True)
    search_user = st.sidebar.text_input("اكتب اسم الشخص بالظبط:", key="search_u").strip()
    
    active_chat = None
    if search_user:
        check_exist = c.execute(
            "SELECT username FROM users WHERE username = ?", 
            (search_user,)
        ).fetchone()
        if check_exist:
            if search_user == my_name:
                st.sidebar.warning("مش هينفع تكلم نفسك يا هندسة!")
            else:
                active_chat = search_user
                st.sidebar.success(f"تم فتح الشات مع: {active_chat}")
        else:
            st.sidebar.error("المستخدم ده مش مسجل في البرنامج لسه.")

    # 5. الشات الرئيسي
    if active_chat:
        st.markdown(f"<div class='main-header'>🟢 محادثة نشطة مع: {active_chat}</div>", unsafe_allow_html=True)
        
        # تحديث الرسائل لـ مقروءة
        c.execute(
            "UPDATE messages SET is_read = 1 WHERE sender = ? AND receiver = ?", 
            (active_chat, my_name)
        )
        conn.commit()
        
        # جلب الرسائل
        chat_messages = c.execute("""
            SELECT id, sender, message, file_path, file_type, time, is_read 
            FROM messages 
            WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
            ORDER BY id ASC
        """, (my_name, active_chat, active_chat, my_name)).fetchall()
        
        # عرض الرسائل
        for msg_id, sender, text, f_path, f_type, tm, is_read in chat_messages:
            is_me = (sender == my_name)
            box_class = "msg-box-sent" if is_me else "msg-box-recv"
            read_status = " ✔️✔️" if (is_me and is_read == 1) else (" ✔️" if is_me else "")
            
            with st.markdown('<div class="msg-container">', unsafe_allow_html=True):
                st.markdown(f"""
                    <div class="{box_class}">
                        <div style="font-size: 11px; color: #008069; font-weight: bold; margin-bottom: 2px;">{sender}</div>
                """, unsafe_allow_html=True)
                
                if text:
                    st.write(text)
                
                # عرض المرفقات بناءً على نوعها
                if f_path and os.path.exists(f_path):
                    with open(f_path, "rb") as file_data:
                        bytes_data = file_data.read()
                        if f_type == "image":
                            st.image(bytes_data, width=250)
                        elif f_type == "audio":
                            st.audio(bytes_data, format="audio/wav")
                        elif f_type == "file":
                            st.download_button(
                                label="📁 تحميل المستند", 
                                data=bytes_data, 
                                file_name=os.path.basename(f_path), 
                                key=f"dl_{msg_id}"
                            )
                
                st.markdown(f'<div class="time-text">{tm}{read_status}</div></div></div>', unsafe_allow_html=True)

        # 6. صندوق الإرسال المتطور (نص ومرفقات)
        st.markdown("<hr>", unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "📎 أرسل (صورة، مستند، أو تسجيل صوتي):", 
            type=["png", "jpg", "jpeg", "pdf", "docx", "txt", "mp3", "wav", "m4a"]
        )
        
        with st.form(key="send_form_v3", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                txt_input = st.text_input("اكتب رسالتك هنا...", label_visibility="collapsed")
            with col2:
                btn_send = st.form_submit_button("إرسال 🚀")
                
            if btn_send and (txt_input or uploaded_file):
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
                """, (my_name, active_chat, txt_input, saved_path, file_type, now_str))
                conn.commit()
                st.rerun()
    else:
        st.info("قم بإنشاء حساب أو تسجيل الدخول، ثم ابحث عن اسم مستخدم آخر من القائمة الجانبية لبدء المحادثة!")
