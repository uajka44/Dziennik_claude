"""
Skrypt czyszczący - usuwa niepotrzebne pliki po przejściu na komunikację przez bazę danych
"""
import os

def cleanup_old_files():
    """Usuwa stare pliki komunikacyjne"""
    
    files_to_remove = [
        "E:/Trading/dziennik/python/Dziennik_claude/utils/mql5_paths.py",
        "C:/Users/anasy/AppData/Roaming/MetaQuotes/Terminal/7B8FFB3E490B2B8923BCC10180ACB2DC/MQL5/Files/current_edit_ticket.txt"
    ]
    
    print("=== CZYSZCZENIE STARYCH PLIKÓW ===")
    
    for file_path in files_to_remove:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"✅ Usunięto: {file_path}")
            else:
                print(f"ℹ️ Nie istnieje: {file_path}")
        except Exception as e:
            print(f"❌ Błąd usuwania {file_path}: {e}")
    
    print("\n🎉 Czyszczenie zakończone!")
    print("📊 System używa teraz wyłącznie komunikacji przez bazę danych")

if __name__ == "__main__":
    cleanup_old_files()
