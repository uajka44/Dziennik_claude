"""
Migrator dla danych SL opening z tabeli position_opening_sl do positions
"""
import sqlite3
from datetime import datetime
from database.connection import get_db_connection, execute_query, execute_update
from config.database_config import DB_PATH, POSITIONS_TABLE


class SLOpeningMigrator:
    """Klasa do migracji danych SL opening między tabelami"""
    
    def __init__(self):
        self.backup_created = False
    
    def run_migration(self):
        """Główna metoda migracji - uruchamiana przy starcie i przy wyszukaj"""
        try:
            # 1. Sprawdź czy kolumna sl_opening istnieje, jeśli nie - dodaj
            self._ensure_sl_opening_column()
            
            # 2. Stwórz backup (jednorazowo)
            if not self.backup_created:
                self._create_backup()
                self.backup_created = True
            
            # 3. Migruj dane
            migrated_count = self._migrate_data()
            
            print(f"[SL Migration] Zmigrowano {migrated_count} rekordów")
            return migrated_count
            
        except Exception as e:
            print(f"[SL Migration] Błąd migracji: {e}")
            return 0
    
    def _ensure_sl_opening_column(self):
        """Sprawdza czy kolumna sl_opening istnieje w tabeli positions, jeśli nie - dodaje"""
        try:
            # Sprawdź czy kolumna już istnieje
            query = f"PRAGMA table_info({POSITIONS_TABLE})"
            columns = execute_query(query)
            
            column_names = [col[1] for col in columns]  # col[1] to nazwa kolumny
            
            if 'sl_opening' not in column_names:
                print("[SL Migration] Dodaję kolumnę sl_opening do tabeli positions...")
                
                # Dodaj kolumnę sl_opening
                alter_query = f"ALTER TABLE {POSITIONS_TABLE} ADD COLUMN sl_opening REAL"
                execute_update(alter_query)
                
                print("[SL Migration] Kolumna sl_opening została dodana!")
            else:
                print("[SL Migration] Kolumna sl_opening już istnieje")
                
        except Exception as e:
            print(f"[SL Migration] Błąd przy sprawdzaniu/dodawaniu kolumny: {e}")
            raise
    
    def _create_backup(self):
        """Tworzy jednorazowy backup tabeli position_opening_sl"""
        try:
            # Sprawdź czy backup już istnieje
            check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='position_opening_sl_backup'"
            existing = execute_query(check_query)
            
            if existing:
                print("[SL Migration] Backup już istnieje")
                return
            
            # Sprawdź czy tabela position_opening_sl istnieje
            check_source = "SELECT name FROM sqlite_master WHERE type='table' AND name='position_opening_sl'"
            source_exists = execute_query(check_source)
            
            if not source_exists:
                print("[SL Migration] Tabela position_opening_sl nie istnieje - pomijam backup")
                return
            
            # Stwórz backup
            backup_query = """
            CREATE TABLE position_opening_sl_backup AS 
            SELECT * FROM position_opening_sl
            """
            execute_update(backup_query)
            
            # Dodaj timestamp do backupu
            timestamp_query = """
            ALTER TABLE position_opening_sl_backup 
            ADD COLUMN backup_created TEXT DEFAULT CURRENT_TIMESTAMP
            """
            execute_update(timestamp_query)
            
            print(f"[SL Migration] Utworzono backup tabeli position_opening_sl")
            
        except Exception as e:
            print(f"[SL Migration] Błąd tworzenia backupu: {e}")
            # Nie przerywamy migracji z powodu błędu backupu
    
    def _migrate_data(self):
        """Migruje dane z position_opening_sl do positions.sl_opening"""
        try:
            # Sprawdź czy tabela position_opening_sl istnieje
            check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='position_opening_sl'"
            table_exists = execute_query(check_query)
            
            if not table_exists:
                print("[SL Migration] Tabela position_opening_sl nie istnieje")
                return 0
            
            # Pobierz wszystkie dane z position_opening_sl
            select_query = "SELECT ticket, sl_opening FROM position_opening_sl"
            opening_sl_data = execute_query(select_query)
            
            if not opening_sl_data:
                print("[SL Migration] Brak danych do migracji")
                return 0
            
            migrated_count = 0
            
            for ticket, sl_value in opening_sl_data:
                try:
                    # Sprawdź czy ticket istnieje w positions i czy sl_opening jest NULL
                    check_positions_query = f"""
                    SELECT ticket, sl_opening FROM {POSITIONS_TABLE} 
                    WHERE ticket = ? AND (sl_opening IS NULL OR sl_opening = '')
                    """
                    existing_position = execute_query(check_positions_query, (ticket,))
                    
                    if existing_position:
                        # Ticket istnieje w positions i sl_opening jest puste - aktualizuj
                        print(f"[SL Migration] Znaleziono ticket {ticket} w positions, sl_opening={existing_position[0][1]}")
                        
                        update_query = f"""
                        UPDATE {POSITIONS_TABLE} 
                        SET sl_opening = ? 
                        WHERE ticket = ?
                        """
                        
                        print(f"[SL Migration] Wykonuję UPDATE dla ticket {ticket}: sl_opening = {sl_value}")
                        rows_affected = execute_update(update_query, (sl_value, ticket))
                        print(f"[SL Migration] UPDATE zwrócił rows_affected = {rows_affected}")
                        
                        if rows_affected > 0:
                            # Sprawdź czy rzeczywiście się zapisało
                            verify_query = f"SELECT sl_opening FROM {POSITIONS_TABLE} WHERE ticket = ?"
                            verify_result = execute_query(verify_query, (ticket,))
                            
                            if verify_result and verify_result[0][0] == sl_value:
                                # Aktualizacja się udała - usuń z position_opening_sl
                                delete_query = "DELETE FROM position_opening_sl WHERE ticket = ?"
                                execute_update(delete_query, (ticket,))
                                migrated_count += 1
                                print(f"[SL Migration] ✅ Zmigrowano ticket {ticket}: sl_opening = {sl_value}")
                            else:
                                print(f"[SL Migration] ❌ Weryfikacja nieudana dla ticket {ticket}: oczekiwano {sl_value}, znaleziono {verify_result[0][0] if verify_result else 'NULL'}")
                        else:
                            print(f"[SL Migration] ❌ UPDATE nie wpłynął na żadne wiersze dla ticket {ticket}")
                    else:
                        # Ticket nie istnieje w positions lub sl_opening już ma wartość - zostaw w position_opening_sl
                        position_exists_query = f"SELECT ticket FROM {POSITIONS_TABLE} WHERE ticket = ?"
                        position_check = execute_query(position_exists_query, (ticket,))
                        
                        if position_check:
                            print(f"[SL Migration] Ticket {ticket} już ma sl_opening - pomijam")
                        else:
                            print(f"[SL Migration] Ticket {ticket} nie istnieje w positions - zostawiam w buforze")
                
                except Exception as e:
                    print(f"[SL Migration] Błąd przy migrowaniu ticket {ticket}: {e}")
                    continue
            
            return migrated_count
            
        except Exception as e:
            print(f"[SL Migration] Błąd podczas migracji danych: {e}")
            return 0
    
    def get_migration_status(self):
        """Zwraca status migracji - ile zostało rekordów w position_opening_sl"""
        try:
            # Sprawdź czy tabela istnieje
            check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='position_opening_sl'"
            table_exists = execute_query(check_query)
            
            if not table_exists:
                return {"table_exists": False, "pending_records": 0}
            
            # Policz rekordy w position_opening_sl
            count_query = "SELECT COUNT(*) FROM position_opening_sl"
            result = execute_query(count_query)
            pending_count = result[0][0] if result else 0
            
            return {
                "table_exists": True, 
                "pending_records": pending_count,
                "backup_exists": self._backup_exists()
            }
            
        except Exception as e:
            print(f"[SL Migration] Błąd sprawdzania statusu: {e}")
            return {"table_exists": False, "pending_records": 0, "error": str(e)}
    
    def check_backup_for_ticket(self, ticket):
        """Sprawdza czy dany ticket istnieje w backupie"""
        try:
            # Sprawdź czy backup istnieje
            if not self._backup_exists():
                return {"backup_exists": False, "ticket_found": False}
            
            # Szukaj ticket w backupie
            query = "SELECT ticket, sl_opening FROM position_opening_sl_backup WHERE ticket = ?"
            result = execute_query(query, (ticket,))
            
            if result:
                ticket_data = result[0]
                return {
                    "backup_exists": True,
                    "ticket_found": True,
                    "ticket": ticket_data[0],
                    "sl_value": ticket_data[1]
                }
            else:
                return {
                    "backup_exists": True,
                    "ticket_found": False
                }
                
        except Exception as e:
            return {"error": str(e)}

    def restore_from_backup(self):
        """Przywraca dane z backupu do position_opening_sl (w przypadku problemów)"""
        try:
            if not self._backup_exists():
                return {"success": False, "error": "Backup nie istnieje"}
            
            # Sprawdź ile jest rekordów w backupie
            count_query = "SELECT COUNT(*) FROM position_opening_sl_backup"
            backup_count = execute_query(count_query)[0][0]
            
            if backup_count == 0:
                return {"success": False, "error": "Backup jest pusty"}
            
            # Przywróć dane do position_opening_sl
            restore_query = """
            INSERT OR REPLACE INTO position_opening_sl (ticket, sl_opening, opening_time)
            SELECT ticket, sl_opening, opening_time FROM position_opening_sl_backup
            """
            
            rows_affected = execute_update(restore_query)
            
            return {
                "success": True, 
                "restored_count": rows_affected,
                "message": f"Przywrócono {rows_affected} rekordów z backupu"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def restore_from_backup(self):
        """Przywraca dane z backupu do positions.sl_opening"""
        try:
            # Sprawdź czy backup istnieje
            if not self._backup_exists():
                print("[SL Migration] Backup nie istnieje")
                return 0
            
            print("[SL Migration] Rozpoczynam przywracanie z backupu...")
            
            # Sprawdź strukturę backupu
            structure_query = "PRAGMA table_info(position_opening_sl_backup)"
            columns_info = execute_query(structure_query)
            column_names = [col[1] for col in columns_info]
            
            # Znajdź kolumnę SL w backupie
            sl_column = None
            if 'sl' in column_names:
                sl_column = 'sl'
            elif 'stop_loss' in column_names:
                sl_column = 'stop_loss'
            elif 'sl_value' in column_names:
                sl_column = 'sl_value'
            else:
                print(f"[SL Migration] Nie można znaleźć kolumny SL w backupie. Dostępne: {column_names}")
                return 0
            
            print(f"[SL Migration] Używam kolumny: {sl_column}")
            
            # Pobierz dane z backupu
            backup_query = f"SELECT ticket, {sl_column} FROM position_opening_sl_backup"
            backup_data = execute_query(backup_query)
            
            if not backup_data:
                print("[SL Migration] Brak danych w backupie")
                return 0
            
            print(f"[SL Migration] Znaleziono {len(backup_data)} rekordów w backupie")
            
            restored_count = 0
            
            for ticket, sl_value in backup_data:
                try:
                    # Sprawdź czy ticket istnieje w positions
                    check_query = f"SELECT ticket, sl_opening FROM {POSITIONS_TABLE} WHERE ticket = ?"
                    existing = execute_query(check_query, (ticket,))
                    
                    if existing:
                        current_sl_opening = existing[0][1]
                        
                        # Aktualizuj tylko jeśli sl_opening jest NULL lub puste
                        if current_sl_opening is None or current_sl_opening == '':
                            update_query = f"UPDATE {POSITIONS_TABLE} SET sl_opening = ? WHERE ticket = ?"
                            rows_affected = execute_update(update_query, (sl_value, ticket))
                            
                            if rows_affected > 0:
                                # Weryfikuj czy się zapisało
                                verify_query = f"SELECT sl_opening FROM {POSITIONS_TABLE} WHERE ticket = ?"
                                verify_result = execute_query(verify_query, (ticket,))
                                
                                if verify_result and verify_result[0][0] == sl_value:
                                    restored_count += 1
                                    print(f"[SL Migration] ✅ Przywrócono ticket {ticket}: sl_opening = {sl_value}")
                                else:
                                    print(f"[SL Migration] ❌ Weryfikacja nieudana dla ticket {ticket}")
                            else:
                                print(f"[SL Migration] ❌ UPDATE nie wpłynął na ticket {ticket}")
                        else:
                            print(f"[SL Migration] ⏭️ Ticket {ticket} już ma sl_opening = {current_sl_opening}")
                    else:
                        print(f"[SL Migration] ⚠️ Ticket {ticket} nie istnieje w positions")
                        
                except Exception as e:
                    print(f"[SL Migration] Błąd przy ticket {ticket}: {e}")
                    continue
            
            print(f"[SL Migration] Przywrócono {restored_count} rekordów z backupu")
            return restored_count
            
        except Exception as e:
            print(f"[SL Migration] Błąd przywracania z backupu: {e}")
            return 0
    
    def _backup_exists(self):
        """Sprawdza czy backup istnieje"""
        try:
            check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='position_opening_sl_backup'"
            result = execute_query(check_query)
            return len(result) > 0
        except:
            return False


# Singleton instance
_migrator_instance = None

def get_sl_migrator():
    """Zwraca singleton instance migratora"""
    global _migrator_instance
    if _migrator_instance is None:
        _migrator_instance = SLOpeningMigrator()
    return _migrator_instance
