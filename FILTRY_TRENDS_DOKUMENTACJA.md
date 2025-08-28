# Dokumentacja Filtrów TrendS i TrendL

## Opis funkcjonalności

Dodano nowe filtry do przeglądarki danych w sekcji "Filtry":

### TrendS
- **Lokalizacja**: Wiersz 2, kolumna 1-2 w ramce "Filtry"
- **Interfejs**: Rozwijana lista z checkboxami podobnie jak filtry Setup
- **Wartości**: -3, -2, -1, 0, 1, 2, 3, puste
- **Domyślnie**: Wszystkie wartości zaznaczone
- **Logika**: Filtr aktywuje się gdy nie wszystkie wartości są zaznaczone

### TrendL  
- **Lokalizacja**: Wiersz 2, kolumna 3-4 w ramce "Filtry"
- **Interfejs**: Rozwijana lista z checkboxami podobnie jak filtry Setup
- **Wartości**: -3, -2, -1, 0, 1, 2, 3, puste
- **Domyślnie**: Wszystkie wartości zaznaczone
- **Logika**: Filtr aktywuje się gdy nie wszystkie wartości są zaznaczone

## Implementacja

### Nowe komponenty GUI (gui/data_viewer.py)

1. **Dropdown TrendS**:
   ```python
   self.trends_dropdown = CheckboxDropdown(self.filter_frame, callback=self.load_data, default_text="TrendS")
   self.trends_dropdown.grid(row=2, column=1, padx=5, pady=5, sticky="w")
   ```

2. **Dropdown TrendL**:
   ```python
   self.trendl_dropdown = CheckboxDropdown(self.filter_frame, callback=self.load_data, default_text="TrendL")
   self.trendl_dropdown.grid(row=2, column=3, padx=5, pady=5, sticky="w")
   ```

3. **Nowa metoda ładowania wartości**:
   ```python
   def _load_trend_values(self, dropdown):
       """Ładuje wartości trendów (-3 do +3 oraz puste) do dropdown"""
       try:
           # Wartości od -3 do +3
           for value in range(-3, 4):  # -3, -2, -1, 0, 1, 2, 3
               dropdown.add_item(
                   str(value),  # klucz jako string
                   str(value),  # wyświetlany tekst
                   checked=True  # domyślnie wszystkie zaznaczone
               )
           
           # Dodaj opcję "puste" dla wartości NULL
           dropdown.add_item(
               "NULL",  # klucz
               "puste",  # wyświetlany tekst
               checked=True  # domyślnie zaznaczone
           )
   ```

### Logika filtrowania w load_data()

1. **Filtr TrendS**:
   ```python
   selected_trends = self.trends_dropdown.get_selected()
   if selected_trends and len(selected_trends) < len(self.trends_dropdown.items):
       trend_conditions = []
       for trend_val in selected_trends:
           if trend_val == "NULL":
               trend_conditions.append("trends IS NULL")
           else:
               trend_conditions.append("trends = ?")
               base_params.append(int(trend_val))
       
       if trend_conditions:
           trends_clause = " OR ".join(trend_conditions)
           where_conditions.append(f"({trends_clause})")
   ```

2. **Filtr TrendL**:
   ```python
   selected_trendl = self.trendl_dropdown.get_selected()
   if selected_trendl and len(selected_trendl) < len(self.trendl_dropdown.items):
       trendl_conditions = []
       for trend_val in selected_trendl:
           if trend_val == "NULL":
               trendl_conditions.append("trendl IS NULL")
           else:
               trendl_conditions.append("trendl = ?")
               base_params.append(int(trend_val))
       
       if trendl_conditions:
           trendl_clause = " OR ".join(trendl_conditions)
           where_conditions.append(f"({trendl_clause})")
   ```

### Integracja z kalkulatorem TP

W metodzie `_calculate_tp_for_range()` dodano informacje o aktywnych filtrach:

```python
# Sprawdź filtry TrendS i TrendL
selected_trends = self.trends_dropdown.get_selected()
if len(selected_trends) < len(self.trends_dropdown.items):
    active_filters.append(f"TrendS: {', '.join(selected_trends)}")
    
selected_trendl = self.trendl_dropdown.get_selected()
if len(selected_trendl) < len(self.trendl_dropdown.items):
    active_filters.append(f"TrendL: {', '.join(selected_trendl)}")
```

## Aktualizowane pliki

1. **gui/data_viewer.py**:
   - Dodano komponenty GUI dla filtrów TrendS i TrendL
   - Dodano metodę `_load_trend_values()`
   - Zaktualizowano metodę `load_data()` z logiką filtrowania
   - Zaktualizowano metodę `_calculate_tp_for_range()` z informacjami o filtrach

2. **test_trend_filters.py** (nowy):
   - Plik testowy do weryfikacji implementacji filtrów

## Mapowanie pól bazy danych

- **TrendS** → kolumna `trends` w tabeli `positions`
- **TrendL** → kolumna `trendl` w tabeli `positions`

*Uwaga: W `config/field_definitions.py` są jako `trends` i `trendl` (małe litery)*

## Logika kombinacji filtrów

- **TrendS i TrendL**: Oba muszą być spełnione (logika AND)
- **NULL/puste**: Zaznaczenie "puste" pokazuje rekordy z NULL w danym polu
- **Domyślne zachowanie**: Wszystkie checkboxy zaznaczone = brak filtrowania

## Testowanie

1. Uruchom aplikację: `python main.py`
2. Przejdź do zakładki "Przeglądarka danych"
3. W sekcji "Filtry" znajdziesz nowe filtry "TrendS:" i "TrendL:"
4. Kliknij aby rozwinąć listę z checkboxami
5. Odznacz niektóre wartości i sprawdź filtrowanie
6. Sprawdź czy filtr działa z kalkulatorem TP

## Rozwiązywanie problemów

- **Brak danych**: Sprawdź czy pola `trends` i `trendl` istnieją w bazie
- **Błędy SQL**: Sprawdź czy nazwy kolumn są poprawne (`trends`, `trendl`)
- **Filtry nieaktywne**: Sprawdź czy `CheckboxDropdown.get_selected()` zwraca poprawne wartości

## Zgodność

- **Wersja**: Dziennik AI 3.0
- **Wymagane**: Istniejące komponenty `CheckboxDropdown`
- **Zależności**: Pola `trends` i `trendl` w tabeli `positions`
