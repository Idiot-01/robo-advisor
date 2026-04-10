import json
import requests
import yfinance as yf
from datetime import datetime
import os
from google import genai

# Configuration
SYMBOL = "MSTR"
CG_API_KEY = os.getenv("CG_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_mnav_data():
    """Fetches Bitcoin holdings and market cap to calculate mNAV."""
    url = "https://api.coingecko.com/api/v3/companies/public_treasury/bitcoin"
    headers = {"accept": "application/json", "x-cg-demo-api-key": CG_API_KEY}
    response = requests.get(url, headers=headers)
    data = response.json()
    
    mstr_btc_data = next((c for c in data['companies'] if "MSTR" in c['symbol'].upper()), None)
    btc_holdings = mstr_btc_data['total_holdings']

    ticker = yf.Ticker(SYMBOL)
    market_cap = ticker.info.get('marketCap')
    btc_price = yf.Ticker("BTC-USD").fast_info.get('lastPrice')
    
    btc_value_usd = btc_holdings * btc_price
    return round(market_cap / btc_value_usd, 4)

def generate_ai_advice(history):
    """Sends the last 30 days of data to Gemini for a brief insight."""
    if not GEMINI_API_KEY:
        return "AI Analysis unavailable: API Key missing."
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    recent_data = history[-30:]
    prompt = f"Analyze this mNAV time-series and provide a 2-sentence insight: {json.dumps(recent_data)}"
    
    try:
        # Using gemini-2.0-flash for current compatibility
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "Market analysis currently updating..."

def update_files(new_mnav):
    """Updates data.json and advice.txt safely."""
    # 1. Load existing data
    if os.path.exists('data.json') and os.path.getsize('data.json') > 0:
        with open('data.json', 'r') as f:
            data = json.load(f)
    else:
        data = []

    today = datetime.now().strftime("%Y-%m-%d")
    new_entry = {"date": today, "mnav": new_mnav}
    
    # 2. Duplicate Check: If today exists, just update the advice, don't double-append
    if data and data[-1]['date'] == today:
        print(f"Entry for {today} already exists. Updating mNAV and refreshing advice.")
        data[-1]['mnav'] = new_mnav
    else:
        data.append(new_entry)

    # 3. Save updated history
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=2)

    # 4. Generate and save the daily insight
    advice = generate_ai_advice(data)
    with open('advice.txt', 'w') as f:
        f.write(advice)
    print("Files successfully updated.")

if __name__ == "__main__":
    try:
        val = get_mnav_data()
        update_files(val)
    except Exception as e:
        print(f"Critical Script Error: {e}")