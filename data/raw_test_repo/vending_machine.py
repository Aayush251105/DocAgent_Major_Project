from decimal import Decimal
from typing import Optional, List, Tuple
from .models.product import Item
from .payment.payment_processor import Handler, Tx, TxStatus, Cash
from .inventory.inventory_manager import Store

class SysErr(Exception):
    """
    Summary: Custom exception class for system errors.

    Description: 
    The `SysErr` class is a custom exception class designed to handle system-level errors. It is a subclass of Python's built-in `Exception` class and is used to indicate that an error has occurred within the system. This class is useful for providing a clear and specific error handling mechanism for system-level issues.

    Example:
    ```python
    try:
        # Simulate a system error
        raise SysErr("A system error occurred")
    except SysErr as e:
        print(f"Caught an error: {e}")
    ```

    Args:
    - None: This exception does not accept any arguments.

    Returns:
    - None: This exception does not return any value. It is used to raise an error.

    Raises:
    - None: This exception does not raise any additional exceptions. It is used to indicate that a system-level error has occurred.
    """
    pass

class Sys:
    """
    Summary: Manages the state and operations of a vending machine.

    Description: The `Sys` class represents a vending machine system, handling item listing, purchasing, and transaction management.

    Attributes:
    - store (Store): The store containing items.
    - h (Handler): The handler for processing transactions.
    - _tx (Optional[Tx]): The current transaction.

    Methods:
    - ls(): Lists all items in the store with their positions.
    - pick(pos: int): Retrieves an item from the store at the specified position.
    - add_money(amt: Decimal): Adds money to the account using the specified handler.
    - buy(pos: int): Buys an item from the vending machine.
    - cancel(): Cancels the current transaction and returns any refund.
    """

    def __init__(self, h: Optional[Handler]=None):
        self.store = Store()
        self.h = h or Cash()
        self._tx: Optional[Tx] = None

    def ls(self) -> List[Tuple[int, Item]]:
        """
        Summary: Lists all items in the store with their positions.

        Description: 
        The `ls` method is used to list all items in the store along with their positions. It retrieves the items from the store, finds their positions, and returns a sorted list of tuples containing the position and item.

        Example:
        ```python
        class Item:
            def __init__(self, code: str, val: Decimal):
                self.code = code
                self.val = val

        class Store:
            def ls(self) -> List[Item]:
                return [Item('A1', Decimal('1.00')), Item('A2', Decimal('2.00'))]

            def find(self, code: str) -> Optional[int]:
                items = self.ls()
                for i, item in enumerate(items):
                    if item.code == code:
                        return i
                return None

        class VendingMachine:
            def __init__(self, store: Store):
                self.store = store

            def ls(self) -> List[Tuple[int, Item]]:
                items = []
                for item in self.store.ls():
                    pos = self.store.find(item.code)
                    if pos is not None:
                        items.append((pos, item))
                return sorted(items, key=lambda x: x[0])

        # Usage example
        store = Store()
        vm = VendingMachine(store)
        items = vm.ls()
        for pos, item in items:
            print(f"Position: {pos}, Item: {item.code}, Value: {item.val}")
        ```

        Args:
        - None

        Returns:
        - List[Tuple[int, Item]]: A list of tuples containing the position and item.

        Raises:
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
        Summary: Retrieves an item from the store at the specified position.

        Description: 
        The `pick` method is used to retrieve an item from the store at the specified position. It checks if the item exists and is available before returning it. If the position is invalid or the item is unavailable, it raises an exception.

        Example:
        ```python
        class Item:
            def __init__(self, code: str, val: Decimal):
                self.code = code
                self.val = val

            def check(self) -> bool:
                return True

        class Store:
            def __init__(self):
                self.items = [Item('A1', Decimal('1.00')), Item('A2', Decimal('2.00'))]

            def get_at(self, pos: int) -> Optional[Item]:
                if pos < 0 or pos >= len(self.items):
                    return None
                return self.items[pos]

        class VendingMachine:
            def __init__(self, store: Store):
                self.store = store

            def pick(self, pos: int) -> Optional[Item]:
                item = self.store.get_at(pos)
                if not item:
                    raise SysErr('invalid pos')
                if not item.check():
                    raise SysErr('unavailable')
                return item

        # Usage example
        store = Store()
        vm = VendingMachine(store)
        item = vm.pick(0)
        print(f"Item: {item.code}, Value: {item.val}")
        ```

        Args:
        - pos (int): The position of the item in the store.

        Returns:
        - Optional[Item]: The item at the specified position if available, otherwise None.

        Raises:
        - SysErr: Raised if the position is invalid or the item is unavailable. Check the position and availability of the item to avoid these errors.
        """
        item = self.store.get_at(pos)
        if not item:
            raise SysErr('invalid pos')
        if not item.check():
            raise SysErr('unavailable')
        return item

    def add_money(self, amt: Decimal) -> None:
        """
        Summary: Adds money to the account using the specified handler.

        Description: 
        The `add_money` method is used to add a specified amount of money to the account using a handler object. It checks if the handler is an instance of the `Cash` class and then calls the `add` method of the handler to add the money. This method is useful for depositing funds into an account using a cash handler.

        Example:
        ```python
        class Cash:
            def add(self, amt: Decimal) -> None:
                print(f"Adding {amt} to the account")

        class Account:
            def __init__(self, handler: Cash):
                self.h = handler

            def add_money(self, amt: Decimal) -> None:
                if not isinstance(self.h, Cash):
                    raise SysErr('cash not supported')
                self.h.add(amt)

        # Usage example
        cash_handler = Cash()
        account = Account(cash_handler)
        account.add_money(Decimal('50'))
        ```

        Args:
        - `amt` (Decimal): The amount of money to add to the account.

        Returns:
        - None: This method does not return any value. It adds money to the account.

        Raises:
        - SysErr: Raised if the handler is not an instance of the `Cash` class. Ensure that the handler is a valid cash handler to avoid this error.
        """
        if not isinstance(self.h, Cash):
            raise SysErr('cash not supported')
        self.h.add(amt)

    def buy(self, pos: int) -> Tuple[Item, Optional[Decimal]]:
        """
        Summary: Buys an item from the vending machine.

        Description: 
        The `buy` method is used to purchase an item from the vending machine. It takes the position of the item as an argument, processes the transaction using the handler, and handles the item's dispensing. If the transaction is successful and the item is dispensed, it returns the item and any refund amount. If the transaction fails or the item cannot be dispensed, it raises an exception.

        Example:
        ```python
        class Item:
            def __init__(self, val: Decimal):
                self.val = val

            def mod(self) -> bool:
                return True

        class Cash:
            def add(self, amt: Decimal) -> None:
                pass

            def proc(self, amt: Decimal) -> Tx:
                return Tx(id='123', amt=amt, st=TxStatus.DONE, mth='cash')

            def rev(self, tx: Tx) -> bool:
                return True

            def ret(self) -> Decimal:
                return Decimal('0.00')

        class VendingMachine:
            def __init__(self, items: List[Item], handler: Cash):
                self.items = items
                self.h = handler

            def pick(self, pos: int) -> Item:
                if pos < 0 or pos >= len(self.items):
                    raise IndexError("Invalid position")
                return self.items[pos]

            def buy(self, pos: int) -> Tuple[Item, Optional[Decimal]]:
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

        # Usage example
        items = [Item(Decimal('1.00')), Item(Decimal('2.00'))]
        cash_handler = Cash()
        vm = VendingMachine(items, cash_handler)
        item, refund = vm.buy(0)
        print(f"Item bought: {item.val}, Refund: {refund}")
        ```

        Args:
        - `pos` (int): The position of the item to be purchased.

        Returns:
        - Tuple[Item, Optional[Decimal]]: A tuple containing the purchased item and any refund amount.

        Raises:
        - IndexError: Raised if the position is out of range. Ensure that the position is valid to avoid this error.
        - SysErr: Raised if the transaction fails or the item cannot be dispensed. Check the transaction status and item mod method to handle these errors.
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
        Summary: Cancels the current transaction and returns any refund.

        Description: 
        The `cancel` method is used to cancel the current transaction and return any refund amount. It checks if a transaction is currently in progress, reverses the transaction using the handler, and handles the refund if applicable. If the transaction is not in progress or the reversal fails, it raises an exception.

        Example:
        ```python
        class Cash:
            def add(self, amt: Decimal) -> None:
                pass

            def proc(self, amt: Decimal) -> Tx:
                return Tx(id='123', amt=amt, st=TxStatus.DONE, mth='cash')

            def rev(self, tx: Tx) -> bool:
                return True

            def ret(self) -> Decimal:
                return Decimal('0.00')

        class VendingMachine:
            def __init__(self, items: List[Item], handler: Cash):
                self.items = items
                self.h = handler
                self._tx = None

            def pick(self, pos: int) -> Item:
                if pos < 0 or pos >= len(self.items):
                    raise IndexError("Invalid position")
                return self.items[pos]

            def buy(self, pos: int) -> Tuple[Item, Optional[Decimal]]:
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

        # Usage example
        items = [Item(Decimal('1.00')), Item(Decimal('2.00'))]
        cash_handler = Cash()
        vm = VendingMachine(items, cash_handler)
        vm.buy(0)
        refund = vm.cancel()
        print(f"Refund: {refund}")
        ```

        Args:
        - None

        Returns:
        - Optional[Decimal]: The refund amount if applicable, otherwise None.

        Raises:
        - SysErr: Raised if there is no current transaction or if the reversal fails. Check if a transaction is in progress and handle the reversal to avoid these errors.
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