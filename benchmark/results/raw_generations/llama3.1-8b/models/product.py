from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Item:
    '''
    class Store:
        """
        Summary:
        Represents a store with associated attributes for tracking and management in various contexts.

        Description:
        This class serves as a blueprint for creating stores that can be tracked and managed within a system. Each store has attributes such as a capacity, a map of positions to item codes, and a dictionary of items. The primary motivation behind this class is to facilitate resource management, inventory tracking, or any scenario where items need to be monitored for validity and availability.

        Use this class when you need to represent stores that may have a limited capacity or quantity of items, such as in inventory systems, gaming resources, or token management. It provides methods to retrieve items by position, list all valid items, and manage the store's capacity.

        The class fits into larger systems by allowing for easy integration with resource management workflows, enabling developers to track store states and manage their lifecycle effectively.

        Example:
        ```python
        # Create a store with a capacity of 10
        store = Store(cap=10)

        # Add items to the store
        store.add(Item(code='A123', label='Sample Item', val=10.0, count=5, exp=datetime.now() + timedelta(days=1)))

        # Retrieve an item by position
        item = store.get_at(0)

        # List all valid items in the store
        valid_items = store.ls()
        ```

        Parameters:
        - cap (int): The maximum number of items the store can hold.

        Attributes:
        - cap (int): The maximum number of items the store can hold.
        - _map (dict): A dictionary mapping positions to item codes.
        - _data (dict): A dictionary of items, keyed by their codes.

        Methods:
        - add: Adds an item to the store.
        - get_at: Retrieves an item from the store by its position.
        - ls: Lists all valid items in the store.
        """
        cap: int
        _map: dict
        _data: dict

        def __init__(self, cap: int):
            """
            Summary:
            Initializes a new store with a specified capacity.

            Description:
            This method sets the capacity of the store and initializes the internal dictionaries for mapping positions to item codes and storing items.

            Args:
            - cap (int): The maximum number of items the store can hold.

            Returns:
            None

            Raises:
            - No exceptions are raised by this method.
            """
            self.cap = cap
            self._map = {}
            self._data = {}

        def add(self, item: Item):
            """
            Summary:
            Adds an item to the store.

            Description:
            This method adds an item to the store by updating the internal dictionaries. It maps the item's position to its code and stores the item in the dictionary.

            Args:
            - item (Item): The item to add to the store.

            Returns:
            None

            Raises:
            - No exceptions are raised by this method.
            """
            self._map[len(self._map)] = item.code
            self._data[item.code] = item

        def get_at(self, pos: int) -> Optional[Item]:
            """
            Summary:
            Retrieves an item from the store by its position.

            Description:
            This method is used to fetch an item from the store using its position. It looks up the item in the internal `_map` dictionary, which maps positions to item codes, and then retrieves the corresponding `Item` object from the `_data` dictionary.

            Args:
            - pos (int): The position of the item to retrieve.

            Returns:
            Optional[Item]: The `Item` object associated with the provided position if found, otherwise `None`.

            Raises:
            - No exceptions are raised by this method.
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
            This method is used to retrieve a list of all items that are currently valid in the store. It iterates through the internal `_data` dictionary, which contains all items, and applies the `check` method to each item to determine its validity. Only items that return `True` from the `check` method are included in the resulting list.

            Args:
            - None

            Returns:
            List[Item]: A list of `Item` objects that are currently valid in the store. If no items are valid, an empty list is returned.

            Raises:
            - No exceptions are raised by this method.
            """
            return [obj for obj in self._data.values() if obj.check()]
    '''
    code: str
    label: str
    val: float
    count: int
    exp: Optional[datetime] = None
    grp: str = 'misc'

    def check(self) -> bool:
        """
        Summary:
        Validates the current object's state based on count and expiration.

        Description:
        This method checks two key conditions to determine if the object is still valid: its count is greater than zero and it has not exceeded its expiration timestamp.

        Args:
        - None

        Returns:
        bool: True if the object is valid (count > 0 and not expired), False otherwise.

        Raises:
        - No exceptions are raised by this method.
        """
        if self.count <= 0:
            return False
        if self.exp and datetime.now() > self.exp:
            return False
        return True

    def mod(self, n: int=1) -> bool:
        """
        Summary:
        Determines if the current count can be safely decremented by a specified value.

        Description:
        This method checks if the `count` attribute is greater than or equal to the provided integer `n`. If so, it decrements `count` by `n` and returns `True`. If `count` is less than `n`, it returns `False`, indicating that the operation could not be performed.

        Args:
        - n (int, optional): The value to decrement from `count`. Must be a positive integer that does not exceed the current `count`. Default is 1.

        Returns:
        bool: Returns `True` if the decrement was successful (i.e., `count` was greater than or equal to `n`), otherwise returns `False`.

        Raises:
        - No exceptions are raised by this method. Ensure that `n` is a positive integer and does not exceed the current `count` to avoid logical errors.
        """
        if self.count >= n:
            self.count -= n
            return True
        return False