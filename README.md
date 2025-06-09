# Kraken DCA Bot

A Python-based Dollar Cost Averaging (DCA) bot for automatically purchasing cryptocurrencies on the Kraken exchange at regular intervals.

## What is Dollar Cost Averaging?

Dollar Cost Averaging is an investment strategy where you invest a fixed amount of money at regular intervals, regardless of the asset's price. This approach reduces the impact of volatility and eliminates the need to time the market.

## Features

- **Automated Purchases**: Buy cryptocurrencies automatically with fixed EUR amounts
- **Multiple Coins**: Support for configuring multiple cryptocurrency pairs
- **Notifications**: 
  - Telegram alerts for purchase success/failure
  - Email notifications with transaction details
- **Logging**: 
  - CSV logging of all transactions for record-keeping
  - Koinly-compatible CSV export for tax reporting
- **Balance Checking**: Verifies sufficient funds before executing trades
- **Docker Support**: Run as a containerized application

## Installation

### Prerequisites

- Python 3.11+
- Kraken account with API keys
- (Optional) Telegram bot token and chat ID
- (Optional) Email account for notifications

### Local Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/kraken-dca-bot.git
   cd kraken-dca-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a configuration file:
   ```bash
   cp config.example.json config.json
   ```

4. Edit `config.json` with your Kraken API keys and preferences

### Docker Installation

1. Build the Docker image:
   ```bash
   docker build -t kraken-dca-bot .
   ```

2. Create and configure your `config.json` file

3. Run the container:
   ```bash
   docker run -v $(pwd)/config.json:/app/config.json -v $(pwd)/logs:/app/logs kraken-dca-bot
   ```

## Configuration

Copy `config.example.json` to `config.json` and edit the following sections:

```json
{
    "kraken": {
        "api_key": "YOUR_KRAKEN_API_KEY_HERE",
        "private_key": "YOUR_KRAKEN_PRIVATE_KEY_HERE"
    },
    "coins": [
        {
            "pair": "XBTEUR",
            "amount": 50
        },
        {
            "pair": "ETHEUR",
            "amount": 50
        }
    ],
    "notifications": {
        "telegram": {
            "bot_token": "YOUR_TELEGRAM_BOT_TOKEN_HERE",
            "chat_id": "YOUR_TELEGRAM_CHAT_ID_HERE"
        },
        "email": {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "from_email": "your.email@example.com",
            "to_email": "your.email@example.com",
            "username": "your.email@example.com",
            "password": "YOUR_EMAIL_APP_PASSWORD_HERE"
        }
    },
    "csv_log_file": "/app/kraken_trades.csv"
}
```

### Configuration Options

- **kraken**: Your Kraken API credentials
  - `api_key`: Your Kraken API key
  - `private_key`: Your Kraken private key

- **coins**: List of coins to purchase
  - `pair`: Trading pair (e.g., "XBTEUR" for Bitcoin/Euro)
  - `amount`: Fixed amount in EUR to spend on each purchase

- **notifications**: Configure notification channels
  - `telegram`: Telegram bot settings
    - `bot_token`: Your Telegram bot token
    - `chat_id`: Your Telegram chat ID
  - `email`: Email notification settings
    - `smtp_server`: SMTP server address
    - `smtp_port`: SMTP port
    - `from_email`: Sender email
    - `to_email`: Recipient email
    - `username`: SMTP username
    - `password`: SMTP password or app password

- **csv_log_file**: Path to save transaction logs

## Usage

### Running Manually

Run the bot with:

```bash
python buy.py
```

### Scheduled Execution

For regular DCA purchases, set up a cron job:

```bash
# Run DCA bot every Monday at 8:00 AM
0 8 * * 1 cd /path/to/kraken-dca-bot && python buy.py
```

### Docker Scheduled Execution

You can run the Docker container on a schedule:

```bash
# Run DCA bot every Monday at 8:00 AM
0 8 * * 1 docker run -v /path/to/config.json:/app/config.json -v /path/to/logs:/app/logs kraken-dca-bot
```

## How It Works

1. The bot reads your configuration file
2. Checks your EUR balance on Kraken
3. For each configured coin:
   - Verifies sufficient funds
   - Gets the current market price
   - Calculates the volume to purchase based on your configured EUR amount
   - Places a market buy order
   - Logs the transaction and sends notifications
   - Creates Koinly-compatible CSV entries for tax reporting
4. Updates your remaining balance for subsequent purchases

## Transaction Logging

The bot logs all transactions in two formats:

1. **Standard CSV Log**: Contains timestamp, pair, price, volume, euro amount, and transaction ID.
2. **Koinly-compatible CSV**: Formatted specifically for import into Koinly tax software, containing all the required fields for proper tax calculations and reporting.

The Koinly file is automatically created with the same name as your main log file but with `_koinly` suffix (e.g., `kraken_trades_koinly.csv`).

## Security Considerations

- Store your `config.json` with API keys securely
- Use restrictive API key permissions (trade only, no withdrawals)
- For email notifications with Gmail, use an app password instead of your account password
- Consider using environment variables for sensitive information when running in production

## Troubleshooting

- Check logs for detailed error messages
- Verify your Kraken API keys have the correct permissions
- Ensure your notification settings are correct
- Verify you have sufficient EUR balance in your Kraken account

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is provided as-is with no warranty. Use at your own risk. The authors are not responsible for any financial losses incurred through the use of this bot.
