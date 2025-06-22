"""
Test systemu komunikacji przez bazę danych
"""
import sys
import os

# Dodaj ścieżkę do modułów
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.communication import CommunicationManager


def test_communication_system():
    """Test komunikacji przez bazę danych"""
    
    print("=== TEST KOMUNIKACJI PRZEZ BAZĘ DANYCH ===")
    
    # Stwórz manager komunikacji
    comm = CommunicationManager()
    
    # Test zapisywania ticket
    test_ticket = 555666
    print(f"\n1. Zapisuję ticket: {test_ticket}")
    comm.set_current_edit_ticket(test_ticket)
    
    # Test odczytywania ticket
    read_ticket = comm.get_current_edit_ticket()
    print(f"2. Odczytano ticket: {read_ticket}")
    
    assert read_ticket == test_ticket, f"Błąd: oczekiwano {test_ticket}, otrzymano {read_ticket}"
    
    # Test czyszczenia sesji
    print(f"\n3. Czyszczę sesję edycji")
    comm.clear_edit_session()
    
    cleared_ticket = comm.get_current_edit_ticket()
    print(f"4. Po wyczyszczeniu: {cleared_ticket}")
    
    assert cleared_ticket == 0, f"Błąd: po wyczyszczeniu oczekiwano 0, otrzymano {cleared_ticket}"
    
    # Test wszystkich danych
    print(f"\n5. Wszystkie dane komunikacji:")
    comm.debug_print_all()
    
    # Symulacja heartbeat MQL5
    comm.update_mql5_heartbeat()
    print(f"6. Zaktualizowano heartbeat MQL5")
    
    print("\n🎉 Test komunikacji przeszedł pomyślnie!")
    print("📊 Tabela 'communication' w multi_candles.db jest gotowa")
    print("🔗 MQL5 może teraz odczytywać dane przez klawisz 'G'")
    
    return True


if __name__ == "__main__":
    test_communication_system()
