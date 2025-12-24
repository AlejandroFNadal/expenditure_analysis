"""
Interactive categorization CLI
"""
from database import Database, ExpenseCategory, Expense, Account
from typing import List, Optional


class InteractiveCategorizer:
    def __init__(self, db: Database):
        self.db = db
        self.categories_cache: List[ExpenseCategory] = []

    def refresh_categories(self):
        """Refresh the categories cache"""
        self.categories_cache = self.db.get_categories()

    def display_categories(self):
        """Display available categories"""
        self.refresh_categories()
        if not self.categories_cache:
            print("\n📋 No categories defined yet.")
            return

        print("\n📋 Available categories:")
        for i, cat in enumerate(self.categories_cache, 1):
            desc = f" - {cat.description}" if cat.description else ""
            print(f"  {i}. {cat.name}{desc}")

    def select_category(self, expense: Expense) -> Optional[ExpenseCategory]:
        """
        Let user select a category for an expense
        Returns the selected category or None
        Returns 'TRANSFER' string to indicate transfer selection
        """
        self.refresh_categories()

        if not self.categories_cache:
            print("\n⚠️  No categories available. Let's create one first.")
            return self.create_new_category()

        # Format date for display
        date_str = expense.date.strftime('%d.%m.%Y') if hasattr(expense.date, 'strftime') else str(expense.date)

        print(f"\n💰 Expense: {expense.description}")
        print(f"   Amount: {expense.amount} CHF")
        print(f"   Date: {date_str}")
        print("\n📋 Which category does this belong to?")

        for i, cat in enumerate(self.categories_cache, 1):
            print(f"  {i}. {cat.name}")
        print(f"  {len(self.categories_cache) + 1}. Create new category")
        print(f"  {len(self.categories_cache) + 2}. Mark as transfer")
        print(f"  0. Skip this expense")

        while True:
            try:
                choice = input("\nYour choice: ").strip()
                if not choice:
                    continue

                choice_num = int(choice)

                if choice_num == 0:
                    return None
                elif choice_num == len(self.categories_cache) + 1:
                    return self.create_new_category()
                elif choice_num == len(self.categories_cache) + 2:
                    return 'TRANSFER'  # Special marker for transfer
                elif 1 <= choice_num <= len(self.categories_cache):
                    return self.categories_cache[choice_num - 1]
                else:
                    print("❌ Invalid choice. Please try again.")
            except ValueError:
                print("❌ Please enter a number.")
            except (EOFError, KeyboardInterrupt):
                print("\n\n👋 Exiting categorization...")
                raise  # Re-raise to trigger outer handler

    def create_new_category(self) -> Optional[ExpenseCategory]:
        """Create a new expense category"""
        try:
            print("\n➕ Create new category")
            name = input("Category name: ").strip()
            if not name:
                print("❌ Category name cannot be empty.")
                return None

            description = input("Description (optional): ").strip()

            category = self.db.add_category(name, description)
            print(f"✅ Category '{name}' created!")
            return category
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Exiting categorization...")
            raise  # Re-raise to trigger outer handler

    def ask_for_pattern(self, expense: Expense, category: ExpenseCategory) -> Optional[tuple]:
        """
        Ask user what text pattern indicates this category
        Returns tuple of (pattern, amount) or None
        """
        print(f"\n🔍 What text in '{expense.description}' told you this was '{category.name}'?")
        print("   (This will help auto-categorize similar expenses in the future)")

        try:
            pattern = input("Pattern (or press Enter to skip): ").strip()
            if not pattern:
                print("⚠️  No pattern saved. You'll be asked again for similar expenses.")
                return None

            # Validate pattern exists in description
            if pattern.upper() not in expense.description.upper():
                print(f"⚠️  Warning: '{pattern}' not found in description. Saving anyway...")

            # Ask if they want to include the amount
            include_amount = input(f"Also match amount {expense.amount:.2f} CHF? (y/N): ").strip().lower()
            amount = expense.amount if include_amount == 'y' else None

            return (pattern, amount)
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Exiting categorization...")
            raise  # Re-raise to trigger outer handler

    def select_transfer_target(self, expense: Expense, source_account: Account) -> Optional[Account]:
        """
        Let user select a target account for a transfer
        Returns the selected account or None
        """
        accounts = self.db.get_accounts()

        # Filter out source account
        target_accounts = [acc for acc in accounts if acc.id != source_account.id]

        if not target_accounts:
            print("\n⚠️  No other accounts available for transfer.")
            print("   Create additional accounts using 'add-account' command.")
            return None

        print(f"\n💸 Transfer: {expense.description}")
        print(f"   Amount: {expense.amount} CHF")
        print(f"   From: {source_account.name}")
        print("\n📋 Transfer to which account?")

        for i, acc in enumerate(target_accounts, 1):
            balance_info = f" (Balance: {acc.balance:.2f} CHF)" if acc.balance != 0 else ""
            print(f"  {i}. {acc.name}{balance_info}")
        print(f"  0. Cancel (not a transfer)")

        while True:
            try:
                choice = input("\nYour choice: ").strip()
                if not choice:
                    continue

                choice_num = int(choice)

                if choice_num == 0:
                    return None
                elif 1 <= choice_num <= len(target_accounts):
                    return target_accounts[choice_num - 1]
                else:
                    print("❌ Invalid choice. Please try again.")
            except ValueError:
                print("❌ Please enter a number.")
            except (EOFError, KeyboardInterrupt):
                print("\n\n👋 Exiting categorization...")
                raise  # Re-raise to trigger outer handler

    def ask_for_transfer_pattern(self, expense: Expense, source_account: Account, target_account: Account) -> Optional[str]:
        """
        Ask user what text pattern indicates this transfer
        Returns the pattern or None
        """
        print(f"\n🔍 What text in '{expense.description}' indicates transfer to '{target_account.name}'?")
        print("   (This will help auto-detect similar transfers in the future)")

        try:
            pattern = input("Pattern (or press Enter to skip): ").strip()
            if not pattern:
                print("⚠️  No pattern saved. You'll be asked again for similar transfers.")
                return None

            # Validate pattern exists in description
            if pattern.upper() not in expense.description.upper():
                print(f"⚠️  Warning: '{pattern}' not found in description. Saving anyway...")

            return pattern
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Exiting categorization...")
            raise  # Re-raise to trigger outer handler

    def categorize_expenses(self):
        """
        Main interactive loop to categorize uncategorized expenses
        """
        uncategorized = self.db.get_uncategorized_expenses()

        if not uncategorized:
            print("\n✨ All expenses are categorized!")
            return

        print(f"\n📊 Found {len(uncategorized)} uncategorized expenses")
        print("=" * 60)

        categorized_count = 0
        skipped_count = 0

        try:
            for expense in uncategorized:
                # Get source account (should be set from import)
                source_account = expense.account
                if not source_account:
                    source_account = self.db.get_main_account()

                # Try to auto-detect transfer first
                if source_account:
                    auto_target = self.db.find_transfer_by_description(expense.description, source_account)
                    if auto_target:
                        expense.is_transfer = True
                        expense.target_account = auto_target
                        # Update account balances
                        source_account.balance -= expense.amount
                        auto_target.balance += expense.amount
                        self.db.session.commit()
                        categorized_count += 1
                        print(f"\n✅ Auto-detected transfer: {expense.description[:50]}... → {auto_target.name}")
                        continue

                # Try to auto-categorize
                auto_category = self.db.find_category_by_description(expense.description, expense.amount)
                if auto_category:
                    self.db.update_expense_category(expense, auto_category)
                    categorized_count += 1
                    print(f"\n✅ Auto-categorized: {expense.description[:50]}... → {auto_category.name}")
                    continue

                # Ask user to categorize or mark as transfer
                category = self.select_category(expense)

                if category is None:
                    skipped_count += 1
                    continue

                # Handle transfer selection
                if category == 'TRANSFER':
                    if not source_account:
                        print("❌ Cannot create transfer: no source account.")
                        skipped_count += 1
                        continue

                    target_account = self.select_transfer_target(expense, source_account)
                    if target_account:
                        # Mark as transfer
                        expense.is_transfer = True
                        expense.target_account = target_account
                        # Update balances
                        source_account.balance -= expense.amount
                        target_account.balance += expense.amount
                        self.db.session.commit()
                        categorized_count += 1

                        # Ask for pattern
                        pattern = self.ask_for_transfer_pattern(expense, source_account, target_account)
                        if pattern:
                            self.db.add_transfer_indicator(pattern, source_account, target_account)
                            print(f"💾 Transfer pattern '{pattern}' saved ({source_account.name} → {target_account.name})")
                    else:
                        skipped_count += 1
                    continue

                # Update expense with category
                self.db.update_expense_category(expense, category)
                categorized_count += 1

                # Ask for pattern to help with future auto-categorization
                pattern_result = self.ask_for_pattern(expense, category)
                if pattern_result:
                    pattern, amount = pattern_result
                    self.db.add_category_indicator(pattern, category, amount)
                    amount_str = f" + amount {amount:.2f} CHF" if amount else ""
                    print(f"💾 Pattern '{pattern}'{amount_str} saved for category '{category.name}'")

        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 Categorization interrupted. All progress has been saved.")

        print("\n" + "=" * 60)
        print(f"✅ Categorized: {categorized_count}")
        print(f"⏭️  Skipped: {skipped_count}")

    def setup_initial_categories(self):
        """Helper to set up initial categories"""
        self.refresh_categories()
        if self.categories_cache:
            print("\n📋 Categories already exist. Skipping setup.")
            return

        print("\n🎯 Setting up default expense categories...")

        default_categories = [
            "Salary",
            "HealthInsuranceReturns",
            "Food",
            "Social Life",
            "Self Development",
            "Transportation",
            "Culture",
            "Household",
            "Apparel",
            "Health",
            "Education",
            "Gift",
            "Other",
            "Tech",
            "Coffee working",
            "Services",
            "Holidays",
            "Investing",
            "Sporty Social Life",
            "Social Transportation",
            "Donation",
            "Entertainment",
            "Corrections",
            "Inserted"
        ]

        for name in default_categories:
            self.db.add_category(name)
            print(f"  ✅ Added: {name}")

        print(f"\n✨ Created {len(default_categories)} categories!")


if __name__ == "__main__":
    # Test interactive categorizer
    db = Database()
    categorizer = InteractiveCategorizer(db)
    categorizer.setup_initial_categories()
    categorizer.display_categories()
    db.close()
