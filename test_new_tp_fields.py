"""
Test nowych pól TP w głównym oknie
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Dodaj ścieżkę do modułów
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_tp_fields():
    """Test nowych pól TP"""
    try:
        print("Test: Importowanie potrzebnych modułów...")
        
        # Test importów
        from gui.widgets.custom_entries import NumericEntry
        from gui.widgets.date_picker import StopLossSelector
        from config.instrument_tickets_config import get_instrument_tickets_config
        
        print("✓ Wszystkie importy udane")
        
        # Tworzenie okna testowego
        root = tk.Tk()
        root.title("Test nowych pól TP")
        root.geometry("800x600")
        
        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Test StopLossSelector
        print("Test: Tworzenie StopLossSelector...")
        sl_frame = ttk.LabelFrame(main_frame, text="Test StopLossSelector")
        sl_frame.pack(fill="x", pady=10)
        
        sl_selector = StopLossSelector(sl_frame)
        sl_selector.pack(padx=10, pady=10)
        
        print("✓ StopLossSelector utworzony")
        
        # Test NumericEntry
        print("Test: Tworzenie NumericEntry...")
        numeric_frame = ttk.LabelFrame(main_frame, text="Test NumericEntry")
        numeric_frame.pack(fill="x", pady=10)
        
        ttk.Label(numeric_frame, text="Spread:").grid(row=0, column=0, padx=5, pady=5)
        spread_entry = NumericEntry(numeric_frame, width=10, allow_decimal=True)
        spread_entry.insert(0, "0")
        spread_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(numeric_frame, text="BE Prog:").grid(row=1, column=0, padx=5, pady=5)
        be_prog_entry = NumericEntry(numeric_frame, width=10, allow_decimal=True)
        be_prog_entry.insert(0, "10.0")
        be_prog_entry.grid(row=1, column=1, padx=5, pady=5)
        
        print("✓ NumericEntry utworzone")
        
        # Test checkboxów
        print("Test: Tworzenie checkboxów...")
        options_frame = ttk.LabelFrame(main_frame, text="Test opcji")
        options_frame.pack(fill="x", pady=10)
        
        detailed_logs_var = tk.BooleanVar()
        detailed_logs_cb = ttk.Checkbutton(
            options_frame, 
            text="Szczegółowe logi", 
            variable=detailed_logs_var
        )
        detailed_logs_cb.pack(padx=10, pady=5)
        
        save_to_db_var = tk.BooleanVar()
        save_to_db_cb = ttk.Checkbutton(
            options_frame, 
            text="Zapisz do bazy", 
            variable=save_to_db_var
        )
        save_to_db_cb.pack(padx=10, pady=5)
        
        print("✓ Checkboxy utworzone")
        
        # Test funkcji pobierania wartości
        def test_values():
            try:
                print("\n=== TEST POBIERANIA WARTOŚCI ===")
                
                # Test SL selector
                sl_types = sl_selector.get_selected_sl_types()
                sl_staly_values = sl_selector.get_sl_staly_values()
                print(f"SL typy: {sl_types}")
                print(f"SL stały values: {sl_staly_values}")
                
                # Test numeric entries
                spread = spread_entry.get_float()
                be_prog = be_prog_entry.get_float()
                print(f"Spread: {spread}")
                print(f"BE prog: {be_prog}")
                
                # Test checkboxów
                detailed_logs = detailed_logs_var.get()
                save_to_db = save_to_db_var.get()
                print(f"Detailed logs: {detailed_logs}")
                print(f"Save to DB: {save_to_db}")
                
                messagebox.showinfo(
                    "Test wartości", 
                    f"SL typy: {sl_types}\n"
                    f"SL stały: {sl_staly_values}\n"
                    f"Spread: {spread}\n"
                    f"BE prog: {be_prog}\n"
                    f"Logi: {detailed_logs}\n"
                    f"Zapis: {save_to_db}"
                )
                
            except Exception as e:
                print(f"Błąd testu wartości: {e}")
                messagebox.showerror("Błąd", f"Błąd pobierania wartości:\n{e}")
        
        # Przycisk testu
        test_button = ttk.Button(main_frame, text="Test pobierania wartości", command=test_values)
        test_button.pack(pady=10)
        
        print("✓ Test interface utworzony")
        print("\n🎉 Wszystkie testy przeszły pomyślnie!")
        print("Uruchamianie okna testowego...")
        
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Błąd testu: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("=== TEST NOWYCH PÓL TP ===")
    test_tp_fields()
