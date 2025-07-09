#!/usr/bin/env python3
"""
Skrypt do naprawy logiki filtra 007 w data_viewer.py
"""

def fix_filter_007():
    """Poprawia logikę filtra 007 w data_viewer.py"""
    
    file_path = r"E:\Trading\dziennik\python\Dziennik_claude\gui\data_viewer.py"
    
    try:
        # Przeczytaj plik
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"Plik {file_path} przeczytany, rozmiar: {len(content)} znaków")
        
        # Sprawdź obecność starej logiki
        if "magic_007_filter_var" in content:
            print("✅ Znaleziono starą zmienną magic_007_filter_var")
            
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
            
            if old_logic in content:
                print("✅ Znaleziono starą logikę filtra - zamieniam...")
                content = content.replace(old_logic, new_logic)
                
                # Zapisz poprawiony plik
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("✅ Plik został pomyślnie zaktualizowany!")
                
            else:
                print("❌ Nie znaleziono dokładnej starej logiki")
                print("Sprawdzam obecność fragmentów...")
                
                # Sprawdź linie zawierające magic_007_filter_var
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if "magic_007_filter_var" in line:
                        print(f"Linia {i}: {line.strip()}")
        
        else:
            print("❌ Nie znaleziono magic_007_filter_var")
            
            if "remove_007_filter_var" in content:
                print("✅ Nowa zmienna remove_007_filter_var już istnieje")
            else:
                print("❌ Nie znaleziono ani starej, ani nowej zmiennej")
                
        print("\n" + "="*60)
        print("PODSUMOWANIE OCZEKIWANEGO DZIAŁANIA FILTRA:")
        print("- Checkbox 'Usuń 007' domyślnie ODZNACZONY")
        print("- Gdy ODZNACZONY: wyświetla WSZYSTKIE trejdy (nic nie filtruje)")
        print("- Gdy ZAZNACZONY: ukrywa trejdy z magic_number = 7")
        print("="*60)
                
    except Exception as e:
        print(f"❌ Błąd: {e}")

if __name__ == "__main__":
    print("Uruchamianie naprawy filtra 007...")
    fix_filter_007()
    print("Naprawa zakończona.")
