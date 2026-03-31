import streamlit as st
from fpdf import FPDF
import os
import google.generativeai as genai

# --- 1. セキュリティ設定 ---
LAB_PASSWORD = "aoilabo1-205" 

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        st.title("🔑 実験設計・文献探索エンジン")
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

# --- 2. AIの設定（Google検索ツールを有効化） ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    api_key = "YOUR_LOCAL_API_KEY"

genai.configure(api_key=api_key)

# 検索ツールを定義
tools = [{"google_search_retrieval": {}}]

def get_model():
    # 検索機能を使用するため、1.5-flash または 1.5-pro を指定
    return genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        tools=tools
    )

model = get_model()

# --- 3. メインUI ---
st.title("🔬 実験設計 & リアルタイム文献探索")
st.caption("AIがネット上の学術情報を検索し、具体的な実験条件と参考文献を提案します。")

col_l, col_r = st.columns([2, 3])

with col_l:
    st.header("📝 実験設計プロトコル")
    main_theme = st.text_input("プロジェクト名", "例：LPD法による酸化バナジウム薄膜合成")
    sub_title = st.text_input("今回のサブ実験名", "例：溶液pHと析出速度の相関評価")
    
    s1 = st.text_area("1. 物理的境界条件と設定レンジ", height=100)
    s2 = st.text_area("2. パラメータの分解能", height=100)
    s3 = st.text_area("3. 成功・失敗の判定基準", height=100)

    if st.button("AIに相談（ネット検索を実行）"):
        if not (main_theme and sub_title):
            st.error("テーマと実験名を入力してください。")
        else:
            with st.spinner("最新の論文を検索しながらプランを精査中..."):
                prompt = f"""
                あなたは材料科学の専門家です。Google検索を活用して、以下の実験計画を査読し、具体的な参考文献を提示してください。
                
                テーマ: {main_theme} / 実験名: {sub_title}
                入力状況: {s1}, {s2}, {s3}

                【回答への要求】
                1. ネット検索を行い、このテーマに関連する実在する論文（著者、年、タイトル）を3つ程度挙げてください。
                2. 挙げた論文に基づき、具体的な実験数値（温度、濃度、pHなど）を逆提案してください。
                3. 日本語で解説し、検索に使用した英語キーワードも併記してください。
                """
                # 検索ツールを伴う生成
                response = model.generate_content(prompt)
                st.session_state['feedback'] = response.text

with col_r:
    st.header("🤖 AI指導員：査読 ＆ 文献提案")
    if 'feedback' in st.session_state:
        st.markdown(st.session_state['feedback'])

# --- 4. PDF出力 ---
st.divider()
if st.button("PDFレポートを生成"):
    # (中略：以前のPDF出力コードと同様)
    st.info("PDFを生成しました。")