import json
import requests
import yfinance as yf
from datetime import datetime
import os
from google import genai
import time
from google.api_core import exceptions

# Configuration
SYMBOL = "MSTR"
CG_API_KEY = os.getenv("CG_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_mnav_data():
    # 1. Get BTC Holdings from CoinGecko
    url = "https://api.coingecko.com/api/v3/companies/public_treasury/bitcoin"
    headers = {"accept": "application/json", "x-cg-demo-api-key": CG_API_KEY}
    response = requests.get(url, headers=headers)
    data = response.json()
    mstr_btc_data = next((c for c in data['companies'] if "MSTR" in c['symbol'].upper()), None)
    btc_holdings = mstr_btc_data['total_holdings']

    # 2. Get Market Cap from Yahoo Finance
    ticker = yf.Ticker(SYMBOL)
    market_cap = ticker.info.get('marketCap')
    btc_price = yf.Ticker("BTC-USD").fast_info.get('lastPrice')
    
    btc_value_usd = btc_holdings * btc_price
    return round(market_cap / btc_value_usd, 4)

def generate_ai_advice(history):
    if not GEMINI_API_KEY:
        return "AI Analysis unavailable: Key missing."
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    recent_data = history[-30:]
    
    prompt = f"Analyze this mNAV time-series: {json.dumps(recent_data)}"

    # Robust Retry Loop
    max_retries = 5
    for i in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.0-flash", 
                contents=prompt
            )
            return response.text
        except exceptions.ResourceExhausted:
            if i < max_retries - 1:
                wait_time = (i + 1) * 5 # Wait 5s, then 10s
                print(f"Rate limit hit. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                return "The analyst is busy right now. Check back tomorrow!"

def update_files(new_mnav):
    # Load existing data with safety check
    if os.path.exists('data.json') and os.path.getsize('data.json') > 0:
        with open('data.json', 'r') as f:
            data = json.load(f)
    else:
        data = []

    new_entry = {"date": datetime.now().strftime("%Y-%m-%d"), "mnav": new_mnav}
    
    # Avoid duplicates
    if not data or data[-1]['date'] != new_entry['date']:
        data.append(new_entry)

    # Save Data
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=2)

    # Generate and Save Advice
    advice = generate_ai_advice(data)
    with open('advice.txt', 'w') as f:
        f.write(advice)

if __name__ == "__main__":
    val = get_mnav_data()
    update_files(val)