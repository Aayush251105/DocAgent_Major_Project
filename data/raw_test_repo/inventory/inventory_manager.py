from typing import Dict, List, Optional
from ..models.product import Item

class Store:
    """
    Summary:
    Represents a store for managing items with a fixed capacity.

    Description:
    The `Store` class is designed to manage a collection of items with a fixed capacity. It provides methods for adding, removing, and retrieving items, as well as checking their validity. The store uses two internal dictionaries: `_data` to map item codes to `Item` objects and `_map` to track item positions. This class is essential for inventory management in systems where items need to be stored, accessed, and managed efficiently.

    WHY: This class is used when you need to manage a collection of items with a fixed capacity, providing functionalities to add, remove, and retrieve items.
    WHEN: Use this class when you need to implement inventory management features in your application.
    WHERE: This class is part of the inventory management module and is used in scenarios where items need to be stored and accessed.
    HOW: The class uses two dictionaries to manage items: `_data` for item code to `Item` object mapping and `_map` for position to item code mapping. Methods like `put`, `get`, `get_at`, `ls`, and `find` provide the necessary functionalities to manage the items.

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
        Adds an item to the store.

        Description:
        The `put` method is used to add an item to the store. This method handles two main scenarios: updating the count of an existing item and adding a new item with a specified or default position. The method first checks if the item already exists in the store by its code. If it does, it increments the count of the existing item. If the item does not exist, it attempts to add the item to the store at a specified position or the next available position.

        WHY: This method is used when you need to add a new item to the store or update the count of an existing item.
        WHEN: Use this method when you need to add items to the store or update their counts.
        WHERE: This method is part of the `Store` class and is used in scenarios where items need to be added or updated.
        HOW: The method first checks if the item's code exists in the `_data` dictionary. If it does, it increments the count of the existing item. If not, it checks if a position is specified and valid. If a position is specified, it checks if the position is already occupied. If the position is valid and not occupied, it adds the item to the store at that position. If no position is specified, it finds the next available position and adds the item there. If no valid position is found, it returns `False`.

        Args:
        obj (Item): The item to add to the store. This item must have a unique code.
        pos (Optional[int]): The position at which to add the item. This position must be within the valid range of the store's capacity (0 to `cap-1`). If not specified, the item will be added to the next available position.

        Returns:
        bool: `True` if the item was successfully added or updated, otherwise `False`.

        Raises:
        N/A

        Examples:
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
        Summary:
        Removes an item from the store.

        Description:
        The `rm` method is used to remove an item from the store by its unique code. This method is essential for managing the store's inventory by removing items that are no longer needed or are outdated. The method first checks if the item exists in the store. If it does, it removes the item from both the internal `_data` dictionary and the `_map` dictionary, which tracks item positions.

        WHY: This method is used when you need to remove an item from the store.
        WHEN: Use this method when you need to delete items from the store.
        WHERE: This method is part of the `Store` class and is used in scenarios where items need to be removed.
        HOW: The method first checks if the item's code exists in the `_data` dictionary. If it does, it iterates through the `_map` dictionary to remove any entries that reference the item's code. After removing the item from the `_map`, it deletes the item from the `_data` dictionary. If the item does not exist, it returns `False`.

        Args:
        code (str): The unique code of the item to remove from the store.

        Returns:
        bool: `True` if the item was successfully removed, otherwise `False`.

        Raises:
        N/A

        Examples:
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
        Summary:
        Retrieves an item from the store by its unique code.

        Description:
        The `get` method is used to fetch an item from the store using its unique code. This method is essential for accessing item details without needing to know its position in the store. The method looks up the item in the internal `_data` dictionary, which maps item codes to `Item` objects.

        WHY: This method is used when you need to access the details of an item based on its code.
        WHEN: Use this method when you need to retrieve an item's information.
        WHERE: This method is part of the `Store` class and is used in scenarios where item details need to be accessed.
        HOW: The method uses the `get` method of the `_data` dictionary to retrieve the `Item` object associated with the provided code. If the code does not exist in the dictionary, it returns `None`.

        Args:
        code (str): The unique code of the item to retrieve. This code must match an existing item in the store.

        Returns:
        Optional[Item]: The `Item` object associated with the provided code if found, otherwise `None`.

        Raises:
        N/A

        Examples:
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
        Summary:
        Retrieves an item from the store by its position.

        Description:
        The `get_at` method is used to fetch an item from the store using its position. This method is essential for accessing item details when the position is known, without needing to know the item's code. The method looks up the item in the internal `_map` dictionary, which maps positions to item codes, and then retrieves the corresponding `Item` object from the `_data` dictionary.

        WHY: This method is used when you need to access the details of an item based on its position.
        WHEN: Use this method when you need to retrieve an item's information using its position.
        WHERE: This method is part of the `Store` class and is used in scenarios where item details need to be accessed by position.
        HOW: The method first checks if the provided position exists in the `_map` dictionary. If it does, it retrieves the item code associated with that position and then uses this code to fetch the `Item` object from the `_data` dictionary. If the position does not exist, it returns `None`.

        Args:
        pos (int): The position of the item to retrieve. This position must be within the valid range of the store's capacity (0 to `cap-1`).

        Returns:
        Optional[Item]: The `Item` object associated with the provided position if found, otherwise `None`.

        Raises:
        N/A

        Examples:
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
        Summary:
        Lists all valid items in the store.

        Description:
        The `ls` method is used to retrieve a list of all items that are currently valid in the store. This method is essential for generating reports or performing inventory checks. The method iterates through the internal `_data` dictionary, which contains all items, and applies the `check` method to each item to determine its validity. Only items that return `True` from the `check` method are included in the resulting list.

        WHY: This method is used when you need to generate a list of all valid items in the store.
        WHEN: Use this method when you need to perform inventory checks or generate reports based on the current state of the store.
        WHERE: This method is part of the `Store` class and is used in scenarios where a list of valid items is required.
        HOW: The method iterates over the values in the `_data` dictionary, applying the `check` method to each item. If the `check` method returns `True`, the item is included in the resulting list. If no items are valid, the method returns an empty list.

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
        The `find` method searches for an item in the store using its unique code and returns the position where the item is stored. This method is useful when you need to locate an item's position without retrieving the item itself. The method iterates through the internal `_map` dictionary, which maps positions to item codes, to find the matching code.

        WHEN: Use this method when you need to determine the storage position of an item based on its code.
        WHERE: This method is part of the `Store` class and is used in scenarios where item positions need to be tracked or accessed.
        HOW: The method iterates over the `_map` dictionary, checking each value (item code) against the provided code. If a match is found, it returns the corresponding key (position). If no match is found, it returns `None`.

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