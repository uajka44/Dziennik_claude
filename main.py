"""
Główny plik uruchomieniowy aplikacji Dziennik Transakcji AI 3.0
"""
import tkinter as tk
import sys
import os

# Dodaj ścieżkę do modułów
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gui.main_window import MainWindow
    from tkinter import messagebox
except ImportError as e:
    print(f"Błąd importu: {e}")
    print("Sprawdź czy wszystkie wymagane moduły są zainstalowane:")
    print("- tkinter")
    print("- tkcalendar")
    sys.exit(1)


def main():
    """Funkcja główna aplikacji"""
    try:
        # Tworzenie głównego okna
        root = tk.Tk()
        
        # Ustawienie ikon i stylów
        try:
            # Możesz dodać ikonę aplikacji tutaj
            # root.iconbitmap("icon.ico")
            pass
        except:
            pass
        
        # Inicjalizacja głównego okna aplikacji
        app = MainWindow(root)
        
        # Obsługa zamykania aplikacji
        def on_closing():
            if messagebox.askokcancel("Zamknij", "Czy na pewno chcesz zamknąć aplikację?"):
                try:
                    # Zamknij połączenia z bazą danych
                    from database.connection import get_db_connection
                    db = get_db_connection()
                    db.close_connection()
                except:
                    pass
                
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Uruchomienie głównej pętli aplikacji
        root.mainloop()
        
    except Exception as e:
        print(f"Błąd podczas uruchamiania aplikacji: {e}")
        messagebox.showerror(
            "Błąd krytyczny", 
            f"Nie można uruchomić aplikacji:\n{e}\n\nSprawdź konfigurację i spróbuj ponownie."
        )
        sys.exit(1)


if __name__ == "__main__":
    print("Uruchamianie Dziennik Transakcji AI 3.0...")
    print("Sprawdzanie zależności...")
    
    # Sprawdź wymagane moduły
    required_modules = [
        'tkinter',
        'sqlite3', 
        'datetime',
        'threading',
        'csv'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    # Sprawdź tkcalendar osobno (może wymagać instalacji)
    try:
        import tkcalendar
    except ImportError:
        print("UWAGA: Moduł 'tkcalendar' nie jest zainstalowany.")
        print("Zainstaluj go poleceniem: pip install tkcalendar")
        missing_modules.append('tkcalendar')
    
    if missing_modules:
        print(f"Brakujące moduły: {', '.join(missing_modules)}")
        print("Zainstaluj je przed uruchomieniem aplikacji.")
        sys.exit(1)
    
    print("Wszystkie zależności są dostępne.")
    print("Uruchamianie aplikacji...")
    
    main()
