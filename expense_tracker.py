#!/usr/bin/env python3
"""
Expenditure Analysis Tool - Main Entry Point
"""
import argparse
import sys
from pathlib import Path
from database import Database
from csv_parser import CSVParser
from categorizer import InteractiveCategorizer
from reports import Reporter
from settings import Settings
from tui.app import ExpenseTrackerApp


def import_csv(db: Database, csv_path: str):
    """Import CSV file into database"""
    if not Path(csv_path).exists():
        print(f"❌ Error: File '{csv_path}' not found.")
        return

    parser = CSVParser(db)
    print(f"\n📥 Importing transactions from {csv_path}...")

    imported, skipped = parser.import_transactions(csv_path)

    print(f"✅ Imported: {imported} new transactions")
    print(f"⏭️  Skipped: {skipped} duplicate transactions")


def setup_categories(db: Database):
    """Setup initial expense categories and accounts"""
    # Setup categories
    categorizer = InteractiveCategorizer(db)
    categorizer.setup_initial_categories()

    # Setup accounts
    print("\n🏦 Setting up default accounts...")

    default_accounts = [
        ("Main", "Primary account", True),  # (name, description, is_main)
        ("RevolutCHF", "Revolut CHF account", False),
        ("Wise", "Wise account", False),
        ("CHF Savings", "CHF savings account", False),
        ("CryptoUSD", "Crypto USD account", False),
        ("Cash Savings", "Cash savings", False),
        ("Stocks", "Stock investments", False)
    ]

    existing_accounts = db.get_accounts()
    if existing_accounts:
        print("📋 Accounts already exist. Skipping account setup.")
    else:
        for name, description, is_main in default_accounts:
            db.add_account(name, description, is_main)
            main_indicator = " [MAIN]" if is_main else ""
            print(f"  ✅ Added: {name}{main_indicator}")

        print(f"\n✨ Created {len(default_accounts)} accounts!")


def categorize(db: Database):
    """Interactively categorize expenses"""
    categorizer = InteractiveCategorizer(db)
    categorizer.categorize_expenses()


def show_monthly_report(db: Database, settings: Settings, num_months: int = None):
    """Show monthly spending report"""
    reporter = Reporter(db, settings)
    reporter.print_monthly_report(num_months)


def show_category_summary(db: Database, settings: Settings):
    """Show spending summary by category"""
    reporter = Reporter(db, settings)
    reporter.print_category_summary()


def list_categories(db: Database):
    """List all expense categories"""
    categorizer = InteractiveCategorizer(db)
    categorizer.display_categories()


def add_account(db: Database):
    """Interactively add a new account"""
    try:
        print("\n➕ Add new account")
        name = input("Account name: ").strip()
        if not name:
            print("❌ Account name cannot be empty.")
            return

        description = input("Description (optional): ").strip()

        is_main_input = input("Set as main account? (y/N): ").strip().lower()
        is_main = is_main_input == 'y'

        account = db.add_account(name, description, is_main)
        main_indicator = " [MAIN]" if is_main else ""
        print(f"✅ Account '{name}'{main_indicator} created with balance 0.00 CHF!")

    except (EOFError, KeyboardInterrupt):
        print("\n👋 Cancelled.")
    except Exception as e:
        print(f"❌ Error: {e}")


