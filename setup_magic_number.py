#!/usr/bin/env python3
"""
Skrypt dodający kolumnę magic_number do tabeli positions jeśli nie istnieje
"""

import sys
import os
import sqlite3

# Dodaj katalog główny do ścieżki
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def add_magic_number_column():
    """Dodaje kolumnę magic_number do tabeli positions"""
    print("=== DODAWANIE KOLUMNY MAGIC_NUMBER ===\n")
    
    try:
        from config.database_config import DB_PATH, DB_PATH2
        
        # Sprawdź które bazy istnieją
        databases = []
        if os.path.exists(DB_PATH):
            databases.append(("główna", DB_PATH))
        if os.path.exists(DB_PATH2):
            databases.append(("alternatywna", DB_PATH2))
        
        if not databases:
            print("❌ Nie znaleziono żadnej bazy danych!")
            print(f"Sprawdzone ścieżki:")
            print(f"  - {DB_PATH}")
            print(f"  - {DB_PATH2}")
            return False
        
        success_count = 0
        
        for db_name, db_path in databases:
            print(f"Przetwarzanie bazy {db_name}: {db_path}")
            
            try:
                # Połącz z bazą
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Sprawdź czy tabela positions istnieje
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='positions'")
                if not cursor.fetchone():
                    print(f"  ❌ Tabela 'positions' nie istnieje w bazie {db_name}")
                    conn.close()
                    continue
                
                # Sprawdź czy kolumna magic_number już istnieje
                cursor.execute("PRAGMA table_info(positions)")
                columns = [info[1] for info in cursor.fetchall()]
                
                if 'magic_number' in columns:
                    print(f"  ✅ Kolumna 'magic_number' już istnieje w bazie {db_name}")
                    
                    # Sprawdź ile rekordów ma magic_number
                    cursor.execute("SELECT COUNT(*) FROM positions WHERE magic_number IS NOT NULL")
                    count_with_magic = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM positions")
                    total_count = cursor.fetchone()[0]
                    
                    print(f"     - Rekordów z magic_number: {count_with_magic}/{total_count}")
                    
                else:
                    print(f"  📝 Dodawanie kolumny 'magic_number' do bazy {db_name}...")
                    
                    # Dodaj kolumnę
                    cursor.execute("ALTER TABLE positions ADD COLUMN magic_number INTEGER")
                    
                    print(f"  ✅ Kolumna 'magic_number' dodana do bazy {db_name}")
                
                # Opcjonalnie: dodaj przykładowe dane testowe
                print(f"  🔍 Sprawdzanie przykładowych danych...")
                
                # Sprawdź czy są jakieś rekordy
                cursor.execute("SELECT COUNT(*) FROM positions")
                total_records = cursor.fetchone()[0]
                
                if total_records > 0:
                    # Sprawdź czy są jakieś z magic_number = 7
                    cursor.execute("SELECT COUNT(*) FROM positions WHERE magic_number = 7")
                    magic_007_count = cursor.fetchone()[0]
                    
                    if magic_007_count == 0:
                        print(f"  💡 Brak rekordów z magic_number = 7. Czy dodać przykładowe? (y/n): ", end="")
                        try:
                            choice = input().lower().strip()
                            if choice in ['y', 'yes', 'tak', 't']:
                                # Znajdź pierwsze kilka ticketów i ustaw im magic_number = 7
                                cursor.execute("SELECT ticket FROM positions LIMIT 3")
                                sample_tickets = [row[0] for row in cursor.fetchall()]
                                
                                for ticket in sample_tickets:
                                    cursor.execute("UPDATE positions SET magic_number = 7 WHERE ticket = ?", (ticket,))
                                
                                conn.commit()
                                print(f"  ✅ Ustawiono magic_number = 7 dla {len(sample_tickets)} przykładowych rekordów")
                                print(f"     - Tickety: {sample_tickets}")
                            else:
                                print(f"  ⏭️ Pominięto dodawanie przykładowych danych")
                        except EOFError:
                            print(f"  ⏭️ Pominięto dodawanie przykładowych danych (brak input)")
                    else:
                        print(f"  ✅ Znaleziono {magic_007_count} rekordów z magic_number = 7")
                
                conn.commit()
                conn.close()
                success_count += 1
                print(f"  ✅ Baza {db_name} przetworzona pomyślnie\n")
                
            except Exception as e:
                print(f"  ❌ Błąd przetwarzania bazy {db_name}: {e}\n")
                if 'conn' in locals():
                    conn.close()
        
        if success_count > 0:
            print(f"🎉 Pomyślnie przetworzono {success_count} baz danych!")
            print("\nMożesz teraz uruchomić aplikację i używać filtra 007:")
            print("  python main.py")
            print("\nLub przetestować:")
            print("  python test_magic_filter.py")
            return True
        else:
            print("❌ Nie udało się przetworzyć żadnej bazy danych")
            return False
            
    except Exception as e:
        print(f"❌ Błąd ogólny: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_magic_number_stats():
    """Pokazuje statystyki magic_number w bazach"""
    print("\n=== STATYSTYKI MAGIC_NUMBER ===\n")
    
    try:
        from config.database_config import DB_PATH, DB_PATH2
        
        databases = []
        if os.path.exists(DB_PATH):
            databases.append(("główna", DB_PATH))
        if os.path.exists(DB_PATH2):
            databases.append(("alternatywna", DB_PATH2))
        
        for db_name, db_path in databases:
            print(f"Baza {db_name}: {db_path}")
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Sprawdź czy kolumna istnieje
                cursor.execute("PRAGMA table_info(positions)")
                columns = [info[1] for info in cursor.fetchall()]
                
                if 'magic_number' not in columns:
                    print(f"  ❌ Kolumna magic_number nie istnieje")
                    conn.close()
                    continue
                
                # Statystyki magic_number
                cursor.execute("""
                    SELECT 
                        magic_number,
                        COUNT(*) as count,
                        AVG(CASE WHEN profit_points IS NOT NULL THEN profit_points/100.0 ELSE 0 END) as avg_profit
                    FROM positions 
                    GROUP BY magic_number 
                    ORDER BY magic_number
                """)
                
                results = cursor.fetchall()
                
                print(f"  📊 Rozkład magic_number:")
                for magic_num, count, avg_profit in results:
                    magic_display = str(magic_num) if magic_num is not None else "NULL"
                    print(f"     {magic_display}: {count} transakcji, średni profit: {avg_profit:.2f}")
                
                # Specjalnie dla 007
                cursor.execute("SELECT COUNT(*) FROM positions WHERE magic_number = 7")
                count_007 = cursor.fetchone()[0]
                print(f"  🎯 Magic Number 007: {count_007} transakcji")
                
                conn.close()
                print()
                
            except Exception as e:
                print(f"  ❌ Błąd: {e}\n")
                if 'conn' in locals():
                    conn.close()
                    
    except Exception as e:
        print(f"❌ Błąd ogólny: {e}")

if __name__ == "__main__":
    print("Skrypt konfiguracji kolumny magic_number\n")
    
    print("Opcje:")
    print("1. Dodaj kolumnę magic_number (jeśli nie istnieje)")
    print("2. Pokaż statystyki magic_number")
    print("3. Oba powyższe")
    print("\nWybierz opcję (1/2/3): ", end="")
    
    try:
        choice = input().strip()
        
        if choice == "1":
            add_magic_number_column()
        elif choice == "2":
            show_magic_number_stats()
        elif choice == "3":
            success = add_magic_number_column()
            if success:
                show_magic_number_stats()
        else:
            print("Nieprawidłowy wybór. Uruchamiam opcję 1...")
            add_magic_number_column()
            
    except KeyboardInterrupt:
        print("\n\nPrzerwano przez użytkownika.")
    except EOFError:
        print("Brak input - uruchamiam opcję 1...")
        add_magic_number_column()
