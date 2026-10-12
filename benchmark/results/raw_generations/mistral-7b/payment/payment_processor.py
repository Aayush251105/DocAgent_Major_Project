from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from decimal import Decimal

class TxStatus(Enum):
    """
    TxStatus
    ---------

    Enum representing the status of a transaction.

    The `TxStatus` enum is used to define the possible statuses of a transaction in a system. It includes four states: `WAIT` for pending transactions, `DONE` for completed transactions, `ERR` for failed transactions, and `RET` for refunded transactions. This enum helps in managing and tracking the state of transactions throughout their lifecycle.

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
    Tx
    ----

    Represents a transaction in the system.

    The `Tx` class is used to model a transaction in a system. It encapsulates essential details about a transaction, including its unique identifier, amount, status, method, and an optional message. This class is crucial for tracking and managing transactions within the system.

    - `id` (str): A string representing the unique identifier of the transaction. It must be a non-empty string.
    - `amt` (Decimal): A `Decimal` representing the amount of the transaction. It must be a non-negative value.
    - `st` (TxStatus): An instance of `TxStatus` representing the current status of the transaction. It must be one of the predefined statuses: `WAIT`, `DONE`, `ERR`, or `RET`.
    - `mth` (str): A string representing the method used for the transaction. It must be a non-empty string.
    - `msg` (Optional[str]): An optional string representing a message related to the transaction. It can be `None` or a non-empty string.
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
    """

    @abstractmethod
    def proc(self, amt: Decimal) -> Tx:
        """
        proc
        ------

        Processes a transaction and returns a `Tx` object representing the transaction.

        The `proc` method is used to process a transaction. It takes an amount as input and returns a `Tx` object representing the transaction. The specific implementation of this method is not provided in the given code component.

        - Args:
          - `amt`: A `Decimal` representing the amount of the transaction.

        - Returns:
          - A `Tx` object representing the processed transaction.

        Raises:
        - No exceptions are raised by this method.
        """
        pass

    @abstractmethod
    def rev(self, tx: Tx) -> bool:
        """
        rev
        ------

        Reverse a transaction and return a boolean indicating success.

        The `rev` method is used to reverse a transaction. It takes a `Tx` object as input and returns a boolean indicating whether the reversal was successful. The specific implementation of this method is not provided in the given code component.

        - Args:
          - `tx`: A `Tx` object representing the transaction to be reversed.

        - Returns:
          - A `bool` indicating whether the transaction was successfully reversed.

        Raises:
        - No exceptions are raised by this method.
        """
        pass

class Cash(Handler):
    '''
    class Cash(Handler):
        """
        Manages account transactions using cash.

        The `Cash` class manages account transactions using cash. It provides methods for adding funds, processing transactions, reversing transactions, and refunding the account balance. This class is essential for financial applications where cash transactions need to be handled efficiently and accurately.

        Attributes:
        - `bal` (Decimal): The current balance of the account.
        """

        def __init__(self):
            """
            Initializes an instance of the Cash class with an initial balance of 0.
            """
            self.bal = Decimal('0.00')

        def add(self, amt: Decimal) -> None:
            """
            Increases the account balance by a specified amount.

            Increases the account balance by a specified amount. This method is used to credit the account with funds, reflecting transactions such as deposits or income.

            Args:
            - `amt` (Decimal): The amount to be added to the account balance. Must be a positive decimal value.

            Returns:
            - None: This method does not return any value. It modifies the account balance in place.

            Raises:
            - ValueError: Raised if the amount is negative. Ensure that the amount is always positive to avoid this error.
            """
            self.bal += amt

        def proc(self, amt: Decimal) -> Tx:
            """
            Processes a transaction by deducting the amount from the balance if sufficient funds are available.

            Processes a transaction by deducting the specified amount from the account balance if there are sufficient funds. If the balance is insufficient, it returns a transaction with an error status. This method is essential for managing account balances and tracking transactions.

            - `amt` (Decimal): A `Decimal` representing the amount to be deducted from the account balance. It must be a non-negative value.

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
            Reverses a completed transaction by adding the transaction amount back to the account balance.

            Reverses a completed transaction. It adds the transaction amount back to the account balance and updates the transaction status to `RET` (refunded). This method is useful when you need to undo a previously completed transaction.

            - Args:
              - `tx`: A `Tx` object representing the transaction to be reversed. The transaction must have a status of `DONE`.

            - Returns:
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
            Refunds the entire balance of the account.

            Refunds the entire balance of the account. It returns the current balance and sets the account balance to zero. This method is useful when you need to process a full refund of an account.

            - Returns:
              - A `Decimal` representing the refunded amount. This will be the same as the current balance before the refund.

            Raises:
            - No exceptions are raised by this method.
            """
            tmp = self.bal
            self.bal = Decimal('0.00')
            return tmp
    '''

    def __init__(self):
        self.bal: Decimal = Decimal('0.00')

    def add(self, amt: Decimal) -> None:
        """
        add
        ------

        Increases the account balance by a specified amount.

        The `add` method increases the account balance by a specified amount. This method is used to credit the account with funds, reflecting transactions such as deposits or income.

        Args:
        - `amt` (Decimal): The amount to be added to the account balance. Must be a positive decimal value.

        Returns:
        - None: This method does not return any value. It modifies the account balance in place.

        Raises:
        - ValueError: Raised if the amount is negative. Ensure that the amount is always positive to avoid this error.
        """
        self.bal += amt

    def proc(self, amt: Decimal) -> Tx:
        """
        proc
        ------

        Processes a transaction by deducting the amount from the balance if sufficient funds are available.

        The `proc` method is used to process a transaction by deducting the specified amount from the account balance if there are sufficient funds. If the balance is insufficient, it returns a transaction with an error status. This method is essential for managing account balances and tracking transactions.

        - `amt` (Decimal): A `Decimal` representing the amount to be deducted from the account balance. It must be a non-negative value.

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
        rev
        ------

        Reverses a completed transaction by adding the transaction amount back to the account balance.

        The `rev` method is used to reverse a completed transaction. It adds the transaction amount back to the account balance and updates the transaction status to `RET` (refunded). This method is useful when you need to undo a previously completed transaction.

        - Args:
          - `tx`: A `Tx` object representing the transaction to be reversed. The transaction must have a status of `DONE`.

        - Returns:
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
        ret
        ------

        Refunds the entire balance of the account.

        The `ret` method is used to refund the entire balance of the account. It returns the current balance and sets the account balance to zero. This method is useful when you need to process a full refund of an account.

        - Returns:
          - A `Decimal` representing the refunded amount. This will be the same as the current balance before the refund.

        Raises:
        - No exceptions are raised by this method.
        """
        tmp = self.bal
        self.bal = Decimal('0.00')
        return tmp