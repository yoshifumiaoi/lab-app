import streamlit as st
from fpdf import FPDF
import os
import google.generativeai as genai

# --- 1. セキュリティ設定 ---
# 公開時はこの値を研究室独自のパスワードに変更してください
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

# --- 2. AIの設定 ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.warning("⚠️ Settings > Secrets で GEMINI_API_KEY を設定してください。")
    st.stop()

# 検索ツールを有効化
tools = [{"google_search_retrieval": {}}]
model = genai.GenerativeModel(model_name='gemini-1.5-flash', tools=tools)

# --- 3. メインUI ---
st.title("🔬 実験設計 & リアルタイム文献探索")
st.caption("AIがネット上の学術情報を検索し、具体的な実験条件と参考文献を提案します。")

col_l, col_r = st.columns([2, 3])

with col_l:
    st.header("📝 実験設計プロトコル")
    
    # 複数行入力（text_area）に変更
    main_theme = st.text_area("プロジェクト名 / 研究背景", 
                              placeholder="例：LPD法による酸化バナジウム薄膜合成。デバイス応用を見据えた低温プロセス開発。", height=80)
    
    sub_title = st.text_area("今回のサブ実験名 / 検証内容", 
                             placeholder="例：溶液pHと析出速度の相関。特にpH 4.0付近の結晶性への影響。", height=80)
    
    s1 = st.text_area("1. 物理적境界条件と設定レンジ", height=100)
    s2 = st.text_area("2. パラメータの分解能", height=100)
    s3 = st.text_area("3. 成功・失敗の判定基準", height=100)

    if st.button("AIに相談（ネット検索を実行）"):
        if not (main_theme and sub_title and s1):
            st.error("テーマ、実験名、条件を入力してください。")
        else:
            with st.spinner("最新の論文を検索しながらプランを精査中..."):
                prompt = f"""
                あなたは材料科学の専門家です。Google検索を活用して、以下の実験計画を査読し、具体的な参考文献を提示してください。
                
                【テーマ・背景】: {main_theme}
                【実験内容】: {sub_title}
                【設計要件】: 1.{s1} / 2.{s2} / 3.{s3}

                【回答構成】
                1. 理論的整合性のチェック: 物理化学的な視点から条件設定の妥当性を指摘。
                2. 実在する参考文献の提示: Google検索結果に基づき、著者・年・タイトルを明記。
                3. 具体的数値の逆提案: 論文に基づき「〇〇℃」「〇〇M」などの数値を提示。
                4. 検索に使用した英語キーワードの併記。
                """
                response = model.generate_content(prompt)
                st.session_state['feedback'] = response.text

with col_r:
    st.header("🤖 AI指導員：査読 ＆ 文献提案")
    if 'feedback' in st.session_state:
        st.markdown(st.session_state['feedback'])

# --- 4. PDF出力 ---
st.divider()
if st.button("PDFレポートを生成・保存"):
    pdf = FPDF()
    pdf.add_page()
    font_path = "ipaexg.ttf"
    if os.path.exists(font_path):
        pdf.add_font("IPAexG", fname=font_path)
        pdf.set_font("IPAexG", size=14)
        pdf.cell(0, 10, "実験実施計画書（AI査読付）", ln=True, align='C')
        pdf.set_font("IPAexG", size=9)
        pdf.ln(5)
        
        sections = [
            ("■ プロジェクト背景", main_theme),
            ("■ サブ実験内容", sub_title),
            ("■ 物理的境界条件", s1),
            ("■ パラメータ分解能", s2),
            ("■ 判定基準", s3)
        ]
        
        for t, c in sections:
            pdf.set_font("IPAexG", 'B', 10)
            pdf.cell(0, 8, t, ln=True)
            pdf.set_font("IPAexG", size=9)
            pdf.multi_cell(0, 6, c)
            pdf.ln(2)
        
        if 'feedback' in st.session_state:
            pdf.add_page()
            pdf.set_font("IPAexG", 'B', 11)
            pdf.cell(0, 10, "■ AIによる具体的提案と参考文献リスト", ln=True)
            pdf.set_font("IPAexG", size=9)
            pdf.multi_cell(0, 5, st.session_state['feedback'])
            
        pdf_file = "Experiment_Plan_Refined.pdf"
        pdf.output(pdf_file)
        with open(pdf_file, "rb") as f:
            st.download_button("PDFをダウンロード", f, file_name=pdf_file)
