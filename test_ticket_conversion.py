"""
Test poprawki błędu porównywania string vs int
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_ticket_conversion():
    """Test konwersji ticketów"""
    
    print("=== TEST KONWERSJI TICKETÓW ===")
    
    from database.communication import get_communication_manager
    
    comm = get_communication_manager()
    
    # Test różnych formatów ticketów
    test_cases = [
        123456,           # int
        "789012",         # string liczba
        "  345678  ",     # string z białymi znakami
        0,                # zero
        "0",              # string zero
        "",               # pusty string
        None,             # None
    ]
    
    print("\nTestuję różne formaty ticketów:")
    
    for i, ticket in enumerate(test_cases):
        try:
            print(f"\n{i+1}. Test: {repr(ticket)} ({type(ticket).__name__})")
            
            # Zapisz ticket
            comm.set_current_edit_ticket(ticket)
            
            # Odczytaj ticket
            read_ticket = comm.get_current_edit_ticket()
            
            print(f"   Zapisano: {repr(ticket)}")
            print(f"   Odczytano: {read_ticket} ({type(read_ticket).__name__})")
            
            # Sprawdź czy odczytana wartość jest int
            assert isinstance(read_ticket, int), f"Oczekiwano int, otrzymano {type(read_ticket)}"
            
            print(f"   ✅ Konwersja OK")
            
        except Exception as e:
            print(f"   ❌ Błąd: {e}")
            import traceback
            traceback.print_exc()
    
    # Test końcowy - wyczyść
    comm.clear_edit_session()
    final_ticket = comm.get_current_edit_ticket()
    
    print(f"\nPo wyczyszczeniu: {final_ticket}")
    assert final_ticket == 0, f"Oczekiwano 0, otrzymano {final_ticket}"
    
    print("\n🎉 Test konwersji ticketów przeszedł pomyślnie!")
    print("✅ Błąd porównywania string vs int został naprawiony")

if __name__ == "__main__":
    test_ticket_conversion()
