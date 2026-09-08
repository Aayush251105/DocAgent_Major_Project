from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from decimal import Decimal

class TxStatus(Enum):
    """
    Summary: Transaction status enum with four states.
    Description: Defines pending, completed, failed, and refunded transaction statuses.
    Attributes: WAIT (pending), DONE (completed), ERR (failed), RET (refunded)
    """
    WAIT = 'pending'
    DONE = 'completed'
    ERR = 'failed'
    RET = 'refunded'

@dataclass
class Tx:
    """
    Transaction object with essential details.
    Models a transaction including its identifier, amount, status, method, and optional message.
    Attributes:
    id: Unique string identifier
    amt: Decimal amount
    st: Transaction status (TxStatus)
    mth: Transaction method string
    msg: Optional message string
    """
    id: str
    amt: Decimal
    st: TxStatus
    mth: str
    msg: Optional[str] = None

class Handler(ABC):
    """
    Summary: Abstract base class for transaction processing and reversal

    Description: Defines the interface for processing and reversing transactions, requiring concrete subclasses to implement the `proc` and `rev` methods.
    """

    @abstractmethod
    def proc(self, amt: Decimal) -> Tx:
        """
        Summary: Returns a transaction object with the provided amount.

        Description: This method returns a `Tx` object that represents a transaction with the given amount. The implementation does not perform any processing.

        Args:
        - `amt`: A `Decimal` representing the transaction amount.

        Returns: A `Tx` object

        Raises: No exceptions.
        """
        pass

    @abstractmethod
    def rev(self, tx: Tx) -> bool:
        """
        Summary: Reverses a transaction and returns a boolean indicating success.

        Description: This method reverses a transaction by updating its status.

        Args: `tx` (a transaction object to reverse)

        Returns: True if the transaction was successfully reversed, else False.

        Raises: No exceptions.
        """
        pass

class Cash(Handler):
    """
    Summary: Cash-based account transaction handler for processing and managing financial operations.
    Description: Handles cash transactions including deposits, withdrawals, reversals, and refunds while maintaining account balance.
    Attributes: bal (Decimal) - current account balance in cash units.
    """

    def __init__(self):
        self.bal: Decimal = Decimal('0.00')

    def add(self, amt: Decimal) -> None:
        """
        Summary: Increases account balance by a specified positive amount.

        Description: Credits the account with funds through in-place addition of the provided amount.

        Args:
        - amt (Decimal): Positive amount to add to the balance (negative values raise ValueError)

        Returns:
        - None: Modifies balance in-place without returning value

        Raises:
        - ValueError: If amt is negative (ensure positive amounts for valid transactions)
        """
        self.bal += amt

    def proc(self, amt: Decimal) -> Tx:
        """
        Summary: Deducts a specified amount from the account balance if sufficient funds are available; otherwise returns an error transaction.
        Description: Processes the transaction by deducting the amount from the balance when funds are sufficient; otherwise returns a transaction with error status.
        Args:
        - `amt` (Decimal): Non-negative amount to deduct from the balance
        Returns:
        - `Tx`: Transaction object with status `DONE` (success) or `ERR` (failure with message)
        """
        if self.bal >= amt:
            self.bal -= amt
            return Tx(id=f'C_{id(self)}', amt=amt, st=TxStatus.DONE, mth='cash')
        return Tx(id=f'C_{id(self)}', amt=amt, st=TxStatus.ERR, mth='cash', msg='insufficient')

    def rev(self, tx: Tx) -> bool:
        """
        Summary: Reverses a completed transaction by adding the amount back to the account balance and updating the transaction status to `RET`.

        Description: Adds the transaction amount to the account balance and sets the transaction status to `RET` when the transaction was `DONE`.

        Args:
        - `tx` (Tx): Transaction object with status `DONE`.

        Returns:
        - bool: True if the transaction was successfully reversed, else False.
        """
        if tx.st == TxStatus.DONE:
            self.bal += tx.amt
            tx.st = TxStatus.RET
            return True
        return False

    def ret(self) -> Decimal:
        """
        Summary: Refunds the entire account balance and returns the refunded amount.

        Description: Sets the account balance to zero and returns the previous balance.

        Returns: Decimal - the amount that was refunded (the account's balance before the refund)
        """
        tmp = self.bal
        self.bal = Decimal('0.00')
        return tmp