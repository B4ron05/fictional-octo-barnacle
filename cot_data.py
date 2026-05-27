import pandas as pd
import requests

def fetch_cot_data(cftc_ticker, weeks_to_fetch=2):
    """
    Fetches COT data and calculates Long/Short Percentages.
    """
    url = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"
    params = {
        "cftc_contract_market_code": cftc_ticker,
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": weeks_to_fetch
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"API Request Failed: {response.text}")
        
    data = response.json()
    if not data or len(data) < 2:
        return None
        
    df = pd.DataFrame(data)
    numeric_cols = ['noncomm_positions_long_all', 'noncomm_positions_short_all']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric)
    
    # --- Current Week ---
    curr_long = df['noncomm_positions_long_all'].iloc[0]
    curr_short = df['noncomm_positions_short_all'].iloc[0]
    curr_total = curr_long + curr_short
    
    curr_long_pct = round((curr_long / curr_total) * 100, 2)
    curr_short_pct = round((curr_short / curr_total) * 100, 2)
    
    # --- Previous Week ---
    prev_long = df['noncomm_positions_long_all'].iloc[1]
    prev_short = df['noncomm_positions_short_all'].iloc[1]
    prev_total = prev_long + prev_short
    
    prev_long_pct = round((prev_long / prev_total) * 100, 2)
    
    # Calculate the shift in bullish sentiment
    change_pct = round(curr_long_pct - prev_long_pct, 2)
    
    return {
        "long_pct": curr_long_pct,
        "short_pct": curr_short_pct,
        "change_pct": change_pct
    }