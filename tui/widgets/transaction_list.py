"""
Transaction list widget with vim-style navigation
"""
from textual.widgets import DataTable
from typing import Optional, List
from database import Database, Expense


class TransactionList(DataTable):
    """DataTable widget for displaying transactions with vim navigation"""

    def __init__(self, db: Database, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.transactions: List[Expense] = []
        self.filter_mode = "all"  # all, uncategorized, search
        self.search_term = ""

    def on_mount(self) -> None:
        """Called when widget is mounted"""
        # Add columns
        self.add_column("Date", width=12)
        self.add_column("Description", width=40)
        self.add_column("Amount", width=12)
        self.add_column("Category", width=20)
        self.refresh_transactions()

    def refresh_transactions(self) -> None:
        """Refresh transactions from database based on filter mode"""
        # Clear existing rows
        self.clear()

        # Get transactions based on filter using database methods
        if self.filter_mode == "uncategorized":
            self.transactions = self.db.get_uncategorized_expenses()
        elif self.filter_mode == "search" and self.search_term:
            self.transactions = self.db.search_expenses(self.search_term)
        else:  # all
            self.transactions = self.db.get_all_expenses(order_desc=True)

        # Add rows
        for expense in self.transactions:
            self.add_transaction_row(expense)

    def add_transaction_row(self, expense: Expense) -> None:
        """Add a single transaction row to the table"""
        # Format date
        date_str = expense.date.strftime('%d.%m.%Y')

        # Format description (truncate if needed)
        description = expense.description[:38] + "..." if len(expense.description) > 40 else expense.description

        # Format amount with color
        amount = expense.amount
        if expense.is_credit:
            amount_str = f"[green]+{amount:.2f}[/green]"
        else:
            amount_str = f"[red]-{amount:.2f}[/red]"

        # Format category
        if expense.is_transfer:
            if expense.target_account:
                category_str = f"[cyan]→ {expense.target_account.name}[/cyan]"
            else:
                category_str = "[cyan]Transfer[/cyan]"
        elif expense.category:
            category_str = expense.category.name
        else:
            category_str = "[yellow]Uncategorized[/yellow]"

        # Add row
        self.add_row(date_str, description, amount_str, category_str)

    def get_selected_transaction(self) -> Optional[Expense]:
        """Get the currently selected transaction"""
        if not self.transactions:
            return None

        cursor_row = self.cursor_coordinate.row
        if 0 <= cursor_row < len(self.transactions):
            return self.transactions[cursor_row]
        return None

    def move_cursor_down(self) -> None:
        """Move cursor down (vim j)"""
        self.action_cursor_down()

    def move_cursor_up(self) -> None:
        """Move cursor up (vim k)"""
        self.action_cursor_up()

    def jump_to_top(self) -> None:
        """Jump to top of list (vim gg)"""
        if self.row_count > 0:
            self.move_cursor(row=0, column=0)

    def jump_to_bottom(self) -> None:
        """Jump to bottom of list (vim G)"""
        if self.row_count > 0:
            self.move_cursor(row=self.row_count - 1, column=0)

    def set_filter_uncategorized(self) -> None:
        """Filter to show only uncategorized transactions"""
        self.filter_mode = "uncategorized"
        self.refresh_transactions()

    def set_filter_all(self) -> None:
        """Show all transactions"""
        self.filter_mode = "all"
        self.search_term = ""
        self.refresh_transactions()

    def search(self, term: str) -> None:
        """Search transactions by description"""
        self.filter_mode = "search"
        self.search_term = term
        self.refresh_transactions()
