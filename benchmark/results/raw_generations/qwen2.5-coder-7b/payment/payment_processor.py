from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from decimal import Decimal

class TxStatus(Enum):
    """
    Summary:
    Represents the status of a transaction.

    Description:
    The `TxStatus` enum defines the possible statuses of a transaction in a system, including pending, completed, failed, and refunded states. This enum aids in managing and tracking transaction statuses throughout their lifecycle.

    Attributes:
    - `WAIT`: Enum member representing a pending transaction status.
    - `DONE`: Enum member representing a completed transaction status.
    - `ERR`: Enum member representing a failed transaction status.
    - `RET`: Enum member representing a refunded transaction status.
    """
    WAIT = 'pending'
    DONE = 'completed'
    ERR = 'failed'
    RET = 'refunded'

@dataclass
class Tx:
    """
    Summary:
    Represents a transaction in the system.

    Description:
    The `Tx` class models a transaction in a system, encapsulating details such as its unique identifier, amount, status, method, and an optional message. This class is essential for tracking and managing transactions within the system.

    Attributes:
    - `id`: A string representing the unique identifier of the transaction.
    - `amt`: A `Decimal` representing the amount of the transaction.
    - `st`: An instance of `TxStatus` representing the current status of the transaction.
    - `mth`: A string representing the method used for the transaction.
    - `msg`: An optional string representing a message related to the transaction.
    """
    id: str
    amt: Decimal
    st: TxStatus
    mth: str
    msg: Optional[str] = None

class Handler(ABC):
    """
    Summary: Abstract base class for handling transactions.

    Description: 
    The `Handler` class is an abstract base class designed to handle transactions. It defines two abstract methods: `proc` and `rev`. These methods must be implemented by any concrete subclass to process and reverse transactions, respectively. The `Handler` class is intended to be used in systems where transaction processing and reversal are required, such as financial applications or payment gateways.

    Parameters:
    - `initial_bal`: A `Decimal` representing the initial balance of the account.

    Attributes:
    - `bal`: A `Decimal` representing the current balance of the account.

    HOW:
    The `Handler` class provides a framework for processing and reversing transactions. Concrete subclasses must implement the `proc` and `rev` methods to define the specific behavior for these operations. The `proc` method processes a transaction and returns a `Tx` object, while the `rev` method reverses a transaction and returns a boolean indicating success.
    """

    @abstractmethod
    def proc(self, amt: Decimal) -> Tx:
        """
        Summary:
        Processes a transaction.

        Description:
        The `proc` method processes a transaction by deducting the specified amount from the account balance if there are sufficient funds. If the balance is insufficient, it returns a transaction with an error status. This method is essential for managing account balances and tracking transactions.

        Args:
        - `amt`: A `Decimal` representing the amount to be deducted from the account balance. It must be a non-negative value.

        Returns:
        - A `Tx` object representing the transaction. If the transaction is successful, the status will be `DONE`. If the transaction fails due to insufficient funds, the status will be `ERR` and a message will be provided.

        Raises:
        - No exceptions are raised by this method. However, it is important to ensure that the `amt` parameter is non-negative to avoid unexpected behavior.
        """
        pass

    @abstractmethod
    def rev(self, tx: Tx) -> bool:
        """
        Summary:
        Reverses a transaction.

        Description:
        The `rev` method reverses a previously processed transaction. It takes a `Tx` object as input and returns `True` if the reversal is successful, otherwise `False`.

        Args:
        - `tx`: A `Tx` object representing the transaction to be reversed.

        Returns:
        - A `bool` indicating whether the transaction was successfully reversed.

        Raises:
        - No exceptions are raised by this method.
        """
        pass

class Cash(Handler):
    """
    Summary: Manages account transactions using cash.

    Description: 
    The `Cash` class is a concrete implementation of the `Handler` abstract base class, designed to manage account transactions using cash. It provides methods for adding funds, processing transactions, reversing transactions, and refunding the account balance. This class is essential for financial applications where cash transactions need to be handled efficiently and accurately.

    Parameters:
    - `initial_bal`: A `Decimal` representing the initial balance of the account.

    Attributes:
    - `bal`: A `Decimal` representing the current balance of the account.
    """

    def __init__(self):
        self.bal: Decimal = Decimal('0.00')

    def add(self, amt: Decimal) -> None:
        """
        Summary:
        Adds a specified amount to the account balance.

        Description:
        The `add` method increases the account balance by a specified amount. This method is used to credit the account with funds, reflecting transactions such as deposits or income.

        Args:
        - `amt` (Decimal): The amount to be added to the account balance. Must be a positive decimal value.

        Returns:
        - None: This method does not return any value. It modifies the account balance in place.

        Raises:
        - ValueError: Raised if the amount is negative. Ensure that the amount is always positive to avoid this error.

        Examples:
        ```python
        # Create an account with an initial balance of 100
        account = Account(initial_balance=100)

        # Add 50 to the account balance
        account.add(Decimal('50'))

        # The account balance should now be 150
        print(account.bal)  # Output: 150
        ```
        """
        self.bal += amt

    def proc(self, amt: Decimal) -> Tx:
        """
        Summary:
        Processes a transaction by deducting the amount from the balance if sufficient funds are available.

        Description:
        The `proc` method processes a transaction by deducting the specified amount from the account balance if there are sufficient funds. If the balance is insufficient, it returns a transaction with an error status. This method is essential for managing account balances and tracking transactions.

        Args:
        - `amt`: A `Decimal` representing the amount to be deducted from the account balance. It must be a non-negative value.

        Returns:
        - A `Tx` object representing the transaction. If the transaction is successful, the status will be `DONE`. If the transaction fails due to insufficient funds, the status will be `ERR` and a message will be provided.

        Raises:
        - No exceptions are raised by this method. However, it is important to ensure that the `amt` parameter is non-negative to avoid unexpected behavior.
        """
        if self.bal >= amt:
            self.bal -= amt
            return Tx(id=f'C_{id(self)}', amt=amt, st=TxStatus.DONE, mth='cash')
        return Tx(id=f'C_{id(self)}', amt=amt, st=TxStatus.ERR, mth='cash', msg='insufficient')

    def rev(self, tx: Tx) -> bool:
        """
        Summary:
        Reverses a completed transaction by adding the transaction amount back to the account balance.

        Description:
        The `rev` method reverses a completed transaction by adding the transaction amount back to the account balance and updating the transaction status to `RET` (refunded). This method is useful when you need to undo a previously completed transaction.

        Args:
        - `tx`: A `Tx` object representing the transaction to be reversed. The transaction must have a status of `DONE`.

        Returns:
        - A `bool` indicating whether the transaction was successfully reversed. If the transaction status is not `DONE`, the method will return `False`.

        Raises:
        - No exceptions are raised by this method. However, it is important to ensure that the transaction status is `DONE` to avoid unexpected behavior.
        """
        if tx.st == TxStatus.DONE:
            self.bal += tx.amt
            tx.st = TxStatus.RET
            return True
        return False

    def ret(self) -> Decimal:
        """
        Summary:
        Refunds the current balance of the account.

        Description:
        The `ret` method refunds the entire balance of the account, returning the current balance and setting the account balance to zero. This method is useful for processing a full refund of an account.

        Returns:
        - A `Decimal` representing the refunded amount, which is the same as the current balance before the refund.

        Raises:
        - No exceptions are raised by this method.
        """
        tmp = self.bal
        self.bal = Decimal('0.00')
        return tmp