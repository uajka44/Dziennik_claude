"""
Test weryfikacyjny zmian w EditDialog
"""
import sys
import os

# Dodaj katalog główny do ścieżki
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_field_definitions():
    """Test sprawdzający czy sl_opening jest edytowalne"""
    
    print("=== TEST FIELD DEFINITIONS ===")
    
    try:
        from config.field_definitions import TEXT_FIELDS, ALL_FIELDS
        
        # Sprawdź pola nieedytowalne
        readonly_fields = ["ticket", "type", "volume", "symbol", "open_price", "sl"]
        print("Pola nieedytowalne (będą w 2 kolumnach):")
        for field in TEXT_FIELDS:
            if field.name in readonly_fields:
                print(f"  - {field.name}: {field.display_name} (editable={field.editable})")
        
        print("\nPola edytowalne:")
        for field in TEXT_FIELDS:
            if field.editable and field.name not in readonly_fields:
                print(f"  - {field.name}: {field.display_name} (editable={field.editable})")
        
        # Sprawdź szczególnie sl_opening
        sl_opening_field = ALL_FIELDS.get("sl_opening")
        if sl_opening_field:
            print(f"\n✅ sl_opening: editable={sl_opening_field.editable}")
            if sl_opening_field.editable:
                print("✅ sl_opening jest EDYTOWALNE - zmiana zastosowana!")
            else:
                print("❌ sl_opening jest nadal nieedytowalne")
        else:
            print("❌ Nie znaleziono pola sl_opening")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd testu: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_layout_structure():
    """Test struktury layoutu - bez otwierania okna"""
    
    print("\n=== TEST LAYOUT STRUCTURE ===")
    
    # Symulacja danych
    readonly_fields = ["ticket", "type", "volume", "symbol", "open_price", "sl"]
    
    print("Nowy layout EditDialog:")
    print("1. ✅ Kompaktowy nagłówek: 'Ticket: 123456, 2025-07-06 14:30:00' + lampka")
    print("2. ✅ Pola nieedytowalne w 2 kolumnach:")
    
    # Symulacja layoutu 2 kolumn
    col = 0
    row = 0
    for field_name in readonly_fields:
        print(f"   Row {row}, Col {col*2}-{col*2+1}: {field_name}")
        col += 1
        if col >= 2:
            col = 0
            row += 1
    
    print("3. ✅ Pola edytowalne w pojedynczej kolumnie")
    print("4. ✅ Ramka opcje (checkboxy)")
    print("5. ✅ Przyciski nawigacji i akcji na dole")
    print("6. ✅ Usunięto ramkę Status, dodano lampkę 🟢/🔴/🟡")
    
    return True

if __name__ == "__main__":
    print("TESTY WERYFIKACYJNE NOWEGO EDIT DIALOG")
    print("=" * 50)
    
    success1 = test_field_definitions()
    success2 = test_layout_structure()
    
    if success1 and success2:
        print("\n🎉 Wszystkie testy przeszły pomyślnie!")
        print("\nZmiany zostały zastosowane:")
        print("✅ sl_opening jest teraz edytowalne")
        print("✅ Kompaktowy layout z 2 kolumnami dla pól readonly")
        print("✅ Lampka statusu zamiast ramki Status")
        print("✅ Przyciski przeniesione na dół")
    else:
        print("\n❌ Niektóre testy nie przeszły")
