import streamlit as st
import pandas as pd
import google.generativeai as genai
import datetime
import requests

# ==========================================
# 1. CẤU HÌNH THÔNG SỐ (THẦY ĐIỀN VÀO ĐÂY)
# ==========================================
st.set_page_config(page_title="V-Edu 2026 - Luyện thi Vật lý", layout="wide")

SHEET_ID = "1p_ilhHY3gdTflc34afx2g5R5I-SkSR_dCxQI0vwFcq4"
USERS_GID = "0"
QUESTIONS_GID = "1486686052"
PROGRESS_GID = "778611050"
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzc94XGxN1mLCS-_bbBBhm8YgH_oi6W1m8MJA65WIxEWEBm9ufGzO-ch2Mp0poPFLN3/exec"

# Cấu hình Google Gemini AI
try:
    # Lấy chìa khóa từ Két sắt khi đẩy lên mạng
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    # Nếu chạy thử trên máy tính chưa có két sắt, thầy dán API Key trực tiếp vào dòng dưới:
    genai.configure(api_key=" AIzaSyBpyydr5r54YlH36qY14SlWW6jv7oC8isI")

model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')

# ==========================================
# 2. CÁC HÀM XỬ LÝ DỮ LIỆU & BỘ NHỚ
# ==========================================
@st.cache_data(ttl=10)
def load_google_sheet(sheet_id, gid):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    try:
        return pd.read_csv(url)
    except Exception as e:
        return None

# Khởi tạo bộ nhớ tạm để không mất dữ liệu khi chuyển tab
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
        user_input = st.text_input("Tên đăng nhập (Username):")
        pass_input = st.text_input("Mật khẩu:", type="password")
        submit_btn = st.form_submit_button("Đăng nhập")
        
        if submit_btn:
            df_users = load_google_sheet(SHEET_ID, USERS_GID)
            if df_users is not None and not df_users.empty:
                df_users['Password'] = df_users['Password'].astype(str)
                user_match = df_users[(df_users['Username'] == user_input) & (df_users['Password'] == pass_input)]
                
                if not user_match.empty:
                    st.session_state.logged_in = True
                    st.session_state.username = user_match.iloc[0]['Username']
                    st.session_state.ho_ten = user_match.iloc[0]['Ho_Ten']
                    st.session_state.role = user_match.iloc[0]['Vai_Tro']
                    st.rerun()
                else:
                    st.error("❌ Sai tên đăng nhập hoặc mật khẩu!")
            else:
                st.error("Không thể tải cơ sở dữ liệu. Vui lòng kiểm tra lại cấu hình SHEET_ID.")

