import streamlit as st
import pandas as pd
import google.generativeai as genai
import datetime
import requests

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG
# ==========================================
st.set_page_config(page_title="V-Edu 2026 - Hệ thống Luyện thi Vật lý", layout="wide")

# THẦY ĐIỀN CÁC THÔNG SỐ CỦA THẦY VÀO ĐÂY:
SHEET_ID = "1p_ilhHY3gdTflc34afx2g5R5I-SkSR_dCxQI0vwFcq4"
USERS_GID = "0"
QUESTIONS_GID = "1486686052"
PROGRESS_GID = "778611050"
WEB_APP_URL = " ttps://script.google.com/macros/s/AKfycbzc94XGxN1mLCS-_bbBBhm8YgH_oi6W1m8MJA65WIxEWEBm9ufGzO-ch2Mp0poPFLN3/exec"

# Cấu hình Google Gemini AI
try:
    # Lấy chìa khóa từ Két sắt khi đẩy lên mạng
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    # Nếu chạy thử trên máy tính chưa có két sắt, thầy dán API Key trực tiếp vào dòng dưới:
    genai.configure(api_key=" AIzaSyBpyydr5r54YlH36qY14SlWW6jv7oC8isI")

model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')

# ==========================================
# 2. HÀM TẢI DỮ LIỆU (LOAD_GOOGLE_SHEET)
# ==========================================
@st.cache_data(ttl=10)
def load_google_sheet(sheet_id, gid):
    """Hàm này giúp đọc dữ liệu từ Google Sheets và xử lý lỗi định dạng số"""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        
        # Vệ sĩ dữ liệu: Tự động chuyển dấu phẩy (,) thành dấu chấm (.) để tính toán
        cols_to_fix = ['Diem_Phan_I', 'Diem_Phan_II', 'Diem_Phan_III', 'Tong_Diem']
        for col in cols_to_fix:
            if col in df.columns:
                # Chuyển về chuỗi, thay dấu phẩy, ép về số, nếu lỗi thì để là 0
                df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu từ Sheets: {e}")
        return pd.DataFrame()

# Khởi tạo bộ nhớ (Session State)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = ""
    st.session_state.ho_ten = ""
if "diem_p1" not in st.session_state: st.session_state.diem_p1 = 0.0
if "diem_p2" not in st.session_state: st.session_state.diem_p2 = 0.0
if "diem_p3" not in st.session_state: st.session_state.diem_p3 = 0.0

# ==========================================
# 3. GIAO DIỆN ĐĂNG NHẬP
# ==========================================
def login_page():
    st.title("🔐 Hệ sinh thái V-Edu 2026")
    st.markdown("---")
    with st.form("login_form"):
        u = st.text_input("Tên đăng nhập:")
        p = st.text_input("Mật khẩu:", type="password")
        if st.form_submit_button("Đăng nhập"):
            df_u = load_google_sheet(SHEET_ID, USERS_GID)
            if not df_u.empty:
                df_u['Password'] = df_u['Password'].astype(str)
                user = df_u[(df_u['Username'] == u) & (df_u['Password'] == p)]
                if not user.empty:
                    st.session_state.logged_in = True
                    st.session_state.username = user.iloc[0]['Username']
                    st.session_state.ho_ten = user.iloc[0]['Ho_Ten']
                    st.session_state.role = user.iloc[0]['Vai_Tro']
                    st.rerun()
                else: st.error("Sai tài khoản hoặc mật khẩu!")

# ==========================================
# 4. GIAO DIỆN HỌC SINH
# ==========================================
def student_dashboard():
    st.title(f"🎓 Chào em, {st.session_state.ho_ten}!")
    df_q = load_google_sheet(SHEET_ID, QUESTIONS_GID)
    
    t1, t2 = st.tabs(["📝 Làm bài", "📈 Tiến bộ"])
    
    with t1:
        # Code hiển thị 3 phần thi (Rút gọn để thầy dễ nhìn)
        st.info("Hệ thống đã sẵn sàng. Hãy trả lời các câu hỏi bên dưới.")
        # (Thầy có thể dán lại code chi tiết Phần I, II, III vào đây sau)
        
        if st.button("💾 Lưu điểm vào hệ thống", type="primary"):
            tong = st.session_state.diem_p1 + st.session_state.diem_p2 + st.session_state.diem_p3
            payload = {
                "thoi_gian": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "username": st.session_state.username, "ho_ten": st.session_state.ho_ten,
                "diem_i": st.session_state.diem_p1, "diem_ii": st.session_state.diem_p2,
                "diem_iii": st.session_state.diem_p3, "tong_diem": tong
            }
            try:
                r = requests.post(WEB_APP_URL, json=payload)
                if r.status_code == 200: st.success("Lưu thành công!"); st.balloons()
            except: st.error("Lỗi gửi điểm!")

    with t2:
        st.subheader("Biểu đồ năng lực")
        df_p = load_google_sheet(SHEET_ID, PROGRESS_GID)
        if not df_p.empty:
            my_data = df_p[df_p['Username'] == st.session_state.username]
            if not my_data.empty:
                st.line_chart(my_data.set_index('Thoi_Gian')['Tong_Diem'])
                st.dataframe(my_data)
            else: st.write("Chưa có dữ liệu.")

# ==========================================
# 5. GIAO DIỆN GIÁO VIÊN (ĐÃ SỬA LỖI MEAN)
# ==========================================
def teacher_dashboard():
    st.title("⚙️ Dashboard Quản lý")
    if st.button("🔄 Làm mới dữ liệu"): st.cache_data.clear()
    
    df_p = load_google_sheet(SHEET_ID, PROGRESS_GID)
    if not df_p.empty:
        # Tính toán an toàn, tránh lỗi string
        diem_so = pd.to_numeric(df_p['Tong_Diem'], errors='coerce').fillna(0)
        st.metric("Điểm Trung Bình Lớp", round(diem_so.mean(), 2))
        st.bar_chart(diem_so.value_counts().sort_index())
        st.dataframe(df_p)
    else:
        st.write("Chưa có học sinh nào nộp bài.")

# ĐIỀU HƯỚNG
if not st.session_state.logged_in: login_page()
elif st.session_state.role == "Giáo viên": teacher_dashboard()
else: student_dashboard()
