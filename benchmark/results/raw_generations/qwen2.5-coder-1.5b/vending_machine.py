from decimal import Decimal
from typing import Optional, List, Tuple
from .models.product import Item
from .payment.payment_processor import Handler, Tx, TxStatus, Cash
from .inventory.inventory_manager import Store

class SysErr(Exception):
    """
    <SUMMARY>
            Custom exception class for system errors.
        </SUMMARY>
        <DESCRIPTION>
            The `SysErr` class is a custom exception class designed to handle system-level errors. It is a subclass of Python's built-in `Exception` class and is used to indicate that an error has occurred within the system. This class is useful for providing a clear and specific error handling mechanism for system-level issues.
        </DESCRIPTION>
        <PARAMETERS>
            None: This exception does not accept any arguments.
        </PARAMETERS>
        <ATTRIBUTES>
            None: This exception does not have any public attributes.
        </ATTRIBUTES>
        <EXAMPLES>
            ```python
            try:
                # Simulate a system error
                raise SysErr("A system error occurred")
            except SysErr as e:
                print(f"Caught an error: {e}")
            ```
        </EXAMPLES>
        <RETURNS>
            None: This exception does not return any value. It is used to raise an error.
        </RETURNS>
        <RAISES>
            None: This exception does not raise any additional exceptions. It is used to indicate that a system-level error has occurred.
        </RAISES>
    """
    pass

class Sys:
    """
    <SUMMARY>
            Manages the state and operations of a vending machine.
        </SUMMARY>
        <DESCRIPTION>
            The `Sys` class represents a vending machine system, handling item listing, purchasing, and transaction management.
        </DESCRIPTION>
        <ATTRIBUTES>
            - store (Store): The store containing items.
            - h (Handler): The handler for processing transactions.
            - _tx (Optional[Tx]): The current transaction.
        </ATTRIBUTES>
        <METHODS>
            - ls(): Lists all items in the store with their positions.
            - pick(pos: int): Retrieves an item from the store at the specified position.
            - add_money(amt: Decimal): Adds money to the account using the specified handler.
            - buy(pos: int): Buys an item from the vending machine.
            - cancel(): Cancels the current transaction and returns any refund.
        </METHODS>
    """

    def __init__(self, h: Optional[Handler]=None):
        self.store = Store()
        self.h = h or Cash()
        self._tx: Optional[Tx] = None

    def ls(self) -> List[Tuple[int, Item]]:
        """
        <SUMMARY>
                Lists all items in the store with their positions.
            </SUMMARY>
            <DESCRIPTION>
                The `ls` method is used to list all items in the store along with their positions. It retrieves the items from the store, finds their positions, and returns a sorted list of tuples containing the position and item.
            </DESCRIPTION>
            <ARGS>
                - None
            </ARGS>
            <RETURNS>
                List[Tuple[int, Item]]: A list of tuples containing the position and item.
            </RETURNS>
            <RAISES>
                None
            </RAISES>
        """
        items = []
        for item in self.store.ls():
            pos = self.store.find(item.code)
            if pos is not None:
                items.append((pos, item))
        return sorted(items, key=lambda x: x[0])

    def pick(self, pos: int) -> Optional[Item]:
        """
        <SUMMARY>
                Retrieves an item from the store at the specified position.
            </SUMMARY>
            <DESCRIPTION>
                The `pick` method is used to retrieve an item from the store at the specified position. It checks if the item exists and is available before returning it. If the position is invalid or the item is unavailable, it raises an exception.
            </DESCRIPTION>
            <ARGS>
                - pos (int): The position of the item in the store.
            </ARGS>
            <RETURNS>
                Optional[Item]: The item at the specified position if available, otherwise None.
            </RETURNS>
            <RAISES>
                SysErr: Raised if the position is invalid or the item is unavailable. Check the position and availability of the item to avoid these errors.
            </RAISES>
        """
        item = self.store.get_at(pos)
        if not item:
            raise SysErr('invalid pos')
        if not item.check():
            raise SysErr('unavailable')
        return item

    def add_money(self, amt: Decimal) -> None:
        """
        <SUMMARY>
                Adds money to the account using the specified handler.
            </SUMMARY>
            <DESCRIPTION>
                The `add_money` method is used to add a specified amount of money to the account using a handler object. It checks if the handler is an instance of the `Cash` class and then calls the `add` method of the handler to add the money. This method is useful for depositing funds into an account using a cash handler.
            </DESCRIPTION>
            <ARGS>
                - `amt` (Decimal): The amount of money to add to the account.
            </ARGS>
            <RETURNS>
                None: This method does not return any value. It adds money to the account.
            </RETURNS>
            <RAISES>
                SysErr: Raised if the handler is not an instance of the `Cash` class. Ensure that the handler is a valid cash handler to avoid this error.
            </RAISES>
        """
        if not isinstance(self.h, Cash):
            raise SysErr('cash not supported')
        self.h.add(amt)

    def buy(self, pos: int) -> Tuple[Item, Optional[Decimal]]:
        """
        <SUMMARY>
                Buys an item from the vending machine.
            </SUMMARY>
            <DESCRIPTION>
                The `buy` method is used to purchase an item from the vending machine. It takes the position of the item as an argument, processes the transaction using the handler, and handles the item's dispensing. If the transaction is successful and the item is dispensed, it returns the item and any refund amount. If the transaction fails or the item cannot be dispensed, it raises an exception.
            </DESCRIPTION>
            <ARGS>
                - `pos` (int): The position of the item to be purchased.
            </ARGS>
            <RETURNS>
                Tuple[Item, Optional[Decimal]]: A tuple containing the purchased item and any refund amount.
            </RETURNS>
            <RAISES>
                IndexError: Raised if the position is out of range. Ensure that the position is valid to avoid this error.
                SysErr: Raised if the transaction fails or the item cannot be dispensed. Check the transaction status and item mod method to handle these errors.
            </RAISES>
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
        <SUMMARY>
                Cancels the current transaction and returns any refund.
            </SUMMARY>
            <DESCRIPTION>
                The `cancel` method is used to cancel the current transaction and return any refund amount. It checks if a transaction is currently in progress, reverses the transaction using the handler, and handles the refund if applicable. If the transaction is not in progress or the reversal fails, it raises an exception.
            </DESCRIPTION>
            <ARGS>
                - None
            </ARGS>
            <RETURNS>
                Optional[Decimal]: The refund amount if applicable, otherwise None.
            </RETURNS>
            <RAISES>
                SysErr: Raised if there is no current transaction or if the reversal fails. Check if a transaction is in progress and handle the reversal to avoid these errors.
            </RAISES>
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