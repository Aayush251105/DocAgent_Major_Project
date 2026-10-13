from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Item:
    """
    **Item Class Docstring:**

    **Summary:**
    Represents an item with associated attributes for tracking and management in various contexts.

    **Description:**
    This class serves as a blueprint for creating items that can be tracked and managed within a system.

    **Parameters:**
    - code (str): A unique identifier for the item.
    - label (str): A descriptive name for the item.
    - val (float): The value associated with the item, representing its worth.
    - count (int): The quantity of the item available.
    - exp (Optional[datetime]): An optional expiration date for the item.
    - grp (str): A classification group for the item.

    **Attributes:**
    - code (str): The unique identifier for the item.
    - label (str): The name or description of the item.
    - val (float): The monetary or functional value of the item.
    - count (int): The current quantity of the item available.
    - exp (Optional[datetime]): The expiration date of the item, if applicable.
    - grp (str): The group classification of the item.

    **Methods:**
    - check(): Checks if the item is still valid based on count and expiration.
    - mod(n): Decrements the count of the item by n.
    """
    code: str
    label: str
    val: float
    count: int
    exp: Optional[datetime] = None
    grp: str = 'misc'

    def check(self) -> bool:
        """
        Checks if an object is still valid based on count and expiration. Returns True if the object is valid (count > 0 and not expired), False otherwise.
        """
        if self.count <= 0:
            return False
        if self.exp and datetime.now() > self.exp:
            return False
        return True

    def mod(self, n: int=1) -> bool:
        """
        Checks if the current count can be decremented by a specified value. Returns True if the decrement was successful, False otherwise.
        """
        if self.count >= n:
            self.count -= n
            return True
        return False