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

    df = max(tables, key=len)

    df.columns = df.columns.str.strip()

    return df
