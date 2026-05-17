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
            login_user = st.text_input("اسم المستخدم:", key="main_login_u").strip()
            login_pass = st.text_input("كلمة السر:", type="password", key="main_login_p")
            if st.button("تسجيل الدخول وفتح الشات 🚀", use_container_width=True):
                user_data = c.execute(
                    "SELECT * FROM users WHERE username = ? AND password = ?", 
                    (login_user, login_pass)
                ).fetchone()
                if user_data:
                    st.session_state['logged_in_user'] = login_user
                    st.success(f"تم الدخول بنجاح! مرحباً {login_user}")
                    st.rerun()
                else:
                    st.error("اسم المستخدم أو كلمة السر غير صحيحة!")
                    
        with tab2:
            reg_user = st.text_input("اختر اسم مستخدم جديد:", key="main_reg_u").strip()
            reg_pass = st.text_input("اختر كلمة سر:", type="password", key="main_reg_p")
            if st.button("إنشاء الحساب الآن ✅", use_container_width=True):
                if reg_user and reg_pass:
                    try:
                        c.execute(
                            "INSERT INTO users (username, password) VALUES (?, ?)", 
                            (reg_user, reg_pass)
                        )
                        conn.commit()
                        st.success("تم إنشاء حسابك بنجاح! يمكنك الآن التوجه لتبويب تسجيل الدخول.")
                    except sqlite3.IntegrityError:
                        st.error("الاسم ده مسجل به مستخدم آخر بالفعل، اختر اسماً فريداً!")
                else:
                    st.warning("برجاء إدخال البيانات كاملة.")

# ==========================================
# 4. واجهة التطبيق بعد تسجيل الدخول الناجح
# ==========================================
else:
    my_name = st.session_state['logged_in_user']
    
    # أ) الشريط الجانبي (المستخدمين دايماً مفتوحين وظاهرين)
    st.sidebar.markdown(f"<h3>🟢 {my_name}</h3>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 تسجيل الخروج", key="logout_btn"):
        st.session_state['logged_in_user'] = None
        st.session_state['active_chat'] = None
        st.rerun()
        
    st.sidebar.markdown("<hr style='border-color:#222c32; margin:10px 0;'>", unsafe_allow_html=True)
    st.sidebar.markdown("<p style='color:#8696a0; font-weight:bold; padding-right:10px;'>📥 المحادثات المتاحة:</p>", unsafe_allow_html=True)
    
    # جلب كل المستخدمين المسجلين في النظام ما عدا أنا
    all_users = c.execute("SELECT username FROM users WHERE username != ?", (my_name,)).fetchall()
    
    if all_users:
        for user in all_users:
            u_name = user[0]
            # عرض اسم كل مستخدم كزرار ثابت مفتوح دايماً في السايدبار
            if st.sidebar.button(f"👤 {u_name}", key=f"user_btn_{u_name}"):
                st.session_state['active_chat'] = u_name
                st.rerun()
    else:
        st.sidebar.markdown("<p style='color:gray; padding-right:10px;'>لا يوجد مستخدمين آخرين مسجلين حالياً.</p>", unsafe_allow_html=True)

    # ب) صفحة الشات الرئيسية
    active_chat = st.session_state['active_chat']
    
    if active_chat:
        st.markdown(f"<div class='main-header'>🟢 محادثة نشطة مع: {active_chat}</div>", unsafe_allow_html=True)
        
        # تحويل الرسائل المستلمة لـ مقروءة
        c.execute(
            "UPDATE messages SET is_read = 1 WHERE sender = ? AND receiver = ?", 
            (active_chat, my_name)
        )
        conn.commit()
        
        # جلب الرسائل المتبادلة
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
                
                if f_path and os.path.exists(f_path):
                    with open(f_path, "rb") as file_data:
                        bytes_data = file_data.read()
                        if f_type == "image":
                            st.image(bytes_data, width=220)
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

        # صندوق الإرسال السفلي (نص ومرفقات)
        st.markdown("<hr>", unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "📎 أرفق ميديا (صورة، ملف صوتي، مستند):", 
            type=["png", "jpg", "jpeg", "pdf", "docx", "txt", "mp3", "wav", "m4a"],
            key="media_uploader"
        )
        
        with st.form(key="send_form_v4", clear_on_submit=True):
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
        st.info("👋 مرحباً بك! اختر أي مستخدم من القائمة الثابتة على اليمين لبدء الشات معه الآن.")
