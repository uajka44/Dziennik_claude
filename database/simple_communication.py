"""
Minimalna wersja systemu komunikacji - tylko ticket
"""
from database.connection import get_db_connection


class SimpleCommunicationManager:
    """Uproszczona wersja managera komunikacji"""
    
    def __init__(self):
        self._ensure_simple_table()
    
    def _ensure_simple_table(self):
        """Tworzy prostą tabelę z tylko kluczem i wartością"""
        try:
            db = get_db_connection()
            
            # Bardzo prosta tabela
            query = """
            CREATE TABLE IF NOT EXISTS simple_communication (
                ticket INTEGER DEFAULT 0
            )
            """
            
            db.execute_update(query)
            
            # Wstaw pierwszy rekord jeśli tabela pusta
            check = db.execute_query("SELECT COUNT(*) FROM simple_communication")
            if check[0][0] == 0:
                db.execute_update("INSERT INTO simple_communication (ticket) VALUES (0)")
            
            print("[SimpleCommunicationManager] Prosta tabela komunikacji gotowa")
            
        except Exception as e:
            print(f"[SimpleCommunicationManager] Błąd: {e}")
    
    def set_current_edit_ticket(self, ticket):
        """Ustawia aktualny ticket"""
        try:
            db = get_db_connection()
            db.execute_update("UPDATE simple_communication SET ticket = ?", (int(ticket),))
            print(f"[SimpleCommunicationManager] Ustawiono ticket: {ticket}")
        except Exception as e:
            print(f"[SimpleCommunicationManager] Błąd zapisu: {e}")
    
    def get_current_edit_ticket(self):
        """Pobiera aktualny ticket"""
        try:
            db = get_db_connection()
            result = db.execute_query("SELECT ticket FROM simple_communication LIMIT 1")
            if result and len(result) > 0:
                return int(result[0][0])
            return 0
        except Exception as e:
            print(f"[SimpleCommunicationManager] Błąd odczytu: {e}")
            return 0
    
    def clear_edit_session(self):
        """Czyści sesję edycji"""
        self.set_current_edit_ticket(0)


# Test prostego systemu
if __name__ == "__main__":
    comm = SimpleCommunicationManager()
    
    # Test
    comm.set_current_edit_ticket(999)
    ticket = comm.get_current_edit_ticket()
    print(f"Test: zapisano 999, odczytano {ticket}")
    
    comm.clear_edit_session()
    ticket = comm.get_current_edit_ticket()
    print(f"Po wyczyszczeniu: {ticket}")
