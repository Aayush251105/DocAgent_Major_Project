from typing import Dict, List, Optional
from ..models.product import Item

class Store:
    '''
    The generated docstring for the `Store` class is:

            ```
            def __init__(self, capacity: int):
                """
                Initializes a new instance of the `Store` class.

                This constructor creates a new instance of the `Store` class and initializes its internal `_data` and `_map` dictionaries. The `capacity` parameter specifies the maximum number of items that can be stored in the store.

                WHY: This constructor is used when you need to create a new instance of the `Store` class.
                WHEN: Use this constructor when you need to create a new store with a specific capacity.
                WHERE: This constructor is part of the `Store` class and is used in scenarios where a new store needs to be created.
                HOW: The constructor initializes the `_data` and `_map` dictionaries with empty lists and sets the `capacity` attribute to the provided value.

                Args:
                    capacity (int): The maximum number of items that can be stored in the store.

                Returns:
                    N/A

                Raises:
                    N/A

                Examples:
                ```python
                # Creating a new store with a capacity of 10
                store = Store(10)
                ```
                """
                self._data = {}
                self._map = {}
                self.capacity = capacity

            def add(self, item: Item) -> bool:
                """
                Adds an item to the store.

                This method adds an item to the store if there is enough capacity. The method first checks if the store has enough capacity to accommodate the new item. If there is enough capacity, the method adds the item to the internal `_data` dictionary, which maps item codes to `Item` objects. The method also updates the internal `_map` dictionary, which maps positions to item codes, to reflect the new item's position.

                WHY: This method is used when you need to add an item to the store.
                WHEN: Use this method when you need to add an item to the store.
                WHERE: This method is part of the `Store` class and is used in scenarios where items need to be added to the store.
                HOW: The method first checks if the store has enough capacity to accommodate the new item. If there is enough capacity, the method adds the item to the `_data` dictionary and updates the `_map` dictionary. If there is not enough capacity, the method returns `False`.

                Args:
                    item (Item): The item to add to the store.

                Returns:
                    bool: `True` if the item was added successfully, otherwise `False`.

                Raises:
                    N/A

                Examples:
                ```python
                # Assuming 'store' is an instance of Store and 'item' is an instance of Item
                success = store.add(item)
                if success:
                    print("Item added successfully.")
                else:
                    print("Failed to add item.")
                ```
                """
                if len(self._data) >= self.capacity:
                    return False
                self._data[item.code] = item
                self._map[len(self._data)] = item.code
                return True

            def rm(self, code: str) -> bool:
                """
                Removes an item from the store.

                This method removes an item from the store by its unique code. The method first checks if the item exists in the store. If it does, the method removes the item from the internal `_data` dictionary, which maps item codes to `Item` objects. The method also updates the internal `_map` dictionary, which maps positions to item codes, to reflect the removed item's position.

                WHY: This method is used when you need to remove an item from the store.
                WHEN: Use this method when you need to remove an item from the store.
                WHERE: This method is part of the `Store` class and is used in scenarios where items need to be removed from the store.
                HOW: The method first checks if the item exists in the store. If it does, the method removes the item from the `_data` dictionary and updates the `_map` dictionary. If the item does not exist, the method returns `False`.

                Args:
                    code (str): The unique code of the item to remove. This code must match an existing item in the store.

                Returns:
                    bool: `True` if the item was removed successfully, otherwise `False`.

                Raises:
                    N/A

                Examples:
                ```python
                # Assuming 'store' is an instance of Store and 'item_code' is a valid item code
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
                Retrieves an item from the store by its unique code.

                This method is used to fetch an item from the store using its unique code. This method is essential for accessing item details without needing to know its position in the store. The method looks up the item in the internal `_data` dictionary, which maps item codes to `Item` objects.

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
                Retrieves an item from the store by its position.

                This method is used to fetch an item from the store using its position. This method is essential for accessing item details when the position is known, without needing to know the item's code. The method looks up the item in the internal `_map` dictionary, which maps positions to item codes, and then retrieves the corresponding `Item` object from the `_data` dictionary.

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
                Lists all valid items in the store.

                This method returns a list of all valid items in the store. The method first checks if there are any items in the store. If there are, the method returns a list of all valid items in the store. If there are no items in the store, the method returns an empty list.

                WHY: This method is used when you need to retrieve a list of all valid items in the store.
                WHEN: Use this method when you need to retrieve a list of all valid items in the store.
                WHERE: This method is part of the `Store` class and is used in scenarios where a list of all valid items in the store needs to be retrieved.
                HOW: The method first checks if there are any items in the store. If there are, the method returns a list of all valid items in the store. If there are no items in the store, the method returns an empty list.

                Args:
                    N/A

                Returns:
                    List[Item]: A list of all valid items in the store.

                Raises:
                    N/A

                Examples:
                ```python
                # Assuming 'store' is an instance of Store
                items = store.ls()
                print(items)
                ```
                """
                if len(self._data) == 0:
                    return []
                return [item for item in self._data.values()]
            ```

            The generated docstring for the `Item` class is:

            ```
            def __init__(self, code: str, name: str, price: float):
                """
                Initializes a new instance of the `Item` class.

                This constructor creates a new instance of the `Item` class and initializes its internal attributes. The `code`, `name`, and `price` parameters are used to set the initial values of the `Item` object.

                WHY: This constructor is used when you need to create a new instance of the `Item` class.
                WHEN: Use this constructor when you need to create a new item with specific attributes.
                WHERE: This constructor is part of the `Item` class and is used in scenarios where a new item needs to be created.
                HOW: The constructor initializes the `code`, `name`, and `price` attributes with the provided values.

                Args:
                    code (str): The unique code of the item.
                    name (str): The name of the item.
                    price (float): The price of the item.

                Returns:
                    N/A

                Raises:
                    N/A

                Examples:
                ```python
                # Creating a new item with a code, name, and price
                item = Item("ABC123", "Apple", 1.99)
                ```
                """
                self.code = code
                self.name = name
                self.price = price

            def __str__(self) -> str:
                """
                Returns a string representation of the `Item` object.

                This method returns a string representation of the `Item` object. The method first checks if the `Item` object has a valid `code` attribute. If it does, the method returns a string with the `code`, `name`, and `price` attributes. If the `Item` object does not have a valid `code` attribute, the method returns an empty string.

                WHY: This method is used when you need to convert an `Item` object to a string.
                WHEN: Use this method when you need to convert an `Item` object to a string.
                WHERE: This method is part of the `Item` class and is used in scenarios where an `Item` object needs to be converted to a string.
                HOW: The method first checks if the `Item` object has a valid `code` attribute. If it does, the method returns a string with the `code`, `name`, and `price` attributes. If the `Item` object does not have a valid `code` attribute, the method returns an empty string.

                Args:
                    N/A

                Returns:
                    str: A string representation of the `Item` object.

                Raises:
                    N/A

                Examples:
                ```python
                # Assuming 'item' is an instance of Item
                print(str(item))
                ```
                """
                if self.code is not None:
                    return f"{self.code} - {self.name} - ${self.price}"
                return ""
            ```

            The generated docstring for the `main` function is:

            ```
            def main():
                """
                The main function of the program.

                This function is the entry point of the program. It creates a new instance of the `Store` class and adds a few items to the store. The function then retrieves the items from the store and prints their details.

                WHY: This function is used as the entry point of the program.
                WHEN: Use this function as the entry point of the program.
                WHERE: This function is part of the `main` module and is used in scenarios where the program needs to be executed.
                HOW: The function creates a new instance of the `Store` class and adds a few items to the store. The function then retrieves the items from the store and prints their details.

                Args:
                    N/A

                Returns:
                    N/A

                Raises:
                    N/A

                Examples:
                ```python
                # Assuming 'store' is an instance of Store
                main()
                ```
                """
                store = Store(5)
                item1 = Item("ABC123", "Apple", 1.99)
                item2 = Item("DEF456", "Orange", 2.99)
                item3 = Item("GHI789", "Banana", 0.99)
                store.add(item1)
                store.add(item2)
                store.add(item3)
                items = store.ls()
                for item in items:
                    print(item)
            ```

            The generated docstring for the `Item` class is:

            ```
            class Item:
                """
                Represents an item in the store.

                This class represents an item in the store. It has a unique code, name, and price. The class also has a `__str__` method that allows the item to be converted to a string.

                WHY: This class is used to represent an item in the store.
                WHEN: Use this class when you need to represent an item in the store.
                WHERE: This class is part of the `main` module and is used in scenarios where an item needs to be represented.
                HOW: The class has a `__init__` method that initializes the internal attributes with the provided values. The class also has a `__str__` method that allows the item to be converted to a string.

                Args:
                    N/A

                Returns:
                    N/A

                Raises:
                    N/A

                Examples:
                ```python
                # Assuming 'item' is an instance of Item
                print(item)
                ```
                """
                def __init__(self, code: str, name: str, price: float):
                    """
                    Initializes a new instance of the `Item` class.

                    This constructor creates a new instance of the `Item` class and initializes its internal attributes. The `code`, `name`, and `price` parameters are used to set the initial values of the `Item` object.

                    WHY: This constructor is used when you need to create a new instance of the `Item` class.
                    WHEN: Use this constructor when you need to create a new item with specific attributes.
                    WHERE: This constructor is part of the `Item` class and is used in scenarios where a new item needs to be created.
                    HOW: The constructor initializes the `code`, `name`, and `price` attributes with the provided values.

                    Args:
                        code (str): The unique code of the item.
                        name (str): The name of the item.
                        price (float): The price of the item.

                    Returns:
                        N/A

                    Raises:
                        N/A

                    Examples:
                    ```python
                    # Creating a new item with a code, name, and price
                    item = Item("ABC123", "Apple", 1.99)
                    ```
                    """
                    self.code = code
                    self.name = name
                    self.price = price

                def __str__(self) -> str:
                    """
                    Returns a string representation of the `Item` object.

                    This method returns a string representation of the `Item` object. The method first checks if the `Item` object has a valid `code`
    '''

    def __init__(self, cap: int=20):
        self.cap = cap
        self._data: Dict[str, Item] = {}
        self._map: Dict[int, str] = {}

    def put(self, obj: Item, pos: Optional[int]=None) -> bool:
        '''
        def put(self, obj: Item, pos: Optional[int]=None) -> bool:
            """
            Adds an item to the store.

            This method is used to add an item to the store. This method handles two main scenarios: updating the count of an existing item and adding a new item with a specified or default position. The method first checks if the item already exists in the store by its code. If it does, it increments the count of the existing item. If the item does not exist, it attempts to add the item to the store at a specified position or the next available position.

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
        def rm(self, code: str) -> bool:
            """
            Removes an item from the store.

            This method is used to remove an item from the store by its unique code. This method is essential for managing the store's inventory by removing items that are no longer needed or are outdated. The method first checks if the item exists in the store. If it does, it removes the item from both the internal `_data` dictionary and the `_map` dictionary, which tracks item positions.

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
        '''
        if code not in self._data:
            return False
        for k, v in list(self._map.items()):
            if v == code:
                del self._map[k]
        del self._data[code]
        return True

    def get(self, code: str) -> Optional[Item]:
        '''
        def get(self, code: str) -> Optional[Item]:
            """
            Retrieves an item from the store by its unique code.

            This method is used to fetch an item from the store using its unique code. This method is essential for accessing item details without needing to know its position in the store. The method looks up the item in the internal `_data` dictionary, which maps item codes to `Item` objects.

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
        '''
        return self._data.get(code)

    def get_at(self, pos: int) -> Optional[Item]:
        '''
        def get_at(self, pos: int) -> Optional[Item]:
            """
            Retrieves an item from the store by its position.

            This method is used to fetch an item from the store using its position. This method is essential for accessing item details when the position is known, without needing to know the item's code. The method looks up the item in the internal `_map` dictionary, which maps positions to item codes, and then retrieves the corresponding `Item` object from the `_data` dictionary.

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
            Lists all valid items in the store.

            This method is used to retrieve a list of all items that are currently valid in the store. This method is essential for generating reports or performing inventory checks. The method iterates through the internal `_data` dictionary, which contains all items, and applies the `check` method to each item to determine its validity. Only items that return `True` from the `check` method are included in the resulting list.

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
        '''
        return [obj for obj in self._data.values() if obj.check()]

    def find(self, code: str) -> Optional[int]:
        '''
        def find(self, code: str) -> Optional[int]:
            """
            Finds the position of an item in the store by its code.

            This method searches for an item in the store using its unique code and returns the position where the item is stored. This method is useful when you need to locate an item's position without retrieving the item itself. The method iterates through the internal `_map` dictionary, which maps positions to item codes, to find the matching code.

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
        '''
        for k, v in self._map.items():
            if v == code:
                return k
        return None