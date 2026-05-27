import requests
from datetime import datetime, timedelta

def fetch_real_forecasts(fmp_api_key):
    """
    Scans the FMP Economic Calendar for the most recent US macro events
    and extracts the actual vs. consensus forecast data.
    """
    # Look back 45 days to ensure we catch the last monthly announcements
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d')
    
    url = f"https://financialmodelingprep.com/api/v3/economic_calendar?from={start_date}&to={end_date}&apikey={fmp_api_key}"
    
    response = requests.get(url)
    # if response.status_code != 200:
       # raise Exception("Failed to connect to FMP API.")
        
    data = response.json()
    
    if not isinstance(data, list):
        raise Exception(f"API Error: {data.get('Error Message', 'Invalid API Key')}")

    target_events = {
        "Fed Interest Rate Decision": "Interest Rate",
        "Unemployment Rate": "Unemployment",
        "Inflation Rate YoY": "CPI",
        "Producer Price Index YoY": "PPI"
    }

    results = {
        "Interest Rate": {"actual": "N/A", "forecast": "N/A", "difference": 0, "date": "N/A"},
        "Unemployment": {"actual": "N/A", "forecast": "N/A", "difference": 0, "date": "N/A"},
        "CPI": {"actual": "N/A", "forecast": "N/A", "difference": 0, "date": "N/A"},
        "PPI": {"actual": "N/A", "forecast": "N/A", "difference": 0, "date": "N/A"}
    }

    for event in reversed(data):
        if event.get('country') == 'US' and event.get('event') in target_events:
            key = target_events[event['event']]
            
            actual = event.get('actual')
            estimate = event.get('estimate')
            
            # The fixed logic gate
            if results[key]["actual"] == "N/A" and actual is not None and estimate is not None:
                diff = round(actual - estimate, 2)
                
                results[key] = {
                    "actual": actual,
                    "forecast": estimate,
                    "difference": diff,
                    "date": event.get('date', '')[:10] 
                }

    return results