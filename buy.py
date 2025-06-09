import json
import time
import base64
import hashlib
import hmac
import requests
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import csv
from datetime import datetime
import os
from typing import Dict, List, Any, Optional, Tuple


API_URL = "https://api.kraken.com"

# ====== Classes for Better Organization ======

class KrakenAPI:
    """Handles all interactions with the Kraken API"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
    
    def get_signature(self, urlpath: str, data: Dict[str, Any]) -> str:
        """Generate Kraken API signature"""
        postdata = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()
        mac = hmac.new(base64.b64decode(self.api_secret), message, hashlib.sha512)
        return base64.b64encode(mac.digest()).decode()
    
    def request(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to the Kraken API"""
        data['nonce'] = str(int(time.time()*1000))
        urlpath = f'/0/private/{path}'
        headers = {
            'API-Key': self.api_key,
            'API-Sign': self.get_signature(urlpath, data)
        }
        
        resp = requests.post(API_URL + urlpath, headers=headers, data=data)
        response_json = resp.json()
        
        if response_json.get('error'):
            print(f"\n{'!'*50}")
            print(f"[ERROR] Kraken API error in {path}: {response_json['error']}")
            print(f"{'!'*50}\n")
        
        return response_json
    
    def get_account_balance(self) -> Dict[str, Any]:
        """Query the account balance from Kraken API"""
        print("\n" + "="*60)
        print("ACCOUNT BALANCE".center(60))
        print("="*60)
        return self.request('Balance', {})
    
    def get_current_price(self, pair: str) -> float:
        """Get current price for a trading pair"""
        url = f"{API_URL}/0/public/Ticker?pair={pair}"
        response = requests.get(url)
        response_json = response.json()
        
        if response_json['error']:
            raise Exception(f"Kraken API error: {response_json['error']}")
        
        result = response_json['result']
        ticker_key = list(result.keys())[0]
        price = float(result[ticker_key]['c'][0])
        print(f"[INFO] Current price for {pair}: {price:.6f} EUR")
        return price
    
    def place_market_buy_order(self, pair: str, volume: float) -> Dict[str, Any]:
        """Place a market buy order"""
        print(f"\n[INFO] Placing market buy order:")
        print(f"       Pair:   {pair}")
        print(f"       Volume: {volume:.8f}")
        
        data = {
            'ordertype': 'market',
            'type': 'buy',
            'volume': f"{volume:.8f}",
            'pair': pair
        }
        
        response = self.request('AddOrder', data)
        if not response.get('error'):
            print(f"\n[SUCCESS] Order placed successfully:")
            print(f"          Transaction ID: {response.get('result', {}).get('txid', ['Unknown'])[0]}")
        
        return response


class NotificationManager:
    """Handles all notification methods"""
    
    def __init__(self, config: Dict[str, Any]):
        telegram_cfg = config.get('notifications', {}).get('telegram', {})
        self.telegram_token = telegram_cfg.get('bot_token')
        self.telegram_chat_id = telegram_cfg.get('chat_id')
        
        email_cfg = config.get('notifications', {}).get('email', {})
        self.smtp_server = email_cfg.get('smtp_server')
        self.smtp_port = email_cfg.get('smtp_port')
        self.email_address = email_cfg.get('from_email')
        self.email_password = email_cfg.get('password')
        self.recipient_email = email_cfg.get('to_email')
    
    def send_telegram(self, message: str) -> None:
        """Send a message via Telegram"""
        if not (self.telegram_token and self.telegram_chat_id):
            return
            
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        data = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, data=data)
            if response.status_code != 200:
                print(f"[ERROR] Telegram error: {response.text}")
            else:
                print("[INFO] Telegram message sent.")
        except Exception as e:
            print(f"[ERROR] Failed to send Telegram message: {e}")
    
    def send_email(self, subject: str, body: str) -> None:
        """Send a notification email"""
        if not all([self.smtp_server, self.smtp_port, self.email_address, 
                    self.email_password, self.recipient_email]):
            return
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = self.recipient_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.sendmail(self.email_address, self.recipient_email, msg.as_bytes())
                
            print(f"[INFO] Email sent to {self.recipient_email}")
        except Exception as e:
            print(f"[ERROR] Failed to send email: {str(e)}")
    
    def notify(self, message: str) -> None:
        """Send notifications through all configured channels"""
        self.send_telegram(message)
        self.send_email("Kraken DCA Bot Notification", message)


