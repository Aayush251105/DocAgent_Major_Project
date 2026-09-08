from decimal import Decimal
from typing import Optional, List, Tuple
from .models.product import Item
from .payment.payment_processor import Handler, Tx, TxStatus, Cash
from .inventory.inventory_manager import Store

class SysErr(Exception):
    """
    No docstring provided.
    """
    pass

class Sys:
    """
    Summary: Central controller for vending machine operations and transaction management.
    Description: Manages item inventory, transactions, and user interactions in a vending machine system.
    Parameters: h (Optional[Handler]): Transaction handler for processing operations.
    Attributes:
    - store: Store containing items
    - h: Transaction handler
    - _tx: Current active transaction
    """

    def __init__(self, h: Optional[Handler]=None):
        self.store = Store()
        self.h = h or Cash()
        self._tx: Optional[Tx] = None

    def ls(self) -> List[Tuple[int, Item]]:
        """
        Summary: Returns a sorted list of items with their positions in the store.
        Description: Maps each item to its position in the store and returns the list sorted by position.
        Returns: List of tuples (position, item)
        Raises: None
        """
        items = []
        for item in self.store.ls():
            pos = self.store.find(item.code)
            if pos is not None:
                items.append((pos, item))
        return sorted(items, key=lambda x: x[0])

    def pick(self, pos: int) -> Optional[Item]:
        """
        Summary: Returns a valid item from the store at the given position.  
        Description: Checks the position and item availability; if invalid, raises an exception.  
        Returns: Item - The item at the specified position if available and valid.  
        Raises: SysErr - Raised if the position is invalid or the item is unavailable.
        """
        item = self.store.get_at(pos)
        if not item:
            raise SysErr('invalid pos')
        if not item.check():
            raise SysErr('unavailable')
        return item

    def add_money(self, amt: Decimal) -> None:
        """
        Summary: Deposits funds into the account using a validated cash handler.
        Description: Validates handler type before adding money to the account.
        Args: amt (Decimal) - amount to deposit
        Returns: None
        Raises: SysErr if handler is not a Cash instance
        """
        if not isinstance(self.h, Cash):
            raise SysErr('cash not supported')
        self.h.add(amt)

    def buy(self, pos: int) -> Tuple[Item, Optional[Decimal]]:
        """
        Purchases an item and returns it with any refund amount.
        Processes the transaction using the handler and dispenses the item if successful.
        pos (int): Position of the item to purchase.
        Returns: Tuple of purchased item and optional refund amount.
        Raises: IndexError (invalid position) or SysErr (transaction failure or dispensing failure)
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
        Summary: Cancels the current transaction and returns any refund amount.
        Description: Reverses the active transaction and returns the refund if applicable.
        Returns: Optional[Decimal] - Refund amount if transaction was canceled successfully, otherwise None.
        Raises: SysErr - Raised if no active transaction or reversal fails.
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