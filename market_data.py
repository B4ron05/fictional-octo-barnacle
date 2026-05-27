import yfinance as yf

def fetch_liquidity_metrics():
    """
    Fetches the current and previous daily closing prices for major market overlays.
    """
    tickers = {
        "VIX (Volatility)": "^VIX",
        "US Dollar Index": "DX-Y.NYB",
        "10-Yr Treasury Yield": "^TNX"
    }
    
    results = {}
    
    for name, ticker in tickers.items():
        try:
            # We fetch the last 5 days just to ensure we catch the last 2 valid trading days 
            # (skipping weekends/holidays automatically)
            data = yf.Ticker(ticker).history(period="5d")
            
            if len(data) >= 2:
                current_val = round(data['Close'].iloc[-1], 2)
                prev_val = round(data['Close'].iloc[-2], 2)
                
                # Calculate Daily Change
                diff = round(current_val - prev_val, 2)
                
                results[name] = {
                    "value": current_val,
                    "previous": prev_val,
                    "difference": diff
                }
            else:
                results[name] = {"value": "N/A", "previous": "N/A", "difference": 0}
        except Exception:
            results[name] = {"value": "Error", "previous": "Error", "difference": 0}
            
    return results