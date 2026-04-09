import json
import requests
import yfinance as yf
from datetime import datetime
import os

# Configuration
SYMBOL = "MSTR"
# Get the key from GitHub Secrets environment variable
CG_API_KEY = os.getenv("CG_API_KEY")

def get_data():
    if not CG_API_KEY:
        print("Error: CG_API_KEY not found in environment variables.")
        exit(1)

    # 1. Get BTC Holdings from CoinGecko
    url = "https://api.coingecko.com/api/v3/companies/public_treasury/bitcoin"
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": CG_API_KEY
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"API Error {response.status_code}: {response.text}")
        exit(1)

    data = response.json()
    
    # Safely find MicroStrategy
    companies = data.get('companies', [])
    mstr_btc_data = next((c for c in companies if c['symbol'] == 'MSTR'), None)
    
    if not mstr_btc_data:
        print("Error: Could not find MSTR data in API response.")
        exit(1)
    
    btc_holdings = mstr_btc_data['total_holdings']
    btc_value_usd = mstr_btc_data['total_value_usd']
    # Derived BTC price used by CoinGecko for this calculation
    btc_price = btc_value_usd / btc_holdings

    # 2. Get Stock Market Cap from Yahoo Finance
    ticker = yf.Ticker(SYMBOL)
    # yfinance sometimes returns None if the API is throttled; use a fallback
    market_cap = ticker.info.get('marketCap')
    
    if not market_cap:
        # Fallback: Price * Shares (approx for MSTR)
        price = ticker.fast_info.get('lastPrice')
        market_cap = price * 180000000 # Rough estimate if info fails
        print(f"Warning: Using fallback market cap calculation.")

    # 3. Calculate mNAV
    mnav = market_cap / btc_value_usd
    return round(mnav, 4)

def update_json(new_mnav):
    # Ensure the file exists
    if not os.path.exists('data.json'):
        with open('data.json', 'w') as f:
            json.dump([], f)

    with open('data.json', 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []
    
    new_entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "mnav": new_mnav
    }
    
    # Only append if today's date isn't already there
    if not data or data[-1]['date'] != new_entry['date']:
        data.append(new_entry)
        # Keep only last 30 days of data to keep the file small
        data = data[-30:] 
        with open('data.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Successfully added entry for {new_entry['date']}")
    else:
        print("Entry for today already exists. Skipping.")

if __name__ == "__main__":
    val = get_data()
    print(f"Calculated mNAV: {val}")
    update_json(val)
