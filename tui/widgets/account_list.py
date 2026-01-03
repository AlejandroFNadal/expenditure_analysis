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
        self.balances_hidden = True  # Start with balances hidden for privacy

    def on_mount(self) -> None:
        """Called when widget is mounted"""
        self.refresh_accounts()

    def toggle_balance_visibility(self) -> None:
        """Toggle between showing and hiding balances"""
        self.balances_hidden = not self.balances_hidden
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
            balance = self.db.get_account_balance(account)
            total += balance

            if self.balances_hidden:
                # Show masked balance with same color coding
                color = "green" if balance >= 0 else "red"
                balance_str = f"[{color}]##### CHF[/{color}]"
            else:
                if balance >= 0:
                    balance_str = f"[green]{balance:,.2f} CHF[/green]"
                else:
                    balance_str = f"[red]{balance:,.2f} CHF[/red]"

            table.add_row(name, balance_str)

        # Add total row
        table.add_row("", "")
        total_style = "green" if total >= 0 else "red"

        if self.balances_hidden:
            total_str = f"[bold {total_style}]##### CHF[/bold {total_style}]"
        else:
            total_str = f"[bold {total_style}]{total:,.2f} CHF[/bold {total_style}]"

        table.add_row(
            f"[bold]Total[/bold]",
            total_str
        )

        # Update the content
        self.update(table)
