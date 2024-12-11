from typing import Dict, List, override
from openai import OpenAI
from text_apis.interface import ServiceAPI
from text_apis.message import Message

# Instantiate the OpenAI client


class LocalAPI(ServiceAPI):
    def __init__(self) -> None:
        self.client = OpenAI(api_key="unused", base_url="http://localhost:5001/v1")

    @override
    def generate_text(self, messages: List[Message], chat_settings: Dict):
        response = self.client.chat.completions.create(
            model="any",  # or "gpt-3.5-turbo" based on access
            messages=messages,
            max_tokens=chat_settings["tokens"],
            temperature=chat_settings["temp"],
        )

        # Access the content from the response
        return response.choices[0].message.content
