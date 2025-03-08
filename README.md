# Food Chatbot - Telegram Bot

A Telegram bot powered by Google's Gemini AI model that can answer questions and engage in conversations.

## Setup

1. Make sure you have Python 3.8+ installed.

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Configure your environment variables:
   - Fill in your actual API keys:
   - Edit `.env` with your actual values:
   ```
   TELEGRAM_TOKEN=your_telegram_bot_token
   GOOGLE_API_KEY=your_google_api_key
   ```

## Creating Your Own Bot

To create your own Telegram bot:

1. Talk to [@BotFather](https://t.me/botfather) on Telegram.
2. Use the `/newbot` command and follow the instructions.
3. Copy the token provided by BotFather to your `.env` file.

## Features

- Responds to `/start` and `/help` commands
- Suggests restaurants based on criteria and location
- Integrates with OpenStreetMap API to find nearby restaurants

## License

This project is open source and available under the MIT License. 