def list_accounts(db: Database):
    """List all accounts"""
    accounts = db.get_accounts()

    if not accounts:
        print("\n📋 No accounts found.")
        print("   Run 'add-account' to create one.")
        return

    print("\n📋 Accounts:")
    print("=" * 80)
    for account in accounts:
        main_indicator = " [MAIN]" if account.is_main else ""
        desc = f" - {account.description}" if account.description else ""
        print(f"  {account.name}{main_indicator}")
        print(f"    Balance: {account.balance:>10.2f} CHF{desc}")

        # Get and display last transaction
        last_txn = db.get_last_transaction_for_account(account)
        if last_txn:
            date_str = last_txn.date.strftime('%d.%m.%Y')
            # Determine transaction type and description
            if last_txn.is_transfer:
                if last_txn.account_id == account.id:
                    # Transfer out from this account
                    txn_type = "Transfer to"
                    other_account = last_txn.target_account.name if last_txn.target_account else "Unknown"
                    txn_desc = other_account
                else:
                    # Transfer into this account
                    txn_type = "Transfer from"
                    source_account = last_txn.account.name if last_txn.account else "Unknown"
                    txn_desc = source_account
            else:
                txn_type = "Credit" if last_txn.is_credit else "Debit"
                txn_desc = last_txn.description[:40] + "..." if len(last_txn.description) > 40 else last_txn.description

            print(f"    Last txn: {date_str} | {txn_type} | {last_txn.amount:.2f} CHF | {txn_desc}")
        else:
            print(f"    Last txn: No transactions")

        # Get and display last categorized transaction
        last_cat = db.get_last_categorized_for_account(account)
        if last_cat:
            date_str = last_cat.date.strftime('%d.%m.%Y')
            if last_cat.is_transfer:
                txn_type = "Transfer"
                if last_cat.target_account:
                    txn_desc = f"→ {last_cat.target_account.name}"
                else:
                    txn_desc = "Transfer"
            else:
                txn_type = last_cat.category.name if last_cat.category else "Unknown"
                txn_desc = last_cat.description[:30] + "..." if len(last_cat.description) > 30 else last_cat.description
            print(f"    Last cat:  {date_str} | {txn_type} | {last_cat.amount:.2f} CHF | {txn_desc}")
        else:
            print(f"    Last cat:  None categorized yet")
        print()
    print("=" * 80)


def delete_account(db: Database):
    """Delete an account with safety checks"""
    accounts = db.get_accounts()

    if not accounts:
        print("\n📋 No accounts found.")
        return

    print("\n🗑️  Delete account")
    print("\n📋 Available accounts:")
    for i, account in enumerate(accounts, 1):
        main_indicator = " [MAIN]" if account.is_main else ""
        print(f"  {i}. {account.name}{main_indicator}")
    print("  0. Cancel")

    try:
        choice = input("\nSelect account to delete: ").strip()
        if not choice or choice == '0':
            print("👋 Cancelled.")
            return

        choice_num = int(choice)
        if not (1 <= choice_num <= len(accounts)):
            print("❌ Invalid choice.")
            return

        account = accounts[choice_num - 1]

        # Safety checks
        if account.is_main:
            print(f"❌ Cannot delete main account '{account.name}'.")
            print("   Set another account as main first.")
            return

        # Check for expenses
        from database import Expense
        expense_count = db.session.query(Expense).filter_by(account_id=account.id).count()
        if expense_count > 0:
            print(f"❌ Cannot delete account '{account.name}'.")
            print(f"   It has {expense_count} associated transactions.")
            return

        # Confirm deletion
        confirm = input(f"⚠️  Delete account '{account.name}'? (y/N): ").strip().lower()
        if confirm != 'y':
            print("👋 Cancelled.")
            return

        if db.delete_account(account):
            print(f"✅ Account '{account.name}' deleted.")
        else:
            print(f"❌ Could not delete account '{account.name}'.")

    except (EOFError, KeyboardInterrupt):
        print("\n👋 Cancelled.")
    except ValueError:
        print("❌ Please enter a number.")
    except Exception as e:
        print(f"❌ Error: {e}")


