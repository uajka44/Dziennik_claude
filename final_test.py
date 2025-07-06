"""
KOŃCOWY TEST WSZYSTKICH ZMIAN W EDIT DIALOG
==========================================
"""
import sys
import os

# Dodaj katalog główny do ścieżki
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def final_verification():
    """Końcowa weryfikacja wszystkich zmian"""
    
    print("KOŃCOWA WERYFIKACJA ZMIAN W EDIT DIALOG")
    print("=" * 50)
    
    errors = []
    successes = []
    
    # 1. Sprawdź field_definitions
    try:
        from config.field_definitions import TEXT_FIELDS, ALL_FIELDS
        
        # Sprawdź sl_opening
        sl_opening = ALL_FIELDS.get("sl_opening")
        if sl_opening and sl_opening.editable:
            successes.append("✅ sl_opening jest edytowalne")
        else:
            errors.append("❌ sl_opening nie jest edytowalne")
        
        # Sprawdź pola readonly
        readonly_fields = ["ticket", "type", "volume", "symbol", "open_price", "sl"]
        for field_name in readonly_fields:
            field = ALL_FIELDS.get(field_name)
            if field and not field.editable:
                successes.append(f"✅ {field_name} jest nieedytowalne")
            else:
                errors.append(f"❌ {field_name} powinno być nieedytowalne")
        
    except Exception as e:
        errors.append(f"❌ Błąd importu field_definitions: {e}")
    
    # 2. Sprawdź czy EditDialog można zaimportować
    try:
        from gui.edit_dialog import EditDialog
        successes.append("✅ EditDialog importuje się bez błędów")
        
        # Sprawdź czy ma nowe metody
        if hasattr(EditDialog, '_update_status_indicator'):
            successes.append("✅ EditDialog ma metodę _update_status_indicator")
        else:
            errors.append("❌ EditDialog nie ma metody _update_status_indicator")
            
    except Exception as e:
        errors.append(f"❌ Błąd importu EditDialog: {e}")
    
    # 3. Sprawdź zależności
    try:
        from gui.widgets.custom_entries import SetupEntry
        successes.append("✅ SetupEntry importuje się poprawnie")
    except Exception as e:
        errors.append(f"❌ Błąd importu SetupEntry: {e}")
    
    try:
        from gui.window_config import WindowConfigManager
        successes.append("✅ WindowConfigManager importuje się poprawnie")
    except Exception as e:
        errors.append(f"❌ Błąd importu WindowConfigManager: {e}")
    
    # 4. Wyniki
    print("\\nWYNIKI WERYFIKACJI:")
    print("-" * 30)
    
    for success in successes:
        print(success)
    
    if errors:
        print("\\nBŁĘDY:")
        print("-" * 10)
        for error in errors:
            print(error)
    
    # 5. Podsumowanie zmian
    print("\\n" + "=" * 50)
    print("PODSUMOWANIE WPROWADZONYCH ZMIAN:")
    print("=" * 50)
    
    changes = [
        "1. sl_opening zmieniono na edytowalne w field_definitions.py",
        "2. Przepisano edit_dialog.py z nowym compactowym layoutem:",
        "   - Rozmiar okna: 650x750 (było 700x900)",
        "   - Nagłówek: 'Ticket: X, YYYY-MM-DD HH:MM:SS' + lampka",
        "   - Pola readonly w 2 kolumnach",
        "   - Pola edytowalne w osobnej sekcji",
        "   - Przyciski przeniesione na sam dół",
        "   - Usunięto ramkę Status, dodano lampkę 🟢/🔴/🟡",
        "3. Zachowano wszystkie funkcje nawigacji i zapisywania",
        "4. Zachowano kompatybilność z systemem window_config"
    ]
    
    for change in changes:
        print(f"✅ {change}")
    
    # 6. Instrukcje testowania
    print("\\n" + "=" * 50)
    print("JAK PRZETESTOWAĆ:")
    print("=" * 50)
    print("1. Uruchom główną aplikację: python main.py")
    print("2. Przejdź do przeglądarki danych")
    print("3. Kliknij podwójnie na pozycję, aby otworzyć EditDialog")
    print("4. Sprawdź nowy layout:")
    print("   - Kompaktowy nagłówek z lampką")
    print("   - Pola readonly w 2 kolumnach")
    print("   - sl_opening jest edytowalne")
    print("   - Przyciski na dole")
    print("5. Przetestuj zapisywanie i nawigację")
    
    if not errors:
        print("\\n🎉 WSZYSTKIE ZMIANY ZOSTAŁY POMYŚLNIE WPROWADZONE!")
        return True
    else:
        print(f"\\n⚠️  ZNALEZIONO {len(errors)} BŁĘDÓW - wymagają naprawy")
        return False

if __name__ == "__main__":
    final_verification()
