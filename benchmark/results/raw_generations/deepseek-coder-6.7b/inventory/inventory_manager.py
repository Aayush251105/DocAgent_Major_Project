from typing import Dict, List, Optional
from ..models.product import Item

class Store:
    '''
    <FOCAL_CODE_COMPONENT>
    class Store:
        def __init__(self, capacity: int):
            self._data = {}
            self._map = {}
            self.capacity = capacity

        def add(self, item: Item) -> bool:
            """
            Summary:
            Adds an item to the store.

            Description:
            The `add` method is used to add a new item to the store. The method checks if the store is full before adding the item. If the store is not full, the method adds the item to the `_data` dictionary using its code as the key and the item itself as the value. It also adds the item's position to the `_map` dictionary.

            WHY: This method is used when you need to add a new item to the store.
            WHEN: Use this method when you need to add a new item to the store.
            WHERE: This method is part of the `Store` class and is used in scenarios where a new item needs to be added to the store.
            HOW: The method first checks if the store is full. If the store is not full, it adds the item to the `_data` dictionary and the item's position to the `_map` dictionary. If the store is full, it returns `False`.

            Args:
            item (Item): The item to add to the store.

            Returns:
            bool: `True` if the item was successfully added, otherwise `False`.

            Raises:
            N/A

            Examples:
            ```python
            # Assuming  'store' is an instance of Store and 'item' is the item to add
            success = store.add(item)
            if success:
                print("Item added successfully.")
            else:
                print("Failed to add item. Store is full.")
            ```
            """
            if len(self._data) >= self.capacity:
                return False
            self._data[item.code] = item
            self._map[len(self._data) - 1] = item.code
            return True

        def rm(self, code: str) -> bool:
            """
            Summary:
            Removes an item from the store by its code.

            Description:
            The `rm` method is used to remove an item from the store using its unique code. The method searches for the item in the `_data` dictionary using the provided code and removes it if found. It also removes the item's position from the `_map` dictionary.

            WHY: This method is used when you need to remove an item from the store.
            WHEN: Use this method when you need to remove an item from the store.
            WHERE: This method is part of the `Store` class and is used in scenarios where an item needs to be removed from the store.
            HOW: The method first checks if the item exists in the `_data` dictionary using the provided code. If the item exists, it removes it from the `_data` dictionary and its position from the `_map` dictionary. If the item does not exist, it returns `False`.

            Args:
            code (str): The unique code of the item to remove from the store.

            Returns:
            bool: `True` if the item was successfully removed, otherwise `False`.

            Raises:
            N/A

            Examples:
            ```python
            # Assuming  'store' is an instance of Store and 'item_code' is the code of the item to remove
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
            Retrieves an item from the store by its code.

            Description:
            The `get` method is used to fetch an item from the store using its unique code. The method retrieves the corresponding `Item` object from the `_data` dictionary.

            WHY: This method is used when you need to access the details of an item based on its code.
            WHEN: Use this method when you need to retrieve an item's information using its code.
            WHERE: This method is part of the `Store` class and is used in scenarios where item details need to be accessed by code.
            HOW: The method first checks if the provided code exists in the `_data` dictionary. If it does, it retrieves the `Item` object associated with that code. If the code does not exist, it returns `None`.

            Args:
            code (str): The unique code of the item to retrieve.

            Returns:
            Optional[Item]: The `Item` object associated with the provided code if found, otherwise `None`.

            Raises:
            N/A

            Examples:
            ```python
            # Assuming  'store' is an instance of Store and 'item_code' is a valid item code
            item = store.get(item_code)
            if item is not None:
                print(f"Item details: {item}")
            else:
                print("Item not found.")
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
            pos (int): The position of the item to retrieve. This position must be within the valid range of the store's capacity (0 to `capacity - 1`).

            Returns:
            Optional[Item]: The `Item` object associated with the provided position if found, otherwise `None`.

            Raises:
            N/A

            Examples:
            ```python
            # Assuming  'store' is an instance of Store and 'position' is a valid position within the store's capacity
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
            List[Item]: A list of all valid items in the store.

            Raises:
            N/A

            Examples:
            ```python
            # Assuming  'store' is an instance of Store
            valid_items = store.ls()
            for item in valid_items:
                print(item)
            ```
            """
            return [item for item in self._data.values() if item.check()]

        def find(self, code: str) -> Optional[int]:
            """
            Summary:
            Finds the position of an item in the store by its code.

            Description:
            The `find` method is used to find the position of an item in the store using its unique code. The method looks up the item in the internal `_map` dictionary, which maps positions to item codes, and returns the position of the item.

            WHY: This method is used when you need to find the position of an item in the store.
            WHEN: Use this method when you need to find the position of an item in the store.
            WHERE: This method is part of the `Store` class and is used in scenarios where you need to find the position of an item in the store.
            HOW: The method first checks if the provided code exists in the `_map` dictionary. If it does, it retrieves the position associated with that code. If the code does not exist, it returns `None`.

            Args:
            code (str): The unique code of the item to find.

            Returns:
            Optional[int]: The position of the item if found, otherwise `None`.

            Raises:
            N/A

            Examples:
            ```python
            # Assuming  'store' is an instance of Store and 'item_code' is a valid item code
            position = store.find(item_code)
            if position is not None:
                print(f"Item is at position: {position}")
            else:
                print("Item not found.")
            ```
            """
            for pos, item_code in self._map.items():
                if item_code == code:
                    return pos
            return None
    </FOCAL_CODE_COMPONENT>
    '''

    def __init__(self, cap: int=20):
        self.cap = cap
        self._data: Dict[str, Item] = {}
        self._map: Dict[int, str] = {}

    def put(self, obj: Item, pos: Optional[int]=None) -> bool:
        '''
        def put(self, obj: Item, pos: Optional[int]=None)  -> bool:
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
            obj  (Item): The item to add to the store. This item must have a unique code.
            pos  (Optional[int]): The position at which to add the item. This position must be within the valid range of the store's capacity  (0 to `cap-1`). If not specified, the item will be added to the next available position.

            Returns:
            bool: `True` if the item was successfully added or updated, otherwise `False`.

            Raises:
            N/A

            Examples:
            ```python
            # Assuming  'store' is an instance of Store and 'item' is an instance of Item
            success  = store.put(item, pos=5)
            if success:
                print("Item added successfully.")
            else:
                print("Failed to add item.")
            ```
             """
             if obj.code in self._data:
                 curr  = self._data[obj.code]
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
        '''
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
        '''
        def rm(self, code: str)  -> bool:
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
            code  (str): The unique code of the item to remove from the store.

            Returns:
            bool: `True` if the item was successfully removed, otherwise `False`.

            Raises:
            N/A

            Examples:
            ```python
            # Assuming  'store' is an instance of Store and 'item_code' is the code of the item to remove
            success  = store.rm(item_code)
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

        ### Instruction:

                Available context:


                You are documenting a FUNCTION or METHOD. Focus on describing 
                the action it performs and its effects.

                Required sections:
                • Summary:
                    - One-line description focusing on WHAT the function does
                    - Avoid repeating the function name
                    - Emphasize the outcome or effect

                • Description:
                    - Use at most one short sentence when the summary alone is not enough.

                Conditional sections:
                • Args  (if present):
                    - Explain the significance of each parameter

                • Returns:
                    - Explain what the return value represents

                • Raises:
                    - List specific conditions triggering each exception
                    - Explain how to prevent or handle exceptions

                Now, generate a high-quality docstring for the following Code Component based on the Available context:
        '''
        if code not in self._data:
            return False
        for k, v in list(self._map.items()):
            if v == code:
                del self._map[k]
        del self._data[code]
        return True

    def get(self, code: str) -> Optional[Item]:
        """
        and
        """
        return self._data.get(code)

    def get_at(self, pos: int) -> Optional[Item]:
        '''
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
        '''
        if pos not in self._map:
            return None
        code = self._map[pos]
        return self._data.get(code)

    def ls(self) -> List[Item]:
        '''
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
            for item in valid valid_items:
                print(f"Valid item: {item}")
            ```
            """
            return [obj for obj in self._data.values() if obj.check()]
        '''
        return [obj for obj in self._data.values() if obj.check()]

    def find(self, code: str) -> Optional[int]:
        """
        Finds the position of an item in the store by its code.

        The `find` method searches for an item in the store using its unique code and returns the position where the item is stored. This method is useful when you need to locate an item's position without retrieving the item itself. The method iterates through the internal `_map` dictionary, which maps positions to item codes, to find the matching code.

        Args:
        code  (str): The unique code of the item to find. This code must match an existing item in the store.

        Returns:
        Optional[int]: The position of the item in the store if found, otherwise `None`.

        Raises:
        N/A

        Examples:
        ```python
        # Assuming 'store' is an instance of Store and 'item_code' is a valid item code
        position  = store.find(item_code)
        if position  is not None:
            print(f"Item found at position: {position}")
        else:
            print("Item not found in the store.")
        ```
        """
        for k, v in self._map.items():
            if v == code:
                return k
        return None