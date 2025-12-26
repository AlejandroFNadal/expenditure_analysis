"""
CSV parser for bank statement imports
"""
import csv
from typing import List, Dict
from database import Database


class CSVParser:
    def __init__(self, db: Database):
        self.db = db

    def parse_zkb_statement(self, csv_path: str) -> List[Dict]:
        """
        Parse ZKB (Zürcher Kantonalbank) CSV statement
        Returns list of parsed transactions

        Handles grouped transactions where a parent transaction is followed by
        sub-transactions with empty dates that show the breakdown.
        Only imports the detailed sub-transactions, skipping the parent summary.
        """
        transactions = []
        last_date = None

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            # ZKB uses semicolon delimiter
            # Read all rows into a list to allow look-ahead
            rows = list(csv.DictReader(f, delimiter=';'))

        # Process rows with look-ahead capability
        i = 0
        while i < len(rows):
            row = rows[i]

            # Extract relevant fields
            date = row.get('Date', '').strip()
            description = row.get('Booking text', '').strip()
            debit = row.get('Debit CHF', '').strip()
            credit = row.get('Credit CHF', '').strip()
            reference = row.get('ZKB reference', '').strip()
            amount_details = row.get('Amount details', '').strip()

            # Handle sub-transactions (no date, but has amount_details)
            if not date and amount_details:
                # This is a grouped sub-transaction
                # Use last_date and amount from "Amount details" field
                if last_date:
                    date = last_date
                    amount = float(amount_details)
                    is_credit = False  # Grouped transactions are typically expenses

                    transactions.append({
                        'date': date,
                        'description': description,
                        'amount': amount,
                        'is_credit': is_credit,
                        'reference': reference
                    })
                i += 1
                continue

            # Skip rows without date or amount
            if not date or (not debit and not credit):
                i += 1
                continue

            # Check if this is a parent transaction (next row is a sub-transaction)
            is_parent = False
            if i + 1 < len(rows):
                next_row = rows[i + 1]
                next_date = next_row.get('Date', '').strip()
                next_amount_details = next_row.get('Amount details', '').strip()
                # If next row has no date but has amount_details, current row is a parent
                if not next_date and next_amount_details:
                    is_parent = True

            # Update last_date for potential grouped transactions
            last_date = date

            # Skip parent transactions (we'll import the detailed sub-transactions instead)
            if is_parent:
                i += 1
                continue

            # Regular transaction - not a parent
            is_credit = bool(credit and not debit)
            amount = float(credit) if is_credit else float(debit)

            transactions.append({
                'date': date,
                'description': description,
                'amount': amount,
                'is_credit': is_credit,
                'reference': reference
            })

            i += 1

        # Reverse to get chronological order (oldest first)
        # CSV is in reverse order (newest first)
        return list(reversed(transactions))

    def import_transactions(self, csv_path: str) -> tuple[int, int]:
        """
        Import transactions from CSV into database
        Returns: (imported_count, skipped_count)
        """
        # Get or create main account
        main_account = self.db.get_main_account()
        if not main_account:
            print("⚠️  No main account found. Creating 'Main Account'...")
            main_account = self.db.add_account("Main Account", "Primary account", is_main=True)

        transactions = self.parse_zkb_statement(csv_path)
        imported = 0
        skipped = 0
        skipped_transactions = []

        for trans in transactions:
            # Check if transaction already exists
            if self.db.expense_exists(
                trans['date'],
                trans['description'],
                trans['amount']
            ):
                skipped += 1
                skipped_transactions.append(trans)
                continue

            # Try to auto-categorize
            category = self.db.find_category_by_description(trans['description'], trans['amount'], trans['is_credit'])

            # Try to auto-detect transfer
            target_account = self.db.find_transfer_by_description(trans['description'], main_account)
            is_transfer = target_account is not None

            # Add to database
            self.db.add_expense(
                date=trans['date'],
                description=trans['description'],
                amount=trans['amount'],
                is_credit=trans['is_credit'],
                category=category if not is_transfer else None,
                reference=trans['reference'],
                account=main_account,
                is_transfer=is_transfer,
                target_account=target_account
            )
            imported += 1

        # Show skipped transactions
        if skipped_transactions:
            print(f"\n📋 Skipped {skipped} duplicate transactions:")
            print("-" * 80)
            for trans in skipped_transactions:
                trans_type = "Credit" if trans['is_credit'] else "Debit"
                print(f"  {trans['date']} | {trans_type:6s} | {trans['amount']:>8.2f} CHF | {trans['description'][:50]}")
            print("-" * 80)

        return imported, skipped


if __name__ == "__main__":
    # Test CSV parsing
    db = Database()
    parser = CSVParser(db)

    # Test parsing (update path as needed)
    transactions = parser.parse_zkb_statement("Account statement 20251223110554.csv")
    print(f"Parsed {len(transactions)} transactions")
    for i, trans in enumerate(transactions[:5], 1):
        print(f"{i}. {trans['date']} - {trans['description']}: {trans['amount']} CHF")

    db.close()
