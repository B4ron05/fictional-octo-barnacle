import requests

def fetch_macro_indicators(api_key):
    """
    Fetches the massive list of indicators required for the institutional dashboard.
    """
    url = "https://api.stlouisfed.org/fred/series/observations"
    
    # Dictionary Format: Name -> (Ticker, Units)
    indicators = {
        # Economic Growth
        "GDP Growth QoQ": ("A191RL1Q225SBEA", "lin"), # GDP is already annualized %
        "Retail Sales MoM": ("RSAFS", "pch"),         # Percent Change from previous month
        "Consumer Confidence": ("UMCSENT", "lin"),    # Raw Index Score
        
        # Inflation Bias
        "CPI YoY": ("CPIAUCSL", "pc1"),
        "PPI YoY": ("PPIFIS", "pc1"),
        "PCE YoY": ("PCEPI", "pc1"),
        "2 Yr Yield": ("DGS2", "lin"),
        
        # Jobs Market Bias
        "Non-Farm Payroll": ("PAYEMS", "chg"),        # Monthly Change in thousands
        "Unemployment Rate %": ("UNRATE", "lin"),
        "Weekly Jobless Claims": ("ICSA", "lin"),     
        "JOLTS Job Openings": ("JTSJOL", "lin")
    }
    
    results = {}
    
    for name, (ticker, unit) in indicators.items():
        params = {
            'series_id': ticker,
            'api_key': api_key,
            'file_type': 'json',
            'sort_order': 'desc',
            'limit': 2,
            'units': unit
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get('observations') and len(data['observations']) >= 2:
                    val1 = float(data['observations'][0]['value'])
                    val2 = float(data['observations'][1]['value'])
                    
                    results[name] = {
                        "value": round(val1, 2),
                        "difference": round(val1 - val2, 2)
                    }
                    continue
        except Exception:
            pass
            
        # Fallback if there is a data error
        results[name] = {"value": "N/A", "difference": 0}
        
    return results