import json
import time
import base64
import hashlib
import hmac
import requests
import urllib.parse

API_URL = "https://api.kraken.com"

def get_kraken_signature(urlpath, data, secret):
    """Generate Kraken API signature using the same method as in queryFund.py"""
    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()

def kraken_request(api_key, api_sec, path, data):
    data['nonce'] = str(int(time.time()*1000))
    urlpath = f'/0/private/{path}'
    headers = {
        'API-Key': api_key,
        'API-Sign': get_kraken_signature(urlpath, data, api_sec)
    }
    resp = requests.post(API_URL + urlpath, headers=headers, data=data)
    response_json = resp.json()
    
    # Only print error responses
    if response_json.get('error'):
        print(f"\n{'!'*50}")
        print(f"[ERROR] Kraken API error in {path}: {response_json['error']}")
        print(f"{'!'*50}\n")
        
    return response_json

def get_current_price(pair):
    url = f"https://api.kraken.com/0/public/Ticker?pair={pair}"
    response = requests.get(url)
    response_json = response.json()
    
    if response_json['error']:
        raise Exception(f"Kraken API error: {response_json['error']}")
    
    result = response_json['result']
    ticker_key = list(result.keys())[0]
    price = float(result[ticker_key]['c'][0])
    print(f"[INFO] Current price for {pair}: {price:.6f} EUR")
    return price

def get_account_balance(api_key, api_sec):
    """Query the account balance from Kraken API"""
    print("\n" + "="*60)
    print("ACCOUNT BALANCE".center(60))
    print("="*60)
    
    data = {
        'nonce': str(int(time.time()*1000))
    }
    response = kraken_request(api_key, api_sec, 'Balance', data)
    return response

def place_market_buy_order(api_key, api_sec, pair, volume):
    print(f"\n[INFO] Placing market buy order:")
    print(f"       Pair:   {pair}")
    print(f"       Volume: {volume:.8f}")
    
    data = {
        'nonce': str(int(time.time()*1000)),
        'ordertype': 'market',
        'type': 'buy',
        'volume': f"{volume:.8f}",
        'pair': pair
    }
    response = kraken_request(api_key, api_sec, 'AddOrder', data)
    if not response.get('error'):
        print(f"\n[SUCCESS] Order placed successfully:")
        print(f"          Transaction ID: {response.get('result', {}).get('txid', ['Unknown'])[0]}")
    return response

def main():
    print("\n" + "="*60)
    print("KRAKEN DCA BOT STARTING".center(60))
    print("="*60)
    print("[INFO] Loading configuration...")
    
    with open('config.json') as f:
        config = json.load(f)

    api_key = config['kraken']['api_key']
    api_sec = config['kraken']['private_key']

    # Query account balance before making any purchases
    balance_response = get_account_balance(api_key, api_sec)
    if balance_response['error']:
        print(f"[ERROR] Failed to fetch account balance: {balance_response['error']}")
        return
    
    account_balance = balance_response['result']
    eur_balance = float(account_balance.get('ZEUR', 0))
    print(f"[INFO] Available EUR balance: {eur_balance:.2f} EUR")
    print("-"*60)

    for coin in config['coins']:
        pair = coin['pair']
        euro_amount = coin['amount']

        print("\n" + "="*60)
        print(f" PROCESSING {pair} ".center(60, '='))
        print("="*60)

        # Check if we have enough funds for this purchase
        if euro_amount > eur_balance:
            print(f"[WARNING] Insufficient funds for {pair}")
            print(f"          Required: {euro_amount:.2f} EUR")
            print(f"          Available: {eur_balance:.2f} EUR")
            print(f"          Skipping this coin.")
            continue

        try:
            price = get_current_price(pair)
            volume = euro_amount / price
            
            print(f"\n[INFO] Purchase summary:")
            print(f"       Pair:       {pair}")
            print(f"       Amount:     {euro_amount:.2f} EUR")
            print(f"       Price:      {price:.6f} EUR")
            print(f"       Volume:     {volume:.8f}")
            
            result = place_market_buy_order(api_key, api_sec, pair, volume)
            
            # Update remaining balance if order was successful
            if not result['error']:
                eur_balance -= euro_amount
                print(f"\n[INFO] Transaction complete")
                print(f"       Remaining EUR balance: {eur_balance:.2f} EUR")
        except Exception as e:
            print(f"\n{'!'*60}")
            print(f"[ERROR] Exception occurred while processing {pair}:")
            print(f"        {str(e)}")
            print(f"{'!'*60}")

    print("\n" + "="*60)
    print(" ALL TRANSACTIONS COMPLETE ".center(60, '='))
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
