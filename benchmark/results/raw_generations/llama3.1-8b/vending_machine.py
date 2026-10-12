from decimal import Decimal
from typing import Optional, List, Tuple
from .models.product import Item
from .payment.payment_processor import Handler, Tx, TxStatus, Cash
from .inventory.inventory_manager import Store

class SysErr(Exception):
    """
    Summary: Custom exception class for system errors.

    Description: 
    The `SysErr` class is a custom exception class designed to handle system-level errors.

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
        The `ls` method lists all items in the store along with their positions.

        Returns:
        - List[Tuple[int, Item]]: A list of tuples containing the position and item.
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
        The `pick` method retrieves an item from the store at the specified position.

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
        The `add_money` method adds a specified amount of money to the account using a handler object.

        Args:
        - `amt` (Decimal): The amount of money to add to the account.

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
        The `buy` method purchases an item from the vending machine, processes the transaction, and handles the item's dispensing.

        Args:
        - `pos` (int): The position of the item to be purchased.

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
        The `cancel` method cancels the current transaction and returns any refund amount.

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