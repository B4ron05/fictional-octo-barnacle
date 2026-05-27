import streamlit as st
import pandas as pd
import finnhub_calendar
import cot_data
import technical_data
import historical_data
import scoring_logic 

st.set_page_config(layout="wide")
st.title("Improved-fishstick 🎯")

# --- CUSTOM CSS UI BUILDER ---
def custom_metric_card(label, value, difference, asset, forecast=None, suffix="", text_override=None):
    bias, color = scoring_logic.evaluate_bias(asset, label, difference)
    diff_str = f"+{difference}" if difference > 0 else f"{difference}"
    
    if text_override:
        content_html = f"""<div style="margin-top: 15px; display: flex; align-items: center;">
<span style="background-color: {color}; color: white; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-right: 10px;">{bias}</span>
<span style="font-size: 14px; color: #D3D3D3;">{text_override}</span>
</div>"""
    else:
        if forecast is not None and forecast != "N/A":
            bottom_text = f'<span style="font-size: 13px; color: #A0A0A0; margin-left: 8px;">Est: {forecast}{suffix} | Surprise: <b style="color: {color};">{diff_str}{suffix}</b></span>'
        else:
            bottom_text = f'<span style="font-size: 13px; color: #A0A0A0; margin-left: 8px;">Delta: <b style="color: {color};">{diff_str}{suffix}</b></span>'
            
        content_html = f"""<h2 style="margin: 0px; margin-top: 5px; color: {color}; font-size: 32px;">{value}{suffix}</h2>
<div style="margin-top: 8px;">
<span style="background-color: {color}; color: white; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: bold;">{bias}</span>
{bottom_text}
</div>"""

    html = f"""<div style="margin-bottom: 20px; padding: 10px; border-radius: 8px; background-color: rgba(255,255,255,0.05); min-height: 100px;">
<p style="margin: 0px; font-size: 14px; font-weight: 600; color: #A0A0A0;">{label}</p>
{content_html}
</div>"""
    st.markdown(html, unsafe_allow_html=True)


# --- CACHING FUNCTIONS ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_macro(api_key): return finnhub_calendar.fetch_finnhub_forecasts(api_key)

@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_cot(ticker): return cot_data.fetch_cot_data(ticker)

@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_technicals(ticker, opt_ticker): return technical_data.fetch_technicals_and_sentiment(ticker, opt_ticker)

@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_yield(): return technical_data.fetch_yield_trend("^TNX")

@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_history(api_key, limit): return historical_data.fetch_fred_history(api_key, limit)


# --- SIDEBAR ---
with st.sidebar:
    st.header("API Connections")
    finnhub_key = st.text_input("Finnhub Key (Live Surprises):", type="password")
    fred_key = st.text_input("FRED Key (Historical Charts):", type="password")
    
    st.divider()
    st.header("Dashboard Settings")
    
    ASSET_MAPPING = {
        "S&P 500": {"cftc": "13874A", "yf": "^GSPC", "opt": "SPY"}, 
        "NASDAQ 100": {"cftc": "209742", "yf": "^NDX", "opt": "QQQ"}, 
        "GOLD": {"cftc": "088691", "yf": "GC=F", "opt": "GLD"}, 
        "SILVER": {"cftc": "084691", "yf": "SI=F", "opt": "SLV"}, 
        "CRUDE OIL": {"cftc": "067651", "yf": "CL=F", "opt": "USO"}, 
        "US DOLLAR INDEX": {"cftc": "098662", "yf": "DX-Y.NYB", "opt": "UUP"}, 
        "10-YR TREASURY": {"cftc": "043602", "yf": "^TNX", "opt": "IEF"}
    }
    
    selected_asset = st.selectbox("Choose an Asset to Analyze:", list(ASSET_MAPPING.keys()))
    cftc_ticker = ASSET_MAPPING[selected_asset]["cftc"]
    yf_ticker = ASSET_MAPPING[selected_asset]["yf"]
    opt_ticker = ASSET_MAPPING[selected_asset]["opt"]
    
    # NEW: The Interactive History Slider Bar
    history_bar = st.slider("Historical Data Range (Prints):", min_value=3, max_value=24, value=6)


