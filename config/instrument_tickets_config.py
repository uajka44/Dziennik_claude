"""
Konfiguracja mapowania ticketów instrumentów
"""
import json
import os
from config.database_config import DB_PATH
from typing import Dict, List, Optional


class InstrumentTicketsConfig:
    """Klasa do zarządzania mapowaniem ticketów instrumentów"""
    
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(DB_PATH), "instrument_tickets.json")
        self._config = None
        self._active_instruments = None
    
    @property
    def config(self) -> Dict[str, List[str]]:
        """Zwraca aktualną konfigurację mapowania"""
        if self._config is None:
            self._config = self._load_config()
        return self._config
    
    def _load_config(self) -> Dict[str, List[str]]:
        """Ładuje konfigurację z pliku"""
        default_config = {
            "DAX": ["ger40.cash", "germany40", "dax40", "ger40"],
            "NASDAQ": ["us100.cash", "us100", "nq100", "nasdaq100", "nas100"],
            "DJ": ["us30.cash", "us30", "dow30", "dj30", "dow jones"],
            "GOLD": ["xauusd", "gold", "złoto", "au"],
            "BTC": ["btcusd", "bitcoin", "btc", "crypto"]
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Obsługa starych i nowych formatów pliku
                if isinstance(data, dict) and 'instruments' in data:
                    # Nowy format z instrumentami i aktywnymi
                    config = data.get('instruments', {})
                    self._active_instruments = data.get('active_instruments', {})
                else:
                    # Stary format - tylko instrumenty
                    config = data if isinstance(data, dict) else default_config
                    self._active_instruments = {}
                
                # Sprawdź czy wszystkie domyślne instrumenty istnieją
                for instrument, tickets in default_config.items():
                    if instrument not in config:
                        config[instrument] = tickets
                    if instrument not in self._active_instruments:
                        self._active_instruments[instrument] = True  # Domyślnie aktywne
                
                return config
            else:
                # Pierwszy raz - utwórz domyślną konfigurację
                self._active_instruments = {
                    "DAX": True,
                    "NASDAQ": True,
                    "DJ": True, 
                    "GOLD": True,
                    "BTC": False
                }
                return default_config
                
        except Exception as e:
            print(f"Błąd podczas ładowania konfiguracji ticketów: {e}")
            self._active_instruments = {}
            return default_config
    
    def reload_config(self):
        """Wymusza ponowne załadowanie konfiguracji"""
        self._config = None
        self._active_instruments = None
    
    def get_active_instruments(self) -> Dict[str, bool]:
        """Zwraca słownik aktywnych instrumentów"""
        if self._active_instruments is None:
            # Trigger ładowania konfiguracji
            _ = self.config
        return self._active_instruments or {}
    
    def is_instrument_active(self, instrument: str) -> bool:
        """Sprawdza czy instrument jest aktywny"""
        active_instruments = self.get_active_instruments()
        return active_instruments.get(instrument.upper(), False)
    
    def get_active_instruments_list(self) -> List[str]:
        """Zwraca listę nazw aktywnych instrumentów"""
        active = self.get_active_instruments()
        return [name for name, is_active in active.items() if is_active]
    
    def get_main_instrument_for_ticket(self, ticket: str) -> Optional[str]:
        """
        Zwraca główną nazwę instrumentu dla podanego ticketu (case-insensitive)
        
        Args:
            ticket: Ticket do sprawdzenia (np. "ger40.cash", "GERMANY40")
            
        Returns:
            Nazwa głównego instrumentu (np. "DAX") lub None jeśli nie znaleziono
        """
        if not ticket:
            return None
        
        # Normalizacja ticketu z bazy - case insensitive
        ticket_clean = ticket.strip().lower().replace('\x00', '')
        
        for main_instrument, tickets_list in self.config.items():
            # Sprawdź wszystkie tickety dla tego instrumentu (case-insensitive)
            for mapped_ticket in tickets_list:
                if ticket_clean == mapped_ticket.strip().lower():
                    return main_instrument
        
        return None
    
    def get_tickets_for_instrument(self, instrument: str) -> List[str]:
        """
        Zwraca listę ticketów dla głównego instrumentu
        
        Args:
            instrument: Nazwa głównego instrumentu (np. "DAX")
            
        Returns:
            Lista ticketów dla tego instrumentu
        """
        return self.config.get(instrument.upper(), [])
    
    def get_all_tickets(self) -> List[str]:
        """
        Zwraca listę wszystkich ticketów ze wszystkich instrumentów
        
        Returns:
            Lista wszystkich ticketów
        """
        all_tickets = []
        for tickets_list in self.config.values():
            all_tickets.extend(tickets_list)
        return all_tickets
    
    def get_all_instruments(self) -> List[str]:
        """
        Zwraca listę wszystkich głównych instrumentów
        
        Returns:
            Lista nazw głównych instrumentów
        """
        return list(self.config.keys())
    
    def normalize_instrument_name(self, ticket: str) -> str:
        """
        Normalizuje nazwę ticketu do głównej nazwy instrumentu
        
        Args:
            ticket: Ticket do normalizacji
            
        Returns:
            Główna nazwa instrumentu lub oryginalny ticket jeśli nie znaleziono mapowania
        """
        main_instrument = self.get_main_instrument_for_ticket(ticket)
        return main_instrument if main_instrument else ticket


# Globalna instancja konfiguracji
_instrument_tickets_config = None

def get_instrument_tickets_config() -> InstrumentTicketsConfig:
    """Zwraca globalną instancję konfiguracji ticketów instrumentów"""
    global _instrument_tickets_config
    if _instrument_tickets_config is None:
        _instrument_tickets_config = InstrumentTicketsConfig()
    return _instrument_tickets_config

def reload_instrument_tickets_config():
    """Wymusza ponowne załadowanie konfiguracji ticketów"""
    global _instrument_tickets_config
    if _instrument_tickets_config:
        _instrument_tickets_config.reload_config()
