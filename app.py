import streamlit as st
import pandas as pd
import google.generativeai as genai
import datetime

# ==========================================
# CẤU HÌNH HỆ THỐNG & API
# ==========================================
# 1. Điền API Key của Google Gemini
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3.1-flash-lite-preview') # Hoặc gemini-1.5-flash

# 2. Điền thông tin Google Sheets của thầy
SHEET_ID = "1p_ilhHY3gdTflc34afx2g5R5I-SkSR_dCxQI0vwFcq4"
USERS_GID = "0"
QUESTIONS_GID = "1486686052"

# Hàm tải dữ liệu từ Google Sheets (có lưu cache để web chạy nhanh)
@st.cache_data(ttl=60)
def load_google_sheet(sheet_id, gid):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    try:
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"Không thể tải dữ liệu. Lỗi: {e}")
        return pd.DataFrame()

# ==========================================
# KHỞI TẠO BỘ NHỚ TRẠNG THÁI (SESSION STATE)
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = ""
    st.session_state.ho_ten = ""

# ==========================================
# MODULE 1: GIAO DIỆN ĐĂNG NHẬP
# ==========================================
def login_page():
    st.title("🔐 Hệ sinh thái V-Edu 2026")
    st.write("Vui lòng đăng nhập để vào hệ thống ôn thi Vật lý.")
    
    with st.form("login_form"):
        user_input = st.text_input("Tên đăng nhập (Username):")
        pass_input = st.text_input("Mật khẩu:", type="password")
        submit_btn = st.form_submit_button("Đăng nhập")
        
        if submit_btn:
            df_users = load_google_sheet(SHEET_ID, USERS_GID)
            if not df_users.empty:
                # Ép kiểu mật khẩu về chuỗi để so sánh cho chuẩn
                df_users['Password'] = df_users['Password'].astype(str)
                
                # Tìm tài khoản trong Database
                user_match = df_users[(df_users['Username'] == user_input) & (df_users['Password'] == pass_input)]
                
                if not user_match.empty:
                    st.session_state.logged_in = True
                    st.session_state.username = user_match.iloc[0]['Username']
                    st.session_state.ho_ten = user_match.iloc[0]['Ho_Ten']
                    st.session_state.role = user_match.iloc[0]['Vai_Tro']
                    st.rerun() # Tải lại trang sau khi đăng nhập thành công
                else:
                    st.error("❌ Sai tên đăng nhập hoặc mật khẩu!")

# ==========================================
# MODULE 2: GIAO DIỆN HỌC SINH (LUYỆN ĐỀ)
# ==========================================
def student_dashboard():
    st.title(f"🎓 Xin chào em, {st.session_state.ho_ten}!")
    st.success("Hệ thống đã tải thành công ngân hàng câu hỏi mới nhất.")
    
    df_questions = load_google_sheet(SHEET_ID, QUESTIONS_GID)
    
    tab1, tab2 = st.tabs(["📝 Làm bài kiểm tra", "📊 Lịch sử học tập"])
    
    with tab1:
        st.subheader("Cấu trúc đề thi Vật lý 2026")
        
        # Hiển thị Phần I
        st.markdown("### Phần I: Trắc nghiệm 4 lựa chọn")
        q1 = df_questions[df_questions['Phan_Thi'] == 'Phan_I']
        if not q1.empty:
            cau_hoi_1 = q1.iloc[0]
            st.markdown(f"**Câu 1:** {cau_hoi_1['Noi_Dung']}")
            q1_ans = st.text_input("Nhập đáp án của em (A, B, C hoặc D):", key="q1")
            if st.button("Chấm điểm Phần I"):
                if q1_ans.strip().upper() == str(cau_hoi_1['Dap_An']).strip().upper():
                    st.success("✅ Chính xác! +0.25 điểm")
                else:
                    st.error(f"❌ Sai rồi. Đáp án đúng là {cau_hoi_1['Dap_An']}")
        
        st.markdown("---")
        # Hiển thị Phần III (AI Chấm)
        st.markdown("### Phần III: Trả lời ngắn (Trợ lý AI hỗ trợ)")
        q3 = df_questions[df_questions['Phan_Thi'] == 'Phan_III']
        if not q3.empty:
            cau_hoi_3 = q3.iloc[0]
            st.markdown(f"**Câu hỏi:** {cau_hoi_3['Noi_Dung']}")
            q3_ans = st.text_input("Nhập đáp án số cuối cùng:", key="q3")
            
            if st.button("Nộp bài Phần III & Xem nhận xét"):
                if q3_ans.strip() == str(cau_hoi_3['Dap_An']).strip():
                    st.success("✅ Hoàn toàn chính xác! +0.25 điểm")
                    st.balloons()
                else:
                    st.error(f"❌ Đáp án {q3_ans} chưa chính xác.")
                    with st.spinner("🤖 Trợ lý AI đang soạn lời giải chi tiết..."):
                        prompt = f"""
                        Đóng vai giáo viên Vật lý kiên nhẫn.
                        Đề bài: {cau_hoi_3['Noi_Dung']}
                        Đáp án chuẩn: {cau_hoi_3['Dap_An']}
                        Lời giải tham khảo: {cau_hoi_3['Loi_Giai_Chi_Tiet']}
                        Học sinh làm sai. Hãy giải thích từng bước (dùng công thức LaTeX) nhưng không nói toẹt đáp án cuối cùng.
                        """
                        try:
                            response = model.generate_content(prompt)
                            st.info(response.text)
                        except Exception as e:
                            st.error("Lỗi AI: " + str(e))
                            
    with tab2:
        st.info("Tính năng theo dõi biểu đồ tiến bộ sẽ được cập nhật trong phiên bản tới.")
        
    if st.sidebar.button("🚪 Đăng xuất"):
        st.session_state.logged_in = False
        st.rerun()

# ==========================================
# MODULE 3: GIAO DIỆN GIÁO VIÊN (QUẢN TRỊ)
# ==========================================
def teacher_dashboard():
    st.title("⚙️ Bảng Điều Khiển Của Giáo Viên")
    st.write(f"Đang đăng nhập dưới quyền Tổ trưởng CM: **{st.session_state.ho_ten}**")
    
    df_users = load_google_sheet(SHEET_ID, USERS_GID)
    df_questions = load_google_sheet(SHEET_ID, QUESTIONS_GID)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Tổng số học sinh", len(df_users[df_users['Vai_Tro'] == 'Học sinh']))
    with col2:
        st.metric("Số lượng câu hỏi trong kho", len(df_questions))
        
    st.subheader("📋 Danh sách câu hỏi hiện tại")
    st.dataframe(df_questions, use_container_width=True)
    
    st.info("Để thêm câu hỏi mới hoặc cập nhật điểm, thầy vui lòng mở trực tiếp file Google Sheets để chỉnh sửa. Dữ liệu sẽ tự động đồng bộ lên web sau 60 giây.")
    
    if st.sidebar.button("🚪 Đăng xuất"):
        st.session_state.logged_in = False
        st.rerun()

# ==========================================
# ĐIỀU HƯỚNG TRANG CHÍNH
# ==========================================
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.role == "Giáo viên":
        teacher_dashboard()
    elif st.session_state.role == "Học sinh":
        student_dashboard()
