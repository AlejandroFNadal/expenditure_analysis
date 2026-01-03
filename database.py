"""
Database setup and management for expenditure analysis using SQLAlchemy
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, func, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, date as date_type
from typing import Optional, List

Base = declarative_base()


class Account(Base):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    is_main = Column(Boolean, default=False)
    balance = Column(Float, default=0.0)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    expenses = relationship("Expense", foreign_keys="Expense.account_id", back_populates="account")
    transfers_to = relationship("Expense", foreign_keys="Expense.target_account_id", back_populates="target_account")

    def __repr__(self):
        return f"<Account(name='{self.name}', is_main={self.is_main})>"


class ExpenseCategory(Base):
    __tablename__ = 'expense_categories'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    expenses = relationship("Expense", back_populates="category")
    indicators = relationship("CategoryIndicator", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ExpenseCategory(name='{self.name}')>"


class Expense(Base):
    __tablename__ = 'expenses'

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default='CHF')
    is_credit = Column(Boolean, default=False)
    reference = Column(String)
    category_id = Column(Integer, ForeignKey('expense_categories.id'))
    account_id = Column(Integer, ForeignKey('accounts.id'))
    is_transfer = Column(Boolean, default=False)
    target_account_id = Column(Integer, ForeignKey('accounts.id'))
    imported_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("ExpenseCategory", back_populates="expenses")
    account = relationship("Account", foreign_keys=[account_id], back_populates="expenses")
    target_account = relationship("Account", foreign_keys=[target_account_id], back_populates="transfers_to")

    __table_args__ = (
        Index('idx_expenses_date', 'date'),
        Index('idx_expenses_category', 'category_id'),
        Index('idx_expenses_account', 'account_id'),
    )

    def __repr__(self):
        return f"<Expense(date='{self.date}', description='{self.description}', amount={self.amount})>"


class CategoryIndicator(Base):
    __tablename__ = 'category_indicators'

    id = Column(Integer, primary_key=True)
    pattern = Column(String, nullable=False)
    amount = Column(Float, nullable=True)  # Optional: match specific amount
    is_credit = Column(Boolean, nullable=True)  # None=both, True=credit only, False=debit only
    category_id = Column(Integer, ForeignKey('expense_categories.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("ExpenseCategory", back_populates="indicators")

    def __repr__(self):
        amount_str = f", amount={self.amount}" if self.amount else ""
        credit_str = ""
        if self.is_credit is not None:
            credit_str = f", credit_only" if self.is_credit else f", debit_only"
        return f"<CategoryIndicator(pattern='{self.pattern}'{amount_str}{credit_str})>"


class TransferIndicator(Base):
    __tablename__ = 'transfer_indicators'

    id = Column(Integer, primary_key=True)
    pattern = Column(String, nullable=False)
    source_account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    target_account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    source_account = relationship("Account", foreign_keys=[source_account_id])
    target_account = relationship("Account", foreign_keys=[target_account_id])

    def __repr__(self):
        return f"<TransferIndicator(pattern='{self.pattern}')>"


class Database:
    def __init__(self, db_path: str = "expenses.db"):
        # Validate db_path is a string
        if not isinstance(db_path, str):
            raise TypeError(
                f"db_path must be a string, not {type(db_path).__name__}. "
                f"Got: {db_path!r}"
            )

        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def add_category(self, name: str, description: str = "") -> ExpenseCategory:
        """Add a new expense category"""
        category = ExpenseCategory(name=name, description=description)
        self.session.add(category)
        self.session.commit()
        return category

    def get_categories(self) -> List[ExpenseCategory]:
        """Get all expense categories"""
        return self.session.query(ExpenseCategory).order_by(ExpenseCategory.name).all()

    def get_category_by_name(self, name: str) -> Optional[ExpenseCategory]:
        """Get category by name"""
        return self.session.query(ExpenseCategory).filter_by(name=name).first()

    def add_account(self, name: str, description: str = "", is_main: bool = False) -> Account:
        """Add a new account"""
        # If setting as main, unset any existing main account
        if is_main:
            existing_main = self.get_main_account()
            if existing_main:
                existing_main.is_main = False

        account = Account(name=name, description=description, is_main=is_main)
        self.session.add(account)
        self.session.commit()
        return account

    def get_accounts(self) -> List[Account]:
        """Get all accounts"""
        return self.session.query(Account).order_by(Account.name).all()

    def get_main_account(self) -> Optional[Account]:
        """Get the main account"""
        return self.session.query(Account).filter_by(is_main=True).first()

    def get_account_by_name(self, name: str) -> Optional[Account]:
        """Get account by name"""
        return self.session.query(Account).filter_by(name=name).first()

    def get_last_transaction_for_account(self, account: Account) -> Optional[Expense]:
        """
        Get the most recent transaction for an account
        Considers both expenses from the account and transfers to the account
        """
        last_expense = self.session.query(Expense).filter(
            (Expense.account_id == account.id) | (Expense.target_account_id == account.id)
        ).order_by(Expense.date.desc()).first()
        return last_expense

    def get_last_categorized_for_account(self, account: Account) -> Optional[Expense]:
        """
        Get the most recent categorized transaction for an account
        Considers both categorized expenses and transfers
        """
        last_categorized = self.session.query(Expense).filter(
            Expense.account_id == account.id,
            (Expense.category_id.isnot(None)) | (Expense.is_transfer == True)
        ).order_by(Expense.date.desc()).first()
        return last_categorized

    def set_main_account(self, account: Account):
        """Set an account as the main account"""
        # Unset any existing main account
        existing_main = self.get_main_account()
        if existing_main:
            existing_main.is_main = False

        account.is_main = True
        self.session.commit()

    def update_account_balance(self, account: Account, balance: float):
        """
        Set an account's balance by creating a balance adjustment transaction
        """
        current_balance = self.get_account_balance(account)
        difference = balance - current_balance

        if difference == 0:
            return  # No change needed

        # Create a balance adjustment transaction
        is_credit = difference > 0
        amount = abs(difference)

        # Get or create "Inserted" category for balance adjustments
        inserted_category = self.get_category_by_name("Inserted")
        if not inserted_category:
            inserted_category = self.add_category("Inserted", "Manual balance adjustments")

        # Add adjustment transaction
        self.add_expense(
            date=date_type.today(),
            description=f"Balance adjustment for {account.name}",
            amount=amount,
            is_credit=is_credit,
            category=inserted_category,
            account=account
        )

    def delete_account(self, account: Account) -> bool:
        """
        Delete an account with safety checks
        Returns True if deleted, False if prevented
        """
        # Prevent deleting main account
        if account.is_main:
            return False

        # Check if account has expenses
        expense_count = self.session.query(Expense).filter_by(account_id=account.id).count()
        if expense_count > 0:
            return False

        self.session.delete(account)
        self.session.commit()
        return True

    def add_expense(self, date, description: str, amount: float,
                    is_credit: bool = False, category: Optional[ExpenseCategory] = None,
                    reference: str = "", account: Optional[Account] = None,
                    is_transfer: bool = False, target_account: Optional[Account] = None) -> Expense:
        """Add a new expense. Date can be string (DD.MM.YYYY) or date object"""
        # Convert string date to date object if needed
        if isinstance(date, str):
            date = datetime.strptime(date, '%d.%m.%Y').date()

        expense = Expense(
            date=date,
            description=description,
            amount=amount,
            is_credit=is_credit,
            category=category,
            reference=reference,
            account=account,
            is_transfer=is_transfer,
            target_account=target_account
        )
        self.session.add(expense)
        self.session.commit()
        return expense

    def update_expense(self, expense: Expense, new_amount: Optional[float] = None,
                      new_description: Optional[str] = None, new_category: Optional[ExpenseCategory] = None) -> Expense:
        """Update an existing expense

        Args:
            expense: The expense to update
            new_amount: New amount (if provided)
            new_description: New description (if provided)
            new_category: New category (if provided)
        """
        if new_amount is not None:
            expense.amount = new_amount

        if new_description is not None:
            expense.description = new_description

        if new_category is not None:
            expense.category = new_category

        self.session.commit()
        return expense

    def add_category_indicator(self, pattern: str, category: ExpenseCategory, amount: Optional[float] = None, is_credit: Optional[bool] = None):
        """Add a text pattern (and optionally amount and credit/debit type) that indicates a category

        Args:
            pattern: Text pattern to match in description
            category: Category to assign
            amount: Optional amount to match
            is_credit: None=match both credits and debits, True=credits only, False=debits only
        """
        indicator = CategoryIndicator(pattern=pattern.upper(), category=category, amount=amount, is_credit=is_credit)
        self.session.add(indicator)
        try:
            self.session.commit()
        except:
            self.session.rollback()

    def find_category_by_description(self, description: str, amount: Optional[float] = None, is_credit: Optional[bool] = None) -> Optional[ExpenseCategory]:
        """
        Find a category based on text patterns and optionally amount and credit/debit type
        Priority: Rules with amount > Rules without amount, then by longest pattern

        Args:
            description: Transaction description to match
            amount: Optional amount to match
            is_credit: Whether the transaction is a credit (True) or debit (False)
        """
        description_upper = description.upper()

        # Query indicators ordered by priority: amount-based rules first, then longest pattern
        indicators = self.session.query(CategoryIndicator).order_by(
            CategoryIndicator.amount.isnot(None).desc(),  # Rules with amount first
            func.length(CategoryIndicator.pattern).desc()  # Then longest pattern
        ).all()

        for ind in indicators:
            # Check if pattern matches
            if ind.pattern not in description_upper:
                continue

            # If indicator has amount requirement, check if it matches
            if ind.amount is not None:
                if amount is None or abs(amount - ind.amount) > 0.01:  # Allow small rounding differences
                    continue

            # If indicator has credit/debit requirement, check if it matches
            if ind.is_credit is not None:
                if is_credit is None or ind.is_credit != is_credit:
                    continue

            # Found a match - return it (already in priority order)
            return ind.category

        return None

    def add_transfer_indicator(self, pattern: str, source_account: Account, target_account: Account):
        """Add a text pattern that indicates a transfer between accounts"""
        indicator = TransferIndicator(
            pattern=pattern.upper(),
            source_account=source_account,
            target_account=target_account
        )
        self.session.add(indicator)
        try:
            self.session.commit()
        except:
            self.session.rollback()

    def find_transfer_by_description(self, description: str, source_account: Account) -> Optional[Account]:
        """
        Find a transfer target account based on text patterns in the description
        Returns the target account if a match is found
        """
        description_upper = description.upper()

        # Get all indicators for this source account and find matches
        indicators = self.session.query(TransferIndicator).filter_by(
            source_account_id=source_account.id
        ).all()
        matches = [(ind, len(ind.pattern)) for ind in indicators if ind.pattern in description_upper]

        if matches:
            # Return target account with longest matching pattern
            best_match = max(matches, key=lambda x: x[1])
            return best_match[0].target_account
        return None

    def get_uncategorized_expenses(self) -> List[Expense]:
        """Get all expenses without a category and not transfers, in chronological order"""
        return self.session.query(Expense).filter(
            Expense.category_id.is_(None),
            Expense.is_transfer == False
        ).order_by(Expense.date.asc()).all()

    def get_all_expenses(self, order_desc: bool = True) -> List[Expense]:
        """Get all expenses ordered by date"""
        query = self.session.query(Expense)
        if order_desc:
            return query.order_by(Expense.date.desc()).all()
        return query.order_by(Expense.date.asc()).all()

    def search_expenses(self, term: str) -> List[Expense]:
        """Search expenses by description (case-insensitive)"""
        return self.session.query(Expense).filter(
            Expense.description.ilike(f'%{term}%')
        ).order_by(Expense.date.desc()).all()

    def get_recent_expenses(self, limit: int = 5) -> List[Expense]:
        """Get the most recent expenses"""
        return self.session.query(Expense).order_by(
            Expense.date.desc()
        ).limit(limit).all()

    def get_expenses_with_balance(self, expenses: List[Expense], order_desc: bool = True) -> List[tuple]:
        """
        Calculate running balance after each transaction.
        Starts from zero and applies each transaction chronologically.

        Args:
            expenses: List of Expense objects to calculate balances for
            order_desc: If True, return in descending date order (newest first)

        Returns:
            List of (Expense, float) tuples with balance after each transaction
        """
        if not expenses:
            return []

        # Sort expenses chronologically (oldest first) for calculation
        sorted_expenses = sorted(expenses, key=lambda e: (e.date, e.id))

        # Start all account balances at zero
        account_balances = {}

        # Calculate balance after each transaction
        result = []
        for expense in sorted_expenses:
            if expense.account_id:
                # Initialize account balance if not seen before
                if expense.account_id not in account_balances:
                    account_balances[expense.account_id] = 0.0
                if expense.target_account_id and expense.target_account_id not in account_balances:
                    account_balances[expense.target_account_id] = 0.0

                # Apply this transaction
                if expense.is_transfer and expense.target_account_id:
                    account_balances[expense.account_id] -= expense.amount
                    account_balances[expense.target_account_id] += expense.amount
                    balance_after = account_balances[expense.account_id]
                elif expense.is_credit:
                    # Credit: add to balance
                    account_balances[expense.account_id] += expense.amount
                    balance_after = account_balances[expense.account_id]
                else:
                    # Debit: subtract from balance
                    account_balances[expense.account_id] -= expense.amount
                    balance_after = account_balances[expense.account_id]

                result.append((expense, balance_after))
            else:
                # No account associated - show 0
                result.append((expense, 0.0))

        # Return in requested order
        if order_desc:
            return list(reversed(result))
        return result

    def get_account_balance(self, account: Account) -> float:
        """
        Calculate current balance for a specific account from all transactions

        Args:
            account: The account to calculate balance for

        Returns:
            float: Current balance based on all transactions

        TODO: Optimize this with SQL aggregation query for better performance with large datasets
        """
        # Get all transactions involving this account
        expenses = self.session.query(Expense).filter(
            (Expense.account_id == account.id) | (Expense.target_account_id == account.id)
        ).order_by(Expense.date.asc(), Expense.id.asc()).all()

        if not expenses:
            return 0.0

        balance = 0.0
        for expense in expenses:
            if expense.account_id == account.id:
                # This account is the source
                if expense.target_account_id:
                    # Transfer: always subtract from source
                    balance -= expense.amount
                else:
                    # Regular transaction: check is_credit
                    if expense.is_credit:
                        balance += expense.amount
                    else:
                        balance -= expense.amount
            elif expense.target_account_id == account.id:
                # This account is the target: always add
                balance += expense.amount

        return balance

    def update_expense_category(self, expense: Expense, category: ExpenseCategory):
        """Update the category of an expense"""
        expense.category = category
        self.session.commit()

    def delete_expense(self, expense: Expense):
        """Delete an expense"""
        self.session.delete(expense)
        self.session.commit()

    def get_monthly_report(self):
        """Get spending by category per month"""
        from sqlalchemy import func, case

        query = self.session.query(
            func.strftime('%Y-%m', Expense.date).label('month'),
            ExpenseCategory.name.label('category'),
            func.sum(
                case(
                    (Expense.is_credit == True, Expense.amount),
                    else_=-Expense.amount
                )
            ).label('total')
        ).outerjoin(ExpenseCategory).group_by('month', ExpenseCategory.name).order_by('month desc', 'total desc')

        return query.all()

    def expense_exists(self, date, description: str, amount: float) -> bool:
        """Check if an expense already exists (to avoid duplicates). Date can be string or date object"""
        # Convert string date to date object if needed
        if isinstance(date, str):
            date = datetime.strptime(date, '%d.%m.%Y').date()

        count = self.session.query(Expense).filter_by(
            date=date,
            description=description,
            amount=amount
        ).count()
        return count > 0

    def clear_all_transactions(self):
        """Delete all transactions from the database"""
        self.session.query(Expense).delete()
        self.session.commit()

    def close(self):
        """Close database connection"""
        self.session.close()


if __name__ == "__main__":
    # Test database creation
    db = Database()
    print("Database schema created successfully with SQLAlchemy!")
    db.close()
