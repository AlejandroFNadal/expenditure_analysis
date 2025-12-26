"""
Main TUI application for the Expense Tracker
"""
from textual.app import App
from textual.screen import Screen
from textual.widgets import Static
from textual.containers import Container
from database import Database
from settings import Settings
from tui.screens.dashboard import DashboardScreen
from tui.screens.transactions import TransactionsScreen
from tui import keybindings


class HelpScreen(Screen):
    """Help screen showing keybindings"""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("q", "dismiss", "Close"),
    ]

    def __init__(self, help_text: str = None, **kwargs):
        super().__init__(**kwargs)
        self.help_text = help_text or keybindings.DASHBOARD_HELP

    def compose(self):
        """Create child widgets"""
        yield Container(
            Static("[bold cyan]Help[/bold cyan]", id="help-title"),
            Static(self.help_text, id="help-content"),
            Static("\n[dim]Press ESC or q to close[/dim]", id="help-footer"),
            id="help-container"
        )

    def action_dismiss(self) -> None:
        """Close the help screen"""
        self.app.pop_screen()


class ExpenseTrackerApp(App):
    """Main TUI application"""

    CSS = """
    Screen {
        background: $surface;
    }

    #title {
        padding: 1;
        text-align: center;
        background: $boost;
    }

    #dashboard-container {
        padding: 1;
    }

    #main-content {
        height: 100%;
    }

    #left-panel {
        width: 35%;
        padding: 1;
        border: solid $primary;
    }

    #right-panel {
        width: 65%;
        padding: 1;
        border: solid $primary;
    }

    .section-title {
        padding: 1 0;
        text-style: bold;
        color: $accent;
    }

    #accounts {
        height: auto;
        padding: 1;
    }

    #stats {
        height: auto;
        padding: 1;
    }

    #recent {
        height: 1fr;
        padding: 1;
    }

    #transactions-container {
        padding: 1;
    }

    #transaction-list {
        height: 1fr;
        margin: 1 0;
    }

    #status-bar {
        dock: bottom;
        background: $boost;
        padding: 0 1;
        color: $text-muted;
    }

    /* Modal styles */
    #category-modal, #search-modal, #confirm-modal {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }

    #modal-title {
        text-align: center;
        padding: 1;
        background: $boost;
    }

    #category-list {
        height: 20;
        margin: 1 0;
        border: solid $primary;
    }

    #search-input {
        margin: 1 0;
    }

    #confirm-message {
        padding: 2;
        text-align: center;
    }

    #modal-buttons {
        align: center middle;
        height: auto;
    }

    #modal-buttons Button {
        margin: 0 1;
    }

    /* Help screen */
    #help-container {
        width: 80;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 2;
        align: center middle;
    }

    #help-title {
        text-align: center;
        padding: 1;
        background: $boost;
    }

    #help-content {
        padding: 2;
        color: $text;
    }

    #help-footer {
        text-align: center;
        padding: 1;
    }

    DataTable {
        height: 100%;
    }

    DataTable > .datatable--cursor {
        background: $accent 20%;
    }

    DataTable > .datatable--hover {
        background: $accent 10%;
    }
    """

    SCREENS = {
        "dashboard": DashboardScreen,
        "help": HelpScreen,
    }

    def __init__(self, db: Database, settings: Settings):
        super().__init__()
        self.db = db
        self.settings = settings

    def on_mount(self) -> None:
        """Called when app is mounted"""
        self.title = "Expense Tracker"
        self.sub_title = "vim-style TUI"
        self.push_screen(DashboardScreen(self.db, self.settings))

    def action_push_screen_transactions(self) -> None:
        """Push transactions screen"""
        self.push_screen(TransactionsScreen(self.db, self.settings))

    def push_screen(self, screen, **kwargs):
        """Override push_screen to handle string screen names"""
        # Handle string-based screen names
        if screen == "transactions":
            screen = TransactionsScreen(self.db, self.settings)
        elif screen == "help":
            # Determine which help text to show based on current screen
            current_screen = self.screen
            if isinstance(current_screen, TransactionsScreen):
                help_text = keybindings.TRANSACTIONS_HELP
            else:
                help_text = keybindings.DASHBOARD_HELP
            screen = HelpScreen(help_text=help_text)

        return super().push_screen(screen, **kwargs)
