from decimal import Decimal
from typing import Optional, List, Tuple
from .models.product import Item
from .payment.payment_processor import Handler, Tx, TxStatus, Cash
from .inventory.inventory_manager import Store

class SysErr(Exception):
    """
    Summary: Custom exception for system-level errors.
    Description: Subclass of Exception used to indicate system-level errors.
    Raises: None. This exception is raised to signal system errors.
    """
    pass

class Sys:
    """
    Summary: Manages vending machine operations and transactions.  
    Description: Coordinates item listings, purchases, and transaction handling.  
    Parameters: h (Handler): Transaction handler, defaults to Cash.  
    Attributes: store (Store): Item repository. h (Handler): Transaction handler. _tx (Tx): Current transaction.
    """

    def __init__(self, h: Optional[Handler]=None):
        self.store = Store()
        self.h = h or Cash()
        self._tx: Optional[Tx] = None

    def ls(self) -> List[Tuple[int, Item]]:
        """
        Summary: Lists all items with their positions.  
        Description: Returns a sorted list of item-position tuples.  
        Returns: List[Tuple[int, Item]] - Sorted list of position and item tuples.
        """
        items = []
        for item in self.store.ls():
            pos = self.store.find(item.code)
            if pos is not None:
                items.append((pos, item))
        return sorted(items, key=lambda x: x[0])

    def pick(self, pos: int) -> Optional[Item]:
        """
        Summary: Retrieves an item from the specified position.  
        Description: Checks validity and availability before returning.  
        Args: pos (int): The position of the item in the store.  
        Returns: Optional[Item]: The item if available, otherwise None.  
        Raises: SysErr: If position is invalid or item is unavailable. Verify position and availability.
        """
        item = self.store.get_at(pos)
        if not item:
            raise SysErr('invalid pos')
        if not item.check():
            raise SysErr('unavailable')
        return item

    def add_money(self, amt: Decimal) -> None:
        """
        Summary: Adds a specified amount to the account using the configured cash handler.

        Description: Validates the handler is a Cash instance before depositing funds.

        Args: 
        - `amt` (Decimal) – The amount of money to add to the account.

        Returns: 
        - None – The method does not return a value.

        Raises: 
        - SysErr – If the handler is not a Cash instance, ensuring only supported handlers are used.
        """
        if not isinstance(self.h, Cash):
            raise SysErr('cash not supported')
        self.h.add(amt)

    def buy(self, pos: int) -> Tuple[Item, Optional[Decimal]]:
        """
        Summary: Purchases an item and returns it along with any refund.  
        Description: Processes a transaction to purchase the item at the specified position, handles dispensing, and returns the item with potential refund.  
        Args: pos (int): The position of the item to be purchased.  
        Returns: Tuple[Item, Optional[Decimal]]: The purchased item and refund amount if applicable.  
        Raises: IndexError: If the position is out of range. SysErr: If the transaction fails or the item cannot be dispensed.
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

        Description: Ends the transaction and processes a refund if applicable.

        Args: None

        Returns: Optional[Decimal] - The refund amount if applicable, otherwise None.

        Raises: SysErr - If no transaction exists or reversal fails. Ensure a transaction is active before calling.
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