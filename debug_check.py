#!/usr/bin/env python
"""
Debug script - sprawdza czy nasze zmiany są w pliku data_viewer.py
"""

def check_data_viewer_file():
    """Sprawdza zawartość pliku data_viewer.py"""
    try:
        with open('gui/data_viewer.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Sprawdź kluczowe części naszych zmian
        checks = {
            'main_content_frame': 'main_content_frame' in content,
            'tp_frame': 'tp_frame' in content,
            'calculate_tp_button': 'calculate_tp_button' in content,
            'tp_tree': 'tp_tree' in content,
            'tp_settings_frame': 'tp_settings_frame' in content,
            '_calculate_tp_for_displayed_positions': '_calculate_tp_for_displayed_positions' in content,
            '_simulate_tp_calculations': '_simulate_tp_calculations' in content,
            'Kalkulator TP': 'Kalkulator TP' in content,
            'Oblicz TP dla': 'Oblicz TP dla' in content
        }
        
        print("🔍 Sprawdzanie zawartości pliku gui/data_viewer.py:")
        print("=" * 60)
        
        all_ok = True
        for check_name, result in checks.items():
            status = "✅" if result else "❌"
            print(f"{status} {check_name}: {result}")
            if not result:
                all_ok = False
        
        print("=" * 60)
        if all_ok:
            print("✅ Wszystkie nasze zmiany są w pliku!")
            print("📁 Problem może być z cache Pythona")
            print("💡 Spróbuj usunąć katalog __pycache__ ręcznie")
        else:
            print("❌ Część zmian nie została zapisana!")
            print("💡 Trzeba ponownie edytować plik")
        
        # Sprawdź rozmiar pliku
        file_size = len(content)
        lines_count = content.count('\n')
        print(f"\n📊 Statystyki pliku:")
        print(f"   - Rozmiar: {file_size} znaków")
        print(f"   - Linie: {lines_count}")
        
        # Znajdź fragment z naszymi zmianami
        if 'main_content_frame' in content:
            start_pos = content.find('main_content_frame')
            sample = content[start_pos:start_pos+200]
            print(f"\n📝 Przykład znalezionego kodu:")
            print(f"   {sample[:100]}...")
        
        return all_ok
        
    except FileNotFoundError:
        print("❌ Plik gui/data_viewer.py nie istnieje!")
        return False
    except Exception as e:
        print(f"❌ Błąd odczytu pliku: {e}")
        return False

if __name__ == "__main__":
    check_data_viewer_file()
