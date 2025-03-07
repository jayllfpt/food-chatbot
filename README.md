# Food Chatbot - Telegram Bot

A Telegram bot powered by Google's Gemini AI model that can answer questions and engage in conversations.

## Setup

1. Make sure you have Python 3.8+ installed

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Configure your environment variables:
   - Copy `.env` to `.env.dev` and fill in your actual API keys:
   ```
   cp .env .env.dev
   ```
   - Edit `.env.dev` with your actual values:
   ```
   TELEGRAM_TOKEN=your_telegram_bot_token
   GOOGLE_API_KEY=your_google_api_key
   MODEL_NAME=gemini-2.0-flash
   ```
   - The `.env.dev` file is ignored by git to keep your API keys secure

## Running the Bot

To start the bot, run:
```
python main.py
```

The bot will automatically load environment variables from `.env.dev` if it exists, otherwise it will use `.env`.

## Features

- Responds to `/start`, `/help`, and `/reset` commands
- Processes user messages and generates responses using Google's Gemini AI model
- Uses AI to understand user intent for food suggestions (no fixed keywords needed)
- Provides feedback during processing ("Thinking...")
- Handles errors gracefully
- Stores conversation history in SQLite database
- Manages user session and state
- Collects food criteria and user location
- Suggests restaurants based on criteria and location
- Integrates with OpenStreetMap API to find nearby restaurants
- Provides fallback suggestions when no restaurants are found
- Uses AI to rank restaurants based on criteria relevance
- Maintains conversation context for more natural interactions
- Automatically suggests additional criteria based on user preferences
- Uses standardized prompt templates for consistent AI responses
- **NEW:** Improved user experience with custom keyboards
- **NEW:** Typing indicators for better feedback
- **NEW:** Intelligent error handling with context-specific messages
- **NEW:** Ability to cancel operations at any point
- **NEW:** Centralized fallback handling for consistent error recovery

## Conversation Flow

1. User asks about food suggestions in natural language
2. Bot uses Gemini to detect food-related intent
3. Bot asks for food criteria (e.g., "nướng", "cay", "hải sản")
4. Bot suggests additional criteria based on user's initial input
5. User provides criteria and confirms with "xác nhận" (confirm)
6. Bot asks for user's location
7. User shares location
8. Bot shows "typing" indicator while processing
9. Bot searches for restaurants near the user's location based on criteria
10. Bot ranks restaurants by relevance to the criteria
11. Bot returns top 3 restaurants or suggests dishes if no restaurants are found
12. Bot provides quick action buttons for next steps

## Project Structure

- `main.py`: Entry point that runs the bot
- `bot/main.py`: Main bot implementation with Telegram handlers
- `llm/main.py`: LLM integration with Google's Gemini API
- `database/main.py`: SQLite database management for storing conversation history
- `session/main.py`: User session and state management
- `location/main.py`: OpenStreetMap API integration for finding restaurants
- `criteria/main.py`: Food criteria processing and suggestion
- `prompts/`: Templates for LLM prompts
  - `criteria.py`: Templates for criteria-related prompts
  - `recommendation.py`: Templates for food recommendation prompts
- **NEW:** `fallback/main.py`: Centralized error and fallback handling
- `.env`: Template for environment variables (safe to commit)
- `.env.dev`: Actual environment variables with API keys (not committed)
- `requirements.txt`: Required Python packages
- `food_chatbot.db`: SQLite database file (created automatically)

## Testing Location Services

You can test the location services by running:
```
python -m location.test
```

This will search for restaurants near Hanoi city center and display the top 3 results.

## Creating Your Own Bot

To create your own Telegram bot:

1. Talk to [@BotFather](https://t.me/botfather) on Telegram
2. Use the `/newbot` command and follow the instructions
3. Copy the token provided by BotFather to your `.env.dev` file

## License

This project is open source and available under the MIT License. 