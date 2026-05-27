def evaluate_bias(asset, metric_name, difference):
    """
    Evaluates macro data based on the specific asset class.
    Returns a tuple: (Bias Text, Hex Color)
    """
    BULLISH = "#2962FF"
    BEARISH = "#F44336"
    NEUTRAL = "#808080"

    equities = ["S&P 500", "NASDAQ 100"]
    metals = ["GOLD", "SILVER"]
    energy = ["CRUDE OIL"]
    usd = ["US DOLLAR INDEX"]
    bonds = ["10-YR TREASURY"]

    # --- 1. GROWTH & CONSUMPTION BLOCK ---
    if metric_name in ["GDP Growth QoQ", "Retail Sales MoM", "Consumer Confidence"]:
        if difference > 0:
            if asset in equities or asset in usd or asset in bonds or asset in energy: return "Bullish", BULLISH
            if asset in metals: return "Bearish", BEARISH
        elif difference < 0:
            if asset in equities or asset in usd or asset in bonds or asset in energy: return "Bearish", BEARISH
            if asset in metals: return "Bullish", BULLISH

    # --- 2. INFLATION BLOCK ---
    elif metric_name in ["CPI YoY", "PPI YoY", "PCE YoY"]:
        if difference > 0:
            if asset in equities or asset in bonds or asset in metals: return "Bearish", BEARISH
            if asset in usd or asset in energy: return "Bullish", BULLISH
        elif difference < 0:
            if asset in equities or asset in bonds or asset in metals: return "Bullish", BULLISH
            if asset in usd or asset in energy: return "Bearish", BEARISH

    # --- 3. LABOR MARKET BLOCK ---
    elif metric_name in ["Non-Farm Payroll", "JOLTS Job Openings"]:
        if difference > 0:
            if asset in usd or asset in energy or asset in equities: return "Bullish", BULLISH
            if asset in metals or asset in bonds: return "Bearish", BEARISH
        elif difference < 0:
            if asset in usd or asset in energy or asset in equities: return "Bearish", BEARISH
            if asset in metals or asset in bonds: return "Bullish", BULLISH

    elif metric_name in ["Unemployment Rate %", "Weekly Jobless Claims"]:
        if difference > 0:
            if asset in usd or asset in energy or asset in equities: return "Bearish", BEARISH
            if asset in metals or asset in bonds: return "Bullish", BULLISH
        elif difference < 0:
            if asset in usd or asset in energy or asset in equities: return "Bullish", BULLISH
            if asset in metals or asset in bonds: return "Bearish", BEARISH

    # --- 4. ANCHORING MECHANISM (10 Yr Yield via 21 SMA) ---
    elif metric_name == "10 Yr Yield (21d SMA)":
        if difference > 0:
            if asset in equities or asset in metals or asset in bonds: return "Bearish", BEARISH
            if asset in usd or asset in energy: return "Bullish", BULLISH
        elif difference < 0:
            if asset in equities or asset in metals or asset in bonds: return "Bullish", BULLISH
            if asset in usd or asset in energy: return "Bearish", BEARISH

    # --- 5. INSTITUTIONAL COT & TECHNICALS ---
    elif metric_name in ["Net Change (WoW)", "4H / Daily Trend", "Seasonality Trend", "Put/Call Ratio"]:
        if difference > 0: return "Bullish", BULLISH
        elif difference < 0: return "Bearish", BEARISH

    return "Neutral", NEUTRAL