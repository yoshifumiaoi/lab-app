import streamlit as st
from fpdf import FPDF
import os
import google.generativeai as genai

# --- 1. セキュリティ設定 ---
LAB_PASSWORD = "lab_pro_2026" 

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        st.title("🔑 実験設計コーチング・エンジン")
        pw = st.text_input("研究室専用パスワード", type="password")
        if st.button("ログイン"):
            if pw == LAB_PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("パスワードが違います。")
        return False
    return True

if not check_password():
    st.stop()

# --- 2. 表示フォント修正 ---
st.markdown("""
    <style>
    html, body, [class*="css"], .stMarkdown, .stTextArea label, p {
        font-family: "Helvetica Neue", Arial, "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AIの設定 (最も標準的な呼び出し) ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.warning("⚠️ Settings > Secrets で GEMINI_API_KEY を設定してください。")
    st.stop()

# toolsなどのオプションを一切排除し、標準の1.5-flashのみを指定
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"モデルの起動失敗: {e}")
    st.stop()

# --- 4. メインUI ---
st.title("🔬 実験設計 & 参考文献ナビゲーター")

col_l, col_r = st.columns([2, 3])

with col_l:
    st.header("📝 実験設計プロトコル")
    sub_title = st.text_area("実験名 / 検証内容", height=80)
    hypothesis = st.text_area("実験の仮説", height=100)
    s1 = st.text_area("実験条件（パラメータ）をどのような範囲で振るか", height=100)
    s2 = st.text_area("どのような評価方法を採用するか", height=100)
    s3 = st.text_area("何を判定基準とするか", height=100)

    if st.button("AIに相談する"):
        if not (sub_title or hypothesis):
            st.error("「実験名」または「仮説」を入力してください。")
        else:
            with st.spinner("AIがプランを精査中..."):
                prompt = f"""
                あなたは材料科学の専門家です。以下の実験計画を査読し、物理化学の視点からアドバイスしてください。
                【実験名】: {sub_title} / 【仮説】: {hypothesis} / 【範囲】: {s1} / 【評価】: {s2} / 【基準】: {s3}
                1. 理論的妥当性 2. 具体的数値の提案 3. 推奨文献・キーワード 4. 注意点 を回答してください。
                """
                try:
                    # 検索なしの純粋な生成を実行
                    response = model.generate_content(prompt)
                    st.session_state['feedback'] = response.text
                except Exception as e:
                    st.error(f"AI実行エラー: {e}")

with col_r:
    st.header("🤖 AI指導員：査読結果")
    if 'feedback' in st.session_state:
        st.markdown(st.session_state['feedback'])

# --- 5. PDF出力 ---
st.divider()
if st.button("PDFレポートを生成"):
    pdf = FPDF()
    pdf.add_page()
    font_path = "ipaexg.ttf"
    if os.path.exists(font_path):
        pdf.add_font("IPAexG", fname=font_path)
        pdf.set_font("IPAexG", size=12)
        pdf.cell(0, 10, "実験実施計画書", ln=True, align='C')
        pdf.set_font("IPAexG", size=10)
        pdf.multi_cell(0, 8, f"実験名: {sub_title}\n仮説: {hypothesis}\n条件: {s1}\n評価: {s2}\n基準: {s3}")
        if 'feedback' in st.session_state:
            pdf.add_page()
            pdf.multi_cell(0, 6, f"【AI査読結果】\n{st.session_state['feedback']}")
        pdf.output("report.pdf")
        with open("report.pdf", "rb") as f:
            st.download_button("PDFをダウンロード", f, file_name="report.pdf")
