import streamlit as st
import io
import zipfile

st.title("📦 ULTRA PRO 재고 시스템 GitHub 배포용 ZIP 다운로드")

# ---------------------------
# 1️⃣ app.py 내용 (ULTRA PRO)
# ---------------------------
app_py = '''import streamlit as st
import pandas as pd
import os
import io
import plotly.express as px

st.set_page_config(page_title="ULTRA PRO 재고 관리", layout="wide")

DB_FILE = "database.csv"
COLUMNS = ["브랜드","플랫폼","상품명","상품대표코드","옵션코드","색상","사이즈","재고수량","가격"]

# ---------------------------
# 데이터 로드 / 저장
# ---------------------------
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# ---------------------------
# 세션 초기화
# ---------------------------
if "df" not in st.session_state:
    st.session_state.df = load_data()
if "brands" not in st.session_state:
    st.session_state.brands = ["메무아","안나","뮬랑"]
if "platforms" not in st.session_state:
    st.session_state.platforms = ["W컨셉","네이버","쿠팡","지그재그","에이블리","29cm"]

df = st.session_state.df.copy()

# ---------------------------
# 사이드바 관리
# ---------------------------
st.sidebar.header("관리 설정")
with st.sidebar.expander("브랜드 관리"):
    brand_df = pd.DataFrame(st.session_state.brands, columns=["브랜드"])
    edit = st.data_editor(brand_df, num_rows="dynamic", hide_index=True)
    st.session_state.brands = edit["브랜드"].dropna().tolist()

with st.sidebar.expander("플랫폼 관리"):
    platform_df = pd.DataFrame(st.session_state.platforms, columns=["플랫폼"])
    edit = st.data_editor(platform_df, num_rows="dynamic", hide_index=True)
    st.session_state.platforms = edit["플랫폼"].dropna().tolist()

# ---------------------------
# 상품 등록
# ---------------------------
st.sidebar.header("상품 등록")
mode = st.sidebar.radio("등록 방식", ["단일 등록","비율 분배 등록"])
with st.sidebar.form("add_product"):
    brand = st.selectbox("브랜드", st.session_state.brands)
    name = st.text_input("상품명")
    master = st.text_input("상품대표코드")
    color = st.text_input("색상")
    size = st.text_input("사이즈")
    option = st.text_input("옵션코드 (없으면 자동 생성)")
    price = st.number_input("가격", min_value=0)
    if option == "" and master != "":
        option = f"{master}-{color}-{size}"
    if mode == "단일 등록":
        platform = st.selectbox("플랫폼", st.session_state.platforms)
        qty = st.number_input("재고수량", min_value=0)
        submit = st.form_submit_button("상품 등록")
        if submit:
            new_row = pd.DataFrame([{
                "브랜드": brand,
                "플랫폼": platform,
                "상품명": name,
                "상품대표코드": master,
                "옵션코드": option,
                "색상": color,
                "사이즈": size,
                "재고수량": qty,
                "가격": price
            }])
            st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
            save_data(st.session_state.df)
            st.sidebar.success("등록 완료!")
    else:
        total = st.number_input("총 재고수량", min_value=1, value=100)
        ratios = {}
        for p in st.session_state.platforms:
            ratios[p] = st.number_input(f"{p} 비율(%)", 0, 100, 0)
        submit = st.form_submit_button("분배 등록")
        if submit:
            rows = []
            for p, r in ratios.items():
                if r > 0:
                    qty = int(total * (r / 100))
                    rows.append({
                        "브랜드": brand,
                        "플랫폼": p,
                        "상품명": name,
                        "상품대표코드": master,
                        "옵션코드": option,
                        "색상": color,
                        "사이즈": size,
                        "재고수량": qty,
                        "가격": price
                    })
            new_df = pd.DataFrame(rows)
            st.session_state.df = pd.concat([st.session_state.df, new_df], ignore_index=True)
            save_data(st.session_state.df)
            st.sidebar.success("분배 등록 완료!")

st.title("📦 ULTRA PRO 재고 관리 시스템")
df = st.session_state.df.copy()

# ---------------------------
# 검색 / 필터
# ---------------------------
st.subheader("상품 검색 & 필터")
search = st.text_input("상품명 또는 옵션코드 검색")
if search:
    df = df[df.apply(lambda row: search.lower() in str(row).lower(), axis=1)]
col1, col2 = st.columns(2)
brand_filter = col1.selectbox("브랜드 필터", ["전체"] + st.session_state.brands)
platform_filter = col2.selectbox("플랫폼 필터", ["전체"] + st.session_state.platforms)
if brand_filter != "전체":
    df = df[df["브랜드"] == brand_filter]
if platform_filter != "전체":
    df = df[df["플랫폼"] == platform_filter]

# ---------------------------
# 재고 테이블 / 수정
# ---------------------------
st.subheader("재고 테이블")
edited = st.data_editor(df, use_container_width=True, num_rows="dynamic")
if st.button("수정 저장"):
    st.session_state.df = edited
    save_data(edited)
    st.success("저장 완료!")

# ---------------------------
# 플랫폼별 재고 그래프
# ---------------------------
st.subheader("플랫폼별 재고 현황")
platform_sum = df.groupby("플랫폼")["재고수량"].sum().reset_index()
fig = px.bar(platform_sum, x="플랫폼", y="재고수량")
st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# 브랜드별 비율
# ---------------------------
st.subheader("브랜드 재고 비율")
brand_sum = df.groupby("브랜드")["재고수량"].sum().reset_index()
fig2 = px.pie(brand_sum, names="브랜드", values="재고수량")
st.plotly_chart(fig2, use_container_width=True)

# ---------------------------
# 재고 부족 상품
# ---------------------------
st.subheader("재고 부족 상품 (10개 이하)")
low_stock = df[df["재고수량"] <= 10]
st.dataframe(low_stock, use_container_width=True)

# ---------------------------
# 엑셀 업로드
# ---------------------------
st.subheader("엑셀 대량 업로드")
file = st.file_uploader("엑셀 업로드", type=["xlsx"])
if file:
    upload_df = pd.read_excel(file)
    st.session_state.df = pd.concat([df, upload_df], ignore_index=True)
    save_data(st.session_state.df)
    st.success("업로드 완료!")

# ---------------------------
# 전체 엑셀 다운로드
# ---------------------------
st.subheader("전체 재고 엑셀 다운로드")
def to_excel(data):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        data.to_excel(writer, index=False)
    return output.getvalue()
st.download_button(
    "엑셀 다운로드",
    data=to_excel(df),
    file_name="inventory.xlsx"
)

# ---------------------------
# 플랫폼 업로드 파일 생성
# ---------------------------
st.subheader("📤 플랫폼 업로드 파일 생성")
platform_select = st.selectbox("업로드 플랫폼 선택", st.session_state.platforms)
def make_upload_file(data, platform):
    d = data[data["플랫폼"] == platform].copy()
    if platform == "W컨셉":
        out = d[["옵션코드","재고수량"]]
        out.columns = ["option_code","stock"]
    elif platform == "쿠팡":
        out = d[["옵션코드","재고수량"]]
        out.columns = ["option_id","quantity"]
    elif platform == "네이버":
        out = d[["옵션코드","재고수량"]]
        out.columns = ["option_code","stock"]
    else:
        out = d[["옵션코드","재고수량"]]
    return out
if st.button("업로드 엑셀 생성"):
    upload_df = make_upload_file(df, platform_select)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        upload_df.to_excel(writer, index=False)
    st.download_button(
        "다운로드",
        data=output.getvalue(),
        file_name=f"{platform_select}_재고업로드.xlsx"
    )

# ---------------------------
# DB 백업
# ---------------------------
st.subheader("데이터 백업")
if os.path.exists(DB_FILE):
    st.download_button(
        "DB 백업 다운로드",
        open(DB_FILE,"rb"),
        file_name="database_backup.csv"
    )
'''

# ---------------------------
# 2️⃣ requirements.txt
# ---------------------------
requirements_txt = """streamlit
pandas
xlsxwriter
plotly
"""

# ---------------------------
# 3️⃣ database.csv
# ---------------------------
database_csv = "브랜드,플랫폼,상품명,상품대표코드,옵션코드,색상,사이즈,재고수량,가격\n"

# ---------------------------
# ZIP 생성
# ---------------------------
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("ultra_inventory_pro/app.py", app_py)
    zf.writestr("ultra_inventory_pro/requirements.txt", requirements_txt)
    zf.writestr("ultra_inventory_pro/database.csv", database_csv)

# ---------------------------
# 다운로드 버튼
# ---------------------------
st.download_button(
    label="ULTRA PRO GitHub 배포용 ZIP 다운로드",
    data=zip_buffer.getvalue(),
    file_name="ultra_inventory_pro.zip"
)