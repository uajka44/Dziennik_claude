"""
Konfiguracja Stop Loss stałego dla różnych instrumentów
"""

# Wartości domyślne SL stałego dla poszczególnych instrumentów (w punktach)
DEFAULT_SL_VALUES = {
    "us30.cash": -20,
    "us30": -20,
    "us100.cash": -10,
    "us100": -10,
    "ger40.cash": -10,
    "ger40": -10,
    "XAUUSD": -5,  # Przykładowa wartość dla złota
}

# Dodatkowe aliasy dla instrumentów (w przypadku różnych formatów nazw)
INSTRUMENT_ALIASES = {
    "us30.cash": ["us30", "dow30", "dow jones"],
    "us100.cash": ["us100", "nasdaq100", "nasdaq"],
    "ger40.cash": ["ger40", "dax40", "dax"],
    "XAUUSD": ["xauusd", "gold", "zloto"],
}


def get_default_sl_for_instrument(instrument: str) -> float:
    """
    Zwraca domyślną wartość SL stałego dla instrumentu.
    
    Args:
        instrument: Nazwa instrumentu (np. "us30.cash", "ger40.cash")
        
    Returns:
        Wartość SL stałego w punktach (liczba ujemna dla BUY, dodatnia dla SELL)
    """
    if not instrument:
        return -10  # Wartość domyślna
    
    instrument_clean = instrument.strip().lower().replace('\x00', '')
    
    # Sprawdź bezpośrednie dopasowanie
    for key, value in DEFAULT_SL_VALUES.items():
        if instrument_clean == key.lower():
            return value
    
    # Sprawdź aliasy
    for base_instrument, aliases in INSTRUMENT_ALIASES.items():
        if instrument_clean in [alias.lower() for alias in aliases]:
            return DEFAULT_SL_VALUES.get(base_instrument, -10)
    
    # Wartość domyślna jeśli nie znaleziono
    return -10


def get_available_instruments_with_sl():
    """
    Zwraca słownik wszystkich dostępnych instrumentów z ich domyślnymi wartościami SL.
    
    Returns:
        Dict[str, float]: Słownik instrument -> domyślne SL
    """
    return DEFAULT_SL_VALUES.copy()


def update_sl_for_instrument(instrument: str, sl_value: float):
    """
    Aktualizuje domyślną wartość SL dla instrumentu.
    
    Args:
        instrument: Nazwa instrumentu
        sl_value: Nowa wartość SL
    """
    instrument_clean = instrument.strip().lower().replace('\x00', '')
    
    # Znajdź najbardziej pasujący klucz
    for key in DEFAULT_SL_VALUES.keys():
        if instrument_clean == key.lower():
            DEFAULT_SL_VALUES[key] = sl_value
            return
    
    # Jeśli nie znaleziono, dodaj nowy
    DEFAULT_SL_VALUES[instrument] = sl_value
