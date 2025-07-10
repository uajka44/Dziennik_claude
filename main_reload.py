#!/usr/bin/env python
"""
Tymczasowy plik główny aplikacji z wymuszonym przeładowaniem modułów
"""
import tkinter as tk
import sys
import os
import importlib

# Wymuś przeładowanie modułów
if 'gui.data_viewer' in sys.modules:
    del sys.modules['gui.data_viewer']
if 'gui.main_window' in sys.modules:
    del sys.modules['gui.main_window']

# Dodaj ścieżkę do modułów
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Funkcja główna aplikacji z wymuszonym przeładowaniem"""
    try:
        # Wymuś przeładowanie
        import gui.data_viewer
        import gui.main_window
        importlib.reload(gui.data_viewer)
        importlib.reload(gui.main_window)
        
        from gui.main_window import MainWindow
        
        # Tworzenie głównego okna
        root = tk.Tk()
        
        # Inicjalizacja głównego okna aplikacji
        app = MainWindow(root)
        
        print("✅ Aplikacja uruchomiona z przeładowanymi modułami")
        print("✅ Sprawdź czy widzisz panel 'Kalkulator TP' po prawej stronie")
        
        # Uruchomienie głównej pętli aplikacji
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Błąd podczas uruchamiania aplikacji: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔄 Uruchamianie z wymuszonym przeładowaniem modułów...")
    main()