def clear_transactions(db: Database):
    """Clear all transactions from the database"""
    from database import Expense

    transaction_count = db.session.query(Expense).count()

    if transaction_count == 0:
        print("\n📋 No transactions to clear.")
        return

    print(f"\n⚠️  WARNING: This will DELETE ALL {transaction_count} transactions!")
    print("   Account balances will be reset to 0.00 CHF")
    print("   This action CANNOT be undone.")

    confirm1 = input("\nType 'DELETE' to confirm: ").strip()
    if confirm1 != 'DELETE':
        print("👋 Cancelled.")
        return

    confirm2 = input("Are you absolutely sure? (yes/no): ").strip().lower()
    if confirm2 != 'yes':
        print("👋 Cancelled.")
        return

    try:
        db.clear_all_transactions(reset_balances=True)
        print(f"\n✅ Deleted {transaction_count} transactions and reset all account balances to 0.00 CHF")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def search_and_delete(db: Database):
    """Search for transactions and delete selected ones"""
    from database import Expense

    print("\n🔍 Search for transactions to delete")
    print("=" * 80)

    # Get search criteria
    print("\nSearch by (press Enter to skip):")
    description_search = input("  Description contains: ").strip()
    date_search = input("  Date (DD.MM.YYYY): ").strip()
    amount_search = input("  Amount (exact): ").strip()

    # Build query
    query = db.session.query(Expense)

    if description_search:
        query = query.filter(Expense.description.ilike(f'%{description_search}%'))

    if date_search:
        from datetime import datetime
        try:
            date_obj = datetime.strptime(date_search, '%d.%m.%Y').date()
            query = query.filter(Expense.date == date_obj)
        except ValueError:
            print("❌ Invalid date format. Use DD.MM.YYYY")
            return

    if amount_search:
        try:
            amount_float = float(amount_search)
            query = query.filter(Expense.amount == amount_float)
        except ValueError:
            print("❌ Invalid amount format")
            return

    # Get results
    results = query.order_by(Expense.date.desc()).all()

    if not results:
        print("\n❌ No transactions found matching your criteria.")
        return

    print(f"\n📋 Found {len(results)} transaction(s):")
    print("=" * 80)

    for i, expense in enumerate(results, 1):
        date_str = expense.date.strftime('%d.%m.%Y')
        txn_type = "Credit" if expense.is_credit else "Debit"
        category_name = expense.category.name if expense.category else "Uncategorized"
        if expense.is_transfer:
            if expense.target_account:
                category_name = f"Transfer → {expense.target_account.name}"
            else:
                category_name = "Transfer"

        print(f"\n  {i}. {date_str} | {txn_type} | {expense.amount:.2f} CHF | {category_name}")
        print(f"     {expense.description}")

    print("\n" + "=" * 80)

    # Select transactions to delete
    print("\nEnter transaction numbers to delete (comma-separated, e.g., '1,3,5')")
    print("Or type 'all' to delete all found transactions")
    selection = input("Your choice (or Enter to cancel): ").strip().lower()

    if not selection:
        print("👋 Cancelled.")
        return

    # Determine which transactions to delete
    to_delete = []
    if selection == 'all':
        to_delete = results
    else:
        try:
            indices = [int(x.strip()) for x in selection.split(',')]
            for idx in indices:
                if 1 <= idx <= len(results):
                    to_delete.append(results[idx - 1])
                else:
                    print(f"⚠️  Skipping invalid index: {idx}")
        except ValueError:
            print("❌ Invalid input format")
            return

    if not to_delete:
        print("❌ No valid transactions selected")
        return

    # Confirm deletion
    print(f"\n⚠️  You are about to delete {len(to_delete)} transaction(s).")
    print("   This will revert the balance changes.")
    confirm = input("Type 'yes' to confirm: ").strip().lower()

    if confirm != 'yes':
        print("👋 Cancelled.")
        return

    # Delete transactions
    deleted_count = 0
    for expense in to_delete:
        try:
            db.delete_expense(expense)
            deleted_count += 1
        except Exception as e:
            print(f"❌ Error deleting transaction: {e}")

    print(f"\n✅ Deleted {deleted_count} transaction(s) and reverted balances")


