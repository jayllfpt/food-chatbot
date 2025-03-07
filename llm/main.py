import os
from openai import OpenAI

# Load environment variables
API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash")

# Initialize OpenAI client
client = OpenAI(
    api_key=API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

def get_model_response(client, system_message, user_message):
    """
    Get response from the model using the provided client and messages.
    
    Args:
        client: OpenAI client instance
        system_message (str): System message to set model behavior
        user_message (str): User's input message
    
    Returns:
        str: Model's response content
    """
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]
    )
    return completion.choices[0].message.content

