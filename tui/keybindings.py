"""
Centralized keybinding definitions for the TUI
"""

# Global keybindings available everywhere
GLOBAL_KEYS = {
    'q': 'quit',
    'question_mark': 'help',
    'escape': 'back',
}

# Dashboard screen keybindings
DASHBOARD_KEYS = {
    't': 'show_transactions',
    'r': 'refresh',
    'i': 'import_csv',
    'a': 'add_account',
}

# Transactions screen keybindings
TRANSACTIONS_KEYS = {
    'j': 'nav_down',
    'k': 'nav_up',
    'down': 'nav_down',
    'up': 'nav_up',
    'c': 'categorize',
    't': 'mark_transfer',
    'd': 'delete',
    'slash': 'search',
    'u': 'filter_uncategorized',
    'a': 'show_all',
    'n': 'next_search',
    'N': 'prev_search',
    'enter': 'view_details',
}

# Help text for each screen
DASHBOARD_HELP = """
Dashboard Keybindings:

Navigation:
  t - Show transactions list
  r - Refresh data

Actions:
  i - Import CSV (future)
  a - Add account (future)

Global:
  ? - Show this help
  q - Quit application
"""

TRANSACTIONS_HELP = """
Transactions Keybindings:

Navigation:
  j/k or ↓/↑ - Move down/up
  gg         - Jump to top
  G          - Jump to bottom
  Enter      - View details

Actions:
  c - Categorize transaction
  t - Mark as transfer
  d - Delete transaction

Filtering:
  / - Search transactions
  n - Next search result
  N - Previous search result
  u - Show only uncategorized
  a - Show all (clear filters)

Global:
  ESC - Back to Dashboard
  ?   - Show this help
  q   - Quit application
"""
