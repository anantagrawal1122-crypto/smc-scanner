# import streamlit as st
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import logging

warnings.filterwarnings("ignore")
logging.getLogger("yfinance").setLevel(logging.CRITICAL)

st.set_page_config(page_title="Ultra SMC & Scalping Scanner", layout="wide")
st.title("⚡ PRO TRADER SMC & SCALPING SCANNER")
st.write("Multi-Timeframe Analysis | SMC | Price Action | Scalping Focus")

# Stock Buckets
NIFTY_SMALLCAP = [
    "SUZLON.NS", "AWL.NS", "IRFC.NS", "RVNL.NS", "SJVN.NS", "HUDCO.NS", "IREDA.NS",
    "NBCC.NS", "BSOFT.NS", "HFCL.NS", "ENGINERSIN.NS", "MANAPPURAM.NS", "RCF.NS",
    "FACT.NS", "FSL.NS", "CENTURYTEX.NS", "CDSL.NS", "BEML.NS", "COCHINSHIP.NS",
    "MAZDOCK.NS", "ALOKINDS.NS", "RENUKA.NS", "TRIDENT.NS", "SOUTHBANK.NS", "UCOBANK.NS",
    "IOB.NS", "CENTRALBK.NS", "IDFCFIRSTB.NS", "YESBANK.NS", "JPPOWER.NS", "NHPC.NS"
]

HIGH_VOLUME = [
    "TATASTEEL.NS", "TATAMOTORS.NS", "ZOMATO.NS", "JIOFIN.NS", "PAYTM.NS", "PNB.NS",
    "FEDERALBNK.NS", "REC.NS", "PFC.NS", "BHEL.NS", "NTPC.NS", "COALINDIA.NS",
    "SAIL.NS", "NMDC.NS", "NATIONALUM.NS", "GAIL.NS", "IDEA.NS", "GMRINFRA.NS"
]

NIFTY_MIDCAP = [
    "PERSISTENT.NS", "COFORGE.NS", "MPHASIS.NS", "DIXON.NS", "POLYCAB.NS",
    "KEI.NS", "ASTRAL.NS", "BALKRISIND.NS", "BHARATFORG.NS", "VOLTAS.NS",
    "TRENT.NS", "TIINDIA.NS", "LUPIN.NS", "AUROPHARMA.NS", "MAXHEALTH.NS"
]

NIFTY_50 = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "BHARTIARTL.NS", "ITC.NS", "SBIN.NS", "LT.NS", "AXISBANK.NS",
    "KOTAKBANK.NS", "SUNPHARMA.NS", "M&M.NS", "MARUTI.NS", "TITAN.NS"
]

# Category Selector UI
category = st.selectbox(
    "🎯 Select Category to Scan:",
    ["Nifty Smallcap Focus (Fast Scalping)", "High Volume Momentum Stocks", "Nifty Midcap Focus", "Nifty 50 Largecap"]
)

if category == "Nifty Smallcap Focus (Fast Scalping)":
    SELECTED_STOCKS = NIFTY_SMALLCAP
elif category == "High Volume Momentum Stocks":
    SELECTED_STOCKS = HIGH_VOLUME
elif category == "Nifty Midcap Focus":
    SELECTED_STOCKS = NIFTY_MIDCAP
else:
    SELECTED_STOCKS = NIFTY_50

def download_data(symbol, interval, period):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.dropna(inplace=True)
        return df
    except Exception:
        return None

