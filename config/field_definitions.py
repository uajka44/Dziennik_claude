"""
Definicje pól formularza - centralne miejsce zarządzania strukturą formularza
"""

class FormField:
    """Klasa reprezentująca pojedyncze pole formularza"""

    def __init__(self, name, display_name, editable=True, field_type="text", options=None, default_value=None):
        self.name = name  # Nazwa wewnętrzna (kolumna w bazie)
        self.display_name = display_name  # Nazwa wyświetlana w UI
        self.editable = editable  # Czy pole jest edytowalne
        self.field_type = field_type  # Typ pola: text, multiline, checkbox, readonly
        self.options = options  # Opcje dodatkowe (np. dla dropdowna)
        self.default_value = default_value  # Wartość domyślna

    def __str__(self):
        return f"{self.display_name} ({self.name}): {self.field_type}, editable={self.editable}"


# Definicja pól tekstowych
TEXT_FIELDS = [
    FormField("ticket", "Ticket", editable=False),
    FormField("type", "Typ", editable=False),
    FormField("volume", "Wolumen", editable=False),
    FormField("symbol", "Symbol", editable=False),
    FormField("open_price", "Cena otwarcia", editable=False),
    FormField("sl", "SL", editable=True),
    FormField("sl_opening", "SL (opening)", editable=False),
    FormField("profit_points", "Profit", editable=False),
    FormField("setup", "Setup", editable=True),
    FormField("uwagi", "Uwagi", editable=True, field_type="multiline"),
    FormField("blad", "Błąd", editable=True, field_type="multiline"),
    FormField("trends", "TrendS", editable=True),
    FormField("trendl", "TrendL", editable=True),
    FormField("interwal", "interwal", editable=True),
    FormField("setup_param1", "param 1", editable=True),
    FormField("setup_param2", "param 2", editable=True)
]

# Definicja pól typu checkbox
CHECKBOX_FIELDS = [
    FormField("nieutrzymalem", "Nieutrzymalem", field_type="checkbox"),
    FormField("niedojscie", "Niedojście", field_type="checkbox"),
    FormField("wybicie", "Wybicie", field_type="checkbox"),
    FormField("strefa_oporu", "Strefa oporu", field_type="checkbox"),
    FormField("zdrugiejstrony", "zdrugiejstrony", field_type="checkbox"),
    FormField("ucieczka", "Ucieczka", field_type="checkbox"),
    FormField("Korekta", "korekta", field_type="checkbox"),
    FormField("chcetrzymac", "chcetrzymac", field_type="checkbox"),
    FormField("be", "BE", field_type="checkbox"),
    FormField("skalp", "Skalp", field_type="checkbox")
]

# Kombinowane pole wszystkich pól dla łatwiejszego dostępu
ALL_FIELDS = {}
for field in TEXT_FIELDS + CHECKBOX_FIELDS:
    ALL_FIELDS[field.name] = field

# Definicja kolumn wyświetlanych w tabeli
COLUMNS = ["open_time"] + [field.name for field in TEXT_FIELDS + CHECKBOX_FIELDS]

# Definicja nagłówków kolumn tabeli
COLUMN_HEADERS = {
    "open_time": "Data i czas",
    **{field.name: field.display_name for field in TEXT_FIELDS + CHECKBOX_FIELDS}
}

# Definicja szerokości kolumn tabeli
COLUMN_WIDTHS = {
    "open_time": 150,
    "ticket": 80,
    "type": 80,
    "volume": 80,
    "symbol": 80,
    "open_price": 90,
    "sl": 80,
    "sl_opening": 80,
    "profit_points": 90,
    "setup": 100,
    "uwagi": 150,
    "blad": 150,
    "trends": 80,
    "trendl": 80
}

# Domyślna szerokość dla checkboxów
for field in CHECKBOX_FIELDS:
    if field.name not in COLUMN_WIDTHS:
        COLUMN_WIDTHS[field.name] = 50

# Definicja wyrównania kolumn tabeli
COLUMN_ALIGNMENTS = {
    "ticket": "center"
}

# Domyślne wyrównanie dla checkboxów
for field in CHECKBOX_FIELDS:
    COLUMN_ALIGNMENTS[field.name] = "center"

# Definicja skrótów dla pola Setup - przeniesione do config/setup_config.py
# Używaj get_setup_config().get_shortcut_mapping() zamiast tego słownika
SETUP_SHORTCUTS = {
    # Te skróty zostały przeniesione do setup_config.py
    # Zostają tutaj dla kompatybilności wstecznej, ale używaj nowego systemu
}
