from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from decimal import Decimal

class TxStatus(Enum):
    """
    **TxStatus Enum Docstring:**

    **Summary:**
    Enum representing the status of a transaction.

    **Description:**
    The `TxStatus` enum is used to define the possible statuses of a transaction in a system.

    **Attributes:**
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
    **Tx Class Docstring:**

    **Summary:**
    Represents a transaction in the system.

    **Description:**
    The `Tx` class is used to model a transaction in a system.

    **Attributes:**
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
    **Handler Class Docstring:**

    **Summary:**
    Abstract base class for handling transactions.

    **Description:**
    The `Handler` class is an abstract base class designed to handle transactions. It defines two abstract methods: `proc` and `rev`. These methods must be implemented by any concrete subclass to process and reverse transactions, respectively.

    **Parameters:**
    - `initial_bal`: A `Decimal` representing the initial balance of the account.

    **Attributes:**
    - `bal`: A `Decimal` representing the current balance of the account.

    **Methods:**
    - `proc(amt: Decimal) -> Tx`: Processes a transaction and returns a `Tx` object.
    - `rev(tx: Tx) -> bool`: Reverses a transaction and returns a boolean indicating success.

    **Usage:**
    Concrete subclasses of `Handler` must implement the `proc` and `rev` methods to define the specific behavior for these operations.
    """

    @abstractmethod
    def proc(self, amt: Decimal) -> Tx:
        """
        **proc() Method Docstring:**

        **Summary:**
        Processes a transaction.

        **Description:**
        The `proc` method is used to process a transaction.

        **Args:**
        - `amt`: A `Decimal` representing the amount of the transaction.

        **Returns:**
        - A `Tx` object representing the processed transaction.

        **Raises:**
        - No exceptions are raised by this method.
        """
        pass

    @abstractmethod
    def rev(self, tx: Tx) -> bool:
        """
        **rev() Method Docstring:**

        **Summary:**
        Reverses a transaction.

        **Description:**
        The `rev` method is used to reverse a transaction.

        **Args:**
        - `tx`: A `Tx` object representing the transaction to be reversed.

        **Returns:**
        - A `bool` indicating whether the transaction was successfully reversed.

        **Raises:**
        - No exceptions are raised by this method.
        """
        pass

class Cash(Handler):
    """
    **Cash Class Docstring:**

    **Summary:**
    Manages account transactions using cash.

    **Description:**
    The `Cash` class is a concrete implementation of the `Handler` abstract base class, designed to manage account transactions using cash. It provides methods for adding funds, processing transactions, reversing transactions, and refunding the account balance.

    **Args:**
    - `initial_bal`: The initial balance of the account.

    **Returns:**
    - None: This class does not return any value. It manages the account balance and transactions in place.

    **Raises:**
    - ValueError: Raised if the amount is negative in the `add` and `proc` methods.

    **Methods:**
    - `add(amt: Decimal) -> None`: Adds a specified amount to the account balance.
    - `proc(amt: Decimal) -> Tx`: Processes a transaction by deducting the amount from the balance if sufficient funds are available.
    - `rev(tx: Tx) -> bool`: Reverses a completed transaction by adding the transaction amount back to the account balance.
    - `ret() -> Decimal`: Refunds the current balance of the account.
    """

    def __init__(self):
        self.bal: Decimal = Decimal('0.00')

    def add(self, amt: Decimal) -> None:
        """
        **add() Method Docstring:**

        **Summary:**
        Adds a specified amount to the account balance.

        **Description:**
        The `add` method increases the account balance by a specified amount.

        **Args:**
        - `amt` (Decimal): The amount to be added to the account balance. Must be a positive decimal value.

        **Returns:**
        - None: This method does not return any value. It modifies the account balance in place.

        **Raises:**
        - ValueError: Raised if the amount is negative.
        """
        self.bal += amt

    def proc(self, amt: Decimal) -> Tx:
        """
        **proc() Method Docstring:**

        **Summary:**
        Processes a transaction by deducting the amount from the balance if sufficient funds are available.

        **Description:**
        The `proc` method is used to process a transaction by deducting the specified amount from the account balance if there are sufficient funds.

        **Args:**
        - `amt`: A `Decimal` representing the amount to be deducted from the account balance.

        **Returns:**
        - A `Tx` object representing the transaction.

        **Raises:**
        - No exceptions are raised by this method.
        """
        if self.bal >= amt:
            self.bal -= amt
            return Tx(id=f'C_{id(self)}', amt=amt, st=TxStatus.DONE, mth='cash')
        return Tx(id=f'C_{id(self)}', amt=amt, st=TxStatus.ERR, mth='cash', msg='insufficient')

    def rev(self, tx: Tx) -> bool:
        """
        **rev() Method Docstring:**

        **Summary:**
        Reverses a completed transaction by adding the transaction amount back to the account balance.

        **Description:**
        The `rev` method is used to reverse a completed transaction.

        **Args:**
        - `tx`: A `Tx` object representing the transaction to be reversed.

        **Returns:**
        - A `bool` indicating whether the transaction was successfully reversed.

        **Raises:**
        - No exceptions are raised by this method.
        """
        if tx.st == TxStatus.DONE:
            self.bal += tx.amt
            tx.st = TxStatus.RET
            return True
        return False

    def ret(self) -> Decimal:
        """
        **ret() Method Docstring:**

        **Summary:**
        Refunds the current balance of the account.

        **Description:**
        The `ret` method is used to refund the entire balance of the account.

        **Returns:**
        - A `Decimal` representing the refunded amount.

        **Raises:**
        - No exceptions are raised by this method.
        """
        tmp = self.bal
        self.bal = Decimal('0.00')
        return tmp