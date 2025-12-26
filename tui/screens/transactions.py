"""
Transactions screen with vim-style navigation and categorization
"""
from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import Header, Footer, Static, Input, Button, ListView, ListItem, Label
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
from database import Database, Expense, ExpenseCategory
from settings import Settings
from tui.widgets.transaction_list import TransactionList


class CategorySelectModal(ModalScreen[ExpenseCategory]):
    """Modal for selecting a category"""

    def __init__(self, db: Database, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.categories = []

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        self.categories = self.db.get_categories()

        yield Container(
            Static("[bold]Select Category[/bold]", id="modal-title"),
            ListView(
                *[ListItem(Label(cat.name)) for cat in self.categories],
                id="category-list"
            ),
            Horizontal(
                Button("Cancel", variant="default", id="cancel"),
                Button("New Category", variant="primary", id="new"),
                id="modal-buttons"
            ),
            id="category-modal"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "new":
            # For now, dismiss with None. Future: show new category dialog
            self.dismiss(None)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle category selection"""
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self.categories):
            self.dismiss(self.categories[idx])


class SearchModal(ModalScreen[str]):
    """Modal for searching transactions"""

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Container(
            Static("[bold]Search Transactions[/bold]", id="modal-title"),
            Input(placeholder="Enter search term...", id="search-input"),
            Horizontal(
                Button("Cancel", variant="default", id="cancel"),
                Button("Search", variant="primary", id="search"),
                id="modal-buttons"
            ),
            id="search-modal"
        )

    def on_mount(self) -> None:
        """Focus input when modal opens"""
        self.query_one("#search-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "search":
            search_input = self.query_one("#search-input", Input)
            self.dismiss(search_input.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input"""
        self.dismiss(event.value)


class ConfirmModal(ModalScreen[bool]):
    """Modal for confirming actions"""

    def __init__(self, message: str, **kwargs):
        super().__init__(**kwargs)
        self.message = message

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Container(
            Static("[bold red]Confirm[/bold red]", id="modal-title"),
            Static(self.message, id="confirm-message"),
            Horizontal(
                Button("Cancel", variant="default", id="cancel"),
                Button("Confirm", variant="error", id="confirm"),
                id="modal-buttons"
            ),
            id="confirm-modal"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "cancel":
            self.dismiss(False)
        elif event.button.id == "confirm":
            self.dismiss(True)


class TransactionsScreen(Screen):
    """Transactions list screen with vim navigation"""

    BINDINGS = [
        Binding("j", "nav_down", "Down", show=False),
        Binding("k", "nav_up", "Up", show=False),
        Binding("g", "nav_top", "Top", show=False),
        Binding("G", "nav_bottom", "Bottom", show=False),
        Binding("c", "categorize", "Categorize", show=True),
        Binding("d", "delete", "Delete", show=True),
        Binding("u", "filter_uncategorized", "Uncategorized", show=True),
        Binding("a", "show_all", "Show All", show=True),
        Binding("slash", "search", "Search", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("escape", "back", "Back", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("question_mark", "help", "Help", show=False),
    ]

    def __init__(self, db: Database, settings: Settings, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.settings = settings
        self.gg_pressed = False

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header()
        yield Container(
            Static("[bold cyan]Transactions[/bold cyan]", id="title"),
            TransactionList(self.db, id="transaction-list"),
            Static("j/k:nav c:categorize d:delete u:uncateg a:all /:search ESC:back", id="status-bar"),
            id="transactions-container"
        )
        yield Footer()

    def action_nav_down(self) -> None:
        """Navigate down (vim j)"""
        self.gg_pressed = False
        table = self.query_one("#transaction-list", TransactionList)
        table.move_cursor_down()

    def action_nav_up(self) -> None:
        """Navigate up (vim k)"""
        self.gg_pressed = False
        table = self.query_one("#transaction-list", TransactionList)
        table.move_cursor_up()

    def action_nav_top(self) -> None:
        """Navigate to top (vim gg - requires two presses)"""
        if self.gg_pressed:
            table = self.query_one("#transaction-list", TransactionList)
            table.jump_to_top()
            self.gg_pressed = False
        else:
            self.gg_pressed = True
            # Reset after a short delay
            self.set_timer(1.0, lambda: setattr(self, 'gg_pressed', False))

    def action_nav_bottom(self) -> None:
        """Navigate to bottom (vim G)"""
        self.gg_pressed = False
        table = self.query_one("#transaction-list", TransactionList)
        table.jump_to_bottom()

    async def action_categorize(self) -> None:
        """Categorize selected transaction"""
        table = self.query_one("#transaction-list", TransactionList)
        expense = table.get_selected_transaction()

        if not expense:
            self.notify("No transaction selected", severity="warning")
            return

        if expense.is_transfer:
            self.notify("Cannot categorize transfers", severity="warning")
            return

        if expense.category:
            self.notify(f"Already categorized as: {expense.category.name}", severity="information")

        # Show category selection modal
        category = await self.app.push_screen_wait(CategorySelectModal(self.db))

        if category:
            self.db.update_expense_category(expense, category)
            table.refresh_transactions()
            self.notify(f"Categorized as: {category.name}", severity="information")

    async def action_delete(self) -> None:
        """Delete selected transaction"""
        table = self.query_one("#transaction-list", TransactionList)
        expense = table.get_selected_transaction()

        if not expense:
            self.notify("No transaction selected", severity="warning")
            return

        # Show confirmation modal
        confirmed = await self.app.push_screen_wait(
            ConfirmModal(f"Delete transaction: {expense.description}?\nThis will revert balance changes.")
        )

        if confirmed:
            self.db.delete_expense(expense)
            table.refresh_transactions()
            self.notify("Transaction deleted", severity="information")

    def action_filter_uncategorized(self) -> None:
        """Show only uncategorized transactions"""
        table = self.query_one("#transaction-list", TransactionList)
        table.set_filter_uncategorized()
        self.notify("Showing uncategorized only", severity="information")

    def action_show_all(self) -> None:
        """Show all transactions"""
        table = self.query_one("#transaction-list", TransactionList)
        table.set_filter_all()
        self.notify("Showing all transactions", severity="information")

    async def action_search(self) -> None:
        """Search transactions"""
        search_term = await self.app.push_screen_wait(SearchModal())

        if search_term:
            table = self.query_one("#transaction-list", TransactionList)
            table.search(search_term)
            self.notify(f"Search: {search_term}", severity="information")

    def action_refresh(self) -> None:
        """Refresh transaction list"""
        table = self.query_one("#transaction-list", TransactionList)
        table.refresh_transactions()
        self.notify("Refreshed", severity="information")

    def action_back(self) -> None:
        """Go back to dashboard"""
        self.app.pop_screen()

    def action_help(self) -> None:
        """Show help"""
        self.app.push_screen("help")

    def action_quit(self) -> None:
        """Quit the application"""
        self.app.exit()
