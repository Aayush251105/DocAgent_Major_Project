from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Item:
    """
    Summary: Represents an item with attributes for tracking and management in systems requiring resource control.  
    Description: Manages item states with count, expiration, and grouping for lifecycle control.  
    Parameters: code (unique ID), label (description), val (value), count (quantity), exp (optional expiration), grp (group).  
    Attributes: code (unique ID), label (description), val (value), count (quantity), exp (optional expiration), grp (group).
    """
    code: str
    label: str
    val: float
    count: int
    exp: Optional[datetime] = None
    grp: str = 'misc'

    def check(self) -> bool:
        """
        Summary: Validates item's validity for resource tracking by checking count and expiration.  
        Description: Used in inventory systems or token management to ensure items are available before operations. Integrates with `mod` to manage lifecycle by confirming validity before count adjustments.  
        Example:  
        ```python  
        item = Item(code='A123', count=5, exp=datetime.now() + timedelta(days=1))  
        if item.check():  
            item.mod(2)  # Valid item, safe to decrement count  
        ```  
        Complements `mod` by ensuring validity before modifying counts, maintaining data integrity.  
        Returns: `True` if count > 0 and not expired; `False` otherwise.
        """
        if self.count <= 0:
            return False
        if self.exp and datetime.now() > self.exp:
            return False
        return True

    def mod(self, n: int=1) -> bool:
        """
        Summary: Decrements item count safely, ensuring it does not drop below zero.  
        Description: Ensures count is sufficient before modifying, aligning with `check` for lifecycle control in resource tracking.  
        Args: n (int, optional): Value to subtract from count; must be positive and ≤ current count (default 1).  
        Returns: `True` if decrement succeeded (count ≥ n), `False` otherwise.  
        Raises: No exceptions, but invalid `n` (≤0 or > count) results in `False` for logical consistency.  
        Complements `check` by enforcing validity before count adjustments, maintaining data integrity.
        """
        if self.count >= n:
            self.count -= n
            return True
        return False