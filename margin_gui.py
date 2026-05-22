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
# 自動抓取 TAIFEX 資料
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

    tables = pd.read_html(
        StringIO(response.text)
    )

    # 取最大表格
    df = max(tables, key=len)

    # 清理欄位名稱
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
COL_MAINTAIN = "維持保證金適用比例"
COL_SETTLEMENT = "結算保證金適用比例"

# =========================
# 商品分類
# =========================

normal_df = df[
    ~df[COL_NAME].astype(str).str.contains("小型", na=False)
]

mini_df = df[
    df[COL_NAME].astype(str).str.contains("小型", na=False)
]

# =========================
# 商品類型
# =========================

product_type = st.radio(
    "商品類型",
    ["一般個股期", "小型個股期"]
)

# =========================
# 商品資料
# =========================

if product_type == "一般個股期":

    temp_df = normal_df
    multiplier = 2000

else:

    temp_df = mini_df
    multiplier = 100

# =========================
# 建立選單
# =========================

temp_df = temp_df.copy()

temp_df["選單"] = (
    temp_df[COL_STOCK_ID].astype(str)
    + " - "
    + temp_df[COL_NAME].astype(str)
)

# =========================
# 商品選擇
# =========================

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
# 口數
# =========================

quantity = st.number_input(
    "口數",
    min_value=1,
    step=1,
    value=1
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

        # =========================
        # 保證金比例
        # =========================

        initial_ratio = float(
            str(row[COL_MARGIN]).replace("%", "")
        ) / 100

        maintain_ratio = float(
            str(row[COL_MAINTAIN]).replace("%", "")
        ) / 100

        settlement_ratio = float(
            str(row[COL_SETTLEMENT]).replace("%", "")
        ) / 100

        # =========================
        # 契約價值
        # =========================

        contract_value = (
            price
            * multiplier
            * quantity
        )

        # =========================
        # 保證金計算
        # =========================

        initial_margin = (
            contract_value
            * initial_ratio
        )

        maintain_margin = (
            contract_value
            * maintain_ratio
        )

        settlement_margin = (
            contract_value
            * settlement_ratio
        )

        # =========================
        # 顯示結果
        # =========================

        st.success("計算完成")

        st.write("### 📌 計算結果")

        st.write(f"商品類型：{product_type}")

        st.write(f"股票代號：{stock_id}")

        st.write(f"商品名稱：{stock_name}")

        st.write(f"成交價：{price}")

        st.write(f"口數：{quantity}")

        st.write(f"契約乘數：{multiplier}")

        st.write(
            f"契約總價值：{int(contract_value):,} 元"
        )

        st.write("---")

        st.write(
            f"原始保證金：{int(initial_margin):,} 元"
        )

        st.write(
            f"維持保證金：{int(maintain_margin):,} 元"
        )

        st.write(
            f"結算保證金：{int(settlement_margin):,} 元"
        )

    except Exception as e:

        st.error(f"計算失敗：{e}")
