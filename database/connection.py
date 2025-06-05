"""
Zarządzanie połączeniami z bazą danych - Thread-safe version
"""
import sqlite3
import threading
from config.database_config import DB_PATH


class DatabaseConnection:
    """Thread-safe zarządzanie połączeniami z bazą danych"""
    
    def __init__(self):
        # Używamy thread-local storage dla połączeń
        self._local = threading.local()
    
    def get_connection(self):
        """Zwraca połączenie z bazą danych dla aktualnego wątku"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            # check_same_thread=False pozwala na używanie w różnych wątkach, ale nadal thread-safe
            self._local.connection = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30.0)
            # Ustawienia dla lepszej wydajności
            self._local.connection.execute('PRAGMA journal_mode=WAL;')
            self._local.connection.execute('PRAGMA synchronous=NORMAL;')
            self._local.connection.execute('PRAGMA cache_size=10000;')
            self._local.connection.execute('PRAGMA temp_store=memory;')
        return self._local.connection
    
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
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30.0)
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA synchronous=NORMAL;')
    conn.execute('PRAGMA cache_size=10000;')
    conn.execute('PRAGMA temp_store=memory;')
    return conn
