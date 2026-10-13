from typing import Dict, List, Optional
from ..models.product import Item

class Store:
    """
    Summary: Manages items within a fixed capacity.

    Description: Provides methods for adding, removing, and retrieving items while maintaining a fixed capacity.

    Parameters: cap (int): The fixed capacity of the store (default: 20)

    Attributes: cap (int): The fixed capacity of the store.
    """

    def __init__(self, cap: int=20):
        self.cap = cap
        self._data: Dict[str, Item] = {}
        self._map: Dict[int, str] = {}

    def put(self, obj: Item, pos: Optional[int]=None) -> bool:
        """
        No docstring provided.
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
        Summary: Removes an item from the store by its unique code.

        Description: Deletes the item from the store's data and position mapping dictionaries.

        Args: 
            code (str): The unique code of the item to remove.

        Returns: 
            bool: True if the item was successfully removed, otherwise False.
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
        No docstring provided.
        """
        return self._data.get(code)

    def get_at(self, pos: int) -> Optional[Item]:
        """
        No docstring provided.
        """
        if pos not in self._map:
            return None
        code = self._map[pos]
        return self._data.get(code)

    def ls(self) -> List[Item]:
        """
        Summary: Lists all currently valid items in the store.

        Description: Returns a list of items that pass the `check` validity test.

        Returns: List[Item] of valid items (empty list if none)
        """
        return [obj for obj in self._data.values() if obj.check()]

    def find(self, code: str) -> Optional[int]:
        """
        Summary:
        Locates the storage position of an item using its unique code.

        Description:
        Searches the internal `_map` dictionary for the given code and returns the corresponding position if found, otherwise `None`.

        Args:
        code (str): Unique item code to search for in the store's mapping.

        Returns:
        Optional[int]: Position index in the store if found, else `None`.
        """
        for k, v in self._map.items():
            if v == code:
                return k
        return None