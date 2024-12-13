from dataclasses import dataclass

@dataclass
class Cauldron:
    x: int
    y: int
    ingredients: int = 0  # Track the number of ingredients deposited

    def deposit_ingredient(self):
        """Update the cauldron's state when an ingredient is deposited."""
        self.ingredients += 1
        print(f"Cauldron now has {self.ingredients} ingredients.")

    def has_enough_ingredients(self, threshold: int) -> bool:
        """Check if the cauldron has enough ingredients."""
        return self.ingredients >= threshold