"""
Manager okien edycji - zapewnia że tylko jedno okno edycji jest otwarte w danym czasie
oraz komunikuje z MQL5 o aktualnie edytowanej pozycji przez bazę danych
"""
import threading


class EditWindowManager:
    """Singleton manager dla okien edycji"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._current_window = None
        self._current_ticket = None
        
        # Import communication managera
        from database.communication import get_communication_manager
        self.communication = get_communication_manager()
        
        print(f"[EditManager] Komunikacja przez bazę danych multi_candles.db")
        self._initialized = True
        
        # Inicjalizacja - oznacz że nic nie edytujemy
        self._save_current_ticket(0)
    
    def open_edit_window(self, parent, ticket, values, callback=None, 
                        navigation_handler=None, save_current_first=False):
        """
        Otwiera okno edycji dla podanego ticket
        
        Args:
            parent: Okno rodzic dla dialogu edycji
            ticket: Numer ticket pozycji do edycji
            values: Wartości do edycji (tuple z treeview)
            callback: Opcjonalna funkcja callback po zapisaniu zmian
            navigation_handler: Handler dla nawigacji (next/prev)
            save_current_first: Czy zapisać poprzednie okno przed otwarciem nowego
            
        Returns:
            EditDialog: Instancja okna edycji
        """
        # Zapisz poprzednie okno jeśli żądano
        if save_current_first and self._current_window is not None:
            try:
                self._current_window._save_changes_silent()
                print(f"[EditManager] Zapisano poprzednie okno przed otwarciem nowego")
            except Exception as e:
                print(f"[EditManager] Błąd zapisu poprzedniego okna: {e}")
        
        # Zamknij poprzednie okno jeśli istnieje
        self.close_current_window()
        
        # Importuj tutaj aby uniknąć circular import
        from gui.edit_dialog import EditDialog
        
        # Stwórz nowe okno edycji
        edit_window = EditDialog(parent, ticket, values, 
                                on_save_callback=callback,
                                on_close_callback=self._on_window_closed)
        
        # Ustaw nawigację jeśli podano handler
        if navigation_handler:
            next_callback = lambda: navigation_handler.navigate_next(ticket)
            prev_callback = lambda: navigation_handler.navigate_prev(ticket)
            edit_window.set_navigation_callbacks(next_callback, prev_callback)
        
        # Zapisz referencje
        self._current_window = edit_window
        self._current_ticket = ticket
        
        # Komunikuj z MQL5
        self._save_current_ticket(ticket)
        
        print(f"[EditManager] Otwarto okno edycji dla ticket: {ticket}")
        return edit_window
    
    def close_current_window(self):
        """Zamyka aktualnie otwarte okno edycji"""
        if self._current_window is not None:
            try:
                self._current_window.destroy()
            except:
                pass  # Okno mogło już być zamknięte
            
            self._current_window = None
            self._current_ticket = None
            
            # Komunikuj z MQL5 że nic nie edytujemy
            self._save_current_ticket(0)
            print("[EditManager] Zamknięto okno edycji")
    
    def _on_window_closed(self):
        """Callback wywoływany gdy okno zostanie zamknięte"""
        self._current_window = None
        self._current_ticket = None
        self._save_current_ticket(0)
        print("[EditManager] Okno edycji zostało zamknięte")
    
    def _save_current_ticket(self, ticket):
        """
        Zapisuje aktualny ticket do bazy danych
        
        Args:
            ticket: Numer ticket (0 oznacza brak edycji)
        """
        try:
            self.communication.set_current_edit_ticket(ticket)
            print(f"[EditManager] Zapisano ticket do bazy: {ticket}")
            
        except Exception as e:
            print(f"[EditManager] Błąd zapisu do bazy: {e}")
    
    def get_current_ticket(self):
        """Zwraca aktualnie edytowany ticket (lub None)"""
        return self._current_ticket
    
    def is_editing(self):
        """Sprawdza czy jakieś okno edycji jest otwarte"""
        return self._current_window is not None
    
    def get_communication_file_path(self):
        """Zwraca informacje o komunikacji"""
        return f"Komunikacja przez bazę danych: multi_candles.db -> tabela communication"
