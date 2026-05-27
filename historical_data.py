import requests
import pandas as pd
from datetime import datetime, timedelta

def fetch_fred_history(api_key, lookback_limit=6):
    """
    Queries the Federal Reserve (FRED) API for deep historical macro trends.
    Uses Pandas to specifically resample daily yields into "1st of the month" prints.
    """
    metrics = {
        "GDP Growth QoQ (%)": {"id": "A191RL1Q225SBEA", "units": "lin", "divide": 1},
        "Retail Sales MoM (%)": {"id": "RSAFS", "units": "pch", "divide": 1},      
        "Consumer Confidence": {"id": "UMCSENT", "units": "lin", "divide": 1},
        "CPI YoY (%)": {"id": "CPIAUCSL", "units": "pc1", "divide": 1},             
        "PPI YoY (%)": {"id": "PPIACO", "units": "pc1", "divide": 1},
        "PCE YoY (%)": {"id": "PCEPI", "units": "pc1", "divide": 1},
        "10 Yr Yield (%)": {"id": "DGS10", "units": "lin", "divide": 1},
        "Non-Farm Payroll (k)": {"id": "PAYEMS", "units": "chg", "divide": 1},      
        "Unemployment Rate (%)": {"id": "UNRATE", "units": "lin", "divide": 1},
        "Weekly Jobless Claims (k)": {"id": "ICSA", "units": "lin", "divide": 1000},
        "JOLTS Openings (M)": {"id": "JTSJOL", "units": "lin", "divide": 1000}
    }

    history = {}
    
    # Look back 10 years to ensure we have enough data for quarterly metrics (up to 24 prints = 6 years)
    start_date = (datetime.now() - timedelta(days=365*10)).strftime("%Y-%m-%d")

    for name, config in metrics.items():
        # Notice we removed 'limit' and changed sort_order to 'asc' so Pandas can process time properly
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={config['id']}&api_key={api_key}&file_type=json&sort_order=asc&observation_start={start_date}&units={config['units']}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json().get("observations", [])
                
                chart_data = []
                for obs in data:
                    val = obs.get("value")
                    if val != ".": # FRED returns a "." if a holiday occurred and the market was closed
                        chart_data.append({
                            "Date": obs.get("date"),
                            "Value": round(float(val) / config["divide"], 2)
                        })
                
                if chart_data:
                    df = pd.DataFrame(chart_data)
                    df['Date'] = pd.to_datetime(df['Date'])
                    df.set_index("Date", inplace=True)
                    
                    # NEW: Custom resampling to grab the 1st of the month for the 10Y Yield
                    if name == "10 Yr Yield (%)":
                        df = df.resample('MS').first().dropna()
                        
                    # Slice the exact amount of prints the user requested on the slider!
                    df = df.tail(lookback_limit)
                    df.index = df.index.strftime("%Y-%m-%d")
                    
                    history[name] = df
                else:
                    history[name] = pd.DataFrame()
            else:
                history[name] = pd.DataFrame()
        except Exception as e:
            print(f"FRED Fetch Error for {name}: {e}")
            history[name] = pd.DataFrame()
            
    return history