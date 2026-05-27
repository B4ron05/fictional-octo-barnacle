import yfinance as yf
import pandas as pd
from datetime import datetime

def fetch_technicals_and_sentiment(yf_ticker, options_ticker):
    """
    Fetches price action for moving averages (via yf_ticker), 
    and pulls options chain data for the Put/Call ratio (via options_ticker).
    """
    results = {
        "4H / Daily Trend": {"value": "N/A", "difference": 0},
        "Seasonality Trend": {"value": "N/A", "difference": 0},
        "Put/Call Ratio": {"value": "N/A", "difference": 0}
    }
    
    try:
        # 1. FETCH PRICE ACTION & SEASONALITY
        tk_price = yf.Ticker(yf_ticker)
        hist = tk_price.history(period="5y")
        
        if len(hist) > 50:
            current_price = hist['Close'].iloc[-1]
            sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]
            trend_diff = current_price - sma_50
            results["4H / Daily Trend"] = {"value": round(current_price, 2), "difference": round(trend_diff, 2)}
            
            current_month = datetime.now().month
            monthly_data = hist['Close'].resample('ME').last().pct_change() * 100
            seasonality = monthly_data[monthly_data.index.month == current_month].mean()
            results["Seasonality Trend"] = {"value": f"{datetime.now().strftime('%b')} Avg", "difference": round(seasonality, 2)}
            
        # 2. FETCH CROWD SENTIMENT
        tk_opt = yf.Ticker(options_ticker)
        options_dates = tk_opt.options
        
        if options_dates:
            chain = tk_opt.option_chain(options_dates[0])
            puts_oi = chain.puts['openInterest'].sum()
            calls_oi = chain.calls['openInterest'].sum()
            
            if calls_oi > 0:
                pcr = puts_oi / calls_oi
                results["Put/Call Ratio"] = {"value": round(pcr, 2), "difference": round(pcr - 1.0, 2)}
                
    except Exception as e:
        print(f"YFinance Error: {e}")
        
    return results

def fetch_yield_trend(yield_ticker="^TNX"):
    """
    Fetches the 10-Year Treasury Yield and calculates the 21-day SMA.
    Returns the current yield and the difference from the SMA.
    """
    results = {"value": "N/A", "difference": 0, "sma": "N/A"}
    try:
        tk = yf.Ticker(yield_ticker)
        # 3 months is enough data to safely calculate a 21-day moving average
        hist = tk.history(period="3mo")
        
        if len(hist) >= 21:
            current_yield = hist['Close'].iloc[-1]
            sma_21 = hist['Close'].rolling(window=21).mean().iloc[-1]
            
            results["value"] = round(current_yield, 2)
            results["difference"] = round(current_yield - sma_21, 2)
            results["sma"] = round(sma_21, 2)
            
    except Exception as e:
        print(f"Yield Fetch Error: {e}")
        
    return results