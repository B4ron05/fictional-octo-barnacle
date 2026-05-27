import requests
from datetime import datetime, timedelta

def fetch_finnhub_forecasts(api_key):
    """
    Queries Finnhub's official Economic Calendar API to extract 
    actual values vs. market consensus forecasts.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=45)
    
    from_date = start_date.strftime("%Y-%m-%d")
    to_date = end_date.strftime("%Y-%m-%d")
    
    url = f"https://finnhub.io/api/v1/calendar/economic?from={from_date}&to={to_date}&token={api_key}"
    
    results = {
        "GDP Growth QoQ": {"value": "N/A", "forecast": "N/A", "difference": 0},
        "Retail Sales MoM": {"value": "N/A", "forecast": "N/A", "difference": 0},
        "Consumer Confidence": {"value": "N/A", "forecast": "N/A", "difference": 0},
        "CPI YoY": {"value": "N/A", "forecast": "N/A", "difference": 0},
        "PPI YoY": {"value": "N/A", "forecast": "N/A", "difference": 0},
        "PCE YoY": {"value": "N/A", "forecast": "N/A", "difference": 0},
        "10 Yr Yield": {"value": "N/A", "forecast": "N/A", "difference": 0}, # UPDATED
        "Non-Farm Payroll": {"value": "N/A", "forecast": "N/A", "difference": 0}, 
        "Unemployment Rate %": {"value": "N/A", "forecast": "N/A", "difference": 0},
        "Weekly Jobless Claims": {"value": "N/A", "forecast": "N/A", "difference": 0},
        "JOLTS Job Openings": {"value": "N/A", "forecast": "N/A", "difference": 0}
    }
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            events_list = data.get("economicCalendar", [])
            
            for item in events_list:
                if item.get("country") != "US":
                    continue
                    
                title = item.get("event", "")
                actual = item.get("actual")
                estimate = item.get("estimate")
                
                if actual is not None and estimate is not None:
                    title_lower = title.lower()
                    difference = round(actual - estimate, 2)
                    
                    if "nonfarm payrolls" in title_lower:
                        val = actual / 1000 if actual > 1000 else actual
                        est = estimate / 1000 if abs(estimate) > 1000 else estimate
                        diff = val - est
                        results["Non-Farm Payroll"] = {"value": round(val, 1), "forecast": round(est, 1), "difference": round(diff, 1)}
                        
                    elif "unemployment rate" in title_lower:
                        results["Unemployment Rate %"] = {"value": round(actual, 2), "forecast": round(estimate, 2), "difference": difference}
                        
                    elif "initial jobless claims" in title_lower:
                        results["Weekly Jobless Claims"] = {"value": round(actual, 2), "forecast": round(estimate, 2), "difference": difference}
                        
                    elif "jolts" in title_lower:
                        results["JOLTS Job Openings"] = {"value": round(actual, 2), "forecast": round(estimate, 2), "difference": difference}
                        
                    elif "gdp" in title_lower and "growth" in title_lower:
                        results["GDP Growth QoQ"] = {"value": round(actual, 2), "forecast": round(estimate, 2), "difference": difference}
                        
                    elif "retail sales" in title_lower:
                        results["Retail Sales MoM"] = {"value": round(actual, 2), "forecast": round(estimate, 2), "difference": difference}
                        
                    elif "michigan consumer sentiment" in title_lower:
                        results["Consumer Confidence"] = {"value": round(actual, 2), "forecast": round(estimate, 2), "difference": difference}
                        
                    elif "inflation rate yoy" in title_lower or "cpi yoy" in title_lower:
                        results["CPI YoY"] = {"value": round(actual, 2), "forecast": round(estimate, 2), "difference": difference}
                        
                    elif "ppi" in title_lower:
                        results["PPI YoY"] = {"value": round(actual, 2), "forecast": round(estimate, 2), "difference": difference}
                        
                    elif "pce price index yoy" in title_lower:
                        results["PCE YoY"] = {"value": round(actual, 2), "forecast": round(estimate, 2), "difference": difference}
                        
                    # UPDATED: Now catching the 10-Year auction data
                    elif "10-year note auction" in title_lower or "10-yr note auction" in title_lower:
                        results["10 Yr Yield"] = {"value": round(actual, 2), "forecast": round(estimate, 2), "difference": difference}
                        
    except Exception as e:
        print(f"Finnhub API Error: {e}")
        
    return results