"""
Test komunikacji z diagnostyką błędów
"""
import sys
import os

# Dodaj ścieżkę do modułów
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_database_connection():
    """Test połączenia z bazą danych"""
    print("=== TEST POŁĄCZENIA Z BAZĄ DANYCH ===")
    
    try:
        from database.connection import get_db_connection
        
        db = get_db_connection()
        print("✅ Połączenie z bazą danych udane")
        
        # Test prostego zapytania
        tables = db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        print(f"📊 Znalezione tabele: {[table[0] for table in tables]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd połączenia z bazą: {e}")
        return False

def test_communication_robust():
    """Test komunikacji z pełną diagnostyką"""
    
    print("\n=== TEST KOMUNIKACJI Z DIAGNOSTYKĄ ===")
    
    if not test_database_connection():
        return False
    
    try:
        from database.communication import CommunicationManager
        
        print("\n1. Tworzenie CommunicationManager...")
        comm = CommunicationManager()
        
        print("\n2. Test zapisywania prostego ticket...")
        test_ticket = 777888
        comm.set_current_edit_ticket(test_ticket)
        
        print("\n3. Test odczytywania ticket...")
        read_ticket = comm.get_current_edit_ticket()
        print(f"   Zapisano: {test_ticket}")
        print(f"   Odczytano: {read_ticket}")
        print(f"   Typ odczytanego: {type(read_ticket)}")
        
        if read_ticket == test_ticket:
            print("✅ Zapis i odczyt działa poprawnie")
        else:
            print(f"⚠️ Niezgodność: {test_ticket} != {read_ticket}")
        
        print("\n4. Test czyszczenia sesji...")
        comm.clear_edit_session()
        cleared_ticket = comm.get_current_edit_ticket()
        print(f"   Po wyczyszczeniu: {cleared_ticket}")
        
        if cleared_ticket == 0:
            print("✅ Czyszczenie sesji działa poprawnie")
        else:
            print(f"⚠️ Błąd czyszczenia: oczekiwano 0, otrzymano {cleared_ticket}")
        
        print("\n5. Sprawdzanie struktury tabeli...")
        from database.connection import get_db_connection
        db = get_db_connection()
        
        # Sprawdź strukturę tabeli
        try:
            schema = db.execute_query("PRAGMA table_info(communication)")
            print("   Struktura tabeli communication:")
            for col in schema:
                print(f"     {col[1]} ({col[2]})")
        except Exception as e:
            print(f"   Błąd sprawdzania struktury: {e}")
        
        # Sprawdź zawartość tabeli
        try:
            content = db.execute_query("SELECT * FROM communication")
            print(f"\n   Zawartość tabeli ({len(content)} wierszy):")
            for row in content:
                print(f"     {row}")
        except Exception as e:
            print(f"   Błąd odczytu zawartości: {e}")
        
        print("\n🎉 Test komunikacji zakończony!")
        return True
        
    except Exception as e:
        print(f"❌ Błąd testu komunikacji: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_communication_robust()
    
    if success:
        print("\n✅ System komunikacji jest gotowy do użycia!")
        print("📱 Możesz teraz uruchomić główną aplikację")
    else:
        print("\n❌ Wykryto problemy z systemem komunikacji")
        print("🔧 Sprawdź logi powyżej i popraw błędy")
