"""
Dashboard screen showing accounts, stats, and recent transactions
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.containers import Container, Horizontal, Vertical
from rich.table import Table
from database import Database
from settings import Settings
from reports import Reporter
from tui.widgets.account_list import AccountList
from tui import keybindings


class QuickStats(Static):
    """Widget displaying quick statistics"""

    def __init__(self, db: Database, settings: Settings, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.settings = settings

    def on_mount(self) -> None:
        """Called when widget is mounted"""
        self.refresh_stats()

    def refresh_stats(self) -> None:
        """Refresh statistics"""
        # Get uncategorized count
        uncategorized = self.db.get_uncategorized_expenses()
        uncategorized_count = len(uncategorized)

        # Get category count
        categories = self.db.get_categories()
        category_count = len(categories)

        # Get current month spending
        reporter = Reporter(self.db, self.settings)
        monthly_data = reporter.get_monthly_spending()

        # Get latest period
        current_month_total = 0.0
        if monthly_data:
            latest_period = max(monthly_data.keys())
            period_data = monthly_data[latest_period]
            current_month_total = sum(period_data.values())

        # Create stats table
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Stat", style="bold")
        table.add_column("Value", justify="right")

        # Uncategorized
        if uncategorized_count > 0:
            table.add_row("Uncategorized:", f"[yellow]{uncategorized_count}[/yellow]")
        else:
            table.add_row("Uncategorized:", f"[green]{uncategorized_count}[/green]")

        # This month
        if current_month_total >= 0:
            table.add_row("This period:", f"[green]{current_month_total:,.2f} CHF[/green]")
        else:
            table.add_row("This period:", f"[red]{current_month_total:,.2f} CHF[/red]")

        # Categories
        table.add_row("Categories:", f"{category_count}")

        self.update(table)


class RecentTransactions(Static):
    """Widget displaying recent transactions"""

    def __init__(self, db: Database, **kwargs):
        super().__init__(**kwargs)
        self.db = db

    def on_mount(self) -> None:
        """Called when widget is mounted"""
        self.refresh_transactions()

    def refresh_transactions(self) -> None:
        """Refresh recent transactions"""
        recent = self.db.get_recent_expenses(limit=10)

        # Create table
        table = Table(box=None, padding=(0, 1))
        table.add_column("Date", width=10, style="cyan")
        table.add_column("Description", width=30)
        table.add_column("Amount", width=12, justify="right")
        table.add_column("Category", width=15)

        for expense in recent:
            date_str = expense.date.strftime('%d.%m.%Y')

            # Truncate description
            desc = expense.description[:28] + "..." if len(expense.description) > 30 else expense.description

            # Format amount
            if expense.is_credit:
                amount_str = f"[green]+{expense.amount:.2f}[/green]"
            else:
                amount_str = f"[red]-{expense.amount:.2f}[/red]"

            # Format category
            if expense.is_transfer:
                if expense.target_account:
                    cat_str = f"→ {expense.target_account.name}"
                else:
                    cat_str = "Transfer"
            elif expense.category:
                cat_str = expense.category.name
            else:
                cat_str = "[yellow]Uncateg.[/yellow]"

            table.add_row(date_str, desc, amount_str, cat_str)

        self.update(table)


class DashboardScreen(Screen):
    """Main dashboard screen"""

    BINDINGS = [
        ("t", "show_transactions", "Transactions"),
        ("m", "toggle_balances", "Toggle Balances"),
        ("r", "refresh", "Refresh"),
        ("q", "quit", "Quit"),
        ("question_mark", "help", "Help"),
    ]

    def __init__(self, db: Database, settings: Settings, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.settings = settings

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header()
        yield Container(
            Static("[bold cyan]Expense Tracker - Dashboard[/bold cyan]", id="title"),
            Horizontal(
                Vertical(
                    Static("[bold]ACCOUNTS[/bold]", classes="section-title"),
                    AccountList(self.db, id="accounts"),
                    id="left-panel"
                ),
                Vertical(
                    Static("[bold]QUICK STATS[/bold]", classes="section-title"),
                    QuickStats(self.db, self.settings, id="stats"),
                    Static("[bold]RECENT TRANSACTIONS[/bold]", classes="section-title"),
                    RecentTransactions(self.db, id="recent"),
                    id="right-panel"
                ),
                id="main-content"
            ),
            id="dashboard-container"
        )
        yield Footer()

    def action_show_transactions(self) -> None:
        """Switch to transactions screen"""
        # Screen switching will be handled by the app
        self.app.push_screen("transactions")

    def action_refresh(self) -> None:
        """Refresh all data"""
        accounts = self.query_one("#accounts", AccountList)
        accounts.refresh_accounts()

        stats = self.query_one("#stats", QuickStats)
        stats.refresh_stats()

        recent = self.query_one("#recent", RecentTransactions)
        recent.refresh_transactions()

        self.notify("Data refreshed")

    def action_toggle_balances(self) -> None:
        """Toggle visibility of account balances"""
        accounts = self.query_one("#accounts", AccountList)
        accounts.toggle_balance_visibility()

    def action_help(self) -> None:
        """Show help"""
        self.app.push_screen("help")

    def action_quit(self) -> None:
        """Quit the application"""
        self.app.exit()
