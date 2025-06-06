"""
Zapytania SQL dla aplikacji
"""
from config.database_config import POSITIONS_TABLE, TP_RESULTS_TABLE


class PositionQueries:
    """Zapytania związane z pozycjami"""
    
    @staticmethod
    def get_positions_by_date_range(columns=None):
        """Zapytanie pobierające pozycje z zakresu dat"""
        if columns is None:
            columns = "*"
        elif isinstance(columns, list):
            columns = ", ".join(columns)
            
        return f"""
        SELECT {columns}
        FROM {POSITIONS_TABLE} 
        WHERE open_time BETWEEN ? AND ?
        ORDER BY open_time
        """
    
    @staticmethod
    def get_positions_by_date_range_and_symbol(columns=None):
        """Zapytanie pobierające pozycje z zakresu dat dla konkretnego instrumentu"""
        if columns is None:
            columns = "*"
        elif isinstance(columns, list):
            columns = ", ".join(columns)
            
        return f"""
        SELECT {columns}
        FROM {POSITIONS_TABLE} 
        WHERE open_time BETWEEN ? AND ? AND symbol = ?
        ORDER BY open_time
        """
    
    @staticmethod
    def update_position():
        """Zapytanie aktualizujące pozycję"""
        return f"UPDATE {POSITIONS_TABLE} SET {{}} WHERE ticket = ?"
    
    @staticmethod
    def get_position_by_ticket():
        """Zapytanie pobierające pozycję po ticket"""
        return f"SELECT * FROM {POSITIONS_TABLE} WHERE ticket = ?"


class CandleQueries:
    """Zapytania związane ze świecami"""
    
    @staticmethod
    def get_candles_by_time_range(instrument):
        """Zapytanie pobierające świece z zakresu czasowego dla instrumentu"""
        return f"""
        SELECT time, open, high, low, close, tick_volume, spread, real_volume
        FROM `{instrument}`
        WHERE time BETWEEN ? AND ?
        ORDER BY time
        """
    
    @staticmethod
    def get_candles_from_time(instrument):
        """Zapytanie pobierające świece od określonego czasu"""
        return f"""
        SELECT time, open, high, low, close, tick_volume, spread, real_volume
        FROM `{instrument}`
        WHERE time >= ?
        ORDER BY time
        """
    
    @staticmethod
    def check_table_exists():
        """Zapytanie sprawdzające czy tabela istnieje"""
        return "SELECT name FROM sqlite_master WHERE type='table' AND name=?"


class TPCalculationQueries:
    """Zapytania związane z kalkulacją TP"""
    
    @staticmethod
    def create_tp_results_table():
        """Zapytanie tworzące tabelę wyników kalkulacji TP"""
        return f"""
        CREATE TABLE IF NOT EXISTS {TP_RESULTS_TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket INTEGER NOT NULL,
            open_price REAL NOT NULL,
            open_time INTEGER NOT NULL,
            position_type TEXT NOT NULL,
            symbol TEXT NOT NULL,
            setup TEXT,
            max_tp_sl_staly REAL,
            max_tp_sl_recznie REAL,
            max_tp_sl_be REAL,
            sl_staly_value REAL,
            sl_recznie_value REAL,
            be_prog REAL,
            be_offset REAL,
            spread REAL,
            calculation_date TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    
    @staticmethod
    def insert_tp_result():
        """Zapytanie wstawiające wynik kalkulacji TP"""
        return f"""
        INSERT INTO {TP_RESULTS_TABLE} 
        (ticket, open_price, open_time, position_type, symbol, setup,
         max_tp_sl_staly, max_tp_sl_recznie, max_tp_sl_be,
         sl_staly_value, sl_recznie_value, be_prog, be_offset, spread,
         calculation_date, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    
    @staticmethod
    def get_tp_results_by_date_range():
        """Zapytanie pobierające wyniki kalkulacji z zakresu dat"""
        return f"""
        SELECT * FROM {TP_RESULTS_TABLE}
        WHERE calculation_date BETWEEN ? AND ?
        ORDER BY open_time
        """
    
    @staticmethod
    def delete_tp_results_by_ticket():
        """Zapytanie usuwające wyniki kalkulacji dla konkretnego ticket"""
        return f"DELETE FROM {TP_RESULTS_TABLE} WHERE ticket = ?"
