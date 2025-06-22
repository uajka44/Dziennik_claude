"""
Rozszerzony system komunikacji z MQL5 - dodaje więcej danych niż tylko ticket
"""
import json
import os
from datetime import datetime


class MQLCommunicationManager:
    """Manager komunikacji z MQL5 - rozszerzony o dodatkowe dane"""
    
    def __init__(self, base_path="E:/Trading"):
        self.base_path = base_path
        self.ticket_file = os.path.join(base_path, "current_edit_ticket.txt")
        self.data_file = os.path.join(base_path, "current_edit_data.json")
        
        # Upewnij się że katalog istnieje
        os.makedirs(base_path, exist_ok=True)
        
        # Inicjalizuj puste pliki
        self._save_ticket(0)
        self._save_data({})
    
    def set_editing_position(self, ticket, position_data=None):
        """
        Ustawia aktualnie edytowaną pozycję
        
        Args:
            ticket: Numer ticket
            position_data: Dodatkowe dane pozycji (dict)
        """
        self._save_ticket(ticket)
        
        if position_data is None:
            position_data = {}
        
        # Dodaj timestamp i ticket
        full_data = {
            "ticket": ticket,
            "timestamp": datetime.now().isoformat(),
            "editing": ticket > 0,
            **position_data
        }
        
        self._save_data(full_data)
        
        print(f"[MQLComm] Ustawiono edycję pozycji: {ticket}")
    
    def clear_editing_position(self):
        """Czyści informację o edytowanej pozycji"""
        self.set_editing_position(0, {"status": "no_editing"})
        print(f"[MQLComm] Wyczyszczono edycję pozycji")
    
    def get_current_editing(self):
        """Zwraca informacje o aktualnie edytowanej pozycji"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except:
            return {"ticket": 0, "editing": False}
    
    def _save_ticket(self, ticket):
        """Zapisuje ticket do pliku (kompatybilność z starym systemem)"""
        try:
            with open(self.ticket_file, 'w', encoding='utf-8') as f:
                f.write(str(ticket))
        except Exception as e:
            print(f"[MQLComm] Błąd zapisu ticket: {e}")
    
    def _save_data(self, data):
        """Zapisuje pełne dane do pliku JSON"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[MQLComm] Błąd zapisu danych: {e}")
    
    def update_position_data(self, **kwargs):
        """Aktualizuje dane aktualnie edytowanej pozycji"""
        current_data = self.get_current_editing()
        current_data.update(kwargs)
        current_data["last_update"] = datetime.now().isoformat()
        
        self._save_data(current_data)
    
    def get_communication_files(self):
        """Zwraca ścieżki do plików komunikacyjnych"""
        return {
            "ticket_file": self.ticket_file,
            "data_file": self.data_file
        }


# Przykład użycia w EditManager
def enhanced_communication_example():
    """Przykład jak można rozszerzyć komunikację"""
    
    comm = MQLCommunicationManager()
    
    # Przy otwieraniu pozycji do edycji
    position_data = {
        "symbol": "EURUSD",
        "type": "BUY", 
        "volume": 0.1,
        "open_price": 1.0850,
        "sl": 1.0800,
        "tp": 1.0900,
        "profit_points": 25.5,
        "status": "editing"
    }
    
    comm.set_editing_position(123456, position_data)
    
    # Przy aktualizacji danych (np. zmiana SL)
    comm.update_position_data(
        sl=1.0810,
        sl_changed=True,
        change_reason="user_edit"
    )
    
    # Przy zamknięciu edycji
    comm.clear_editing_position()
    
    # MQL5 może odczytać:
    current = comm.get_current_editing()
    print("Aktualne dane:", current)


if __name__ == "__main__":
    enhanced_communication_example()
