"""
Zarządzanie połączeniami z bazą danych - Thread-safe version
"""
import sqlite3
import threading
import os
from config.database_config import DB_PATH, DB_PATH2


class DatabaseConnection:
    """Thread-safe zarządzanie połączeniami z bazą danych"""
    
    def __init__(self):
        # Używamy thread-local storage dla połączeń
        self._local = threading.local()
        # Przechowujemy aktualną ścieżkę do bazy
        self._current_db_path = None
    
    def get_connection(self):
        """Zwraca połączenie z bazą danych dla aktualnego wątku"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            # Spróbuj połączyć się z główną bazą
            db_path = self._get_available_db_path()
            self._current_db_path = db_path
            
            # check_same_thread=False pozwala na używanie w różnych wątkach, ale nadal thread-safe
            self._local.connection = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
            # Ustawienia dla lepszej wydajności
            self._local.connection.execute('PRAGMA journal_mode=WAL;')
            self._local.connection.execute('PRAGMA synchronous=NORMAL;')
            self._local.connection.execute('PRAGMA cache_size=10000;')
            self._local.connection.execute('PRAGMA temp_store=memory;')
            
            print(f"Połączono z bazą danych: {db_path}")
        return self._local.connection
    
    def _get_available_db_path(self):
        """Zwraca dostępną ścieżkę do bazy danych"""
        # Spróbuj główną bazę
        if os.path.exists(DB_PATH):
            return DB_PATH
        
        # Spróbuj alternatywną bazę
        if os.path.exists(DB_PATH2):
            print(f"Główna baza danych niedostępna ({DB_PATH})")
            print(f"Używam alternatywnej bazy: {DB_PATH2}")
            return DB_PATH2
        
        # Jeśli żadna nie istnieje, wyświetl błąd i spróbuj główną (może zostanie utworzona)
        print(f"UWAGA: Nie znaleziono żadnej bazy danych:")
        print(f"  - Główna: {DB_PATH}")
        print(f"  - Alternatywna: {DB_PATH2}")
        print(f"Próbuję połączyć się z główną bazą...")
        return DB_PATH
        
    def get_current_db_path(self):
        """Zwraca aktualnie używaną ścieżkę do bazy"""
        return self._current_db_path
    
    def close_connection(self):
        """Zamyka połączenie z bazą danych dla aktualnego wątku"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
    
    def execute_query(self, query, params=None):
        """Wykonuje zapytanie SELECT i zwraca wyniki"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()
    
    def execute_update(self, query, params=None):
        """Wykonuje zapytanie UPDATE/INSERT/DELETE"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.rowcount
        finally:
            cursor.close()
    
    def table_exists(self, table_name):
        """Sprawdza czy tabela istnieje"""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.execute_query(query, (table_name,))
        return len(result) > 0


# Globalna instancja dla całej aplikacji
_db_instance = DatabaseConnection()


# Funkcje pomocnicze dla łatwiejszego użycia
def get_db_connection():
    """Zwraca instancję połączenia z bazą danych"""
    return _db_instance

def execute_query(query, params=None):
    """Wykonuje zapytanie SELECT - thread-safe"""
    return _db_instance.execute_query(query, params)

def execute_update(query, params=None):
    """Wykonuje zapytanie UPDATE/INSERT/DELETE - thread-safe"""
    return _db_instance.execute_update(query, params)

def create_new_connection():
    """Tworzy nowe połączenie dla wątku (używane w obliczeniach TP)"""
    # Użyj tej samej logiki wyboru bazy co w głównej klasie
    db_path = _db_instance._get_available_db_path()
    conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA synchronous=NORMAL;')
    conn.execute('PRAGMA cache_size=10000;')
    conn.execute('PRAGMA temp_store=memory;')
    return conn

def get_current_database_info():
    """Zwraca informacje o aktualnie używanej bazie danych"""
    current_path = _db_instance.get_current_db_path()
    if current_path:
        if current_path == DB_PATH:
            return f"Główna baza: {current_path}"
        elif current_path == DB_PATH2:
            return f"Alternatywna baza: {current_path}"
        else:
            return f"Nieznana baza: {current_path}"
    else:
        return "Brak aktywnego połączenia z bazą"
