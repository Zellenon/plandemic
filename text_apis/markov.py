from typing import Dict, List, Tuple, Optional
import random
from collections import defaultdict


class MarkovChain:
    """
    A simple Markov chain implementation for text generation.

    Attributes:
        order (int): The order of the Markov chain (how many words to use as state)
        chain (Dict): The probability mapping for state transitions
        start_states (List): Valid starting states for text generation
    """

    def __init__(self, order: int = 1):
        """
        Initialize a new Markov chain.

        Args:
            order (int): Number of words to use as state (default: 1)
        """
        self.order = order
        self.chain = defaultdict(lambda: defaultdict(int))
        self.start_states = []

    def _get_states(self, words: List[str]) -> List[Tuple[str]]:
        """
        Convert a list of words into state tuples.

        Args:
            words (List[str]): List of words to process

        Returns:
            List[Tuple[str]]: List of state tuples
        """
        states = []
        for i in range(len(words) - self.order):
            current_state = tuple(words[i : i + self.order])
            next_word = words[i + self.order]
            states.append((current_state, next_word))
        return states

    def train(self, text: str) -> None:
        """
        Train the Markov chain on a piece of text.

        Args:
            text (str): Training text
        """
        # Preprocess text into words
        words = text.split()
        if len(words) <= self.order:
            raise ValueError("Text must be longer than Markov chain order")

        # Get valid start states
        self.start_states.append(tuple(words[: self.order]))

        # Build chain
        for state, next_word in self._get_states(words):
            self.chain[state][next_word] += 1

    def _choose_next(self, state: Tuple[str]) -> str | None:
        """
        Choose the next word based on current state.

        Args:
            state (Tuple[str]): Current state

        Returns:
            str: Next word
        """
        possibilities = self.chain[state]
        if not possibilities:
            return None

        # Convert counts to probabilities
        total = sum(possibilities.values())
        choice = random.randint(1, total)

        # Select based on probability
        current = 0
        for word, count in possibilities.items():
            current += count
            if current >= choice:
                return word

        return None

    def generate(self, max_words: int = 100, start_text: Optional[str] = None) -> str:
        """
        Generate text using the trained Markov chain.

        Args:
            max_words (int): Maximum number of words to generate
            start_text (Optional[str]): Optional text to start the generation with

        Returns:
            str: Generated text

        Raises:
            ValueError: If the chain isn't trained or if start_text is longer than max_words
        """
        if not self.start_states:
            raise ValueError("Markov chain must be trained before generating")

        # Process starting text if provided
        if start_text:
            words = start_text.split()
            if len(words) >= max_words:
                return start_text

            # Verify we have enough words to form a state
            if len(words) < self.order:
                raise ValueError(f"Start text must contain at least {self.order} words")

            # Use the last 'order' words as our current state
            current_state = words[-self.order :]
            result = words
        else:
            # Start with a random valid start state
            current_state = list(random.choice(self.start_states))
            result = current_state.copy()

        # Generate subsequent words
        while len(result) < max_words:
            next_word = self._choose_next(tuple(current_state))
            if next_word is None:
                break

            result.append(next_word)
            current_state = current_state[1:] + [next_word]

        return " ".join(result)

    def save(self, filename: str) -> None:
        """
        Save the Markov chain to a file.

        Args:
            filename (str): Path to save file
        """
        import json

        data = {
            "order": self.order,
            "chain": {" ".join(k): dict(v) for k, v in self.chain.items()},
            "start_states": [" ".join(state) for state in self.start_states],
        }
        with open(filename, "w") as f:
            json.dump(data, f)

    @classmethod
    def load(cls, filename: str) -> "MarkovChain":
        """
        Load a Markov chain from a file.

        Args:
            filename (str): Path to load file

        Returns:
            MarkovChain: Loaded Markov chain
        """
        import json

        with open(filename, "r") as f:
            data = json.load(f)

        chain = cls(order=data["order"])
        chain.chain = defaultdict(lambda: defaultdict(int))
        for k, v in data["chain"].items():
            state = tuple(k.split())
            chain.chain[state] = defaultdict(int, v)

        chain.start_states = [tuple(state.split()) for state in data["start_states"]]
        return chain
