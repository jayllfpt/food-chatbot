import os
from dotenv import load_dotenv
from bot.main import run_bot

env_path = ".env.dev"
load_dotenv(dotenv_path=env_path)

if __name__ == "__main__":
    # Run the Telegram bot
    run_bot()