class TradeLogger:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.koinly_csv_path = csv_path.replace(".csv", "_koinly.csv")

    def log_trade(self, pair: str, price: float, volume: float, euro_amount: float, txid: str) -> None:
        timestamp = datetime.utcnow().replace(microsecond=0).isoformat()

        file_exists = os.path.isfile(self.csv_path) and os.path.getsize(self.csv_path) > 0
        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'pair', 'price_eur', 'volume', 'euro_spent', 'order_id'])
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                'timestamp': timestamp,
                'pair': pair,
                'price_eur': f"{price:.2f}",
                'volume': f"{volume:.8f}",
                'euro_spent': f"{euro_amount:.2f}",
                'order_id': txid
            })

        koinly_exists = os.path.isfile(self.koinly_csv_path) and os.path.getsize(self.koinly_csv_path) > 0
        with open(self.koinly_csv_path, 'a', newline='', encoding='utf-8') as kf:
            writer = csv.DictWriter(kf, fieldnames=[
                'Date', 'Sent Amount', 'Sent Currency', 'Received Amount', 'Received Currency',
                'Fee Amount', 'Fee Currency', 'Net Worth Amount', 'Net Worth Currency', 'Label', 'Description', 'TxHash'
            ])
            if not koinly_exists:
                writer.writeheader()
            writer.writerow({
                'Date': timestamp,
                'Sent Amount': euro_amount,
                'Sent Currency': 'EUR',
                'Received Amount': volume,
                'Received Currency': self.convert_kraken_pair_to_symbol(pair),
                'Fee Amount': 0,
                'Fee Currency': '',
                'Net Worth Amount': euro_amount,
                'Net Worth Currency': 'EUR',
                'Label': 'Buy',
                'Description': f'Buy {pair}',
                'TxHash': txid
            })

    def convert_kraken_pair_to_symbol(self, pair: str) -> str:
        # Define known quote currencies Kraken uses
        quote_currencies = ['EUR', 'USD', 'USDT', 'BTC']

        # Remove quote currency suffix if present
        for quote in quote_currencies:
            if pair.endswith(quote):
                base = pair[:-len(quote)]
                break
        else:
            base = pair  # no quote suffix matched

        # Known Kraken exceptions mapping
        if base == 'XBT':
            return 'BTC'

        # Remove leading 'X' or 'Z' if present (Kraken's asset class prefixes)
        if base.startswith(('X', 'Z')):
            base = base[1:]

        # Otherwise, return base as symbol
        return base


class DCABot:
    """Main DCA Bot class that orchestrates the buying process"""
    
    def __init__(self, config_path: str = 'config.json'):
        """Initialize the DCA Bot with configuration"""
        self.config = self._load_config(config_path)
        self.kraken = KrakenAPI(
            self.config['kraken']['api_key'],
            self.config['kraken']['private_key']
        )
        self.notifier = NotificationManager(self.config)
        self.logger = TradeLogger(self.config.get('csv_log_file', 'kraken_trades.csv'))
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load configuration: {str(e)}")
            exit(1)
    
    def run(self) -> None:
        """Execute the DCA buying strategy"""
        print("\n" + "="*60)
        print("KRAKEN DCA BOT STARTING".center(60))
        print("="*60)
        
        # Get account balance
        balance_response = self.kraken.get_account_balance()
        if balance_response['error']:
            error_msg = f"Failed to fetch account balance: {balance_response['error']}"
            print(f"[ERROR] {error_msg}")
            self.notifier.notify(f"❌ {error_msg}")
            return
            
        account_balance = balance_response['result']
        eur_balance = float(account_balance.get('ZEUR', 0))
        print(f"[INFO] Available EUR balance: {eur_balance:.2f} EUR")
        print("-"*60)
        
        # Process each coin
        for coin in self.config.get('coins', []):
            self._process_coin(coin, eur_balance)
            
        print("\n" + "="*60)
        print(" ALL TRANSACTIONS COMPLETE ".center(60, '='))
        print("="*60 + "\n")
    
    def _process_coin(self, coin: Dict[str, Any], eur_balance: float) -> float:
        """Process a single coin purchase and return remaining EUR balance"""
        pair = coin['pair']
        euro_amount = coin['amount']
        
        print("\n" + "="*60)
        print(f" PROCESSING {pair} ".center(60, '='))
        print("="*60)
        
        # Check for sufficient funds
        if euro_amount > eur_balance:
            message = (
                f"⚠️ Insufficient funds for *{pair}*\n"
                f"Required: {euro_amount:.2f} EUR\n"
                f"Available: {eur_balance:.2f} EUR"
            )
            print(f"[WARNING] {message}")
            self.notifier.notify(message)
            return eur_balance
            
        try:
            # Get current price and calculate volume
            price = self.kraken.get_current_price(pair)
            volume = euro_amount / price
            
            print(f"\n[INFO] Purchase summary:")
            print(f"       Pair:       {pair}")
            print(f"       Amount:     {euro_amount:.2f} EUR")
            print(f"       Price:      {price:.6f} EUR")
            print(f"       Volume:     {volume:.8f}")
            
            # Place order
            result = self.kraken.place_market_buy_order(pair, volume)
            
            # Handle successful order
            if not result['error']:
                eur_balance -= euro_amount
                txid = result.get('result', {}).get('txid', ['Unknown'])[0]
                
                # Log and notify
                message = (
                    f"✅ Successfully bought *{pair}*\n"
                    f"Amount: {euro_amount:.2f} EUR\n"
                    f"Price: {price:.6f} EUR\n"
                    f"Volume: {volume:.8f}\n"
                    f"TxID: `{txid}`\n"
                    f"Remaining Balance: {eur_balance:.2f} EUR"
                )
                self.notifier.notify(message)
                self.logger.log_trade(pair, price, volume, euro_amount, txid)
                
        except Exception as e:
            message = f"❌ Error while processing *{pair}*: {e}"
            print(f"[ERROR] {message}")
            self.notifier.notify(message)
            
        return eur_balance


# ====== Main Entry Point ======

def main():
    """Main entry point for the script"""
    bot = DCABot()
    bot.run()


if __name__ == "__main__":
    main()
