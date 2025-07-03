"""
Modele danych reprezentujące struktury z bazy danych
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Position:
    """Model reprezentujący pozycję tradingową"""
    ticket: int
    open_time: int  # Unix timestamp
    type: int  # 0 = buy, 1 = sell
    volume: float
    symbol: str
    open_price: float
    close_price: Optional[float] = None
    close_time: Optional[int] = None
    profit: Optional[float] = None
    profit_points: Optional[float] = None
    sl: Optional[float] = None
    sl_recznie: Optional[float] = None
    tp: Optional[float] = None
    setup: Optional[str] = None
    uwagi: Optional[str] = None
    blad: Optional[str] = None
    trends: Optional[int] = None
    trendl: Optional[int] = None
    interwal: Optional[str] = None
    setup_param1: Optional[str] = None
    setup_param2: Optional[str] = None
    # Checkboxy
    nieutrzymalem: Optional[int] = None
    niedojscie: Optional[int] = None
    wybicie: Optional[int] = None
    strefa_oporu: Optional[int] = None
    zdrugiejstrony: Optional[int] = None
    ucieczka: Optional[int] = None
    Korekta: Optional[int] = None
    chcetrzymac: Optional[int] = None
    be: Optional[int] = None
    
    @property
    def is_buy(self) -> bool:
        """Czy pozycja to buy"""
        return self.type_as_int == 0
    
    @property 
    def is_sell(self) -> bool:
        """Czy pozycja to sell"""
        return self.type_as_int == 1
    
    @property
    def position_type_string(self) -> str:
        """Zwraca typ pozycji jako string"""
        if isinstance(self.type, str):
            # Jeśli typ to string (z bazy), wyczyść null bytes i spacj e
            clean_type = self.type.strip().replace('\x00', '').lower()
            return clean_type
        elif self.type == 0:
            return "buy"
        elif self.type == 1:
            return "sell"
        else:
            return "unknown"
    
    @property
    def type_as_int(self) -> int:
        """Zwraca typ pozycji jako liczbę (0=buy, 1=sell)"""
        if isinstance(self.type, str):
            clean_type = self.type.strip().replace('\x00', '').lower()
            if clean_type == "buy":
                return 0
            elif clean_type == "sell":
                return 1
            else:
                return -1  # unknown
        else:
            return self.type if self.type in [0, 1] else -1
    
    @property
    def open_datetime(self) -> datetime:
        """Konwersja open_time na datetime"""
        return datetime.utcfromtimestamp(self.open_time)


@dataclass
class Candle:
    """Model reprezentujący świeczkę"""
    time: int  # Unix timestamp
    open: float
    high: float
    low: float
    close: float
    tick_volume: Optional[int] = None
    spread: Optional[int] = None
    real_volume: Optional[int] = None
    
    @property
    def datetime(self) -> datetime:
        """Konwersja time na datetime"""
        return datetime.utcfromtimestamp(self.time)


@dataclass
class TPCalculationResult:
    """Model reprezentujący wynik kalkulacji TP"""
    ticket: int
    open_price: float
    open_time: int
    position_type: str  # "buy" lub "sell"
    symbol: str
    setup: Optional[str]
    max_tp_sl_staly: Optional[float] = None
    max_tp_sl_recznie: Optional[float] = None
    max_tp_sl_be: Optional[float] = None
    sl_staly_value: Optional[float] = None
    sl_recznie_value: Optional[float] = None
    be_prog: Optional[float] = None
    be_offset: Optional[float] = None
    spread: Optional[float] = None
    calculation_date: Optional[str] = None
    notes: Optional[str] = None
