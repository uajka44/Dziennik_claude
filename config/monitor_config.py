"""
Konfiguracja monitora nowych zleceń
"""

# Domyślne ustawienia monitora
DEFAULT_MONITOR_SETTINGS = {
    "enabled": True,                    # Czy monitoring jest włączony
    "check_interval": 30,              # Interwał sprawdzania w sekundach
    "play_sound": True,                # Czy odgrywać dźwięk
    "show_console_log": True,          # Czy pokazywać logi w konsoli
    "auto_start": True                 # Czy automatycznie uruchamiać przy starcie aplikacji
}

# Minimalne i maksymalne wartości
MIN_CHECK_INTERVAL = 5      # Minimum 5 sekund
MAX_CHECK_INTERVAL = 300    # Maksimum 5 minut
