"""
Manager konfiguracji okien - zapisuje i przywraca pozycje oraz rozmiary okien
"""
import json
import os
import tkinter as tk


class WindowConfigManager:
    """Manager konfiguracji okien - singleton"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.config_file = os.path.join(os.path.dirname(__file__), "..", "config", "window_config.json")
        self.config_file = os.path.abspath(self.config_file)  # Zamień na absolutną ścieżkę
        self.default_config = {
            "edit_dialog": {
                "width": 700,
                "height": 900,
                "x": None,  # None oznacza centrowanie
                "y": None,
                "remember_position": True
            },
            "main_window": {
                "width": 1200,
                "height": 800,
                "x": None,
                "y": None,
                "remember_position": True
            }
        }
        self.config = self._load_config()
        self._initialized = True
    
    def _load_config(self):
        """Ładuje konfigurację z pliku JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Merge z domyślną konfiguracją (w przypadku nowych opcji)
                config = self.default_config.copy()
                for window_name, window_config in loaded_config.items():
                    if window_name in config:
                        config[window_name].update(window_config)
                
                print(f"[WindowConfig] Załadowano konfigurację z {self.config_file}")
                return config
            else:
                print(f"[WindowConfig] Plik konfiguracji nie istnieje, używam domyślnych ustawień")
                return self.default_config.copy()
                
        except Exception as e:
            print(f"[WindowConfig] Błąd ładowania konfiguracji: {e}")
            return self.default_config.copy()
    
    def _save_config(self):
        """Zapisuje konfigurację do pliku JSON"""
        try:
            # Upewnij się że katalog istnieje
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            print(f"[WindowConfig] Zapisano konfigurację do {self.config_file}")
            
        except Exception as e:
            print(f"[WindowConfig] Błąd zapisu konfiguracji: {e}")
    
    def apply_window_config(self, window, window_name):
        """
        Stosuje konfigurację do okna
        
        Args:
            window: Okno tkinter (Toplevel lub Tk)
            window_name: Nazwa okna w konfiguracji
        """
        if window_name not in self.config:
            print(f"[WindowConfig] Brak konfiguracji dla okna: {window_name}")
            return
        
        config = self.config[window_name]
        
        try:
            width = config.get('width', 800)
            height = config.get('height', 600)
            x = config.get('x')
            y = config.get('y')
            
            if x is not None and y is not None and config.get('remember_position', True):
                # Sprawdź czy pozycja jest na ekranie
                screen_width = window.winfo_screenwidth()
                screen_height = window.winfo_screenheight()
                
                # Dostosuj pozycję jeśli okno wychodzi poza ekran
                if x + width > screen_width:
                    x = screen_width - width - 50
                if y + height > screen_height:
                    y = screen_height - height - 50
                if x < 0:
                    x = 50
                if y < 0:
                    y = 50
                
                geometry = f"{width}x{height}+{x}+{y}"
                print(f"[WindowConfig] Stosuj konfigurację {window_name}: {geometry}")
            else:
                # Centruj okno
                geometry = f"{width}x{height}"
                window.geometry(geometry)
                window.update_idletasks()
                
                # Oblicz pozycję centralną
                screen_width = window.winfo_screenwidth()
                screen_height = window.winfo_screenheight()
                x = (screen_width - width) // 2
                y = (screen_height - height) // 2
                
                geometry = f"{width}x{height}+{x}+{y}"
                print(f"[WindowConfig] Centruj okno {window_name}: {geometry}")
            
            window.geometry(geometry)
            
        except Exception as e:
            print(f"[WindowConfig] Błąd stosowania konfiguracji dla {window_name}: {e}")
    
    def save_window_config(self, window, window_name):
        """
        Zapisuje aktualną konfigurację okna
        
        Args:
            window: Okno tkinter
            window_name: Nazwa okna w konfiguracji
        """
        if window_name not in self.config:
            self.config[window_name] = {}
        
        try:
            # Pobierz aktualne wymiary i pozycję
            geometry = window.geometry()
            
            # Format: "WIDTHxHEIGHT+X+Y"
            if '+' in geometry or '-' in geometry:
                # Znajdź ostatnie wystąpienia + lub -
                parts = geometry.replace('-', '+-').split('+')
                size_part = parts[0]
                x = int(parts[1]) if len(parts) > 1 else 0
                y = int(parts[2]) if len(parts) > 2 else 0
            else:
                size_part = geometry
                x = window.winfo_x()
                y = window.winfo_y()
            
            # Parsuj rozmiar
            width, height = map(int, size_part.split('x'))
            
            # Zapisz konfigurację
            self.config[window_name].update({
                'width': width,
                'height': height,
                'x': x,
                'y': y,
                'remember_position': True
            })
            
            print(f"[WindowConfig] Zapisano konfigurację {window_name}: {width}x{height}+{x}+{y}")
            
            # Automatycznie zapisz do pliku
            self._save_config()
            
        except Exception as e:
            print(f"[WindowConfig] Błąd zapisywania konfiguracji dla {window_name}: {e}")
    
    def get_window_config(self, window_name):
        """Zwraca konfigurację dla konkretnego okna"""
        return self.config.get(window_name, {})
    
    def set_window_config(self, window_name, **kwargs):
        """Ustawia konfigurację dla okna"""
        if window_name not in self.config:
            self.config[window_name] = {}
        
        self.config[window_name].update(kwargs)
        self._save_config()
    
    def reset_window_config(self, window_name=None):
        """Resetuje konfigurację okna do domyślnych wartości"""
        if window_name:
            if window_name in self.default_config:
                self.config[window_name] = self.default_config[window_name].copy()
        else:
            self.config = self.default_config.copy()
        
        self._save_config()
        print(f"[WindowConfig] Zresetowano konfigurację: {window_name or 'wszystkie okna'}")
