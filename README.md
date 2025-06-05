# Dziennik Transakcji AI 3.0

Zrefaktoryzowana i rozszerzona aplikacja do zarządzania dziennikiem transakcji tradingowych z kalkulatorem maksymalnego Take Profit.

## 🆕 Nowe funkcjonalności w wersji 3.0

### ✨ Kalkulator maksymalnego Take Profit
- **Analiza trzech typów Stop Loss**: SL ręczne, SL z bazy, SL stały
- **Symulacja Break Even**: Automatyczne przesuwanie SL po osiągnięciu zadanego zysku
- **Analiza świeczkowa**: Precyzyjne obliczenia na podstawie danych minutowych
- **Uwzględnienie spread'u**: Realistyczne kalkulacje z uwzględnieniem kosztów
- **Eksport wyników**: Zapis do CSV i bazy danych

### 🏗️ Nowa architektura modularna
- **Lepszy podział odpowiedzialności**: Każdy komponent w osobnym pliku
- **Łatwość rozwoju**: Proste dodawanie nowych funkcji
- **AI-friendly**: Mniejsze pliki = lepsza współpraca z AI
- **Testowanie**: Możliwość testowania każdego modułu osobno

## 📁 Struktura projektu

```
📦 venv/
├── 📁 config/              # Konfiguracja
│   ├── database_config.py  # Ustawienia bazy danych
│   └── field_definitions.py # Definicje pól formularza
├── 📁 database/            # Warstwa danych
│   ├── connection.py       # Zarządzanie połączeniami
│   ├── models.py          # Modele danych
│   └── queries.py         # Zapytania SQL
├── 📁 gui/                # Interfejs użytkownika
│   ├── main_window.py     # Główne okno z menu
│   ├── data_viewer.py     # Przeglądarka transakcji
│   ├── tp_calculator.py   # 🆕 Kalkulator TP
│   └── 📁 widgets/        # Komponenty GUI
│       ├── custom_entries.py
│       └── date_picker.py
├── 📁 calculations/       # Logika biznesowa
│   ├── tp_calculator.py   # Główna logika kalkulacji TP
│   ├── candle_analyzer.py # Analiza świeczek
│   └── position_analyzer.py # Analiza pozycji
├── 📁 utils/             # Narzędzia pomocnicze
│   ├── date_utils.py     # Konwersje dat
│   └── formatting.py    # Formatowanie danych
├── main.py              # 🚀 Główny plik uruchomieniowy
├── requirements.txt     # Zależności
└── README.md           # Ten plik
```

## 🚀 Uruchomienie

### 1. Sprawdź zależności
```bash
pip install -r requirements.txt
```

### 2. Uruchom aplikację
```bash
python main.py
```

## 🎯 Funkcjonalności kalkulatora TP

### Parametry wejściowe:
- **Zakres dat**: Wybór okresu do analizy + przycisk "Dzisiaj"
- **Instrumenty**: GER40, US100, US30, XAUUSD (możliwość rozszerzenia)
- **Typy Stop Loss**:
  - SL ręczne (z kolumny `sl_recznie`)
  - SL z bazy (z kolumny `sl`)
  - SL stały (wartość w punktach)
- **Break Even**:
  - Próg BE (w punktach)
  - Offset BE (przesunięcie SL w punktach)
- **Spread**: Uwzględnienie kosztów transakcyjnych

### Algorytm kalkulacji:

#### Podstawowa kalkulacja TP:
1. **Pierwsza świeczka**: Sprawdza tylko `close` (nie znamy przebiegu)
2. **Kolejne świeczki**: Analizuje `high`/`low` dla maksymalnego zysku
3. **Sprawdzenie SL**: Czy cena uderzyła w stop loss
4. **Wynik**: Maksymalny TP w punktach lub `null` jeśli SL

#### Kalkulacja z Break Even:
1. **Monitorowanie progu BE**: Czy zysk osiągnął `be_prog`
2. **Przesunięcie SL**: Na `open_price ± be_offset`
3. **Kontynuacja**: Dalsze obliczenia z nowym SL
4. **Wynik**: Maksymalny TP przed uderzeniem w przesunięty SL

### Wyniki:
- **Tabela wyników**: Dla każdej pozycji osobno
- **Podsumowanie**: Średnie i maksymalne wartości TP
- **Eksport**: CSV i zapis do tabeli `tp_calculation_results`

## 🔧 Konfiguracja

### Baza danych
W pliku `config/database_config.py`:
```python
DB_PATH = r"C:\Users\...\multi_candles.db"
AVAILABLE_INSTRUMENTS = ["ger40.cash", "us100.cash", "us30.cash", "XAUUSD"]
```

### Pola formularza
W pliku `config/field_definitions.py` - centralne miejsce definicji wszystkich pól.

## 📊 Struktura bazy danych

### Tabela `positions` (istniejąca):
- Podstawowe dane transakcji
- Kolumny: `ticket`, `open_time`, `type`, `symbol`, `open_price`, `sl`, `sl_recznie`, etc.

### Tabela `tp_calculation_results` (nowa):
- Wyniki kalkulacji TP
- Kolumny: `ticket`, `max_tp_sl_staly`, `max_tp_sl_recznie`, `max_tp_sl_be`, etc.

### Tabele świeczkowe:
- `ger40.cash`, `us100.cash`, `us30.cash`, `XAUUSD`
- Dane minutowe: `time`, `open`, `high`, `low`, `close`

## 🐛 Rozwiązywanie problemów

### "Brak danych świeczkowych"
- Sprawdź czy tabela dla instrumentu istnieje w bazie
- Sprawdź czy są dane świeczkowe dla wybranego dnia
- Sprawdź czy nazwy instrumentów się zgadzają

### Błędy importu
```bash
pip install tkcalendar
```

### Problemy z bazą danych
- Sprawdź ścieżkę w `config/database_config.py`
- Sprawdź uprawnienia do pliku bazy danych

## 🔄 Migracja z wersji 2.6

1. **Backup**: Skopiuj stary plik `Dziennik_AI_2_6.py`
2. **Dane**: Aplikacja używa tej samej bazy danych
3. **Uruchomienie**: Użyj nowego `main.py`
4. **Konfiguracja**: Sprawdź ustawienia w katalogu `config/`

## 🚧 Przyszłe rozszerzenia

- [ ] Więcej instrumentów
- [ ] Analityka zaawansowana
- [ ] Wykresy i wizualizacje
- [ ] Import danych z MT5
- [ ] Raporty PDF
- [ ] Kopie zapasowe

## 📝 Changelog

### v3.0 (2025)
- ✅ Refaktoryzacja na architekturę modularną
- ✅ Nowy kalkulator maksymalnego Take Profit
- ✅ Obsługa Break Even z przesuwaniem SL
- ✅ Analiza świeczkowa z uwzględnieniem spread'u
- ✅ Eksport wyników do CSV i bazy
- ✅ Nowe GUI z menu i zakładkami
- ✅ Lepsza organizacja kodu

### v2.6 (poprzednia)
- Podstawowa przeglądarka transakcji
- Edycja danych w dialogu
- Filtry dat i podsumowania
