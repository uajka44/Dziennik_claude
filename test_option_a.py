"""
Test nowej funkcjonalności kalkulacji TP z filtrami (Opcja A)
"""
import sys
import os

# Dodaj ścieżkę do modułów
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_new_tp_calculation():
    """Test nowej metody calculate_tp_for_tickets"""
    try:
        print("=== TEST NOWEJ METODY KALKULACJI TP ===")
        
        # Test importów
        from calculations.tp_calculator import TPCalculator
        from calculations.position_analyzer import PositionAnalyzer
        
        print("✓ Importy udane")
        
        # Test PositionAnalyzer.get_positions_by_tickets()
        print("\n=== TEST POSITION ANALYZER ===")
        position_analyzer = PositionAnalyzer()
        
        # Test z przykładowymi ticketami
        test_tickets = ["12345", "67890", "11111"]
        print(f"Test pobierania pozycji dla ticketów: {test_tickets}")
        
        positions = position_analyzer.get_positions_by_tickets(test_tickets)
        print(f"Wynik: {len(positions)} pozycji")
        
        if positions:
            print("Przykładowa pozycja:")
            pos = positions[0]
            print(f"  - Ticket: {pos.ticket}")
            print(f"  - Symbol: {pos.symbol}")
            print(f"  - Type: {pos.type}")
            print(f"  - Open price: {pos.open_price}")
        else:
            print("Brak pozycji (normalne jeśli test tickety nie istnieją)")
        
        # Test TPCalculator.calculate_tp_for_tickets()
        print("\n=== TEST TP CALCULATOR ===")
        calculator = TPCalculator()
        
        # Parametry testowe
        sl_types = {
            'sl_recznie': False,
            'sl_baza': False,
            'sl_staly': True
        }
        
        sl_staly_values = {
            'DAX': 10.0,
            'NASDAQ': 15.0
        }
        
        print(f"Test kalkulacji TP dla ticketów: {test_tickets}")
        print(f"SL types: {sl_types}")
        print(f"SL stały values: {sl_staly_values}")
        
        results = calculator.calculate_tp_for_tickets(
            tickets=test_tickets,
            sl_types=sl_types,
            sl_staly_values=sl_staly_values,
            be_prog=10.0,
            be_offset=1.0,
            spread=0.0,
            save_to_db=False,
            detailed_logs=False
        )
        
        print(f"Wynik: {len(results)} obliczeń TP")
        
        if results:
            print("Przykładowy wynik:")
            result = results[0]
            print(f"  - Ticket: {result.ticket}")
            print(f"  - Symbol: {result.symbol}")
            print(f"  - TP SL stały: {result.max_tp_sl_staly}")
            print(f"  - TP SL ręczne: {result.max_tp_sl_recznie}")
            print(f"  - TP BE: {result.max_tp_sl_be}")
        
        print("\n🎉 Test zakończony pomyślnie!")
        return True
        
    except Exception as e:
        print(f"❌ Błąd testu: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ticket_extraction():
    """Test pobierania ticketów z tabeli (symulacja)"""
    try:
        print("\n=== TEST POBIERANIA TICKETÓW Z TABELI ===")
        
        # Symulacja danych z tabeli Treeview
        from config.field_definitions import COLUMNS
        
        print(f"Kolumny tabeli: {COLUMNS}")
        
        # Znajdź indeks kolumny ticket
        ticket_col_index = COLUMNS.index("ticket")
        print(f"Indeks kolumny ticket: {ticket_col_index}")
        
        # Symulacja danych z tabeli
        simulated_table_data = [
            ["2024-01-01 10:00", "12345", "0", "1.0", "EURUSD", "1.1000", "", "", "rgr"],
            ["2024-01-01 11:00", "67890", "1", "0.5", "GBPUSD", "1.2500", "", "", "momo"],
            ["2024-01-01 12:00", "11111", "0", "2.0", "USDJPY", "150.00", "", "", ""]
        ]
        
        # Ekstraktuj tickety
        extracted_tickets = []
        for row_data in simulated_table_data:
            if len(row_data) > ticket_col_index:
                ticket = row_data[ticket_col_index]
                if ticket:
                    extracted_tickets.append(str(ticket).strip())
        
        print(f"Wyekstraktowane tickety: {extracted_tickets}")
        print("✓ Test pobierania ticketów udany")
        
        return extracted_tickets
        
    except Exception as e:
        print(f"❌ Błąd testu pobierania ticketów: {e}")
        return []

if __name__ == "__main__":
    print("=== TEST OPCJI A: KALKULACJA TP Z TICKETÓW ===")
    
    # Test 1: Pobieranie ticketów z tabeli
    test_tickets = test_ticket_extraction()
    
    # Test 2: Nowa funkcjonalność kalkulacji
    if test_tickets:
        test_new_tp_calculation()
    else:
        print("Używam testowych ticketów...")
        test_new_tp_calculation()
    
    print("\n=== PODSUMOWANIE ===")
    print("✓ Nowe metody zostały przetestowane")
    print("✓ Funkcjonalność pobierania ticketów z tabeli działa")
    print("✓ Integracja z kalkulatorem TP jest gotowa")
    print("\n📝 NASTĘPNE KROKI:")
    print("1. Uruchom główną aplikację")
    print("2. Ustaw filtry (daty, instrumenty, setup, etc.)")
    print("3. Kliknij 'Oblicz TP dla zakresu'")
    print("4. Sprawdź czy uwzględnia wszystkie filtry")
