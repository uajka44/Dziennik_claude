"""
Test naprawy EditDialog - sprawdza czy okno otwiera się poprawnie
"""
import sys
import os
import tkinter as tk

# Dodaj ścieżkę do modułów
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_edit_dialog():
    """Test czy EditDialog otwiera się bez błędów"""
    
    print("=== TEST EDIT DIALOG PO NAPRAWIE ===")
    
    try:
        # Stwórz główne okno testowe
        root = tk.Tk()
        root.withdraw()  # Ukryj główne okno
        
        # Import EditDialog
        from gui.edit_dialog import EditDialog
        
        # Test danych
        test_ticket = 123456
        test_values = (
            "2025-06-22 14:30:00",  # data
            "EURUSD",               # symbol
            "1.0850",               # cena
            "BUY",                  # typ
            "0.1",                  # volume
            "",                     # sl
            "",                     # tp
            "Test pozycja",         # komentarz
            "",                     # setup
            "",                     # profit
            "✓",                    # checkbox1
            "",                     # checkbox2
        )
        
        print("✅ Tworzę EditDialog...")
        
        # Callback testowy
        def test_callback(updated_values):
            print(f"✅ Callback wywołany z {len(updated_values)} wartościami")
        
        def test_close_callback():
            print("✅ Close callback wywołany")
        
        # Stwórz dialog edycji
        dialog = EditDialog(
            parent=root,
            ticket=test_ticket,
            values=test_values,
            on_save_callback=test_callback,
            on_close_callback=test_close_callback
        )
        
        print("✅ EditDialog utworzony pomyślnie!")
        print(f"✅ Ticket: {dialog.ticket}")
        print(f"✅ Window config manager: {dialog.window_config}")
        
        # Test window config
        config = dialog.window_config.get_window_config("edit_dialog")
        print(f"✅ Konfiguracja okna: {config}")
        
        # Zamknij dialog
        dialog.destroy()
        print("✅ Dialog zamknięty poprawnie")
        
        # Zamknij aplikację testową
        root.destroy()
        
        print("\n🎉 Test EditDialog przeszedł pomyślnie!")
        return True
        
    except Exception as e:
        print(f"❌ Błąd testu EditDialog: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_edit_dialog()
