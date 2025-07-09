# FILTR MAGIC NUMBER 007 - DOKUMENTACJA

## Przegląd

Dodano nowy filtr "Magic Number 007" do aplikacji dziennika tradingowego, który pozwala na filtrowanie transakcji według wartości `magic_number`.

## Funkcjonalność

### Zachowanie filtra:
- **Zaznaczony (domyślnie)**: Pokazuje TYLKO trejdy z `magic_number = 7`
- **Odznaczony**: Ukrywa trejdy z `magic_number = 7` (pokazuje wszystkie pozostałe)

### Lokalizacja:
- Sekcja "Filtry" w głównym oknie
- Wiersz 2, kolumna 0-1
- Etykieta: "Filtr 007:"
- Checkbox: "Magic Number 007"

## Implementacja techniczna

### 1. Model danych (`database/models.py`)
```python
@dataclass
class Position:
    # ... istniejące pola ...
    magic_number: Optional[int] = None
```

### 2. Definicje pól (`config/field_definitions.py`)
```python
TEXT_FIELDS = [
    # ... istniejące pola ...
    FormField("magic_number", "Magic Number", editable=True)
]

COLUMN_WIDTHS = {
    # ... istniejące definicje ...
    "magic_number": 90
}
```

### 3. Interface użytkownika (`gui/data_viewer.py`)

#### Checkbox filtra:
```python
# Filtr 007 - Magic Number
ttk.Label(self.filter_frame, text="Filtr 007:").grid(row=2, column=0, padx=5, pady=5, sticky="w")

self.magic_007_filter_var = tk.BooleanVar(value=True)  # Domyślnie włączony
self.magic_007_checkbox = ttk.Checkbutton(
    self.filter_frame,
    text="Magic Number 007",
    variable=self.magic_007_filter_var,
    command=self.load_data
)
self.magic_007_checkbox.grid(row=2, column=1, padx=5, pady=5, sticky="w")
```

#### Logika filtrowania w `load_data()`:
```python
# Warunek dla filtra Magic Number 007
magic_007_filter_active = self.magic_007_filter_var.get()
if magic_007_filter_active:
    # Jeśli filtr 007 jest zaznaczony, pokazuj tylko trejdy z magic_number = 007
    where_conditions.append("magic_number = ?")
    base_params.append(7)
    print("Filtr 007 aktywny - pokazuję tylko trejdy z magic_number = 7")
else:
    # Jeśli filtr 007 jest odznaczony, ukryj trejdy z magic_number = 007
    where_conditions.append("(magic_number IS NULL OR magic_number != ?)")
    base_params.append(7)
    print("Filtr 007 nieaktywny - ukrywam trejdy z magic_number = 7")
```

### 4. Zapytania SQL

#### Z filtrem 007 (checkbox zaznaczony):
```sql
SELECT open_time, ticket, type, volume, symbol, open_price, sl, sl_opening, profit_points, setup, uwagi, blad, trends, trendl, interwal, setup_param1, setup_param2, magic_number, nieutrzymalem, niedojscie, wybicie, strefa_oporu, zdrugiejstrony, ucieczka, Korekta, chcetrzymac, be, skalp
FROM positions 
WHERE open_time BETWEEN ? AND ? AND magic_number = ?
ORDER BY open_time
```

#### Bez filtra 007 (checkbox odznaczony):
```sql
SELECT open_time, ticket, type, volume, symbol, open_price, sl, sl_opening, profit_points, setup, uwagi, blad, trends, trendl, interwal, setup_param1, setup_param2, magic_number, nieutrzymalem, niedojscie, wybicie, strefa_oporu, zdrugiejstrony, ucieczka, Korekta, chcetrzymac, be, skalp
FROM positions 
WHERE open_time BETWEEN ? AND ? AND (magic_number IS NULL OR magic_number != ?)
ORDER BY open_time
```

## Współpraca z innymi filtrami

Filtr 007 współpracuje z istniejącymi filtrami:
- **Instrumenty**: Można łączyć z wyborem konkretnych instrumentów
- **Setup**: Można łączyć z filtrem setupów
- **Zakres dat**: Standardowo ograniczony zakresem dat

Wszystkie filtry są łączone operatorem `AND`.

## Statystyki

Filtr 007 wpływa na wszystkie statystyki wyświetlane w aplikacji:
- Suma profitu
- Liczba transakcji  
- Wygrywające trejdy
- Przegrywające trejdy
- Winrate

## Wymagania bazy danych

### Kolumna magic_number

Aplikacja wymaga aby tabela `positions` miała kolumnę `magic_number`:

```sql
-- Jeśli kolumna nie istnieje, dodaj ją:
ALTER TABLE positions ADD COLUMN magic_number INTEGER;

-- Przykładowe dane testowe:
UPDATE positions SET magic_number = 7 WHERE ticket IN (123456, 789012);
UPDATE positions SET magic_number = 123 WHERE ticket IN (345678, 901234);
```

### Wartości magic_number:
- `7` lub `007` - transakcje przefiltrowane przez filtr 007
- `NULL` - transakcje bez przypisanego magic number
- Inne wartości - transakcje z innymi strategiami/robotami

## Testing

Uruchom test filtra:
```bash
python test_magic_filter.py
```

Test sprawdza:
1. ✅ Import wszystkich modułów
2. ✅ Definicje pól i kolumn
3. ✅ Model Position z magic_number
4. ✅ Interface DataViewer
5. ✅ Generowanie zapytań SQL
6. 🖥️ Opcjonalny test GUI

## Przykład użycia

1. **Uruchom aplikację**: `python main.py`
2. **Przejdź do zakładki**: "Przeglądarka danych"
3. **W sekcji Filtry** znajdź checkbox "Magic Number 007"
4. **Zaznacz checkbox**: Pokazuje tylko trejdy z magic_number = 7
5. **Odznacz checkbox**: Ukrywa trejdy z magic_number = 7
6. **Kliknij "Wyszukaj"**: Dane są automatycznie przefiltrowane

## Uwagi implementacyjne

- Filtr jest **domyślnie włączony** (checkbox zaznaczony)
- Każda zmiana checkbox automatycznie przeładowuje dane
- Wartość `7` jest używana zamiast `007` (jako integer)
- Obsługuje `NULL` values w bazie danych
- Debug info wypisywane do konsoli
- Zintegrowany z istniejącym systemem filtrów

## Historia zmian

- **2025-07-09**: Początkowa implementacja filtra Magic Number 007
  - Dodano pole magic_number do modelu Position
  - Dodano checkbox do GUI
  - Zaimplementowano logikę filtrowania
  - Stworzono testy i dokumentację