# --- MAIN APP ROUTING (TABS) ---
if finnhub_key and fred_key:
    tab_live, tab_history = st.tabs(["🎯 Live Asset Dashboard", "📈 Historical Macro Trends"])
    
    # ==========================================
    # TAB 1: LIVE DASHBOARD 
    # ==========================================
    with tab_live:
        st.markdown(f"### Current Analysis for: **{selected_asset}**")
        with st.spinner("Fetching cached quantitative data..."):
            try:
                macro = get_cached_macro(finnhub_key)
                cot = get_cached_cot(cftc_ticker)
                tech = get_cached_technicals(yf_ticker, opt_ticker)
                yield_data = get_cached_yield()
                
                macro["10 Yr Yield (21d SMA)"] = {
                    "value": yield_data["value"], "difference": yield_data["difference"], "forecast": yield_data["sma"]
                }

                score_map = {"Bullish": 1, "Bearish": -1, "Neutral": 0}
                category_averages = []
                
                tech_sum = 0
                for t_metric in ["4H / Daily Trend", "Seasonality Trend", "Put/Call Ratio"]:
                    bias, _ = scoring_logic.evaluate_bias(selected_asset, t_metric, tech[t_metric]['difference'])
                    tech_sum += score_map.get(bias, 0)
                category_averages.append(tech_sum / 3)

                if cot:
                    bias, _ = scoring_logic.evaluate_bias(selected_asset, "Net Change (WoW)", cot['change_pct'])
                    cot_score = score_map.get(bias, 0)
                    category_averages.append(cot_score / 1) 
                    
                metric_groups = {
                    "Growth": ["GDP Growth QoQ", "Retail Sales MoM", "Consumer Confidence"],
                    "Inflation": ["CPI YoY", "PPI YoY", "PCE YoY", "10 Yr Yield (21d SMA)"],
                    "Jobs": ["Non-Farm Payroll", "Unemployment Rate %", "Weekly Jobless Claims", "JOLTS Job Openings"]
                }
                
                for group_name, metrics in metric_groups.items():
                    group_sum = 0
                    for metric in metrics:
                        bias, _ = scoring_logic.evaluate_bias(selected_asset, metric, macro[metric]['difference'])
                        group_sum += score_map.get(bias, 0)
                    category_averages.append(group_sum / len(metrics))

                total_score = sum(category_averages)
                total_score_rounded = round(total_score, 2)

                if total_score >= 1.5: master_bias, master_color = "VERY BULLISH", "#2962FF"
                elif total_score <= -1.5: master_bias, master_color = "VERY BEARISH", "#F44336"
                else:
                    if total_score > 0.25: master_bias, master_color = "SLIGHTLY BULLISH", "#2962FF"
                    elif total_score < -0.25: master_bias, master_color = "SLIGHTLY BEARISH", "#F44336"
                    else: master_bias, master_color = "NEUTRAL", "#808080"

                st.markdown(f"""
                <div style="text-align: center; margin-top: 10px; margin-bottom: 40px; padding: 25px; border-radius: 12px; background-color: rgba(255,255,255,0.02); border: 2px solid {master_color};">
                    <p style="margin: 0; color: #A0A0A0; font-size: 16px; font-weight: bold; text-transform: uppercase;">Total Institutional Edge Score</p>
                    <h1 style="margin: 10px 0; color: {master_color}; font-size: 52px; letter-spacing: 2px;">{master_bias}</h1>
                    <p style="margin: 0; color: white; font-size: 18px;">Normalized Net Score: <b style="color: {master_color};">{total_score_rounded}</b> <span style="color: #A0A0A0; font-size: 14px;">(Max Range: -5.0 to +5.0)</span></p>
                </div>
                """, unsafe_allow_html=True)

                st.subheader("📊 Technical Bias & Crowd Sentiment")
                t1, t2, t3, t4 = st.columns(4)
                with t1: custom_metric_card("4H / Daily Trend", tech['4H / Daily Trend']['value'], tech['4H / Daily Trend']['difference'], selected_asset)
                with t2: custom_metric_card("Seasonality Trend", tech['Seasonality Trend']['value'], tech['Seasonality Trend']['difference'], selected_asset, suffix="%")
                with t3: custom_metric_card("Put/Call Ratio", tech['Put/Call Ratio']['value'], tech['Put/Call Ratio']['difference'], selected_asset)

                st.divider()
                st.subheader("🏢 Institutional Activity Bias (COT)")
                if cot:
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: st.metric("Long %", f"{cot['long_pct']}%")
                    with c2: st.metric("Short %", f"{cot['short_pct']}%")
                    with c3: custom_metric_card("Net Change (WoW)", f"{cot['change_pct']}", cot['change_pct'], selected_asset, suffix="%")
                else:
                    st.warning(f"No COT data found for {selected_asset}.")

                st.divider()
                st.subheader("📈 Economic Growth Bias")
                g1, g2, g3, g4 = st.columns(4)
                with g1: custom_metric_card("GDP Growth QoQ", macro['GDP Growth QoQ']['value'], macro['GDP Growth QoQ']['difference'], selected_asset, forecast=macro['GDP Growth QoQ']['forecast'], suffix="%")
                with g2: custom_metric_card("Retail Sales MoM", macro['Retail Sales MoM']['value'], macro['Retail Sales MoM']['difference'], selected_asset, forecast=macro['Retail Sales MoM']['forecast'], suffix="%")
                with g3: custom_metric_card("Consumer Confidence", macro['Consumer Confidence']['value'], macro['Consumer Confidence']['difference'], selected_asset, forecast=macro['Consumer Confidence']['forecast'], suffix="")

                st.divider()
                st.subheader("🔥 Inflation Bias")
                i1, i2, i3, i4 = st.columns(4)
                with i1: custom_metric_card("CPI YoY", macro['CPI YoY']['value'], macro['CPI YoY']['difference'], selected_asset, forecast=macro['CPI YoY']['forecast'], suffix="%")
                with i2: custom_metric_card("PPI YoY", macro['PPI YoY']['value'], macro['PPI YoY']['difference'], selected_asset, forecast=macro['PPI YoY']['forecast'], suffix="%")
                with i3: custom_metric_card("PCE YoY", macro['PCE YoY']['value'], macro['PCE YoY']['difference'], selected_asset, forecast=macro['PCE YoY']['forecast'], suffix="%")
                
                if macro['10 Yr Yield (21d SMA)']['value'] == "N/A":
                    yield_text = "Awaiting 10Y yield data..."
                elif macro['10 Yr Yield (21d SMA)']['difference'] > 0:
                    yield_text = f"Yield is rising > 21 SMA ({macro['10 Yr Yield (21d SMA)']['forecast']}%)"
                elif macro['10 Yr Yield (21d SMA)']['difference'] < 0:
                    yield_text = f"Yield is falling < 21 SMA ({macro['10 Yr Yield (21d SMA)']['forecast']}%)"
                else:
                    yield_text = f"Yield is flat on SMA ({macro['10 Yr Yield (21d SMA)']['forecast']}%)"
                    
                with i4: custom_metric_card("10 Yr Yield (21d SMA)", macro['10 Yr Yield (21d SMA)']['value'], macro['10 Yr Yield (21d SMA)']['difference'], selected_asset, text_override=yield_text, suffix="%")

                st.divider()
                st.subheader("💼 Jobs Market Bias")
                j1, j2, j3, j4 = st.columns(4)
                with j1: custom_metric_card("Non-Farm Payroll", macro['Non-Farm Payroll']['value'], macro['Non-Farm Payroll']['difference'], selected_asset, forecast=macro['Non-Farm Payroll']['forecast'], suffix="k")
                with j2: custom_metric_card("Unemployment Rate %", macro['Unemployment Rate %']['value'], macro['Unemployment Rate %']['difference'], selected_asset, forecast=macro['Unemployment Rate %']['forecast'], suffix="%")
                with j3: custom_metric_card("Weekly Jobless Claims", macro['Weekly Jobless Claims']['value'], macro['Weekly Jobless Claims']['difference'], selected_asset, forecast=macro['Weekly Jobless Claims']['forecast'], suffix="")
                with j4: custom_metric_card("JOLTS Job Openings", macro['JOLTS Job Openings']['value'], macro['JOLTS Job Openings']['difference'], selected_asset, forecast=macro['JOLTS Job Openings']['forecast'], suffix="M")
                
            except Exception as e:
                st.error(f"Error fetching data: {e}")

    # ==========================================
    # TAB 2: HISTORICAL MACRO 
    # ==========================================
    with tab_history:
        st.markdown("### Historical Market Trajectory")
        st.caption("Visualizing the historical prints of US macroeconomic data to track underlying trend shifts.")
        
        with st.spinner("Compiling historical data from the Federal Reserve..."):
            all_hist = get_cached_history(fred_key, history_bar)
            
            # UPGRADED: Forces global bar charts (Pillars)
            def render_chart(title, df):
                st.markdown(f"**{title}**")
                if not df.empty:
                    st.bar_chart(df, height=220)
                else:
                    st.info("Awaiting sufficient historical data.")

            st.subheader("🔥 Inflation Trends")
            i1, i2, i3, i4 = st.columns(4)
            with i1: render_chart("CPI YoY (%)", all_hist.get("CPI YoY (%)", pd.DataFrame()))
            with i2: render_chart("PPI YoY (%)", all_hist.get("PPI YoY (%)", pd.DataFrame()))
            with i3: render_chart("PCE YoY (%)", all_hist.get("PCE YoY (%)", pd.DataFrame()))
            with i4: render_chart("10 Yr Yield (%)", all_hist.get("10 Yr Yield (%)", pd.DataFrame()))
            
            st.divider()
            st.subheader("📈 Growth & Consumption")
            g1, g2, g3 = st.columns(3)
            with g1: render_chart("GDP Growth QoQ (%)", all_hist.get("GDP Growth QoQ (%)", pd.DataFrame()))
            with g2: render_chart("Retail Sales MoM (%)", all_hist.get("Retail Sales MoM (%)", pd.DataFrame()))
            with g3: render_chart("Consumer Confidence", all_hist.get("Consumer Confidence", pd.DataFrame()))
            
            st.divider()
            st.subheader("💼 Labor Market")
            j1, j2, j3, j4 = st.columns(4)
            with j1: render_chart("Non-Farm Payroll (k)", all_hist.get("Non-Farm Payroll (k)", pd.DataFrame()))
            with j2: render_chart("Unemployment Rate (%)", all_hist.get("Unemployment Rate (%)", pd.DataFrame()))
            with j3: render_chart("Weekly Jobless Claims (k)", all_hist.get("Weekly Jobless Claims (k)", pd.DataFrame()))
            with j4: render_chart("JOLTS Openings (M)", all_hist.get("JOLTS Openings (M)", pd.DataFrame()))

else:
    st.info("👈 Please enter both your Finnhub and FRED API keys in the sidebar to begin.")