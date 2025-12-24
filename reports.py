"""
Reporting module for expense analysis
"""
from database import Database, Expense, ExpenseCategory
from settings import Settings
from utils import parse_date, get_custom_month_period, get_period_label
from collections import defaultdict
from typing import Dict, List, Tuple
from sqlalchemy import func, case


class Reporter:
    def __init__(self, db: Database, settings: Settings):
        self.db = db
        self.settings = settings

    def get_monthly_spending(self) -> Dict[str, Dict[str, float]]:
        """
        Get spending by category per custom month period
        Returns: {period: {category: total_amount}}
        Excludes transfers
        """
        all_expenses = self.db.session.query(Expense).filter(Expense.is_transfer == False).all()
        month_end_day = self.settings.month_end_day
        spending = defaultdict(lambda: defaultdict(float))

        for expense in all_expenses:
            # Get custom month period
            # expense.date is now a date object, convert to datetime for utils
            try:
                if isinstance(expense.date, str):
                    date = parse_date(expense.date, self.settings.date_format)
                else:
                    # Already a date object, convert to datetime
                    from datetime import datetime
                    date = datetime.combine(expense.date, datetime.min.time())
            except:
                continue  # Skip invalid dates

            period = get_custom_month_period(date, month_end_day)

            # Get category name (or 'Uncategorized')
            category_name = expense.category.name if expense.category else 'Uncategorized'

            # Calculate net amount (credits are positive, expenses are negative)
            amount = expense.amount if expense.is_credit else -expense.amount

            spending[period][category_name] += amount

        return dict(spending)

    def print_monthly_report(self, num_months: int = None):
        """
        Print monthly spending report
        """
        spending = self.get_monthly_spending()

        if not spending:
            print("\n📊 No expenses found to report.")
            return

        # Sort periods descending (most recent first)
        periods = sorted(spending.keys(), reverse=True)
        if num_months is not None:
            periods = periods[:num_months]

        print("\n" + "=" * 80)
        print("📊 MONTHLY SPENDING REPORT")
        print("=" * 80)

        for period in periods:
            period_label = get_period_label(period, self.settings.month_end_day)
            categories = spending[period]

            print(f"\n📅 {period_label}")
            print("-" * 80)

            # Sort categories by spending (highest first)
            sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)

            total = 0.0
            for category, amount in sorted_categories:
                total += amount
                print(f"  {category:30s}  {amount:>10.2f} CHF")

            print("-" * 80)
            print(f"  {'TOTAL':30s}  {total:>10.2f} CHF")

        print("\n" + "=" * 80)

    def print_category_summary(self):
        """
        Print summary by category across all time
        Excludes transfers
        """
        # Query total spending by category (exclude transfers)
        total_col = func.sum(
            case(
                (Expense.is_credit == True, Expense.amount),
                else_=-Expense.amount
            )
        ).label('total')

        query = self.db.session.query(
            ExpenseCategory.name.label('category'),
            total_col,
            func.count(Expense.id).label('count')
        ).outerjoin(ExpenseCategory).filter(
            Expense.is_transfer == False
        ).group_by(ExpenseCategory.name).order_by(total_col.desc())

        results = query.all()

        if not results:
            print("\n📊 No expenses found to report.")
            return

        print("\n" + "=" * 80)
        print("📊 SPENDING BY CATEGORY (All Time)")
        print("=" * 80)

        total_spending = 0.0
        for row in results:
            category = row.category if row.category else 'Uncategorized'
            amount = row.total
            count = row.count
            total_spending += amount
            print(f"  {category:30s}  {amount:>10.2f} CHF  ({count} transactions)")

        print("-" * 80)
        print(f"  {'TOTAL':30s}  {total_spending:>10.2f} CHF")
        print("=" * 80)


if __name__ == "__main__":
    # Test reporting
    db = Database()
    settings = Settings()
    reporter = Reporter(db, settings)

    print("Testing monthly report...")
    reporter.print_monthly_report()

    print("\n\nTesting category summary...")
    reporter.print_category_summary()

    db.close()
