from typing import Dict, List, override
import random
from openai import OpenAI
from text_apis.interface import ServiceAPI
from text_apis.message import Message

# Instantiate the OpenAI client


class GarbageAPI(ServiceAPI):
    def __init__(self) -> None:
        self.word_lengths = {
            1: 0.03,  # a, I
            2: 0.08,  # to, of
            3: 0.17,  # the, and
            4: 0.22,  # that, with
            5: 0.20,  # there, about
            6: 0.12,  # people, things
            7: 0.08,  # because, through
            8: 0.05,  # together, although
            9: 0.03,  # important, according
            10: 0.02,  # everything, understand
        }

        # Common sentence lengths (in words)
        self.sentence_lengths = range(8, 16)

        # Generate some word templates for each length
        self.templates = self._generate_templates()

    @override
    def generate_text(self, messages: List[Message], chat_settings: Dict):
        # Access the content from the response
        return self._generate_text(chat_settings["tokens"])

    def _generate_templates(self):
        """Generate consonant-vowel templates for different word lengths."""
        self.vowels = "aeiou"
        self.consonants = "".join(
            c for c in "qwertyuiopasdfghjklzxcvbnm" if c not in self.vowels
        )
        templates = {}

        for length in range(1, 11):
            templates[length] = []
            for _ in range(5):  # Generate 5 templates per length
                template = []
                for i in range(length):
                    if i % 2 == 0:
                        template.append(random.choice("cv"))
                    else:
                        template.append("v" if template[-1] == "c" else "c")
                templates[length].append("".join(template))

        return templates

    def _generate_word(self, length):
        """Generate a random word of specified length using templates."""
        if length < 1 or length > 10:
            return "x" * length

        template = random.choice(self.templates[length])
        word = ""
        for char in template:
            if char == "c":
                word += random.choice(self.consonants)
            else:
                word += random.choice(self.vowels)
        return word

    def _generate_text(self, target_length):
        """
        Generate random text approximately matching the target length.

        Args:
            target_length (int): Desired length of the text in characters

        Returns:
            str: Generated text
        """
        if target_length < 1:
            return ""

        text = []
        current_length = 0

        while current_length < target_length:
            # Generate a new sentence
            sentence_words = []
            sentence_length = random.choice(self.sentence_lengths)

            for _ in range(sentence_length):
                # Select word length based on frequency distribution
                word_length = random.choices(
                    list(self.word_lengths.keys()),
                    weights=list(self.word_lengths.values()),
                )[0]

                word = self._generate_word(word_length)
                sentence_words.append(word)

            sentence = " ".join(sentence_words)
            sentence = sentence.capitalize() + ". "

            # Check if adding this sentence would exceed target length
            # Allow 10% overflow
            if current_length + len(sentence) > target_length * 1.1:
                break

            text.append(sentence)
            current_length += len(sentence)

        return "".join(text).rstrip()
