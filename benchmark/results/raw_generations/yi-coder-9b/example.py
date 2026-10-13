from decimal import Decimal
from datetime import datetime, timedelta
from models.product import Item
from vending_machine import Sys, SysErr

def main():
    '''
    ```python
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
        - `msg`: A string describing the error.

        Returns:
        - None: This exception does not return any value. It is used to raise an error.

        Raises:
        - None: This exception does not raise any additional exceptions. It is used to indicate that a system-level error has occurred.
        """
        def __init__(self, msg: str):
            self.msg = msg

        def __str__(self):
            return self.msg
    ```
    '''
    s = Sys()
    items = [Item(code='D1', label='Drink1', val=1.5, count=10, grp='d', exp=datetime.now() + timedelta(days=90)), Item(code='S1', label='Snack1', val=1.0, count=15, grp='s', exp=datetime.now() + timedelta(days=30)), Item(code='S2', label='Snack2', val=2.0, count=8, grp='s', exp=datetime.now() + timedelta(days=60))]
    for i, item in enumerate(items):
        s.store.put(item, i)
    try:
        print('Items:')
        for pos, item in s.ls():
            print(f'Pos {pos}: {item.label} - ${item.val:.2f}')
        pos = 0
        print('\nAdding $2.00...')
        s.add_money(Decimal('2.00'))
        item, ret = s.buy(pos)
        print(f'\nBought: {item.label}')
        if ret:
            print(f'Return: ${ret:.2f}')
        print('\nUpdated Items:')
        for pos, item in s.ls():
            print(f'Pos {pos}: {item.label} - ${item.val:.2f} (Count: {item.count})')
    except SysErr as e:
        print(f'Err: {str(e)}')
if __name__ == '__main__':
    main()