# Expenditure Analysis

## Overview
This project analyzes personal or business expenditures from account statements.

## Files
- `Account statement 20251223110554.csv` - Source data containing transaction records

## Purpose
Analyze spending patterns, categorize expenses, and generate insights from financial data.

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up expense categories:
   ```bash
   python expense_tracker.py setup
   ```

3. Import your CSV statement:
   ```bash
   python expense_tracker.py import "Account statement 20251223110554.csv"
   ```

4. Categorize expenses:
   ```bash
   python expense_tracker.py categorize
   ```

5. View reports:
   ```bash
   python expense_tracker.py report
   python expense_tracker.py summary
   ```

## Commands
- `import <file>` - Import CSV bank statement
- `setup` - Set up initial expense categories
- `categorize` - Interactively categorize uncategorized expenses
- `report` - Show monthly spending report (default: last 6 months)
- `summary` - Show total spending by category
- `list-categories` - List all expense categories

## Coding Standards
- **ALL imports must be at the top of the file** - Never put imports inside functions or in the middle of files
- Use SQLAlchemy for database operations
- Follow Python PEP 8 style guidelines

---
Generated with Claude Code
