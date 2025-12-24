"""
Configuration settings for expenditure analysis
"""
import json
import os
from typing import Dict, Any


class Settings:
    DEFAULT_SETTINGS = {
        'month_end_day': 25,  # Month period starts on the 25th
        'currency': 'CHF',
        'date_format': '%d.%m.%Y'
    }

    def __init__(self, config_file: str = 'config.json'):
        self.config_file = config_file
        self.settings = self._load_settings()

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from config file or create with defaults"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            self._save_settings(self.DEFAULT_SETTINGS)
            return self.DEFAULT_SETTINGS.copy()

    def _save_settings(self, settings: Dict[str, Any]):
        """Save settings to config file"""
        with open(self.config_file, 'w') as f:
            json.dump(settings, indent=2, fp=f)

    def get(self, key: str, default=None):
        """Get a setting value"""
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        """Set a setting value and save"""
        self.settings[key] = value
        self._save_settings(self.settings)

    @property
    def month_end_day(self) -> int:
        """Get the day of month when the month period starts"""
        return self.settings.get('month_end_day', 25)

    @month_end_day.setter
    def month_end_day(self, day: int):
        """Set the day of month when the month period starts"""
        if 1 <= day <= 28:  # Ensure it works for all months
            self.set('month_end_day', day)
        else:
            raise ValueError("Month start day must be between 1 and 28")

    @property
    def currency(self) -> str:
        """Get the default currency"""
        return self.settings.get('currency', 'CHF')

    @property
    def date_format(self) -> str:
        """Get the date format"""
        return self.settings.get('date_format', '%d.%m.%Y')


if __name__ == "__main__":
    # Test settings
    settings = Settings()
    print(f"Month ends on day: {settings.month_end_day}")
    print(f"Currency: {settings.currency}")
    print(f"Date format: {settings.date_format}")
