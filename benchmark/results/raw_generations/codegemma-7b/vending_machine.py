from decimal import Decimal
from typing import Optional, List, Tuple
from .models.product import Item
from .payment.payment_processor import Handler, Tx, TxStatus, Cash
from .inventory.inventory_manager import Store

class SysErr(Exception):
    """
    **SysErr Class Docstring:**

    **Summary:**
    Custom exception class for system errors.

    **Description:**
    The `SysErr` class is a custom exception class designed to handle system-level errors. It is a subclass of Python's built-in `Exception` class and is used to indicate that an error has occurred within the system.

    **Args:**
    - None: This exception does not accept any arguments.

    **Returns:**
    - None: This exception does not return any value. It is used to raise an error.

    **Raises:**
    - None: This exception does not raise any additional exceptions. It is used to indicate that a system-level error has occurred.
    """
    pass

class Sys:
    """
    **Sys Class Docstring:**

    **Summary:**
    Manages the state and operations of a vending machine.

    **Description:**
    The `Sys` class represents a vending machine system, handling item listing, purchasing, and transaction management.

    **Attributes:**
    - `store` (Store): The store containing items.
    - `h` (Handler): The handler for processing transactions.
    - `_tx` (Optional[Tx]): The current transaction.

    **Methods:**
    - `ls()`: Lists all items in the store with their positions.
    - `pick(pos: int)`: Retrieves an item from the store at the specified position.
    - `add_money(amt: Decimal)`: Adds money to the account using the specified handler.
    - `buy(pos: int)`: Buys an item from the vending machine.
    - `cancel()`: Cancels the current transaction and returns any refund.
    """

    def __init__(self, h: Optional[Handler]=None):
        self.store = Store()
        self.h = h or Cash()
        self._tx: Optional[Tx] = None

    def ls(self) -> List[Tuple[int, Item]]:
        """
        **ls() Function Docstring:**

        **Summary:**
        Lists all items in the store with their positions.

        **Description:**
        The `ls` method is used to list all items in the store along with their positions.

        **Args:**
        - None

        **Returns:**
        - List[Tuple[int, Item]]: A list of tuples containing the position and item.

        **Raises:**
        - None
        """
        items = []
        for item in self.store.ls():
            pos = self.store.find(item.code)
            if pos is not None:
                items.append((pos, item))
        return sorted(items, key=lambda x: x[0])

    def pick(self, pos: int) -> Optional[Item]:
        """
        **pick() Function Docstring:**

        **Summary:**
        Retrieves an item from the store at the specified position.

        **Description:**
        The `pick` method is used to retrieve an item from the store at the specified position.

        **Args:**
        - pos (int): The position of the item in the store.

        **Returns:**
        - Optional[Item]: The item at the specified position if available, otherwise None.

        **Raises:**
        - `SysErr`: Raised if the position is invalid or the item is unavailable.
        """
        item = self.store.get_at(pos)
        if not item:
            raise SysErr('invalid pos')
        if not item.check():
            raise SysErr('unavailable')
        return item

    def add_money(self, amt: Decimal) -> None:
        """
        **add_money() Function Docstring:**

        **Summary:**
        Adds money to the account using the specified handler.

        **Description:**
        The `add_money` method is used to add a specified amount of money to the account using a handler object.

        **Args:**
        - `amt`: A `Decimal` representing the amount of money to add to the account.

        **Returns:**
        - None: This method does not return any value. It adds money to the account.

        **Raises:**
        - `SysErr`: Raised if the handler is not an instance of the `Cash` class.
        """
        if not isinstance(self.h, Cash):
            raise SysErr('cash not supported')
        self.h.add(amt)

    def buy(self, pos: int) -> Tuple[Item, Optional[Decimal]]:
        """
        **buy() Function Docstring:**

        **Summary:**
        Buys an item from the vending machine.

        **Description:**
        The `buy` method is used to purchase an item from the vending machine. It takes the position of the item as an argument, processes the transaction using the handler, and handles the item's dispensing.

        **Args:**
        - `pos`: The position of the item to be purchased.

        **Returns:**
        - A tuple containing the purchased item and any refund amount.

        **Raises:**
        - `IndexError`: Raised if the position is out of range.
        - `SysErr`: Raised if the transaction fails or the item cannot be dispensed.
        """
        item = self.pick(pos)
        tx = self.h.proc(Decimal(str(item.val)))
        self._tx = tx
        if tx.st != TxStatus.DONE:
            raise SysErr(tx.msg or 'tx failed')
        if not item.mod():
            self.h.rev(tx)
            raise SysErr('dispense failed')
        ret = None
        if isinstance(self.h, Cash):
            ret = self.h.ret()
        return (item, ret)

    def cancel(self) -> Optional[Decimal]:
        """
        **cancel() Function Docstring:**

        **Summary:**
        Cancels the current transaction and returns any refund.

        **Description:**
        The `cancel` method is used to cancel the current transaction and return any refund amount.

        **Args:**
        - None

        **Returns:**
        - Optional[Decimal]: The refund amount if applicable, otherwise None.

        **Raises:**
        - `SysErr`: Raised if there is no current transaction or if the reversal fails.
        """
        if not self._tx:
            raise SysErr('no tx')
        ok = self.h.rev(self._tx)
        if not ok:
            raise SysErr('rev failed')
        ret = None
        if isinstance(self.h, Cash):
            ret = self.h.ret()
        self._tx = None
        return ret