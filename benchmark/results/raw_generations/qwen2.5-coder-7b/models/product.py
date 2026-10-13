from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Item:
    """
    Summary:
    Represents an item with attributes for tracking and management in various contexts.

    Description:
    This class serves as a blueprint for creating items that can be tracked and managed within a system. Each item has attributes such as a unique code, a label, a value, a count, an optional expiration date, and a group classification. The primary motivation behind this class is to facilitate resource management, inventory tracking, or any scenario where items need to be monitored for validity and availability.

    Parameters:
    - code (str): A unique identifier for the item.
    - label (str): A descriptive name for the item.
    - val (float): The value associated with the item, representing its worth.
    - count (int): The quantity of the item available. Must be a non-negative integer.
    - exp (Optional[datetime]): An optional expiration date for the item. If set, the item will be considered invalid after this date.
    - grp (str): A classification group for the item, defaulting to 'misc'.

    Attributes:
    - code (str): The unique identifier for the item.
    - label (str): The name or description of the item.
    - val (float): The monetary or functional value of the item.
    - count (int): The current quantity of the item available, must be non-negative.
    - exp (Optional[datetime]): The expiration date of the item, if applicable.
    - grp (str): The group classification of the item, useful for categorization.
    """
    code: str
    label: str
    val: float
    count: int
    exp: Optional[datetime] = None
    grp: str = 'misc'

    def check(self) -> bool:
        """
        Summary:
        Checks if the item is still valid based on its count and expiration date.

        Description:
        This method evaluates the current state of the item by verifying if its count is greater than zero and if it has not expired. It is used to determine the usability of the item in scenarios requiring validation.

        Returns:
        bool: True if the item is valid, False otherwise.
        """
        if self.count <= 0:
            return False
        if self.exp and datetime.now() > self.exp:
            return False
        return True

    def mod(self, n: int=1) -> bool:
        """
        Summary:
        Decrements the item's count by a specified value if possible.

        Description:
        This method checks if the current count of the item is greater than or equal to the specified value `n`. If so, it decrements the count by `n` and returns `True`. If the count is less than `n`, it returns `False`, indicating that the operation could not be performed.

        Args:
        n (int, optional): The value to decrement from the count. Must be a positive integer that does not exceed the current count. Default is 1.

        Returns:
        bool: True if the decrement was successful, False otherwise.

        Raises:
        No exceptions are raised by this method. Ensure that `n` is a positive integer and does not exceed the current count to avoid logical errors.

        Examples:
        ```python
        item = Item(code='A123', label='Sample Item', val=10.0, count=5)
        result = item.mod(2)  # result will be True, item.count will be 3
        result = item.mod(4)  # result will be False, item.count remains 5
        result = item.mod(0)  # result will be False, as n should be greater than 0
        result = item.mod(-1) # result will be False, as n should be a positive integer
        ```
        """
        if self.count >= n:
            self.count -= n
            return True
        return False