# ==========================================
# 4. GIAO DIỆN HỌC SINH (LUYỆN ĐỀ & BIỂU ĐỒ)
# ==========================================
def student_dashboard():
    st.title(f"🎓 Xin chào em, {st.session_state.ho_ten}!")
    df_questions = load_google_sheet(SHEET_ID, QUESTIONS_GID)
    
    if df_questions is None or df_questions.empty:
        st.error("Chưa tải được Ngân hàng câu hỏi. Đang chờ kết nối...")
        return

    tab1, tab2 = st.tabs(["📝 Làm bài kiểm tra", "📈 Lịch sử & Biểu đồ"])
    
    # ---------------- TAB 1: LÀM BÀI ----------------
    with tab1:
        st.subheader("Cấu trúc đề thi Vật lý 2026")
        
        # --- PHẦN I ---
        st.markdown("### Phần I: Trắc nghiệm 4 lựa chọn")
        q1 = df_questions[df_questions['Phan_Thi'] == 'Phan_I']
        if not q1.empty:
            cau_hoi_1 = q1.iloc[0]
            st.markdown(f"**Câu 1:** {cau_hoi_1['Noi_Dung']}")
            q1_ans = st.text_input("Nhập đáp án của em (A, B, C hoặc D):", key="q1")
            
            if st.button("Chấm điểm Phần I"):
                if q1_ans.strip().upper() == str(cau_hoi_1['Dap_An']).strip().upper():
                    st.success("✅ Chính xác! +0.25 điểm")
                    st.session_state.diem_p1 = 0.25
                else:
                    st.error(f"❌ Sai rồi. Đáp án đúng là {cau_hoi_1['Dap_An']}")
                    st.session_state.diem_p1 = 0.0
                    
        # --- PHẦN II ---
        st.markdown("---")
        st.markdown("### Phần II: Trắc nghiệm Đúng/Sai")
        q2 = df_questions[df_questions['Phan_Thi'] == 'Phan_II']
        if not q2.empty:
            cau_hoi_2 = q2.iloc[0]
            st.markdown(f"**Câu 2:** {cau_hoi_2['Noi_Dung']}")
            
            # Tách đáp án chuẩn từ Google Sheets (VD: Đúng, Sai, Đúng, Sai)
            dap_an_chuan = [ans.strip().title() for ans in str(cau_hoi_2['Dap_An']).split(",")]
            
            col1, col2 = st.columns(2)
            with col1:
                y_a = st.radio("Ý a)", ["Đúng", "Sai"], index=None, horizontal=True, key="p2_a")
                y_b = st.radio("Ý b)", ["Đúng", "Sai"], index=None, horizontal=True, key="p2_b")
            with col2:
                y_c = st.radio("Ý c)", ["Đúng", "Sai"], index=None, horizontal=True, key="p2_c")
                y_d = st.radio("Ý d)", ["Đúng", "Sai"], index=None, horizontal=True, key="p2_d")
                
            if st.button("Chấm điểm Phần II"):
                if len(dap_an_chuan) == 4:
                    so_y_dung = 0
                    if y_a == dap_an_chuan[0]: so_y_dung += 1
                    if y_b == dap_an_chuan[1]: so_y_dung += 1
                    if y_c == dap_an_chuan[2]: so_y_dung += 1
                    if y_d == dap_an_chuan[3]: so_y_dung += 1
                    
                    # Logic chấm điểm lũy tiến
                    diem = 0.0
                    if so_y_dung == 1: diem = 0.1
                    elif so_y_dung == 2: diem = 0.25
                    elif so_y_dung == 3: diem = 0.5
                    elif so_y_dung == 4: diem = 1.0
                    
                    st.session_state.diem_p2 = diem
                    st.success(f"Em trả lời đúng {so_y_dung}/4 ý. Điểm Phần II: +{diem}")
                else:
                    st.error("⚠️ Lỗi dữ liệu: Cột Đáp án Phần II trên Sheets phải có đủ 4 ý, cách nhau bằng dấu phẩy.")

        # --- PHẦN III ---
        st.markdown("---")
        st.markdown("### Phần III: Trả lời ngắn (Trợ lý AI hỗ trợ)")
        q3 = df_questions[df_questions['Phan_Thi'] == 'Phan_III']
        if not q3.empty:
            cau_hoi_3 = q3.iloc[0]
            st.markdown(f"**Câu hỏi:** {cau_hoi_3['Noi_Dung']}")
            q3_ans = st.text_input("Nhập đáp án số cuối cùng:", key="q3")
            
            if st.button("Chấm điểm Phần III & Xem nhận xét AI"):
                # Chuẩn hóa đáp án (phòng trường hợp gõ dấu phẩy thay dấu chấm)
                ans_chuan_hoa = q3_ans.replace(",", ".").strip()
                dap_an_goc = str(cau_hoi_3['Dap_An']).replace(",", ".").strip()
                
                if ans_chuan_hoa == dap_an_goc:
                    st.success("✅ Hoàn toàn chính xác! +0.25 điểm")
                    st.session_state.diem_p3 = 0.25
                else:
                    st.error(f"❌ Đáp án {q3_ans} chưa chính xác.")
                    st.session_state.diem_p3 = 0.0
                    with st.spinner("🤖 Trợ lý AI đang phân tích lỗi sai..."):
                        prompt = f"""
                        Đóng vai giáo viên Vật lý phổ thông. 
                        Đề bài: {cau_hoi_3['Noi_Dung']}. 
                        Đáp án chuẩn: {cau_hoi_3['Dap_An']}. 
                        Lời giải: {cau_hoi_3['Loi_Giai_Chi_Tiet']}. 
                        Học sinh đang làm sai, hãy giải thích từng bước. 
                        Sử dụng cú pháp LaTeX (dùng $$ kẹp hai đầu, ví dụ $$Q = m \cdot \lambda$$) để viết công thức.
                        """
                        try:
                            st.info(model.generate_content(prompt).text)
                        except Exception as e:
                            st.error(f"Lỗi kết nối AI: {e}")

        # --- NÚT LƯU ĐIỂM ---
        st.markdown("---")
        if st.button("💾 Lưu toàn bộ điểm vào Hệ thống", type="primary"):
            with st.spinner("Đang đồng bộ dữ liệu lên máy chủ..."):
                tong = st.session_state.diem_p1 + st.session_state.diem_p2 + st.session_state.diem_p3
                thoigian = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                payload = {
                    "thoi_gian": thoigian,
                    "username": st.session_state.username,
                    "ho_ten": st.session_state.ho_ten,
                    "diem_i": st.session_state.diem_p1,
                    "diem_ii": st.session_state.diem_p2,
                    "diem_iii": st.session_state.diem_p3,
                    "tong_diem": tong
                }
                
                try:
                    res = requests.post(WEB_APP_URL, json=payload)
                    
                    # Giải mã câu trả lời thực sự từ bên trong Google
                    ket_qua = res.json()
                    
                    if res.status_code == 200 and ket_qua.get("status") == "success":
                        st.success(f"🎉 Đã lưu thành công! Tổng điểm của em là: {tong}")
                        st.balloons()
                    else:
                        # Nếu Google bị lỗi ngầm, nó sẽ in thẳng lỗi ra màn hình
                        st.error(f"⚠️ Web gửi được nhưng Google từ chối lưu. Lý do: {ket_qua.get('message', 'Lỗi không xác định')}")
                except Exception as e:
                    st.error(f"Lỗi kết nối mạng: {e}")

    # ---------------- TAB 2: BIỂU ĐỒ ----------------
    with tab2:
        st.subheader("📈 Biểu đồ năng lực của em")
        
        if st.button("🔄 Cập nhật dữ liệu mới nhất"):
            st.cache_data.clear()
            
        df_progress = load_google_sheet(SHEET_ID, PROGRESS_GID)
        
        if df_progress is not None and 'Username' in df_progress.columns:
            my_data = df_progress[df_progress['Username'] == st.session_state.username]
            
            if not my_data.empty:
                st.success("Đã tải thành công dữ liệu học tập của em!")
                
                chart_data = my_data[['Thoi_Gian', 'Tong_Diem']].copy()
                chart_data = chart_data.set_index('Thoi_Gian')
                st.line_chart(chart_data)
                
                st.markdown("**Chi tiết các lần nộp bài:**")
                st.dataframe(my_data[['Thoi_Gian', 'Diem_Phan_I', 'Diem_Phan_II', 'Diem_Phan_III', 'Tong_Diem']], use_container_width=True)
            else:
                st.info("📝 Hiện tại em chưa có bài thi nào được lưu. Hãy sang tab 'Làm bài kiểm tra', hoàn thành bài và bấm nút Lưu đỏ nhé!")
        else:
            st.warning("⚠️ Chưa kết nối được lịch sử. Thầy kiểm tra lại mã PROGRESS_GID hoặc cấu trúc cột trên Sheets.")

    # Nút đăng xuất
    if st.sidebar.button("🚪 Đăng xuất"):
        st.session_state.logged_in = False
        st.rerun()

# ==========================================
# 5. GIAO DIỆN GIÁO VIÊN (QUẢN TRỊ)
# ==========================================
def teacher_dashboard():
    st.title("⚙️ Bảng Điều Khiển Giáo Viên")
    st.write(f"Đang đăng nhập dưới quyền quản trị: **{st.session_state.ho_ten}**")
    st.info("Tại đây thầy có thể xem phổ điểm và tỷ lệ làm đúng từng câu của toàn bộ học sinh. Tính năng sẽ được mở rộng ở phiên bản sau.")
    
    if st.sidebar.button("🚪 Đăng xuất"):
        st.session_state.logged_in = False
        st.rerun()

# ==========================================
# ĐIỀU HƯỚNG TRANG (ROUTER CHÍNH)
# ==========================================
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.role == "Giáo viên":
        teacher_dashboard()
    else:
        student_dashboard()
