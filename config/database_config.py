"""
Konfiguracja bazy danych
"""

# Ścieżka do głównej bazy danych
DB_PATH = r"C:\Users\anasy\AppData\Roaming\MetaQuotes\Terminal\7B8FFB3E490B2B8923BCC10180ACB2DC\MQL5\Files\multi_candles.db"
DB_PATH2 = r"C:\Users\Apollo\AppData\Roaming\MetaQuotes\Terminal\49CDDEAA95A409ED22BD2287BB67CB9C\MQL5\Files\multi_candles.db"


# Nazwy tabel
POSITIONS_TABLE = "positions"
CANDLES_TABLE_PREFIX = ""  # Tabele świeczkowe mają nazwy jak "ger40.cash", "us100.cash" etc.

# Instrumenty dostępne w systemie (w małych literach - znormalizowane)
AVAILABLE_INSTRUMENTS = [
    "ger40.cash",
    "us100.cash", 
    "us30.cash",
    "xauusd"
]

# Nazwa tabeli dla wyników kalkulacji TP
TP_RESULTS_TABLE = "tp_calculation_results"
