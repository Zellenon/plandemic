from enum import Enum
from typing import List

from agents import Agent
from text_apis.message import Message


class TextService(Enum):
    garbage = 0
    lorem_ispum = 1
    markov = 2
    local = 3
    openai = 4


class TextAPI:

    def __init__(self, mode: TextService) -> None:
        self.client = None
        if mode == TextService.garbage:
            from text_apis import garbage

            self.client = garbage.GarbageAPI()
        elif mode == TextService.lorem_ispum:
            pass
        elif mode == TextService.markov:
            pass
        elif mode == TextService.local:
            from text_apis import local

            self.client = local.LocalAPI()
            pass
        elif mode == TextService.openai:
            from text_apis import openai

            self.client = openai.OpenAIAPI()

        self.chat_settings = {"tokens": 100, "temp": 0.7}

    def generate(self, messages: List[Message]) -> str:
        # Call the updated `client.chat.completions.create` method
        response = self.client.generate_text(
            messages=messages, chat_settings=self.chat_settings
        )

        # Access the content from the response
        return response


text_controller = TextAPI(TextService.garbage)
