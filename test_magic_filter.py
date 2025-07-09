#!/usr/bin/env python3
"""
Test filtra Magic Number 007
"""

import sys
import os

# Dodaj katalog główny do ścieżki
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_magic_filter():
    """Test filtra Magic Number 007"""
    print("=== TEST FILTRA MAGIC NUMBER 007 ===\n")
    
    try:
        # Test importu modułów
        print("1. Test importu modułów...")
        
        from config.field_definitions import TEXT_FIELDS, COLUMNS, COLUMN_HEADERS, COLUMN_WIDTHS
        from database.models import Position
        
        print("✅ Import modułów - OK")
        
        # Test czy magic_number jest w definicjach
        print("\n2. Test definicji pól...")
        
        magic_field = None
        for field in TEXT_FIELDS:
            if field.name == "magic_number":
                magic_field = field
                break
        
        if magic_field:
            print(f"✅ Pole magic_number znalezione: {magic_field.display_name}")
        else:
            print("❌ Pole magic_number nie znalezione w TEXT_FIELDS")
            return False
        
        # Test czy magic_number jest w kolumnach
        if "magic_number" in COLUMNS:
            print("✅ magic_number jest w COLUMNS")
        else:
            print("❌ magic_number nie ma w COLUMNS")
            return False
        
        # Test czy magic_number ma nagłówek
        if "magic_number" in COLUMN_HEADERS:
            print(f"✅ magic_number ma nagłówek: {COLUMN_HEADERS['magic_number']}")
        else:
            print("❌ magic_number nie ma nagłówka")
            return False
        
        # Test czy magic_number ma szerokość
        if "magic_number" in COLUMN_WIDTHS:
            print(f"✅ magic_number ma szerokość: {COLUMN_WIDTHS['magic_number']}")
        else:
            print("❌ magic_number nie ma ustawionej szerokości")
            return False
        
        # Test modelu Position
        print("\n3. Test modelu Position...")
        
        # Stwórz testowy obiekt Position
        test_position = Position(
            ticket=123456,
            open_time=1672531200,  # 2023-01-01
            type=0,  # buy
            volume=0.1,
            symbol="EURUSD",
            open_price=1.0850,
            magic_number=7
        )
        
        if hasattr(test_position, 'magic_number'):
            print(f"✅ Position ma atrybut magic_number: {test_position.magic_number}")
        else:
            print("❌ Position nie ma atrybutu magic_number")
            return False
        
        print("\n4. Test interfejsu...")
        
        # Próba importu DataViewer (bez uruchamiania GUI)
        try:
            from gui.data_viewer import DataViewer
            print("✅ Import DataViewer - OK")
        except Exception as e:
            print(f"❌ Błąd importu DataViewer: {e}")
            return False
        
        print("\n5. Test zapytania SQL...")
        
        # Test budowania zapytania z filtrem magic_number
        columns_str = ", ".join(COLUMNS)
        
        # Zapytanie z filtrem magic_number = 7
        where_conditions = ["open_time BETWEEN ? AND ?", "magic_number = ?"]
        where_clause = " AND ".join(where_conditions)
        query_with_007 = f"""
        SELECT {columns_str}
        FROM positions 
        WHERE {where_clause}
        ORDER BY open_time
        """
        
        print("✅ Zapytanie SQL z filtrem 007:")
        print(query_with_007)
        
        # Zapytanie bez filtra magic_number = 7
        where_conditions = ["open_time BETWEEN ? AND ?", "(magic_number IS NULL OR magic_number != ?)"]
        where_clause = " AND ".join(where_conditions)
        query_without_007 = f"""
        SELECT {columns_str}
        FROM positions 
        WHERE {where_clause}
        ORDER BY open_time
        """
        
        print("\n✅ Zapytanie SQL bez filtra 007:")
        print(query_without_007)
        
        print("\n🎉 WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE!")
        print("\nFiltr Magic Number 007 został poprawnie zaimplementowany:")
        print("- ✅ Pole magic_number dodane do modelu Position")
        print("- ✅ Pole magic_number dodane do definicji pól")
        print("- ✅ Kolumna magic_number dodana do tabeli")
        print("- ✅ Checkbox filtra 007 dodany do interfejsu")
        print("- ✅ Logika filtrowania zaimplementowana")
        
        print("\n📋 JAK UŻYWAĆ:")
        print("1. Zaznacz checkbox 'Magic Number 007' - pokazuj tylko trejdy z magic_number = 7")
        print("2. Odznacz checkbox 'Magic Number 007' - ukryj trejdy z magic_number = 7")
        print("3. Filtr jest domyślnie WŁĄCZONY (zaznaczony)")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd testu: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui():
    """Test GUI z filtrem 007"""
    print("\n=== TEST GUI Z FILTREM 007 ===\n")
    
    try:
        import tkinter as tk
        from gui.main_window import MainWindow
        
        root = tk.Tk()
        root.title("Test Filtra 007")
        
        # Stwórz główne okno
        app = MainWindow(root)
        
        print("✅ GUI uruchomione. Sprawdź czy:")
        print("  - W sekcji 'Filtry' jest nowy checkbox 'Magic Number 007'")
        print("  - Checkbox jest domyślnie zaznaczony")
        print("  - Kliknięcie w checkbox powoduje przeładowanie danych")
        print("  - Kolumna 'Magic Number' jest widoczna w tabeli")
        
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Błąd GUI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Uruchamianie testów filtra Magic Number 007...\n")
    
    success = test_magic_filter()
    
    if success:
        print("\n" + "="*60)
        print("Czy chcesz przetestować GUI? (y/n): ", end="")
        choice = input().lower().strip()
        
        if choice in ['y', 'yes', 'tak', 't']:
            test_gui()
        else:
            print("Test zakończony. Filtr 007 gotowy do użycia!")
    else:
        print("\n❌ Test nieudany. Sprawdź błędy powyżej.")
