from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from decimal import Decimal

class TxStatus(Enum):
    """
    Summary: Defines transaction statuses with enum values.  
    Description: Provides enum values for tracking transaction states: WAIT (pending), DONE (completed), ERR (failed), and RET (refunded).  
    Attributes:  
    - `WAIT`: Pending transaction.  
    - `DONE`: Completed transaction.  
    - `ERR`: Failed transaction.  
    - `RET`: Refunded transaction.
    """
    WAIT = 'pending'
    DONE = 'completed'
    ERR = 'failed'
    RET = 'refunded'

@dataclass
class Tx:
    """
    Summary: Represents a transaction with key details.  
    Description: Encapsulates transaction details like ID, amount, status, method, and message.  
    Attributes:  
    - `id`: Unique transaction identifier.  
    - `amt`: Transaction amount as Decimal.  
    - `st`: Current status from TxStatus enum.  
    - `mth`: Payment method used.  
    - `msg`: Optional message related to the transaction.
    """
    id: str
    amt: Decimal
    st: TxStatus
    mth: str
    msg: Optional[str] = None

class Handler(ABC):
    """
    Summary: Abstract base class for managing transaction processing and reversal.  
    Description: Provides a framework for handling transactions with abstract methods for processing (`proc`) and reversing (`rev`).  
    Parameters: initial_bal (Decimal): Initial account balance for subclasses.  
    Attributes: bal (Decimal): Current account balance managed by subclasses.
    """

    @abstractmethod
    def proc(self, amt: Decimal) -> Tx:
        """
        Summary: Processes a transaction by deducting the specified amount and returning a transaction object.  
        Description: Returns a `Tx` object representing the processed transaction, including details like status, amount, and method.  
        Args: amt (Decimal): The amount of the transaction to be processed.  
        Returns: Tx - A transaction object containing the transaction details (id, amount, status, method, and optional message).  
        Raises: No exceptions. Ensure the amount is valid to avoid unexpected behavior.
        """
        pass

    @abstractmethod
    def rev(self, tx: Tx) -> bool:
        """
        Summary: Reverses a completed transaction by restoring the amount to the account balance.  
        Description: Returns True if the transaction was successfully reversed (status was DONE), otherwise False.  
        Args: tx (Tx): Transaction must have status DONE to be reversed.  
        Returns: bool - True if reversed, False otherwise.  
        Raises: No exceptions. Ensure tx is DONE to avoid unexpected behavior.
        """
        pass

class Cash(Handler):
    """
    Summary: Manages cash-based account transactions with deposit, processing, and refund capabilities.  
    Description: Handles cash transactions by modifying balance, processing payments, reversing transactions, and refunding funds.  
    Attributes: bal (Decimal): Current account balance managed through deposit and transaction operations.
    """

    def __init__(self):
        self.bal: Decimal = Decimal('0.00')

    def add(self, amt: Decimal) -> None:
        """
        Summary: Increases the account balance by a specified amount.  
        Description: Credits the account with funds, updating the balance in place.  
        Args:  
        - `amt` (Decimal): Positive amount to add to the balance.  
        Returns: None.  
        Raises:  
        - ValueError: If `amt` is negative; ensure amount is positive.
        """
        self.bal += amt

    def proc(self, amt: Decimal) -> Tx:
        """
        Summary: Deducts amount from balance and returns transaction result.  
        Description: Checks balance; returns Tx with DONE or ERR status.  
        Args: amt (Decimal): Non-negative amount to deduct.  
        Returns: Tx object with status DONE (success) or ERR (insufficient funds).  
        Raises: No exceptions. Ensure amt is non-negative.  
        Attributes: (Not applicable)
        """
        if self.bal >= amt:
            self.bal -= amt
            return Tx(id=f'C_{id(self)}', amt=amt, st=TxStatus.DONE, mth='cash')
        return Tx(id=f'C_{id(self)}', amt=amt, st=TxStatus.ERR, mth='cash', msg='insufficient')

    def rev(self, tx: Tx) -> bool:
        """
        Summary: Reverses a completed transaction by restoring the amount to balance.  
        Description: Updates balance and marks transaction as refunded (RET) if completed.  
        Args: tx (Tx): Transaction must have status DONE to be reversed.  
        Returns: bool - True if reversed (status was DONE), False otherwise.  
        Raises: No exceptions. Ensure tx is DONE to avoid unexpected behavior.  
        Attributes: (Not applicable)
        """
        if tx.st == TxStatus.DONE:
            self.bal += tx.amt
            tx.st = TxStatus.RET
            return True
        return False

    def ret(self) -> Decimal:
        """
        Summary: Refunds full balance and returns the amount.  
        Description: Returns the current balance and resets the account balance to zero.  
        Returns: Decimal representing the refunded amount (pre-refund balance).  
        Raises: No exceptions.  
        Attributes: (Not applicable)
        """
        tmp = self.bal
        self.bal = Decimal('0.00')
        return tmp