from typing import Dict, List, override
from openai import OpenAI
from config import OPENAI_API_KEY
from text_apis.interface import ServiceAPI
from text_apis.message import Message

# Instantiate the OpenAI client


class OpenAIAPI(ServiceAPI):
    def __init__(self) -> None:
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    @override
    def generate_text(self, messages: List[Message], chat_settings: Dict):
        response = self.client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo" based on access
            messages=messages,
            max_tokens=chat_settings["tokens"],
            temperature=chat_settings["temp"],
        )

        # Access the content from the response
        return response.choices[0].message.content
