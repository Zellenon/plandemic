from abc import ABC


class ServiceAPI(ABC):
    def __init__(self) -> None:
        pass

    def generate_text(self, messages, chat_settings):
        response = self.client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo" based on access
            messages=messages,
            max_tokens=chat_settings["tokens"],
            temperature=chat_settings["temp"],
        )

        # Access the content from the response
        return response.choices[0].message.content
