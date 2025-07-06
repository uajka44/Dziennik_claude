"""
Prosty test nowego EditDialog z kompaktowym layoutem
"""
import tkinter as tk
from tkinter import ttk
import sys
import os

# Dodaj katalog główny do ścieżki
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def simple_test():
    """Prosty test bez importowania całej aplikacji"""
    
    print("=== SIMPLE TEST EDIT DIALOG ===")
    
    # Testowe dane
    test_ticket = 123456
    test_values = [
        "2025-07-06 14:30:00",   # data/czas
        "123456",                # ticket
        "BUY",                   # typ
        "0.10",                  # volume
        "EURUSD",                # symbol
        "1.0850",                # open_price
        "1.0800",                # sl
        "1.0900",                # sl_opening
        "15.5",                  # profit_points
        "Test setup",            # setup
        "Testowe uwagi",         # uwagi
        "Testowy błąd",          # blad
        "UP",                    # trends
        "DOWN",                  # trendl
        "M5",                    # interwal
        "param1",                # setup_param1
        "param2",                # setup_param2
        "",                      # nieutrzymalem
        "✓",                     # niedojscie
        "",                      # wybicie
        "✓",                     # strefa_oporu
        "",                      # zdrugiejstrony
        "",                      # ucieczka
        "",                      # Korekta
        "",                      # chcetrzymac
        "✓",                     # be
        ""                       # skalp
    ]
    
    try:
        print("Tworzenie test window...")
        root = tk.Tk()
        root.title("Test Edit Dialog")
        root.geometry("300x200")
        
        def open_edit_dialog():
            try:
                from gui.edit_dialog import EditDialog
                
                def save_callback(values):
                    print(f"✅ Save callback: otrzymano {len(values)} wartości")
                
                def close_callback():
                    print("✅ Close callback wywołany")
                
                # Stwórz EditDialog
                dialog = EditDialog(
                    parent=root,
                    ticket=test_ticket,
                    values=test_values,
                    on_save_callback=save_callback,
                    on_close_callback=close_callback
                )
                
                print("✅ EditDialog utworzony pomyślnie!")
                
            except Exception as e:
                print(f"❌ Błąd tworzenia EditDialog: {e}")
                import traceback
                traceback.print_exc()
        
        # Przycisk do testowania
        ttk.Button(root, text="Otwórz Edit Dialog", 
                  command=open_edit_dialog).pack(pady=50)
        
        ttk.Label(root, text="Kliknij przycisk, aby przetestować\nnowy kompaktowy EditDialog").pack()
        
        print("✅ Test window gotowy. Kliknij przycisk aby przetestować EditDialog.")
        
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Błąd testu: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    simple_test()
