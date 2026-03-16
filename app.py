import streamlit as st
import pandas as pd
import io
import math # 수학 계산용 (내림 처리 등)

# -----------------------------------------------------------------------------
# 1. 초기 설정 및 데이터 구조 정의
# -----------------------------------------------------------------------------
st.set_page_config(page_title="스마트 재고 관리", layout="wide")

# (1) 재고 데이터 초기화
if 'inventory_df' not in st.session_state:
    columns = ['브랜드', '플랫폼', '상품명', '상품대표코드', '옵션코드', '색상', '사이즈', '재고수량', '가격']
    st.session_state.inventory_df = pd.DataFrame(columns=columns)

# (2) 관리 브랜드/플랫폼 초기값 설정
if 'manage_brands' not in st.session_state:
    st.session_state.manage_brands = ["메무아", "안나", "뮬랑"]

if 'manage_platforms' not in st.session_state:
    st.session_state.manage_platforms = ["w컨셉", "네이버", "쿠팡", "지그재그", "에이블리", "29cm"]

# -----------------------------------------------------------------------------
# 2. 엑셀 생성 함수
# -----------------------------------------------------------------------------
def to_excel_with_dropdown(df, brand_list, platform_list):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='데이터')
        
        workbook = writer.book
        worksheet = writer.sheets['데이터']
        
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_fmt)
            worksheet.set_column(col_num, col_num, 15)

        if len(brand_list) > 0:
            worksheet.data_validation('A2:A1000', {'validate': 'list', 'source': brand_list})
        if len(platform_list) > 0:
            worksheet.data_validation('B2:B1000', {'validate': 'list', 'source': platform_list})
        
    return output.getvalue()

# -----------------------------------------------------------------------------
# 3. 사이드바: 설정 및 입력
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ 관리자 설정")

with st.sidebar.expander("🔽 브랜드 목록 관리 (클릭)"):
    st.caption("아래 표에서 브랜드를 추가/삭제하세요.")
    brand_df = pd.DataFrame(st.session_state.manage_brands, columns=["브랜드명"])
    edited_brand_df = st.data_editor(brand_df, num_rows="dynamic", hide_index=True, key="brand_editor")
    brands = edited_brand_df["브랜드명"].dropna().astype(str).tolist()
    st.session_state.manage_brands = brands

with st.sidebar.expander("🔽 플랫폼 목록 관리 (클릭)"):
    st.caption("아래 표에서 플랫폼을 추가/삭제하세요.")
    platform_df = pd.DataFrame(st.session_state.manage_platforms, columns=["플랫폼명"])
    edited_platform_df = st.data_editor(platform_df, num_rows="dynamic", hide_index=True, key="platform_editor")
    platforms = edited_platform_df["플랫폼명"].dropna().astype(str).tolist()
    st.session_state.manage_platforms = platforms

st.sidebar.markdown("---")
st.sidebar.header("📝 상품 등록")

# [NEW] 등록 방식 선택 (탭 대신 라디오 버튼 사용)
reg_mode = st.sidebar.radio("등록 방식 선택", ["단일 등록 (1개)", "비율 분배 등록 (%)"])

with st.sidebar.form("add_product_form"):
    # 공통 입력 항목
    sel_brand = st.selectbox("브랜드", brands)
    input_name = st.text_input("상품명")
    input_master_code = st.text_input("상품대표코드")
    input_option_code = st.text_input("옵션코드")
    
    c1, c2 = st.columns(2)
    input_color = c1.text_input("색상")
    input_size = c2.text_input("사이즈")
    input_price = st.number_input("가격", min_value=0, step=100)

    # --- 1. 단일 등록 모드 ---
    if reg_mode == "단일 등록 (1개)":
        st.markdown("---")
        sel_platform = st.selectbox("플랫폼 선택", platforms)
        input_qty = st.number_input("재고수량", min_value=0, value=0)
        
        submitted = st.form_submit_button("상품 추가")

        if submitted:
            current_codes = st.session_state.inventory_df['옵션코드'].astype(str).tolist()
            # 단일 등록 시 중복 체크 (같은 옵션코드+같은 플랫폼이 있는지 확인이 더 정확하지만, 여기선 단순화)
            # 여기서는 '옵션코드' 자체가 유니크하다고 가정하고 체크
            if str(input_option_code) in current_codes:
                 # 단, 이미 등록된 옵션코드라도 플랫폼이 다르면 허용해야 할 수도 있으나, 
                 # 사용자의 요청에 따라 옵션코드 중복 자체를 막는 로직 유지
                 st.sidebar.error(f"❌ 오류: '{input_option_code}'는 이미 존재하는 옵션코드입니다.")
            else:
                new_data = {
                    '브랜드': sel_brand, '플랫폼': sel_platform, '상품명': input_name,
                    '상품대표코드': input_master_code, '옵션코드': input_option_code,
                    '색상': input_color, '사이즈': input_size,
                    '재고수량': input_qty, '가격': input_price
                }
                st.session_state.inventory_df = pd.concat([st.session_state.inventory_df, pd.DataFrame([new_data])], ignore_index=True)
                st.sidebar.success("추가 완료!")

    # --- 2. 비율 분배 등록 모드 ---
    else:
        st.markdown("---")
        st.write("📊 **플랫폼별 재고 분배**")
        
        # 총 재고 입력
        total_qty = st.number_input("총 재고수량 (Total)", min_value=1, value=100)