def get_market_structure(df, swing=3):
    if df is None or len(df) < (swing * 2 + 5):
        return {"bias": "NEUTRAL", "pattern": "RANGE"}
    
    d = df.copy()
    d["swing_high"] = d["High"].rolling(swing * 2 + 1, center=True).max()
    d["swing_low"] = d["Low"].rolling(swing * 2 + 1, center=True).min()
    
    last_high, last_low = None, None
    for i in range(len(d) - swing - 1, -1, -1):
        if pd.notna(d["swing_high"].iloc[i]):
            last_high = float(d["swing_high"].iloc[i])
            break
    for i in range(len(d) - swing - 1, -1, -1):
        if pd.notna(d["swing_low"].iloc[i]):
            last_low = float(d["swing_low"].iloc[i])
            break

    price = float(d["Close"].iloc[-1])
    if last_high is None or last_low is None:
        return {"bias": "NEUTRAL", "pattern": "RANGE"}

    recent_high = df["High"].iloc[-10:-1].max()
    previous_high = df["High"].iloc[-20:-10].max()
    recent_low = df["Low"].iloc[-10:-1].min()
    previous_low = df["Low"].iloc[-20:-10].min()

    pattern = "UNKNOWN"
    if recent_high > previous_high and recent_low > previous_low:
        pattern = "HH + HL (Uptrend)"
    elif recent_high < previous_high and recent_low < previous_low:
        pattern = "LH + LL (Downtrend)"

    bias = "BULLISH" if price > last_high else ("BEARISH" if price < last_low else "RANGE")
    return {"bias": bias, "pattern": pattern}

def detect_candlestick_pattern(df):
    if df is None or len(df) < 2: return "NONE"
    c, prev = df.iloc[-1], df.iloc[-2]
    body = abs(c["Close"] - c["Open"])
    upper_wick = c["High"] - max(c["Open"], c["Close"])
    lower_wick = min(c["Open"], c["Close"]) - c["Low"]

    if prev["Close"] < prev["Open"] and c["Close"] > c["Open"] and c["Close"] > prev["Open"] and c["Open"] < prev["Close"]:
        return "BULLISH ENGULFING"
    if prev["Close"] > prev["Open"] and c["Close"] < c["Open"] and c["Open"] > prev["Close"] and c["Close"] < prev["Open"]:
        return "BEARISH ENGULFING"
    if lower_wick > body * 2 and c["Close"] > c["Open"]:
        return "BULLISH REJECTION (Pinbar)"
    if upper_wick > body * 2 and c["Close"] < c["Open"]:
        return "BEARISH REJECTION (Pinbar)"
    return "NONE"

def liquidity_sweep(df):
    if df is None or len(df) < 10: return "NONE"
    last = df.iloc[-1]
    prev_high = df["High"].iloc[-8:-1].max()
    prev_low = df["Low"].iloc[-8:-1].min()

    if last["High"] > prev_high and last["Close"] < prev_high: return "BUY-SIDE SWEPT"
    if last["Low"] < prev_low and last["Close"] > prev_low: return "SELL-SIDE SWEPT"
    return "NONE"

def detect_fvg(df):
    if df is None or len(df) < 3: return "NONE"
    c1, c3 = df.iloc[-3], df.iloc[-1]
    if c3["Low"] > c1["High"]: return "BULLISH FVG"
    if c3["High"] < c1["Low"]: return "BEARISH FVG"
    return "NONE"

def detect_ob(df):
    if df is None or len(df) < 6: return "NONE"
    last = df.iloc[-1]
    for i in range(2, 6):
        candle = df.iloc[-i]
        if last["Close"] > last["Open"] and candle["Close"] < candle["Open"]: return "BULLISH OB"
        if last["Close"] < last["Open"] and candle["Close"] > candle["Open"]: return "BEARISH OB"
    return "NONE"

def displacement_and_volume(df):
    if df is None or len(df) < 20: return False, False
    candle = df.iloc[-1]
    body = abs(candle["Close"] - candle["Open"])
    rng = candle["High"] - candle["Low"]
    avg_range = (df["High"].iloc[-20:-1] - df["Low"].iloc[-20:-1]).mean()
    disp = (rng > 0) and ((body / rng) >= 0.55) and (rng > avg_range * 1.2)
    vol = df["Volume"].iloc[-1] > df["Volume"].iloc[-21:-1].mean() * 1.2
    return disp, vol

