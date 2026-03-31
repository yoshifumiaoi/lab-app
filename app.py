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

# --- 2. ブラウザの表示フォント修正 ---
st.markdown("""
    <style>
    html, body, [class*="css"], .stMarkdown, .stTextArea label, p {
        font-family: "Helvetica Neue", Arial, "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AIの設定 ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.warning("⚠️ Settings > Secrets で GEMINI_API_KEY を設定してください。")
    st.stop()

# 検索ツールを有効化
tools = [{"google_search_retrieval": {}}]
try:
    model = genai.GenerativeModel(model_name='models/gemini-1.5-flash', tools=tools)
except:
    model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')

# --- 4. メインUI ---
st.title("🔬 実験設計 & リアルタイム文献探索")
st.caption("AIが最新の学術情報を検索し、実験計画の妥当性を査読・アドバイスします。")

col_l, col_r = st.columns([2, 3])

with col_l:
    st.header("📝 実験設計プロトコル")
    
    # 1. 実験名
    sub_title = st.text_area(
        "実験名 / 検証内容", 
        placeholder="例：LPD法による酸化バナジウム薄膜合成の最適化", 
        height=80
    )

    # 2. 実験の仮説
    hypothesis = st.text_area(
        "実験の仮説", 
        placeholder="例：反応温度を上げることで、析出粒径が微細化し、膜の平坦性が向上すると予想する。", 
        height=100
    )
    
    # 3. 実験条件の範囲（変更箇所）
    s1 = st.text_area(
        "実験条件（パラメータ）をどのような範囲で振るか", 
        placeholder="例：温度（40℃〜80℃、10℃刻み）、溶液濃度（0.01M〜0.1M）",
        height=100
    )
    
    # 4. 評価方法（変更箇所）
    s2 = st.text_area(
        "どのような評価方法を採用するか", 
        placeholder="例：膜厚測定（段差計）、構造解析（XRD）、表面観察（SEM）",
        height=100
    )
    
    # 5. 判定基準（変更箇所）
    s3 = st.text_area(
        "何を判定基準とするか", 
        placeholder="例：膜厚が100nm以上かつ、結晶ピークが半値幅X以下であれば成功とする。",
        height=100
    )

    if st.button("AIに相談（ネット検索を実行）"):
        if not (sub_title or hypothesis):
            st.error("「実験名」または「仮説」の少なくとも一方は入力してください。")
        else:
            with st.spinner("AIが最新論文と照らし合わせて査読中..."):
                prompt = f"""
                あなたは材料科学の専門家です。提供された実験計画に対し、学術的・技術的な視点からアドバイスしてください。
                
                【実験名】: {sub_title if sub_title else "未入力"}
                【仮説】: {hypothesis if hypothesis else "未入力"}
                【パラメータの範囲】: {s1 if s1 else "未入力"}
                【評価・測定方法】: {s2 if s2 else "未入力"}
                【判定基準】: {s3 if s3 else "未入力"}

                【要求】
                1. 理論的妥当性の評価: 物理化学の原理に照らして、設定した範囲や評価方法が適切か指摘してください。
                2. 文献に基づく裏付け: Google検索を用い、このテーマに関連する実在する論文を提示してください。
                3. 未入力・不足項目への提案: 特に評価方法や判定基準が不十分な場合、専門家の視点で「逆提案」してください。
                4. 推奨される具体的な数値や、次のステップ。
                """
                try:
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
if st.button("PDFレポートを生成・保存"):
    pdf = FPDF()
    pdf.add_page()
    font_path = "ipaexg.ttf"
    if os.path.exists(font_path):
        pdf.add_font("IPAexG", fname=font_path)
        pdf.set_font("IPAexG", size=14)
        pdf.cell(0, 10, "実験実施計画書（AI査読レポート）", ln=True, align='C')
        pdf.ln(5)
        
        sections = [
            ("■ 実験名", sub_title),
            ("■ 実験の仮説", hypothesis),
            ("■ 実験条件の範囲", s1),
            ("■ 採用する評価方法", s2),
            ("■ 成功・失敗の判定基準", s3)
        ]
        
        for t, c in sections:
            if c:
                pdf.set_font("IPAexG", style='B', size=10)
                pdf.cell(0, 8, t, ln=True)
                pdf.set_font("IPAexG", size=9)
                pdf.multi_cell(0, 6, str(c))
                pdf.ln(2)
        
        if 'feedback' in st.session_state:
            pdf.add_page()
            pdf.set_font("IPAexG", size=11)
            pdf.cell(0, 10, "■ AIによる具体的提案と参考文献", ln=True)
            pdf.set_font("IPAexG", size=9)
            pdf.multi_cell(0, 5, st.session_state['feedback'])
            
        pdf_file = "Experiment_Design_Report.pdf"
        pdf.output(pdf_file)
        with open(pdf_file, "rb") as f:
            st.download_button("PDFをダウンロード", f, file_name=f"Report_{sub_title[:10] if sub_title else 'Lab'}.pdf")    )
    
    # 3. 物理的境界条件
    s1 = st.text_area("1. 物理的境界条件と設定レンジ", height=100)
    
    # 4. 分解能
    s2 = st.text_area("2. パラメータの分解能", height=100)
    
    # 5. 判定基準
    s3 = st.text_area("3. 成功・失敗の判定基準", height=100)

    if st.button("AIに相談（ネット検索を実行）"):
        # 少なくとも「実験名」か「仮説」のどちらかがあれば実行可能にする
        if not (sub_title or hypothesis):
            st.error("「実験名」または「仮説」の少なくとも一方は入力してください。")
        else:
            with st.spinner("情報を精査中..."):
                # 入力されていない項目を明示するプロンプト
                prompt = f"""
                あなたは材料科学の専門家です。提供された断片的な実験計画に対し、不足部分を補完しながらアドバイスしてください。
                
                【実験名】: {sub_title if sub_title else "未入力"}
                【仮説】: {hypothesis if hypothesis else "未入力"}
                【物理的条件】: {s1 if s1 else "未入力"}
                【分解能】: {s2 if s2 else "未入力"}
                【判定基準】: {s3 if s3 else "未入力"}

                【要求】
                1. 仮説の妥当性評価: 物理化学の原理に基づき、仮説が合理的か、あるいは見落としがないか指摘してください。
                2. 実在する参考文献の提示: Google検索結果に基づき、この検証に役立つ論文を提示してください。
                3. 未入力項目への提案: 「未入力」の項目がある場合、先行研究から推測される適切な条件や指標を「逆提案」してください。
                4. 具体的数値の例示。
                """
                try:
                    response = model.generate_content(prompt)
                    st.session_state['feedback'] = response.text
                except Exception as e:
                    st.error(f"AI実行エラー: {e}")

with col_r:
    st.header("🤖 AI指導員：査読 ＆ 文献提案")
    if 'feedback' in st.session_state:
        st.markdown(st.session_state['feedback'])

# --- 5. PDF出力 ---
st.divider()
if st.button("PDFレポートを生成・保存"):
    pdf = FPDF()
    pdf.add_page()
    font_path = "ipaexg.ttf"
    if os.path.exists(font_path):
        pdf.add_font("IPAexG", fname=font_path)
        pdf.set_font("IPAexG", size=14)
        pdf.cell(0, 10, "実験実施計画書（AI査読付）", ln=True, align='C')
        pdf.ln(5)
        
        sections = [
            ("■ 実験名", sub_title),
            ("■ 実験の仮説", hypothesis),
            ("■ 物理的境界条件", s1),
            ("■ パラメータ分解能", s2),
            ("■ 判定基準", s3)
        ]
        
        for t, c in sections:
            if c: # 入力がある場合のみPDFに記載
                pdf.set_font("IPAexG", style='B', size=10)
                pdf.cell(0, 8, t, ln=True)
                pdf.set_font("IPAexG", size=9)
                pdf.multi_cell(0, 6, str(c))
                pdf.ln(2)
        
        if 'feedback' in st.session_state:
            pdf.add_page()
            pdf.set_font("IPAexG", size=11)
            pdf.cell(0, 10, "■ AIによる具体的提案と参考文献リスト", ln=True)
            pdf.set_font("IPAexG", size=9)
            pdf.multi_cell(0, 5, st.session_state['feedback'])
            
        pdf_file = "Experiment_Plan.pdf"
        pdf.output(pdf_file)
        with open(pdf_file, "rb") as f:
            st.download_button("PDFをダウンロード", f, file_name=f"Plan_{sub_title[:10] if sub_title else 'NoTitle'}.pdf")
