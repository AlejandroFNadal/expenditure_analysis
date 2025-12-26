"""
Account list widget for displaying accounts with balances
"""
from textual.widgets import Static
from rich.table import Table
from database import Database


class AccountList(Static):
    """Widget that displays a list of accounts with their balances"""

    def __init__(self, db: Database, **kwargs):
        super().__init__(**kwargs)
        self.db = db

    def on_mount(self) -> None:
        """Called when widget is mounted"""
        self.refresh_accounts()

    def refresh_accounts(self) -> None:
        """Refresh the account list from database"""
        accounts = self.db.get_accounts()

        # Create a rich table
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Account", style="bold cyan")
        table.add_column("Balance", justify="right", style="green")

        total = 0.0
        for account in accounts:
            # Highlight main account
            if account.is_main:
                name = f"[bold yellow]▶ {account.name}[/bold yellow]"
            else:
                name = f"  {account.name}"

            # Color balance based on positive/negative
            balance = account.balance
            total += balance
            if balance >= 0:
                balance_str = f"[green]{balance:,.2f} CHF[/green]"
            else:
                balance_str = f"[red]{balance:,.2f} CHF[/red]"

            table.add_row(name, balance_str)

        # Add total row
        table.add_row("", "")
        total_style = "green" if total >= 0 else "red"
        table.add_row(
            f"[bold]Total[/bold]",
            f"[bold {total_style}]{total:,.2f} CHF[/bold {total_style}]"
        )

        # Update the content
        self.update(table)
