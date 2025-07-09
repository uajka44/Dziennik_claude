# FILTR "WĄTPLIWE TREJDY" - DOKUMENTACJA

## Przegląd

Zaimplementowano nowy filtr "Wątpliwe trejdy" z listą rozwijaną, który zastąpił poprzedni checkbox "Usuń 007". Filtr pozwala na elastyczne zarządzanie wyświetlaniem trejdów z `magic_number = 7`.

## Opcje filtra

### 🔹 **"nieaktywny"** (domyślna)
- **Zachowanie**: Filtr nie działa, wyświetla wszystkie trejdy
- **SQL**: Brak dodatkowych warunków
- **Komunikat**: `"Filtr 'Wątpliwe trejdy' - nieaktywny, pokazuję wszystkie trejdy"`

### 🔹 **"tylko wątpliwe"**
- **Zachowanie**: Pokazuje TYLKO trejdy z `magic_number = 7`
- **SQL**: `WHERE ... AND magic_number = ?`
- **Komunikat**: `"Filtr 'Wątpliwe trejdy' - pokazuję tylko wątpliwe (magic_number = 7)"`

### 🔹 **"nie pokazuj wątpliwych"**
- **Zachowanie**: Ukrywa trejdy z `magic_number = 7`, pokazuje wszystkie pozostałe
- **SQL**: `WHERE ... AND (magic_number IS NULL OR magic_number != ?)`
- **Komunikat**: `"Filtr 'Wątpliwe trejdy' - ukrywam wątpliwe (magic_number = 7)"`

## Implementacja techniczna

### Interface użytkownika
```python
# Filtr Wątpliwe trejdy - lista rozwijana
ttk.Label(self.filter_frame, text="Wątpliwe trejdy:").grid(row=2, column=0, padx=5, pady=5, sticky="w")

# Lista rozwijana z opcjami filtrowania
self.suspicious_trades_var = tk.StringVar(value="nieaktywny")  # Domyślnie nieaktywny
self.suspicious_trades_combo = ttk.Combobox(
    self.filter_frame,
    textvariable=self.suspicious_trades_var,
    values=["nieaktywny", "tylko wątpliwe", "nie pokazuj wątpliwych"],
    state="readonly",
    width=20
)
self.suspicious_trades_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")
self.suspicious_trades_combo.bind("<<ComboboxSelected>>", lambda e: self.load_data())
```

### Logika filtrowania
```python
# Warunek dla filtra Wątpliwe trejdy
suspicious_filter = self.suspicious_trades_var.get()
if suspicious_filter == "tylko wątpliwe":
    # Pokazuj tylko trejdy z magic_number = 7
    where_conditions.append("magic_number = ?")
    base_params.append(7)
    print("Filtr 'Wątpliwe trejdy' - pokazuję tylko wątpliwe (magic_number = 7)")
elif suspicious_filter == "nie pokazuj wątpliwych":
    # Ukryj trejdy z magic_number = 7
    where_conditions.append("(magic_number IS NULL OR magic_number != ?)")
    base_params.append(7)
    print("Filtr 'Wątpliwe trejdy' - ukrywam wątpliwe (magic_number = 7)")
else:  # nieaktywny
    # Nie dodawaj żadnych warunków - pokazuj wszystkie trejdy
    print("Filtr 'Wątpliwe trejdy' - nieaktywny, pokazuję wszystkie trejdy")
```

## Przykłady zapytań SQL

### Nieaktywny
```sql
SELECT ... FROM positions 
WHERE open_time BETWEEN ? AND ?
ORDER BY open_time
```

### Tylko wątpliwe
```sql
SELECT ... FROM positions 
WHERE open_time BETWEEN ? AND ? 
AND magic_number = ?
ORDER BY open_time
```

### Nie pokazuj wątpliwych
```sql
SELECT ... FROM positions 
WHERE open_time BETWEEN ? AND ? 
AND (magic_number IS NULL OR magic_number != ?)
ORDER BY open_time
```

## Lokalizacja w interface

- **Sekcja**: "Filtry" w głównym oknie
- **Pozycja**: Wiersz 2, kolumna 0-1 (pod filtrami Instrumentów i Setup)  
- **Etykieta**: "Wątpliwe trejdy:"
- **Kontrolka**: Lista rozwijana (Combobox) z 3 opcjami

## Współpraca z innymi filtrami

Filtr "Wątpliwe trejdy" współpracuje z:
- ✅ Filtr instrumentów (CheckboxDropdown)
- ✅ Filtr setupów (CheckboxDropdown + checkbox aktywności)
- ✅ Filtr zakresu dat (DateEntry)
- ✅ Wszystkie statystyki (profit, winrate, liczba transakcji)

Wszystkie filtry są łączone operatorem `AND`.

## Wpływ na statystyki

Filtr wpływa na wszystkie wyświetlane statystyki:
- Suma profitu
- Liczba transakcji
- Wygrywające trejdy  
- Przegrywające trejdy
- Winrate (%)

## Testowanie

### Test interfejsu:
1. Uruchom: `python main.py`
2. Przejdź do zakładki "Przeglądarka danych"
3. Sprawdź listę rozwijaną "Wątpliwe trejdy"
4. Domyślnie powinna być ustawiona na "nieaktywny"

### Test funkcjonalności:
1. **"nieaktywny"**: Sprawdź czy wyświetla wszystkie trejdy
2. **"tylko wątpliwe"**: Sprawdź czy pokazuje tylko trejdy z magic_number = 7
3. **"nie pokazuj wątpliwych"**: Sprawdź czy ukrywa trejdy z magic_number = 7
4. Sprawdź czy statystyki się aktualizują po zmianie opcji

## Zalety nowego rozwiązania

✅ **Intuicyjność**: Nazwy opcji są czytelne i jednoznaczne  
✅ **Elastyczność**: 3 opcje zamiast 2 (checkbox)  
✅ **UX**: Lista rozwijana zajmuje mniej miejsca niż checkbox  
✅ **Przyszłość**: Łatwe dodawanie nowych opcji filtrowania  

## Historia zmian

- **2025-07-09**: Zamiana checkbox "Usuń 007" na listę rozwijaną "Wątpliwe trejdy"
- **2025-07-09**: Dodanie opcji "nieaktywny", "tylko wątpliwe", "nie pokazuj wątpliwych"
- **2025-07-09**: Zaimplementowanie logiki filtrowania dla wszystkich 3 opcji

---
**Status**: ✅ GOTOWE - filtr w pełni funkcjonalny  
**Typ kontrolki**: ttk.Combobox (lista rozwijana)  
**Domyślna wartość**: "nieaktywny"
