import streamlit as st
import pandas as pd
import requests
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
# 抓取 TAIFEX 資料
# =========================

@st.cache_data(ttl=3600)
def load_taifex_data():

    url = "https://www.taifex.com.tw/cht/5/stockMargining"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    response.encoding = "utf-8"

    # =========================
    # DEBUG資訊
    # =========================

    st.write("HTTP狀態碼：", response.status_code)

    st.write("前1000字內容：")

    st.text(response.text[:1000])

    # =========================
    # 讀取表格
    # =========================

    try:

        tables = pd.read_html(
            StringIO(response.text)
        )

        st.write("找到表格數量：", len(tables))

        df = max(tables, key=len)

        st.write("表格預覽：")

        st.dataframe(df.head())

    except Exception as e:

        st.error(f"讀取表格失敗：{e}")

        st.stop()

    # =========================
    # 清理欄位名稱
    # =========================

    df.columns = [
        str(col).replace("\n", " ").strip()
        for col in df.columns
    ]

    return df

# =========================
# 載入資料
# =========================

try:

    df = load_taifex_data()

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
# 檢查欄位
# =========================

st.write("目前欄位：")

st.write(df.columns.tolist())

# =========================
# 商品分類
# =========================

try:

    normal_df = df[
        ~df[COL_NAME].astype(str).str.contains("小型", na=False)
    ]

    mini_df = df[
        df[COL_NAME].astype(str).str.contains("小型", na=False)
    ]

except Exception as e:

    st.error(f"欄位錯誤：{e}")

    st.stop()

# =========================
# 商品類型
# =========================

product_type = st.radio(
    "商品類型",
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
# 商品選單
# =========================

temp_df = temp_df.copy()

temp_df["選單"] = (
    temp_df[COL_STOCK_ID].astype(str)
    + " - "
    + temp_df[COL_NAME].astype(str)
)

stock_select = st.selectbox(
    "選擇商品",
    temp_df["選單"].tolist()
)

# =========================
# 手動輸入股票代號
# =========================

manual_stock = st.text_input(
    "或手動輸入股票代號"
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

        if manual_stock.strip():

            stock_id = manual_stock.strip()

        else:

            stock_id = stock_select.split(" - ")[0]

        # =========================
        # 查詢商品
        # =========================

        result = temp_df[
            temp_df[COL_STOCK_ID].astype(str) == stock_id
        ]

        if result.empty:

            st.error("查無此商品")

            st.stop()

        row = result.iloc[0]

        stock_name = row[COL_NAME]

        margin_ratio = str(
            row[COL_MARGIN]
        )

        margin_ratio_float = float(
            margin_ratio.replace("%", "")
        ) / 100

        # =========================
        # 計算保證金
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

        st.write("商品類型：", product_type)

        st.write("股票代號：", stock_id)

        st.write("商品名稱：", stock_name)

        st.write("成交價：", price)

        st.write("原始保證金比例：", margin_ratio)

        st.write("契約乘數：", multiplier)

        st.write(
            "契約價值：",
            f"{int(contract_value):,}"
        )

        st.write(
            "原始保證金：",
            f"{int(initial_margin):,} 元"
        )

    except Exception as e:

        st.error(f"計算失敗：{e}")
