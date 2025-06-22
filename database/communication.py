"""
Zarządzanie tabelą komunikacji między Python a MQL5
"""
import sqlite3
import json
from datetime import datetime
from database.connection import get_db_connection


class CommunicationManager:
    """Manager komunikacji między Python a MQL5 przez bazę danych"""
    
    def __init__(self):
        self.table_name = "communication"
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Tworzy tabelę komunikacji jeśli nie istnieje"""
        try:
            db = get_db_connection()
            
            # Sprawdź czy tabela istnieje
            check_table_query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='communication'
            """
            
            result = db.execute_query(check_table_query)
            
            if not result or len(result) == 0:
                print("[CommunicationManager] Tworzenie tabeli communication...")
                
                create_table_query = """
                CREATE TABLE communication (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT DEFAULT 'python',
                    description TEXT
                )
                """
                
                db.execute_update(create_table_query)
                print("[CommunicationManager] Tabela communication utworzona")
            else:
                print("[CommunicationManager] Tabela communication już istnieje")
            
            # Dodaj podstawowe klucze jeśli nie istnieją
            self._init_default_keys()
            
        except Exception as e:
            print(f"[CommunicationManager] Błąd tworzenia tabeli: {e}")
            # Fallback - spróbuj stworzyć prostą tabelę
            self._create_simple_table()
    
    def _create_simple_table(self):
        """Tworzy prostą tabelę komunikacji jako fallback"""
        try:
            db = get_db_connection()
            simple_table_query = """
            CREATE TABLE IF NOT EXISTS communication (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
            
            db.execute_update(simple_table_query)
            print("[CommunicationManager] Utworzono prostą tabelę komunikacji")
            
        except Exception as e:
            print(f"[CommunicationManager] Błąd tworzenia prostej tabeli: {e}")
    
    def _init_default_keys(self):
        """Inicjalizuje podstawowe klucze komunikacji"""
        default_keys = [
            ("current_edit_ticket", "0", "Aktualnie edytowany ticket (0 = brak edycji)"),
            ("python_status", "active", "Status aplikacji Python"),
            ("last_edit_action", "none", "Ostatnia akcja edycji"),
            ("mql5_last_read", "0", "Timestamp ostatniego odczytu przez MQL5")
        ]
        
        for key, default_value, description in default_keys:
            self.set_value(key, default_value, description, auto_timestamp=False)
    
    def set_value(self, key, value, description=None, auto_timestamp=True):
        """
        Ustawia wartość dla klucza
        
        Args:
            key: Klucz komunikacji
            value: Wartość (konwertowana na string)
            description: Opis klucza
            auto_timestamp: Czy automatycznie zaktualizować timestamp
        """
        try:
            db = get_db_connection()
            
            # Spróbuj najpierw z pełną strukturą
            try:
                timestamp = datetime.now().isoformat() if auto_timestamp else None
                
                query = """
                INSERT OR REPLACE INTO communication 
                (key, value, timestamp, created_by, description)
                VALUES (?, ?, COALESCE(?, CURRENT_TIMESTAMP), 'python', COALESCE(?, description))
                """
                
                db.execute_update(query, (key, str(value), timestamp, description))
                
            except Exception as e1:
                # Fallback - użyj prostego zapytania
                print(f"[CommunicationManager] Fallback do prostej tabeli dla {key}")
                
                simple_query = "INSERT OR REPLACE INTO communication (key, value) VALUES (?, ?)"
                db.execute_update(simple_query, (key, str(value)))
            
            # Debug tylko dla ważnych zmian
            if key == "current_edit_ticket":
                print(f"[CommunicationManager] Ustawiono {key} = {value}")
                
        except Exception as e:
            print(f"[CommunicationManager] Błąd ustawienia {key}: {e}")
    
    def get_value(self, key, default=None):
        """
        Pobiera wartość dla klucza
        
        Args:
            key: Klucz komunikacji
            default: Wartość domyślna jeśli klucz nie istnieje
            
        Returns:
            str: Wartość klucza lub default
        """
        try:
            db = get_db_connection()
            
            query = "SELECT value FROM communication WHERE key = ?"
            result = db.execute_query(query, (key,))
            
            if result and len(result) > 0 and result[0] and len(result[0]) > 0:
                return result[0][0]
            else:
                return default
                
        except Exception as e:
            print(f"[CommunicationManager] Błąd odczytu {key}: {e}")
            return default
    
    def get_all_data(self):
        """Zwraca wszystkie dane komunikacji"""
        try:
            db = get_db_connection()
            
            query = """
            SELECT key, value, timestamp, created_by, description 
            FROM communication 
            ORDER BY key
            """
            
            result = db.execute_query(query)
            
            data = {}
            for row in result:
                data[row[0]] = {
                    "value": row[1],
                    "timestamp": row[2], 
                    "created_by": row[3],
                    "description": row[4]
                }
            
            return data
            
        except Exception as e:
            print(f"[CommunicationManager] Błąd odczytu wszystkich danych: {e}")
            return {}
    
    def set_current_edit_ticket(self, ticket):
        """Ustawia aktualnie edytowany ticket"""
        # Upewnij się że ticket jest liczbą
        try:
            ticket_int = int(ticket) if ticket is not None else 0
        except (ValueError, TypeError):
            print(f"[CommunicationManager] Błąd konwersji ticket: {ticket}")
            ticket_int = 0
        
        self.set_value("current_edit_ticket", ticket_int, "Aktualnie edytowany ticket")
        
        # Ustaw dodatkowe statusy
        if ticket_int > 0:
            self.set_value("last_edit_action", "edit_started")
        else:
            self.set_value("last_edit_action", "edit_ended")
    
    def get_current_edit_ticket(self):
        """Pobiera aktualnie edytowany ticket"""
        value = self.get_value("current_edit_ticket", "0")
        try:
            # Konwertuj na int, obsługuj różne formaty
            if value is None or value == "":
                return 0
            
            # Jeśli to już int
            if isinstance(value, int):
                return value
            
            # Jeśli to string
            if isinstance(value, str):
                # Usuń białe znaki i spróbuj skonwertować
                clean_value = value.strip()
                if clean_value == "" or clean_value.lower() == "none":
                    return 0
                return int(clean_value)
            
            # Fallback
            return int(value)
            
        except (ValueError, TypeError) as e:
            print(f"[CommunicationManager] Błąd konwersji ticket '{value}': {e}")
            return 0
    
    def clear_edit_session(self):
        """Czyści sesję edycji"""
        self.set_current_edit_ticket(0)
        self.set_value("last_edit_action", "session_cleared")
    
    def update_mql5_heartbeat(self):
        """Aktualizuje heartbeat z MQL5 (wywołane przez MQL5)"""
        self.set_value("mql5_last_read", int(datetime.now().timestamp()), "Ostatni odczyt przez MQL5")
    
    def is_python_active(self):
        """Sprawdza czy Python jest aktywny"""
        return self.get_value("python_status") == "active"
    
    def set_python_status(self, status):
        """Ustawia status aplikacji Python"""
        self.set_value("python_status", status, "Status aplikacji Python")
    
    def debug_print_all(self):
        """Wydrukuje wszystkie dane komunikacji (debug)"""
        data = self.get_all_data()
        print("\n=== DANE KOMUNIKACJI ===")
        for key, info in data.items():
            print(f"{key}: {info['value']} (czas: {info['timestamp']})")
        print("========================\n")


# Singleton instance
_communication_manager = None

def get_communication_manager():
    """Zwraca singleton instance CommunicationManager"""
    global _communication_manager
    if _communication_manager is None:
        _communication_manager = CommunicationManager()
    return _communication_manager


if __name__ == "__main__":
    # Test
    comm = CommunicationManager()
    
    # Test podstawowych operacji
    comm.set_current_edit_ticket(123456)
    print(f"Current ticket: {comm.get_current_edit_ticket()}")
    
    comm.debug_print_all()
    
    comm.clear_edit_session()
    print(f"After clear: {comm.get_current_edit_ticket()}")
