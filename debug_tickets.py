"""
Debug script dla nawigacji - sprawdza formaty ticketów
"""
import sys
import os

# Dodaj ścieżkę do modułów
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import execute_query
from config.field_definitions import COLUMNS
from utils.date_utils import date_range_to_unix
from datetime import date


def debug_tickets():
    """Debuguje formaty ticketów w bazie danych"""
    
    print("=== DEBUG TICKETÓW ===")
    
    # Pobierz kilka pozycji z dzisiaj
    today = date.today()
    start_unix, end_unix = date_range_to_unix(today, today)
    
    columns_str = ", ".join(COLUMNS)
    query = f"""
    SELECT {columns_str}
    FROM positions 
    WHERE open_time BETWEEN ? AND ?
    ORDER BY open_time
    LIMIT 5
    """
    
    rows = execute_query(query, (start_unix, end_unix))
    
    print(f"Znaleziono {len(rows)} pozycji")
    
    ticket_index = COLUMNS.index("ticket")
    
    for i, row in enumerate(rows):
        ticket = row[ticket_index]
        
        print(f"\n--- Pozycja {i+1} ---")
        print(f"Surowy ticket: {repr(ticket)}")
        print(f"Typ: {type(ticket)}")
        print(f"String: '{str(ticket)}'")
        print(f"String stripped: '{str(ticket).strip()}'")
        print(f"String rstrip \\x00: '{str(ticket).strip().rstrip(chr(0))}'")
        
        # Test porównań
        test_values = [
            str(ticket),
            str(ticket).strip(),
            str(ticket).strip().rstrip('\x00'),
            str(ticket).strip().rstrip(chr(0))
        ]
        
        print(f"Wszystkie reprezentacje:")
        for j, val in enumerate(test_values):
            print(f"  {j}: '{val}' (len={len(val)})")


if __name__ == "__main__":
    debug_tickets()
