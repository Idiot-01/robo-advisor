import json
import requests
import yfinance as yf
from datetime import datetime

# Configuration
SYMBOL = "MSTR"
CG_API_KEY = "YOUR_COINGECKO_API_KEY" # This will be handled by GitHub Secrets

def get_data():
    # 1. Get BTC Price and MSTR Holdings from CoinGecko
    url = f"https://api.coingecko.com/api/v3/companies/public_treasury/bitcoin?x_cg_demo_api_key={CG_API_KEY}"
    response = requests.get(url).json()
    mstr_btc_data = next(c for c in response['companies'] if c['symbol'] == 'MSTR')
    
    btc_holdings = mstr_btc_data['total_holdings']
    btc_price = mstr_btc_data['total_value_usd'] / btc_holdings

    # 2. Get Stock Market Cap from Yahoo Finance
    ticker = yf.Ticker(SYMBOL)
    market_cap = ticker.info.get('marketCap')

    # 3. Calculate mNAV
    # mNAV = Market Cap / (BTC Holdings * Current BTC Price)
    mnav = market_cap / (btc_holdings * btc_price)
    
    return round(mnav, 4)

def update_json(new_mnav):
    with open('data.json', 'r') as f:
        data = json.load(f)
    
    new_entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "mnav": new_mnav
    }
    
    # Avoid duplicate entries for the same day
    if data[-1]['date'] != new_entry['date']:
        data.append(new_entry)
        with open('data.json', 'w') as f:
            json.dump(data, f, indent=2)

if __name__ == "__main__":
    val = get_data()
    update_json(val)
