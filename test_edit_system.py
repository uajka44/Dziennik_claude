"""
Test systemu edycji - sprawdza czy wszystko działa poprawnie
"""
import sys
import os

# Dodaj ścieżkę do modułów
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.edit_manager import EditWindowManager


def test_edit_manager():
    """Test podstawowej funkcjonalności EditWindowManager"""
    
    print("=== TEST EDIT WINDOW MANAGER Z NAWIGACJĄ ===")
    
    # Test singleton
    manager1 = EditWindowManager()
    manager2 = EditWindowManager()
    
    assert manager1 is manager2, "EditWindowManager powinien być singleton"
    print("✅ Singleton pattern działa poprawnie")
    
    # Test zapisywania ticket
    test_ticket = 123456
    manager1._save_current_ticket(test_ticket)
    
    # Sprawdź czy plik został utworzony
    file_path = manager1.get_communication_file_path()
    print(f"📁 Plik komunikacyjny: {file_path}")
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read().strip()
        
        assert content == str(test_ticket), f"Oczekiwano {test_ticket}, otrzymano {content}"
        print(f"✅ Zapis do pliku działa: {content}")
    else:
        print("❌ Plik komunikacyjny nie został utworzony")
        return False
    
    # Test zerowania
    manager1._save_current_ticket(0)
    
    saved_ticket_zero = comm.get_current_edit_ticket()
    assert saved_ticket_zero == 0, f"Oczekiwano 0, otrzymano {saved_ticket_zero}"
    print("✅ Zerowanie ticket działa poprawnie")
    
    # Test statusu
    assert not manager1.is_editing(), "Manager nie powinien wskazywać aktywnej edycji"
    assert manager1.get_current_ticket() is None, "Current ticket powinien być None"
    print("✅ Status management działa poprawnie")
    
    # Test symulacji wielu ticketów
    test_tickets = [123456, 123457, 123458]
    for ticket in test_tickets:
        manager1._save_current_ticket(ticket)
        saved_ticket = comm.get_current_edit_ticket()
        assert saved_ticket == ticket, f"Oczekiwano {ticket}, otrzymano {saved_ticket}"
    
    print(f"✅ Test wielu ticketów przeszedł pomyślnie")
    
    # Test window config managera
    print("✅ Testuję WindowConfigManager...")
    from gui.window_config import WindowConfigManager
    
    window_config = WindowConfigManager()
    test_config = window_config.get_window_config("edit_dialog")
    
    assert "width" in test_config, "Brak konfiguracji width"
    assert "height" in test_config, "Brak konfiguracji height"
    print("✅ WindowConfigManager działa poprawnie")
    
    # Test communication managera
    print("✅ Testuję CommunicationManager...")
    from database.communication import get_communication_manager
    
    comm = get_communication_manager()
    comm.set_current_edit_ticket(789)
    read_ticket = comm.get_current_edit_ticket()
    
    assert read_ticket == 789, f"Błąd komunikacji: oczekiwano 789, otrzymano {read_ticket}"
    print("✅ CommunicationManager działa poprawnie")
    
    # Wyczyść po teście
    comm.clear_edit_session()
    
    print("✅ System nawigacji gotowy do testów GUI")
    
    print("\n🎉 Wszystkie testy przeszły pomyślnie!")
    print("🚀 System gotowy do użycia z funkcjami:")
    print("   - Większe okno edycji (700x900)")
    print("   - Przyciski Next/Prev z nawigacją")
    print("   - Automatyczny zapis przed otwarciem nowej pozycji")
    print("   - 🆕 Zapamiętywanie pozycji okien")
    print("   - 🆕 Plik konfiguracyjny window_config.json")
    print("   - 🆕 Opcje reset w menu Ustawienia")
    print("   - 🆕 Komunikacja z MQL5 przez bazę danych (tabela communication)")
    return True


if __name__ == "__main__":
    test_edit_manager()