def set_balance(db: Database):
    """Set an account's balance manually"""
    from datetime import datetime

    accounts = db.get_accounts()

    if not accounts:
        print("\n📋 No accounts found.")
        print("   Run 'add-account' to create one.")
        return

    print("\n💰 Set account balance")
    print("\n📋 Available accounts:")
    for i, account in enumerate(accounts, 1):
        print(f"  {i}. {account.name} (Current: {account.balance:.2f} CHF)")
    print("  0. Cancel")

    try:
        choice = input("\nSelect account: ").strip()
        if not choice or choice == '0':
            print("👋 Cancelled.")
            return

        choice_num = int(choice)
        if not (1 <= choice_num <= len(accounts)):
            print("❌ Invalid choice.")
            return

        account = accounts[choice_num - 1]
        current_balance = account.balance

        balance_input = input(f"\nNew balance for '{account.name}' (current: {current_balance:.2f} CHF): ").strip()
        new_balance = float(balance_input)

        # Calculate difference
        difference = new_balance - current_balance

        if difference == 0:
            print("⚠️  No change in balance.")
            return

        # Ask for date
        date_input = input(f"Date for this adjustment (DD.MM.YYYY) [today]: ").strip()
        if date_input:
            adjustment_date = date_input
        else:
            adjustment_date = datetime.now().strftime("%d.%m.%Y")

        # Get or create "Inserted" category
        inserted_category = db.get_category_by_name("Inserted")
        if not inserted_category:
            inserted_category = db.add_category("Inserted", "Manual balance adjustments")

        # Create adjustment transaction
        is_credit = difference > 0  # Positive difference = credit (income)
        amount = abs(difference)

        description = f"Balance adjustment for {account.name}"

        db.add_expense(
            date=adjustment_date,
            description=description,
            amount=amount,
            is_credit=is_credit,
            category=inserted_category,
            account=account
        )

        print(f"✅ Balance for '{account.name}' updated from {current_balance:.2f} to {new_balance:.2f} CHF")
        print(f"   Created {'credit' if is_credit else 'debit'} transaction of {amount:.2f} CHF on {adjustment_date} (category: Inserted)")

    except (EOFError, KeyboardInterrupt):
        print("\n👋 Cancelled.")
    except ValueError:
        print("❌ Please enter a valid number.")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Expenditure Analysis Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import CSV file
  %(prog)s import statement.csv

  # Set up expense categories
  %(prog)s setup

  # Categorize uncategorized expenses
  %(prog)s categorize

  # Show monthly report
  %(prog)s report

  # Show category summary
  %(prog)s summary

  # List categories
  %(prog)s list-categories
        """
    )

    parser.add_argument(
        'command',
        choices=['import', 'setup', 'categorize', 'report', 'summary', 'list-categories',
                 'add-account', 'list-accounts', 'delete-account', 'set-balance', 'clear-transactions',
                 'search-delete', 'tui'],
        help='Command to execute'
    )

    parser.add_argument(
        'file',
        nargs='?',
        help='CSV file to import (required for import command)'
    )

    parser.add_argument(
        '--months',
        type=int,
        default=None,
        help='Number of months to show in report (default: all)'
    )

    parser.add_argument(
        '--db',
        default='expenses.db',
        help='Database file path (default: expenses.db)'
    )

    args = parser.parse_args()

    # Initialize database and settings
    db = Database(args.db)
    settings = Settings()

    try:
        if args.command == 'import':
            if not args.file:
                print("❌ Error: Please specify a CSV file to import.")
                parser.print_help()
                sys.exit(1)
            import_csv(db, args.file)

        elif args.command == 'setup':
            setup_categories(db)

        elif args.command == 'categorize':
            categorize(db)

        elif args.command == 'report':
            show_monthly_report(db, settings, args.months)

        elif args.command == 'summary':
            show_category_summary(db, settings)

        elif args.command == 'list-categories':
            list_categories(db)

        elif args.command == 'add-account':
            add_account(db)

        elif args.command == 'list-accounts':
            list_accounts(db)

        elif args.command == 'delete-account':
            delete_account(db)

        elif args.command == 'set-balance':
            set_balance(db)

        elif args.command == 'clear-transactions':
            clear_transactions(db)

        elif args.command == 'search-delete':
            search_and_delete(db)

        elif args.command == 'tui':
            app = ExpenseTrackerApp(db, settings)
            app.run()

    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
