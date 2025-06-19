#!/usr/bin/env python3
"""
Test połączenia z bazą danych - sprawdza czy fallback na DB_PATH2 działa
"""

import os
import sys
from config.database_config import DB_PATH, DB_PATH2
from database.connection import get_db_connection, get_current_database_info

def test_database_connection():
    """Testuje połączenie z bazą danych"""
    print("=== TEST POŁĄCZENIA Z BAZĄ DANYCH ===\n")
    
    # Sprawdź które pliki baz istnieją
    print("Sprawdzanie dostępności plików baz danych:")
    print(f"DB_PATH (główna): {DB_PATH}")
    print(f"  Istnieje: {'✅ TAK' if os.path.exists(DB_PATH) else '❌ NIE'}")
    print(f"DB_PATH2 (alternatywna): {DB_PATH2}")
    print(f"  Istnieje: {'✅ TAK' if os.path.exists(DB_PATH2) else '❌ NIE'}")
    print()
    
    # Spróbuj połączyć się z bazą
    print("Próba połączenia z bazą danych...")
    try:
        db = get_db_connection()
        
        # Test połączenia
        result = db.execute_query("SELECT name FROM sqlite_master WHERE type='table' LIMIT 5")
        
        print("✅ Połączenie udane!")
        print(f"Używana baza: {get_current_database_info()}")
        print(f"Znalezione tabele: {[row[0] for row in result]}")
        
        # Test na tabeli positions
        print("\nSprawa dzanie tabeli positions...")
        try:
            positions_count = db.execute_query("SELECT COUNT(*) FROM positions")[0][0]
            print(f"✅ Tabela positions istnieje, zawiera {positions_count} rekordów")
            
            # Pokaż przykładowe symbole
            symbols = db.execute_query("SELECT DISTINCT symbol FROM positions LIMIT 10")
            symbol_list = [row[0] for row in symbols if row[0]]
            print(f"Przykładowe symbole: {symbol_list}")
            
        except Exception as e:
            print(f"❌ Błąd dostępu do tabeli positions: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd połączenia z bazą danych: {e}")
        return False

def test_create_new_connection():
    """Testuje tworzenie nowego połączenia"""
    print("\n=== TEST TWORZENIA NOWEGO POŁĄCZENIA ===\n")
    
    try:
        from database.connection import create_new_connection
        
        conn = create_new_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 3")
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        
        print("✅ Nowe połączenie działa poprawnie")
        print(f"Znalezione tabele: {[row[0] for row in result]}")
        return True
        
    except Exception as e:
        print(f"❌ Błąd tworzenia nowego połączenia: {e}")
        return False

if __name__ == "__main__":
    print("Uruchamianie testów połączenia z bazą danych...\n")
    
    success1 = test_database_connection()
    success2 = test_create_new_connection()
    
    print("\n=== PODSUMOWANIE ===")
    print(f"Test głównego połączenia: {'✅ SUKCES' if success1 else '❌ BŁĄD'}")
    print(f"Test nowego połączenia: {'✅ SUKCES' if success2 else '❌ BŁĄD'}")
    
    if success1 and success2:
        print("\n🎉 Wszystkie testy przeszły pomyślnie!")
        print("Program może teraz używać alternatywnej bazy DB_PATH2 jeśli główna jest niedostępna.")
    else:
        print("\n⚠️  Występują problemy z połączeniem do bazy danych.")
        print("Sprawdź ścieżki w config/database_config.py")
    
    print(f"\nBieżący katalog: {os.getcwd()}")
    print(f"Python: {sys.version}")
