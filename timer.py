# ---------------------------------------------------
# INSTALL
# pip install -r requirements.txt
# ---------------------------------------------------

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import base64
from datetime import datetime
import pytz

from streamlit_autorefresh import st_autorefresh

# ---------------------------------------------------
# AUTO REFRESH EVERY 60 SEC (SAFE METHOD)
# ---------------------------------------------------

st_autorefresh(interval=60000, key="datarefresh")

# ---------------------------------------------------
# PAGE SETTINGS
# ---------------------------------------------------

st.set_page_config(page_title="📊 Live Stock Rundown", layout="wide")

st.title("📊 Live Stock Rundown Tracker")

# ---------------------------------------------------
# TIMEZONE
# ---------------------------------------------------

IST = pytz.timezone("Asia/Kolkata")

# ---------------------------------------------------
# TELEGRAM SETTINGS (OPTIONAL)
# ---------------------------------------------------

BOT_TOKEN = ""
CHAT_ID = ""

telegram_alert = st.toggle("📲 Enable Telegram Alert", value=False)

# ---------------------------------------------------
# SOUND ALERT
# ---------------------------------------------------

sound_alert = st.toggle("🔊 Enable Sound Alert", value=False)

DEFAULT_SOUND_URL = "https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"

# ---------------------------------------------------
# STOCK LIST WITH REFERENCE PRICE
# ---------------------------------------------------

stocks = {

    "NAUKRI.NS": 1084.55,
    "RELIANCE.NS": 1402.25,
    "HDFCBANK.NS": 896.50,
    "INFY.NS": 1278.30,
    "TCS.NS": 2578.54,

}

# ---------------------------------------------------
# SESSION STATE STORAGE
# ---------------------------------------------------

if "rundown_start" not in st.session_state:

    st.session_state.rundown_start = {}

if "alert_sent" not in st.session_state:

    st.session_state.alert_sent = {}

# ---------------------------------------------------
# FETCH LIVE DATA
# ---------------------------------------------------

@st.cache_data(ttl=60)

def fetch_live():

    data = yf.download(

        tickers=list(stocks.keys()),
        period="1d",
        interval="1m",
        group_by="ticker",
        progress=False

    )

    return data

data = fetch_live()

# ---------------------------------------------------
# PROCESS DATA
# ---------------------------------------------------

rows = []

now = datetime.now(IST)

for symbol, ref_price in stocks.items():

    try:

        price = data[symbol]["Close"].iloc[-1]

        name = symbol.replace(".NS","")

        # ------------------------
        # RUNDOWN LOGIC
        # ------------------------

        if price < ref_price:

            if symbol not in st.session_state.rundown_start:

                st.session_state.rundown_start[symbol] = now

        else:

            if symbol in st.session_state.rundown_start:

                del st.session_state.rundown_start[symbol]

        minutes = 0

        if symbol in st.session_state.rundown_start:

            minutes = (

                now - st.session_state.rundown_start[symbol]

            ).total_seconds()/60

        # ------------------------
        # STATUS ICON
        # ------------------------

        if price >= ref_price:

            status = "🟢 Above"

        elif minutes < 15:

            status = f"🟠 {round(minutes,1)} min"

        else:

            status = f"🔴 {round(minutes,1)} min"

            # Telegram Alert

            if telegram_alert:

                if symbol not in st.session_state.alert_sent:

                    msg = f"""

🔴 Rundown Alert

Stock: {name}
Price: ₹{price:.2f}
Time: {round(minutes,1)} min

"""

                    requests.post(

                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",

                        data={

                            "chat_id": CHAT_ID,
                            "text": msg

                        }

                    )

                    st.session_state.alert_sent[symbol] = True

        # ------------------------
        # P2L
        # ------------------------

        p2l = ((price-ref_price)/ref_price)*100

        rows.append({

            "Stock": name,
            "Price": round(price,2),
            "Reference": ref_price,
            "P2L %": round(p2l,2),
            "Rundown": status

        })

    except:

        pass

# ---------------------------------------------------
# DISPLAY TABLE
# ---------------------------------------------------

df = pd.DataFrame(rows)

st.dataframe(

    df,

    use_container_width=True,

    hide_index=True

)

# ---------------------------------------------------
# SOUND ALERT
# ---------------------------------------------------

if sound_alert:

    for r in rows:

        if "🔴" in r["Rundown"]:

            st.markdown(f"""

<audio autoplay>

<source src="{DEFAULT_SOUND_URL}">

</audio>

""", unsafe_allow_html=True)

            break

# ---------------------------------------------------
# AVERAGE
# ---------------------------------------------------

avg = df["P2L %"].mean()

st.subheader(f"📊 Average P2L: {avg:.2f}%")
