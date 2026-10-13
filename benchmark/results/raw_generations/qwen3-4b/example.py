from decimal import Decimal
from datetime import datetime, timedelta
from models.product import Item
from vending_machine import Sys, SysErr

def main():
    """
    Summary: Executes a demonstration of the vending machine system with sample items and transactions.
    Description: Initializes the system, lists items, adds $2.00, and purchases the first item.
    Raises: SysErr - For any operation failure (e.g., invalid positions, unavailable items). Handle exceptions to ensure robust execution.
    """
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