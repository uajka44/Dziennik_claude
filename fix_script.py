#!/usr/bin/env python3
"""
Skrypt do naprawy logiki filtra 007 w data_viewer.py
"""

def fix_filter_logic():
    """Naprawia logikę filtra 007"""
    
    file_path = r"E:\Trading\dziennik\python\Dziennik_claude\gui\data_viewer.py"
    
    # Przeczytaj plik
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Zamień starą logikę na nową
    old_logic = """            # Warunek dla filtra Magic Number 007
            magic_007_filter_active = self.magic_007_filter_var.get()
            if magic_007_filter_active:
                # Jeśli filtr 007 jest zaznaczony, pokazuj tylko trejdy z magic_number = 007
                where_conditions.append("magic_number = ?")
                base_params.append(7)
                print("Filtr 007 aktywny - pokazuję tylko trejdy z magic_number = 7")
            else:
                # Jeśli filtr 007 jest odznaczony, ukryj trejdy z magic_number = 007
                where_conditions.append("(magic_number IS NULL OR magic_number != ?)")
                base_params.append(7)
                print("Filtr 007 nieaktywny - ukrywam trejdy z magic_number = 7")"""

    new_logic = """            # Warunek dla filtra Usuń 007
            remove_007_filter_active = self.remove_007_filter_var.get()
            if remove_007_filter_active:
                # Jeśli filtr "Usuń 007" jest zaznaczony, ukryj trejdy z magic_number = 7
                where_conditions.append("(magic_number IS NULL OR magic_number != ?)")
                base_params.append(7)
                print("Filtr 'Usuń 007' aktywny - ukrywam trejdy z magic_number = 7")
            else:
                # Jeśli filtr "Usuń 007" jest odznaczony, pokazuj wszystkie trejdy
                print("Filtr 'Usuń 007' nieaktywny - pokazuję wszystkie trejdy")"""
    
    # Sprawdź czy stara logika istnieje
    if old_logic in content:
        print("Znaleziono starą logikę filtra - zamieniam na nową...")
        content = content.replace(old_logic, new_logic)
        
        # Zapisz plik
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Logika filtra została pomyślnie zmieniona!")
        print()
        print("PODSUMOWANIE ZMIAN:")
        print("- Checkbox 'Usuń 007' jest domyślnie ODZNACZONY")
        print("- Gdy odznaczony: wyświetla WSZYSTKIE trejdy")
        print("- Gdy zaznaczony: ukrywa trejdy z magic_number = 7")
        
    else:
        print("❌ Nie znaleziono starej logiki filtra - może już została zmieniona?")
        
        # Sprawdź czy nowa logika już istnieje
        if "remove_007_filter_active" in content:
            print("✅ Nowa logika już istnieje w pliku")
        else:
            print("❌ Nie znaleziono ani starej, ani nowej logiki")

if __name__ == "__main__":
    fix_filter_logic()
