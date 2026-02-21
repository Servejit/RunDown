# ---------------------------------------------------
# INSTALL
# pip install streamlit yfinance pandas requests pytz
# ---------------------------------------------------

import streamlit as st
import yfinance as yf
import pandas as pd
import base64
import requests
from datetime import datetime
import pytz

st.set_page_config(page_title="📊 Live Stock P2L", layout="wide")
st.title("📊 Live Prices with P2L")

IST = pytz.timezone("Asia/Kolkata")

# ---------------------------------------------------
# SESSION STATE FOR RUNDOWN

if "rundown_start" not in st.session_state:
    st.session_state.rundown_start = {}

# ---------------------------------------------------
# TELEGRAM SETTINGS

BOT_TOKEN = "YOUR_TOKEN"
CHAT_ID = "YOUR_CHATID"

# ---------------------------------------------------
# STOCK LIST

stocks = {
    "NAUKRI.NS": 1084.55,
    "RELIANCE.NS": 1402.25,
    "HDFCBANK.NS": 896.50,
    "INFY.NS": 1278.30,
}

# ---------------------------------------------------
# FETCH DATA LIVE

@st.cache_data(ttl=60)

def fetch_data():

    symbols = list(stocks.keys())

    data = yf.download(

        tickers=symbols,
        period="1d",
        interval="1m",
        group_by="ticker",
        progress=False,
        threads=True

    )

    rows = []

    now = datetime.now(IST)

    for sym in symbols:

        try:

            ref = stocks[sym]

            price = data[sym]["Close"].iloc[-1]

            stock_name = sym.replace(".NS","")

            # -------------------
            # RUNDOWN LOGIC
            # -------------------

            if price < ref:

                if sym not in st.session_state.rundown_start:

                    st.session_state.rundown_start[sym] = now

            else:

                st.session_state.rundown_start.pop(sym, None)

            minutes = 0

            if sym in st.session_state.rundown_start:

                minutes = (

                    now - st.session_state.rundown_start[sym]

                ).total_seconds()/60


            if price >= ref:

                rundown = "🟢"

            elif minutes < 15:

                rundown = f"🟠 {round(minutes,1)}"

            else:

                rundown = f"🔴 {round(minutes,1)}"


            p2l = ((price - ref)/ref)*100

            rows.append({

                "Stock": stock_name,
                "Price": price,
                "Reference": ref,
                "P2L %": p2l,
                "Rundown": rundown

            })

        except:

            pass

    return pd.DataFrame(rows)

# ---------------------------------------------------
# BUTTONS

col1, col2 = st.columns(2)

with col1:

    if st.button("🔄 Refresh"):

        st.cache_data.clear()

        st.rerun()

with col2:

    sort_clicked = st.button("📈 Sort")

# ---------------------------------------------------
# LOAD

df = fetch_data()

if sort_clicked:

    df = df.sort_values("P2L %")

# ---------------------------------------------------
# SHOW TABLE

st.dataframe(

    df,

    use_container_width=True,

    hide_index=True

)

# ---------------------------------------------------
# AUTO REFRESH

st.caption("Auto refresh every 60 sec")

st.experimental_rerun()
