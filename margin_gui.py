import streamlit as st
import pandas as pd
from playwright.sync_api import sync_playwright
from io import StringIO

# =========================
# 頁面設定
# =========================

st.set_page_config(
    page_title="股票期貨保證金計算器",
    page_icon="📈",
    layout="centered"
)

st.title("📈 股票期貨保證金計算器")

# =========================
# 自動抓取 TAIFEX 資料
# =========================

@st.cache_data(ttl=86400)
def load_taifex_data():

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page()

        page.goto(
            "https://www.taifex.com.tw/cht/5/stockMargining",
            wait_until="networkidle"
        )

        page.wait_for_timeout(5000)

        html = page.content()

        browser.close()

    # 讀取所有表格
    tables = pd.read_html(StringIO(html))

    # 找最大表格
    df = max(tables, key=len)

    # 去除欄位空白
    df.columns = df.columns.str.strip()

    return df

# =========================
# 載入資料
# =========================

try:

    with st.spinner("正在更新 TAIFEX 保證金資料..."):

        df = load_taifex_data()

    st.success("TAIFEX 保證金資料更新完成")

except Exception as e:

    st.error(f"抓取資料失敗：{e}")

    st.stop()

# =========================
# 欄位名稱
# =========================

COL_STOCK_ID = "股票期貨標的 證券代號"
COL_NAME = "股票期貨 中文簡稱"
COL_MARGIN = "原始保證金適用比例"

# =========================
# 商品分類
# =========================

normal_df = df[
    ~df[COL_NAME].astype(str).str.contains(
        "小型",
        na=False
    )
]

mini_df = df[
    df[COL_NAME].astype(str).str.contains(
        "小型",
        na=False
    )
]

# =========================
# 商品類型
# =========================

product_type = st.radio(
    "請選擇商品類型",
    ["一般個股期", "小型個股期"]
)

# =========================
# 選擇資料來源
# =========================

if product_type == "一般個股期":

    temp_df = normal_df
    multiplier = 2000

else:

    temp_df = mini_df
    multiplier = 100

# =========================
# 商品清單
# =========================

temp_df = temp_df.copy()

temp_df["顯示名稱"] = (
    temp_df[COL_STOCK_ID].astype(str)
    + " - "
    + temp_df[COL_NAME].astype(str)
)

stock_select = st.selectbox(
    "選擇商品",
    temp_df["顯示名稱"].tolist()
)

# =========================
# 手動輸入股票代號
# =========================

manual_stock = st.text_input(
    "或直接輸入股票代號（可不填）"
)

# =========================
# 成交價
# =========================

price = st.number_input(
    "輸入成交價",
    min_value=0.0,
    step=1.0
)

# =========================
# 計算按鈕
# =========================

if st.button("計算保證金"):

    try:

        # =========================
        # 股票代號
        # =========================

        if manual_stock.strip() != "":

            stock_id = manual_stock.strip()

        else:

            stock_id = stock_select.split(" - ")[0]

        # =========================
        # 查詢資料
        # =========================

        result = temp_df[
            temp_df[COL_STOCK_ID].astype(str)
            == stock_id
        ]

        if result.empty:

            st.error("查無此商品")

        else:

            row = result.iloc[0]

            stock_name = str(row[COL_NAME])

            margin_ratio = str(row[COL_MARGIN])

            # 去除 %
            margin_ratio_float = float(
                margin_ratio.replace("%", "")
            ) / 100

            # =========================
            # 保證金計算
            # =========================

            contract_value = (
                price * multiplier
            )

            initial_margin = (
                contract_value
                * margin_ratio_float
            )

            # =========================
            # 顯示結果
            # =========================

            st.success("計算完成")

            st.write("## 計算結果")

            st.write(
                f"商品類型：{product_type}"
            )

            st.write(
                f"股票代號：{stock_id}"
            )

            st.write(
                f"商品名稱：{stock_name}"
            )

            st.write(
                f"成交價：{price:,.2f}"
            )

            st.write(
                f"原始保證金比例：{margin_ratio}"
            )

            st.write(
                f"契約乘數：{multiplier:,}"
            )

            st.write(
                f"契約價值：{contract_value:,.0f} 元"
            )

            st.write(
                f"## 原始保證金：{initial_margin:,.0f} 元"
            )

    except Exception as e:

        st.error(str(e))