def calculate_professional_score(direction, w_bias, d_bias, h1_bias, liquidity, fvg, ob, disp, vol, candle, pattern):
    score = 0
    for b in [w_bias, d_bias, h1_bias]:
        if b == direction: score += 10

    if (direction == "BULLISH" and liquidity == "SELL-SIDE SWEPT") or (direction == "BEARISH" and liquidity == "BUY-SIDE SWEPT"):
        score += 15
    if (direction == "BULLISH" and fvg == "BULLISH FVG") or (direction == "BEARISH" and fvg == "BEARISH FVG"):
        score += 10
    if (direction == "BULLISH" and ob == "BULLISH OB") or (direction == "BEARISH" and ob == "BEARISH OB"):
        score += 10
    if disp: score += 15

    if vol: score += 5
    if ("BULLISH" in candle and direction == "BULLISH") or ("BEARISH" in candle and direction == "BEARISH"):
        score += 10
    if ("Uptrend" in pattern and direction == "BULLISH") or ("Downtrend" in pattern and direction == "BEARISH"):
        score += 5

    return min(score, 100)

def analyse_stock(symbol):
    weekly = download_data(symbol, "1wk", "1y")
    daily = download_data(symbol, "1d", "6mo")
    h1 = download_data(symbol, "1h", "1mo")
    m15 = download_data(symbol, "15m", "5d")

    if m15 is None or daily is None or len(m15) < 15: return None

    w_info = get_market_structure(weekly)
    d_info = get_market_structure(daily)
    h1_info = get_market_structure(h1)

    price = float(m15["Close"].iloc[-1])
    liquidity = liquidity_sweep(m15)
    fvg = detect_fvg(m15)
    ob = detect_ob(m15)
    disp, vol = displacement_and_volume(m15)
    candle = detect_candlestick_pattern(m15)

    bullish_votes = [w_info["bias"], d_info["bias"], h1_info["bias"]].count("BULLISH")
    bearish_votes = [w_info["bias"], d_info["bias"], h1_info["bias"]].count("BEARISH")

    if liquidity == "SELL-SIDE SWEPT": bullish_votes += 2
    if liquidity == "BUY-SIDE SWEPT": bearish_votes += 2
    if "BULLISH" in candle: bullish_votes += 1
    if "BEARISH" in candle: bearish_votes += 1

    direction = "BULLISH" if bullish_votes > bearish_votes else ("BEARISH" if bearish_votes > bullish_votes else "NEUTRAL")
    score = calculate_professional_score(direction, w_info["bias"], d_info["bias"], h1_bias=h1_info["bias"], liquidity=liquidity, fvg=fvg, ob=ob, disp=disp, vol=vol, candle=candle, pattern=d_info["pattern"])

    return {
        "Stock": symbol.replace(".NS", ""),
        "Direction": direction,
        "SMC Score": score,
        "Price": round(price, 2),
        "Weekly Bias": w_info["bias"],
        "Daily Bias": d_info["bias"],
        "Daily Pattern": d_info["pattern"],
        "Liquidity": liquidity,
        "FVG": fvg,
        "Order Block": ob,
        "Displacement": "YES" if disp else "NO",
        "Volume Spike": "YES" if vol else "NO",
        "Candle Pattern": candle
    }

if st.button("🚀 Run Market Scan"):
    st.info(f"Scanning {len(SELECTED_STOCKS)} stocks in {category}...")
    results = []
    bar = st.progress(0)
    for idx, sym in enumerate(SELECTED_STOCKS):
        res = analyse_stock(sym)
        if res: results.append(res)
        bar.progress((idx + 1) / len(SELECTED_STOCKS))
    
    if results:
        df_res = pd.DataFrame(results).sort_values(by="SMC Score", ascending=False)
        st.success("✅ Scan Completed!")
        st.dataframe(df_res, use_container_width=True)
