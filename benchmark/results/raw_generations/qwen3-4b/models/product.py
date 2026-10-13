from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Item:
    """
    Represents an item with quantity, value, and optional expiration for resource tracking.

    Tracks item validity via count and expiration checks.

    Attributes: code (str), label (str), val (float), count (int), exp (Optional[datetime]), grp (str)
    """
    code: str
    label: str
    val: float
    count: int
    exp: Optional[datetime] = None
    grp: str = 'misc'

    def check(self) -> bool:
        """
        Confirms object validity via count and expiration checks.  
        Valid when count > 0 and timestamp not expired.  
        Returns bool: True if valid, False otherwise.
        """
        if self.count <= 0:
            return False
        if self.exp and datetime.now() > self.exp:
            return False
        return True

    def mod(self, n: int=1) -> bool:
        """
        Checks if count can be safely decremented by n and updates count if valid.

        Valid when n is positive and count >= n; returns True on success.

        Args:
            n (int): Positive integer to decrement count (must not exceed current count)

        Returns:
            bool: True if decrement succeeded, False otherwise
        """
        if self.count >= n:
            self.count -= n
            return True
        return False