from typing import Dict, List, Optional
from ..models.product import Item

class Store:
    """
    Summary:
    Represents a store for managing items with a fixed capacity.

    Description:
    The `Store` class is designed to manage a collection of items with a fixed capacity. It provides methods for adding, removing, and retrieving items, as well as checking their validity.

    Attributes:
    - `cap` (int): The fixed capacity of the store.
    - `_data` (Dict[str, Item]): A dictionary mapping item codes to `Item` objects.
    - `_map` (Dict[int, str]): A dictionary mapping positions to item codes.

    Methods:
    - `put(code: str, item: Item) -> bool`: Adds an item to the store if there is space available.
    - `get(code: str) -> Optional[Item]`: Retrieves an item by its code.
    - `get_at(pos: int) -> Optional[Item]`: Retrieves an item by its position.
    - `ls() -> List[Item]`: Lists all valid items in the store.
    - `find(code: str) -> Optional[int]`: Finds the position of an item by its code.

    Examples:
    ```python
    # Create a store with a capacity of 10
    store = Store(10)

    # Add an item to the store
    item = Item(code="001", name="Widget", quantity=10)
    store.put("001", item)

    # Retrieve an item by its code
    retrieved_item = store.get("001")
    if retrieved_item:
        print(f"Retrieved item: {retrieved_item}")

    # List all valid items in the store
    valid_items = store.ls()
    for item in valid_items:
        print(f"Valid item: {item}")

    # Find the position of an item by its code
    position = store.find("001")
    if position is not None:
        print(f"Item found at position: {position}")
    ```
    """

    def __init__(self, cap: int=20):
        self.cap = cap
        self._data: Dict[str, Item] = {}
        self._map: Dict[int, str] = {}

    def put(self, obj: Item, pos: Optional[int]=None) -> bool:
        """
        Summary:
        Adds an item to the store, updating its count if it already exists or adding it at a specified or default position.

        Description:
        The `put` method handles two main scenarios: updating the count of an existing item and adding a new item with a specified or default position.

        Args:
        obj (Item): The item to add to the store, which must have a unique code.
        pos (Optional[int]): The position at which to add the item, within the valid range of the store's capacity (0 to `cap-1`). If not specified, the item will be added to the next available position.

        Returns:
        bool: `True` if the item was successfully added or updated, otherwise `False`.

        Raises:
        N/A
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
        Summary:
        Removes an item from the store.

        Description:
        The `rm` method removes an item from the store by its unique code.

        Args:
        code (str): The unique code of the item to remove from the store.

        Returns:
        bool: `True` if the item was successfully removed, otherwise `False`.

        Raises:
        N/A
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
        Summary:
        Retrieves an item from the store by its unique code.

        Description:
        This method fetches an item from the store using its unique code, allowing for item details to be accessed without needing to know its position in the store.

        Args:
        code (str): The unique code of the item to retrieve. This code must match an existing item in the store.

        Returns:
        Optional[Item]: The `Item` object associated with the provided code if found, otherwise `None`.

        Raises:
        N/A
        """
        return self._data.get(code)

    def get_at(self, pos: int) -> Optional[Item]:
        """
        Summary:
        Retrieves an item from the store by its position.

        Description:
        The `get_at` method fetches an item from the store using its position, allowing for item details to be accessed without needing to know the item's code.

        Args:
        pos (int): The position of the item to retrieve. This position must be within the valid range of the store's capacity (0 to `cap-1`).

        Returns:
        Optional[Item]: The `Item` object associated with the provided position if found, otherwise `None`.

        Raises:
        N/A
        """
        if pos not in self._map:
            return None
        code = self._map[pos]
        return self._data.get(code)

    def ls(self) -> List[Item]:
        """
        Summary:
        Lists all valid items in the store.

        Description:
        The `ls` method iterates through the internal `_data` dictionary, applying the `check` method to each item to determine its validity.

        Args:
        N/A

        Returns:
        List[Item]: A list of `Item` objects that are currently valid in the store. If no items are valid, an empty list is returned.

        Raises:
        N/A

        Examples:
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
        Summary:
        Finds the position of an item in the store by its code.

        Description:
        The `find` method searches for an item in the store using its unique code and returns the position where the item is stored. This method is useful when you need to locate an item's position without retrieving the item itself.

        Args:
        code (str): The unique code of the item to find. This code must match an existing item in the store.

        Returns:
        Optional[int]: The position of the item in the store if found, otherwise `None`.

        Raises:
        N/A

        Examples:
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