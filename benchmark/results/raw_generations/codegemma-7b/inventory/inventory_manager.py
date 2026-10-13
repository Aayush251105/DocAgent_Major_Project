from typing import Dict, List, Optional
from ..models.product import Item

class Store:
    """
    **Store Class Docstring:**

    **Summary:**
    Represents a store for managing items with a fixed capacity.

    **Description:**
    The `Store` class is designed to manage a collection of items with a fixed capacity. It provides methods for adding, removing, and retrieving items, as well as checking their validity.

    **Attributes:**
    - `cap` (int): The fixed capacity of the store.
    - `_data` (Dict[str, Item]): A dictionary mapping item codes to `Item` objects.
    - `_map` (Dict[int, str]): A dictionary mapping positions to item codes.

    **Methods:**
    - `put(code: str, item: Item) -> bool`: Adds an item to the store.
    - `get(code: str) -> Optional[Item]`: Retrieves an item by its code.
    - `get_at(pos: int) -> Optional[Item]`: Retrieves an item by its position.
    - `ls() -> List[Item]`: Lists all valid items in the store.
    - `find(code: str) -> Optional[int]`: Finds the position of an item by its code.
    """

    def __init__(self, cap: int=20):
        self.cap = cap
        self._data: Dict[str, Item] = {}
        self._map: Dict[int, str] = {}

    def put(self, obj: Item, pos: Optional[int]=None) -> bool:
        """
        **put() Method Docstring:**

        **Summary:**
        Adds an item to the store.

        **Args:**
        - obj (Item): The item to add to the store.
        - pos (Optional[int]): The position at which to add the item.

        **Returns:**
        - bool: `True` if the item was successfully added or updated, otherwise `False`.

        **Examples:**
        ```python
        # Assuming 'store' is an instance of Store and 'item' is an instance of Item
        success = store.put(item, pos=5)
        if success:
            print("Item added successfully.")
        else:
            print("Failed to add item.")
        ```
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
        **rm() Method Docstring:**

        **Summary:**
        Removes an item from the store.

        **Args:**
        - code (str): The unique code of the item to remove from the store.

        **Returns:**
        - bool: `True` if the item was successfully removed, otherwise `False`.

        **Examples:**
        ```python
        # Assuming 'store' is an instance of Store and 'item_code' is the code of the item to remove
        success = store.rm(item_code)
        if success:
            print("Item removed successfully.")
        else:
            print("Failed to remove item.")
        ```
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
        **get() Method Docstring:**

        **Summary:**
        Retrieves an item from the store by its unique code.

        **Description:**
        The `get` method is used to fetch an item from the store using its unique code.

        **Args:**
        - code (str): The unique code of the item to retrieve.

        **Returns:**
        - Optional[Item]: The `Item` object associated with the provided code if found, otherwise `None`.

        **Raises:**
        - N/A

        **Examples:**
        ```python
        # Assuming 'store' is an instance of Store and 'item_code' is a valid item code
        item = store.get(item_code)
        if item is not None:
            print(f"Item details: {item}")
        else:
            print("Item not found in the store.")
        ```
        """
        return self._data.get(code)

    def get_at(self, pos: int) -> Optional[Item]:
        """
        **get_at() Method Docstring:**

        **Summary:**
        Retrieves an item from the store by its position.

        **Description:**
        The `get_at` method is used to fetch an item from the store using its position.

        **Args:**
        - pos (int): The position of the item to retrieve.

        **Returns:**
        - Optional[Item]: The `Item` object associated with the provided position if found, otherwise `None`.

        **Raises:**
        - N/A

        **Examples:**
        ```python
        # Assuming 'store' is an instance of Store and 'position' is a valid position within the store's capacity
        item = store.get_at(position)
        if item is not None:
            print(f"Item details: {item}")
        else:
            print("Item not found at the specified position.")
        ```
        """
        if pos not in self._map:
            return None
        code = self._map[pos]
        return self._data.get(code)

    def ls(self) -> List[Item]:
        """
        **ls() Method Docstring:**

        **Summary:**
        Lists all valid items in the store.

        **Description:**
        The `ls` method is used to retrieve a list of all items that are currently valid in the store.

        **Returns:**
        - List[Item]: A list of `Item` objects that are currently valid in the store.

        **Examples:**
        ```python
        # Assuming 'store' is an instance of Store
        valid_items = store.ls()
        for item in valid_items:
            print(f"Valid item: {item}")
        ```
        """
        return [obj for obj in self._data.values() if obj.check()]

    def find(self, code: str) -> Optional[int]:
        """
        **find() Method Docstring:**

        **Summary:**
        Finds the position of an item in the store by its code.

        **Description:**
        The `find` method searches for an item in the store using its unique code and returns the position where the item is stored.

        **Args:**
        - code (str): The unique code of the item to find.

        **Returns:**
        - Optional[int]: The position of the item in the store if found, otherwise `None`.

        **Raises:**
        - N/A

        **Examples:**
        ```python
        # Assuming 'store' is an instance of Store and 'item_code' is a valid item code
        position = store.find(item_code)
        if position is not None:
            print(f"Item found at position: {position}")
        else:
            print("Item not found in the store.")
        ```
        """
        for k, v in self._map.items():
            if v == code:
                return k
        return None