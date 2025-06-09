#!/bin/bash

# Move to the project directory
cd /home/rohit/kraken-dca-bot || exit 1

# Build the Docker image
# docker build -t kraken-dca-bot .

docker run --rm \
  -v /home/rohit/kraken-dca-bot/kraken_trades.csv:/app/kraken_trades.csv \
  -v /home/rohit/kraken-dca-bot/config.json:/app/config.json \
  kraken-dca-bot
