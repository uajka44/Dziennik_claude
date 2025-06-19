# Test modyfikacji bazy danych - INSTRUKCJA

## Co zostało zmodyfikowane

Program został zmodyfikowany tak, żeby automatycznie przełączał się na alternatywną bazę danych (DB_PATH2) jeśli główna baza (DB_PATH) nie jest dostępna.

### Zmodyfikowane pliki:

1. **database/connection.py** - dodano logikę fallback'u na DB_PATH2
2. **gui/main_window.py** - wyświetlanie informacji o używanej bazie w status bar
3. **gui/data_viewer.py** - usunięto nieużywany parametr db_path

### Nowe funkcje:

- `_get_available_db_path()` - wybiera dostępną bazę danych
- `get_current_database_info()` - zwraca informacje o używanej bazie
- Komunikaty informujące o przełączeniu na alternatywną bazę

## Jak przetestować

### Test 1: Uruchom test połączenia
```bash
cd C:\Users\Apollo\PYTHON_PROJECTS\Dziennik_claude
python test_database_connection.py
```

Ten test pokaże:
- Które pliki baz danych istnieją
- Z którą bazą program się łączy
- Czy połączenie działa poprawnie

### Test 2: Uruchom główną aplikację
```bash
python main.py
```

W status bar na dole okna zobaczysz informację o tym, z której bazy korzysta program:
- "Główna baza: [ścieżka]" - jeśli używa DB_PATH
- "Alternatywna baza: [ścieżka]" - jeśli używa DB_PATH2

### Test 3: Symulacja niedostępności głównej bazy

1. Zmień nazwę pliku głównej bazy (żeby była tymczasowo niedostępna)
2. Uruchom program - powinien automatycznie przełączyć się na DB_PATH2
3. Sprawdź komunikaty w konsoli i status bar

## Oczekiwane zachowanie

1. **Jeśli DB_PATH istnieje**: Program używa głównej bazy
2. **Jeśli DB_PATH nie istnieje, ale DB_PATH2 istnieje**: Program używa alternatywnej bazy i wyświetla komunikat
3. **Jeśli żadna baza nie istnieje**: Program wyświetla ostrzeżenie i próbuje utworzyć główną bazę

## Komunikaty w konsoli

Program będzie wyświetlał komunikaty typu:
```
Połączono z bazą danych: C:\Users\Apollo\AppData\Roaming\MetaQuotes\Terminal\49CDDEAA95A409ED22BD2287BB67CB9C\MQL5\Files\multi_candles.db
```

lub w przypadku przełączenia:
```
Główna baza danych niedostępna (C:\Users\anasy\AppData\...)
Używam alternatywnej bazy: C:\Users\Apollo\AppData\...
Połączono z bazą danych: C:\Users\Apollo\AppData\...
```

## Rozwiązanie problemu synchronizacji

Teraz program automatycznie wybierze dostępną bazę, co rozwiązuje problem z tym, że na dwóch komputerach masz różne bazy. Program będzie używał tej bazy, która jest aktualnie dostępna na danym komputerze.
