"""
Automatyczne wykrywanie ścieżki MQL5 Files dla komunikacji
"""
import os
import glob


def get_mql5_files_path():
    """Znajduje ścieżkę do katalogu MQL5/Files"""
    
    # Możliwe lokalizacje MetaTrader 5
    base_paths = [
        os.path.expanduser(r"~\AppData\Roaming\MetaQuotes\Terminal"),
        r"C:\Users\*\AppData\Roaming\MetaQuotes\Terminal",
        r"C:\Program Files\MetaTrader 5\MQL5\Files",
        r"C:\Program Files (x86)\MetaTrader 5\MQL5\Files"
    ]
    
    for base_path in base_paths:
        if "*" in base_path:
            # Użyj glob dla ścieżek z wildcardami
            paths = glob.glob(base_path)
            for path in paths:
                mql5_files = os.path.join(path, "*", "MQL5", "Files")
                files_dirs = glob.glob(mql5_files)
                if files_dirs:
                    return files_dirs[0]
        else:
            if os.path.exists(base_path):
                # Znajdź najnowszy terminal
                terminals = [d for d in os.listdir(base_path) 
                           if os.path.isdir(os.path.join(base_path, d)) and len(d) > 30]
                
                if terminals:
                    # Użyj najnowszego (ostatnio zmodyfikowanego)
                    latest_terminal = max(terminals, 
                                        key=lambda x: os.path.getmtime(os.path.join(base_path, x)))
                    
                    files_path = os.path.join(base_path, latest_terminal, "MQL5", "Files")
                    if os.path.exists(files_path):
                        return files_path
            elif os.path.exists(base_path):
                return base_path
    
    return None


def get_communication_file_path(filename="current_edit_ticket.txt"):
    """Zwraca pełną ścieżkę do pliku komunikacyjnego"""
    
    files_path = get_mql5_files_path()
    if files_path:
        return os.path.join(files_path, filename)
    
    # Fallback - utwórz w katalogu projektu
    fallback_path = os.path.join(os.path.dirname(__file__), "..", "..", filename)
    return os.path.abspath(fallback_path)


if __name__ == "__main__":
    # Test
    files_path = get_mql5_files_path()
    print(f"MQL5 Files path: {files_path}")
    
    comm_file = get_communication_file_path()
    print(f"Communication file: {comm_file}")
