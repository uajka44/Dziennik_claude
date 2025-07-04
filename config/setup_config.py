"""
Konfiguracja setupów - definicje skrótów klawiszowych i nazw setupów
"""
import json
import os
from typing import Dict, List, Tuple

# Domyślne setupy przeniesione z field_definitions.py
DEFAULT_SETUP_SHORTCUTS = {
    "r": {"name": "rgr", "description": "RGR setup"},
    "ra": {"name": "ramieszczytowe", "description": "Ramię szczytowe"},
    "m": {"name": "momoschodek", "description": "Momo schodek"},
    "mm": {"name": "momo", "description": "Momentum"},
    "pp": {"name": "przebitypoziom", "description": "Przebity poziom"},
    "p": {"name": "poziom", "description": "Poziom"},
    "s": {"name": "schodek", "description": "Schodek"},
    "rr": {"name": "srgr", "description": "Super RGR"},
    "re": {"name": "retestkonsoli", "description": "Retest konsoli"},
    "n": {"name": "niewazne", "description": "Nieważne"},
    "o": {"name": "odjebalem", "description": "Odjebałem"},
    "ss": {"name": "sschodek", "description": "Super schodek"}
}

class SetupConfigManager:
    """Manager konfiguracji setupów"""
    
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(__file__), "setup_shortcuts.json")
        self._shortcuts = {}
        self.load_config()
    
    def load_config(self):
        """Ładuje konfigurację z pliku lub tworzy domyślną"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._shortcuts = json.load(f)
                print(f"[SetupConfig] Załadowano {len(self._shortcuts)} setupów z pliku")
            else:
                print("[SetupConfig] Brak pliku konfiguracji, tworzę domyślną")
                self._shortcuts = DEFAULT_SETUP_SHORTCUTS.copy()
                self.save_config()
        except Exception as e:
            print(f"[SetupConfig] Błąd ładowania konfiguracji: {e}")
            self._shortcuts = DEFAULT_SETUP_SHORTCUTS.copy()
    
    def save_config(self):
        """Zapisuje konfigurację do pliku"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._shortcuts, f, indent=2, ensure_ascii=False)
            print(f"[SetupConfig] Zapisano {len(self._shortcuts)} setupów do pliku")
        except Exception as e:
            print(f"[SetupConfig] Błąd zapisu konfiguracji: {e}")
    
    def get_shortcuts(self) -> Dict[str, Dict[str, str]]:
        """Zwraca wszystkie skróty setupów"""
        return self._shortcuts.copy()
    
    def get_setup_names(self) -> List[str]:
        """Zwraca listę wszystkich nazw setupów"""
        return [setup["name"] for setup in self._shortcuts.values()]
    
    def get_shortcut_mapping(self) -> Dict[str, str]:
        """Zwraca mapowanie skrót -> nazwa (dla kompatybilności wstecznej)"""
        return {shortcut: data["name"] for shortcut, data in self._shortcuts.items()}
    
    def expand_shortcut(self, shortcut: str) -> str:
        """Rozszerza skrót do pełnej nazwy setupu"""
        if shortcut in self._shortcuts:
            return self._shortcuts[shortcut]["name"]
        return shortcut  # Jeśli nie znaleziono, zwróć oryginalny tekst
    
    def add_setup(self, shortcut: str, name: str, description: str = "") -> bool:
        """Dodaje nowy setup"""
        try:
            self._shortcuts[shortcut] = {
                "name": name,
                "description": description
            }
            self.save_config()
            return True
        except Exception as e:
            print(f"[SetupConfig] Błąd dodawania setupu: {e}")
            return False
    
    def update_setup(self, shortcut: str, name: str, description: str = "") -> bool:
        """Aktualizuje istniejący setup"""
        try:
            if shortcut in self._shortcuts:
                self._shortcuts[shortcut] = {
                    "name": name,
                    "description": description
                }
                self.save_config()
                return True
            return False
        except Exception as e:
            print(f"[SetupConfig] Błąd aktualizacji setupu: {e}")
            return False
    
    def remove_setup(self, shortcut: str) -> bool:
        """Usuwa setup"""
        try:
            if shortcut in self._shortcuts:
                del self._shortcuts[shortcut]
                self.save_config()
                return True
            return False
        except Exception as e:
            print(f"[SetupConfig] Błąd usuwania setupu: {e}")
            return False
    
    def get_setup_data(self, shortcut: str) -> Tuple[str, str, str]:
        """Zwraca dane setupu: (skrót, nazwa, opis)"""
        if shortcut in self._shortcuts:
            data = self._shortcuts[shortcut]
            return shortcut, data["name"], data.get("description", "")
        return shortcut, "", ""

# Singleton instance
_setup_config_manager = None

def get_setup_config() -> SetupConfigManager:
    """Zwraca singleton instance managera setupów"""
    global _setup_config_manager
    if _setup_config_manager is None:
        _setup_config_manager = SetupConfigManager()
    return _setup_config_manager
