from typing import Dict, List, Optional
from ..models.product import Item

class Store:
    """
    Summary: Manages a collection of items with fixed capacity.  
    Description: Uses internal dictionaries to track items by code and position.  
    Parameters: cap (int): Store capacity (default 20).  
    Attributes: cap, _data (item code to Item), _map (position to code).
    """

    def __init__(self, cap: int=20):
        self.cap = cap
        self._data: Dict[str, Item] = {}
        self._map: Dict[int, str] = {}

    def put(self, obj: Item, pos: Optional[int]=None) -> bool:
        """
        Summary: Adds or updates an item, handling existing entries or position allocation.  
        Description: Manages item insertion by code or position, updating counts or allocating new slots.  
        Args: obj (Item) - Must have a unique code. pos (int, optional) - Valid position within 0 to cap-1; defaults to next available.  
        Returns: bool - True if successful, False on position conflicts or full capacity.  
        Raises: No exceptions.  
        Complements: `check()` for validity validation.
        """
        if obj.code in self._data:
            curr = self._data[obj.code]
            curr.count += obj.count
            return True
        if pos is not None:
            if pos < 0 or pos >= self.cap:
                return False
            if pos in self._map:
                return False
            self._map[pos] = obj.code
        else:
            for i in range(self.cap):
                if i not in self._map:
                    self._map[i] = obj.code
                    break
            else:
                return False
        self._data[obj.code] = obj
        return True

    def rm(self, code: str) -> bool:
        """
        Summary: Removes an item by code, updating internal mappings.  
        Description: Deletes the item from `_data` and all associated `_map` entries.  
        Args: code (str): Unique item code to remove; must exist in the store.  
        Returns: bool: `True` if successful, `False` if item not found.  
        Raises: No exceptions.  
        Complements: `put()` for adding/updating items.
        """
        if code not in self._data:
            return False
        for k, v in list(self._map.items()):
            if v == code:
                del self._map[k]
        del self._data[code]
        return True

    def get(self, code: str) -> Optional[Item]:
        """
        Summary: Retrieves item details by code using internal data mapping.  
        Description: Fetches the `Item` object associated with the provided code from the `_data` dictionary.  
        Args: code (str): Unique item code to search for in the store.  
        Returns: Optional[Item]: The `Item` object if found, otherwise `None`.  
        Raises: No exceptions raised.  
        Complements `find` and `mod` for item management lifecycle.
        """
        return self._data.get(code)

    def get_at(self, pos: int) -> Optional[Item]:
        """
        Summary: Retrieves item details by position using internal mapping.  
        Description: Uses `_map` to find the item code and `_data` to fetch the `Item` object.  
        Args: pos (int): Position must be within 0 to `cap-1`.  
        Returns: Optional[Item]: The `Item` object if found, otherwise `None`.  
        Raises: No exceptions raised.  
        Complements `find` and `get` for position-based access.
        """
        if pos not in self._map:
            return None
        code = self._map[pos]
        return self._data.get(code)

    def ls(self) -> List[Item]:
        """
        Summary: Lists valid items using validity check.  
        Description: Filters items via `check()` method.  
        Returns: List of valid `Item` objects.  
        Raises: No exceptions raised.  
        Complements: `check` for validity validation.
        """
        return [obj for obj in self._data.values() if obj.check()]

    def find(self, code: str) -> Optional[int]:
        """
        Summary: Finds item position by code using internal mapping.  
        Description: Uses the `_map` dictionary to locate the item's storage position.  
        Args: code (str): Unique item code to search for.  
        Returns: Optional[int]: Position if found, else None.  
        Raises: No exceptions raised.  
        Complements `check` and `mod` for item management lifecycle.
        """
        for k, v in self._map.items():
            if v == code:
                return k
        return None