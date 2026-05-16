import streamlit as st
import sqlite3
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh

# 1. إعدادات الصفحة والمنطقة الزمنية
st.set_page_config(page_title="WhatsApp V2", page_icon="💬", layout="wide")
egypt_tz = pytz.timezone('Africa/Cairo')

# تحديث تلقائي خفيف كل ثانيتين لتلقي الرسائل الجديدة
st_autorefresh(interval=2000, key="chat_refresh")

# حقن الـ CSS لتغيير الألوان بشكل احترافي وشبيه بالواتساب
st.markdown("""
    <style>
    [data-testid="stMainBlockContainer"] {
        background-color: #efeae2 !important;
    }
    [data-testid="stSidebar"] {
        background-color: #111b21 !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label {
        color: white !important;
    }
    .main-header {
        background-color: #008069;
        padding: 12px;
        color: white !important;
        font-size: 20px;
        font-weight: bold;
        border-radius: 8px;
        margin-bottom: 15px;
        text-align: center;
    }
    .msg-container {
        display: flex;
        flex-direction: column;
        margin: 8px 0;
    }
    .msg-box-sent {
        background-color: #d9fdd3;
        color: #111b21 !important;
        align-self: flex-end;
        padding: 8px 12px;
        border-radius: 8px 0px 8px 8px;
        max-width: 60%;
        box-shadow: 0 1px 1px rgba(0,0,0,0.1);
    }
    .msg-box-recv {
        background-color: #ffffff;
        color: #111b21 !important;
        align-self: flex-start;
        padding: 8px 12px;
        border-radius: 0px 8px 8px 8px;
        max-width: 60%;
        box-shadow: 0 1px 1px rgba(0,0,0,0.1);
    }
    .time-text {
        font-size: 10px;
        color: #667781 !important;
        text-align: right;
        margin-top: 4px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. إنشاء الاتصال بالداتابيز الجديدة
conn = sqlite3.connect("whatsapp_v2.db", check_same_thread=False)
c = conn.cursor()

# إنشاء جدول الرسائل بأعمدة تدعم تعدد الشاتات وعلامات القراءة
c.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    receiver TEXT,
    message TEXT,
    time TEXT,
    is_read INTEGER DEFAULT 0
)
""")
conn.commit()

# 3. التحكم في الواجهة والأسماء من الشريط الجانبي (Sidebar)
st.sidebar.markdown("<h3 style='color:white;'>🔑 تسجيل الدخول</h3>", unsafe_allow_html=True)
my_name = st.sidebar.selectbox("اختر اسمك الحالي:", ["عبد الرحمن", "أحمد", "محمد"])

st.sidebar.markdown("<hr style='border-color:#222c32;'>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='color:#8696a0;'>💬 اختر الشخص الذي تود محادثته:</p>", unsafe_allow_html=True)

# فلترة الأسماء عشان متكلمش نفسك
available_users = [user for user in ["عبد الرحمن", "أحمد", "محمد"] if user != my_name]
active_chat = st.sidebar.radio("المحادثات المتاحة:", available_users)

# 4. تشغيل الشات الرئيسي فوراً بناءً على الاختيارات
if my_name and active_chat:
    st.markdown(f"<div class='main-header'>🟢 محادثة نشطة: {active_chat} (أنت: {my_name})</div>", unsafe_allow_html=True)
    
    # بمجرد فتح الشات، تتحول الرسائل المستلمة لـ "تم القراءة"
    c.execute("UPDATE messages SET is_read = 1 WHERE sender = ? AND receiver = ?", (active_chat, my_name))
    conn.commit()
    
    # جلب الرسائل المتبادلة بين الطرفين فقط من الداتابيز
    chat_messages = c.execute("""
        SELECT id, sender, message, time, is_read 
        FROM messages 
        WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
        ORDER BY id ASC
    """, (my_name, active_chat, active_chat, my_name)).fetchall()
    
    # عرض الرسائل بتصميم الواتساب
    for msg_id, sender, text, tm, is_read in chat_messages:
        is_me = (sender == my_name)
        box_class = "msg-box-sent" if is_me else "msg-box-recv"
        
        # علامات القراءة للرسائل المرسلة مني (صح واحدة أو صحين)
        read_status = ""
        if is_me:
            read_status = " ✔️✔️" if is_read == 1 else " ✔️"
            
        st.markdown(f"""
            <div class="msg-container">
                <div class="{box_class}">
                    <div style="font-size: 11px; color: #008069; font-weight: bold; margin-bottom: 2px;">{sender}</div>
                    <div>{text}</div>
                    <div class="time-text">{tm}{read_status}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # ميزة حذف رسائل معينة
        if is_me or my_name == "عبد الرحمن":
            if st.button(f"🗑️ حذف", key=f"del_{msg_id}"):
                c.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
                conn.commit()
                st.rerun()

    # 5. صندوق إرسال الرسائل (ثابت أسفل الصفحة)
    st.markdown("<hr>", unsafe_allow_html=True)
    with st.form(key="send_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            txt_input = st.text_input("اكتب رسالتك هنا...", label_visibility="collapsed")
        with col2:
            btn_send = st.form_submit_button("إرسال 🚀")
            
        if btn_send and txt_input:
            now_str = datetime.now(egypt_tz).strftime("%I:%M %p")
            c.execute("""
                INSERT INTO messages (sender, receiver, message, time, is_read) 
                VALUES (?, ?, ?, ?, 0)
            """, (my_name, active_chat, txt_input, now_str))
            conn.commit()
            st.rerun()
