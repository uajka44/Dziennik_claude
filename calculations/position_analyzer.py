"""
Analiza pozycji tradingowych
"""
import sqlite3
from database.queries import PositionQueries
from config.database_config import DB_PATH
from config.sl_config import get_default_sl_for_instrument
from database.models import Position
from typing import List, Optional, Dict
from utils.date_utils import date_range_to_unix


class PositionAnalyzer:
    """Klasa do analizy pozycji tradingowych"""
    
    def __init__(self):
        self.position_queries = PositionQueries()
        self._connection = None
    
    def _get_connection(self):
        """Zwraca połączenie dla aktualnego wątku"""
        if self._connection is None:
            self._connection = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30.0)
        return self._connection
    
    def _execute_query(self, query, params=None):
        """Wykonuje zapytanie z obsługą wątków"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()
    
    def close_connection(self):
        """Zamyka połączenie"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def get_positions_for_date_range(self, start_date: str, end_date: str, 
                                   instruments: List[str] = None) -> List[Position]:
        """
        Pobiera pozycje z określonego zakresu dat dla wybranych instrumentów
        
        Args:
            start_date: Data początkowa w formacie 'YYYY-MM-DD'
            end_date: Data końcowa w formacie 'YYYY-MM-DD'
            instruments: Lista instrumentów do filtrowania (None = wszystkie)
        
        Returns:
            Lista obiektów Position
        """
        print(f"PositionAnalyzer: Pobieram pozycje dla {start_date} - {end_date}")
        start_unix, end_unix = date_range_to_unix(start_date, end_date)
        print(f"PositionAnalyzer: Unix timestamps: {start_unix} - {end_unix}")
        
        try:
            # Używamy konkretnych kolumn potrzebnych do kalkulacji TP
            columns = "open_time, ticket, type, volume, symbol, open_price, sl, sl_recznie, setup"
            query = f"""
            SELECT {columns}
            FROM positions 
            WHERE open_time BETWEEN ? AND ?
            ORDER BY open_time
            """
            rows = self._execute_query(query, (start_unix, end_unix))
            print(f"PositionAnalyzer: Znaleziono {len(rows)} wierszy w bazie")
            
            # Debug - sprawdź pierwszą pozycję
            if rows:
                print(f"PositionAnalyzer: Przykładowy wiersz: {rows[0]}")
            
            positions = []
            instruments_found = set()  # Zbieraj nazwy instrumentów z bazy
            
            for row in rows:
                position = self._row_to_position(row)
                
                # Normalizuj nazwę instrumentu (usuń spacje, null bytes i ujednolic wielkość liter)
                normalized_symbol = position.symbol.strip().replace('\x00', '').lower() if position.symbol else ""
                normalized_instruments = [instr.strip().replace('\x00', '').lower() for instr in (instruments or [])]
                
                instruments_found.add(repr(position.symbol))  # repr pokaże spacje
                
                # Filtruj po instrumentach jeśli podano
                if instruments is None or normalized_symbol in normalized_instruments:
                    positions.append(position)
                    print(f"PositionAnalyzer: Dodano pozycję {position.ticket} (oryginalny: {repr(position.symbol)}, znormalizowany: {repr(normalized_symbol)})")
                else:
                    print(f"PositionAnalyzer: Pominięto pozycję {position.ticket} (oryginalny: {repr(position.symbol)}, znormalizowany: {repr(normalized_symbol)}) - nie w instrumentach")
            
            print(f"PositionAnalyzer: Instrumenty znalezione w bazie: {sorted(instruments_found)}")
            print(f"PositionAnalyzer: Instrumenty poszukiwane: {instruments}")
            print(f"PositionAnalyzer: Końcowo zwrócono {len(positions)} pozycji")
            return positions
            
        except Exception as e:
            print(f"Błąd podczas pobierania pozycji: {e}")
            return []
    
    def _row_to_position(self, row) -> Position:
        """Konwertuje wiersz z bazy danych na obiekt Position"""
        # Kolumny: open_time, ticket, type, volume, symbol, open_price, sl, sl_recznie, setup
        
        if len(row) < 6:
            raise ValueError(f"Niewystarczająca liczba kolumn w wierszu: {len(row)}")
        
        print(f"PositionAnalyzer: Konwertuję wiersz: ticket={row[1]}, type={row[2]}, symbol={repr(row[4])}")
        
        return Position(
            open_time=row[0],      # open_time
            ticket=row[1],         # ticket
            type=row[2],           # type
            volume=row[3],         # volume
            symbol=row[4],         # symbol
            open_price=row[5],     # open_price
            sl=row[6] if len(row) > 6 else None,          # sl
            sl_recznie=row[7] if len(row) > 7 else None,  # sl_recznie
            setup=row[8] if len(row) > 8 else None,       # setup
            
            # Pozostałe pola z defaultowymi wartościami
            profit_points=None,
            close_price=None,
            close_time=None,
            profit=None,
            tp=None,
            uwagi=None,
            trends=None,
            trendl=None,
            interwal=None,
            setup_param1=None,
            setup_param2=None,
            nieutrzymalem=None,
            niedojscie=None,
            wybicie=None,
            strefa_oporu=None,
            zdrugiejstrony=None,
            ucieczka=None,
            Korekta=None,
            chcetrzymac=None,
            be=None
        )
    
    def get_position_stop_losses(self, position: Position, 
                                 sl_staly_values: Optional[Dict[str, float]] = None) -> Dict[str, Optional[float]]:
        """
        Zwraca słownik z różnymi typami stop loss dla pozycji
        
        Args:
            position: Obiekt pozycji
            sl_staly_values: Słownik z wartościami SL stałego per instrument (np. {"DAX": 10, "NASDAQ": 15})
        
        Returns:
            Słownik z kluczami: 'sl_recznie', 'sl_baza', 'sl_staly'
        """
        result = {
            'sl_recznie': position.sl_recznie,
            'sl_baza': position.sl,
            'sl_staly': None
        }
        
        # Oblicz SL stały na podstawie mapowania instrumentów
        if sl_staly_values:
            from config.instrument_tickets_config import get_instrument_tickets_config
            
            # Znajdź główny instrument dla pozycji
            tickets_config = get_instrument_tickets_config()
            main_instrument = tickets_config.get_main_instrument_for_ticket(position.symbol)
            
            if main_instrument and main_instrument in sl_staly_values:
                sl_value = sl_staly_values[main_instrument]
                
                if sl_value is not None and sl_value > 0:
                    # 1 punkt = 1.0 (nie dzielimy przez 10000!)
                    if position.is_buy:
                        result['sl_staly'] = position.open_price - sl_value
                    else:  # sell
                        result['sl_staly'] = position.open_price + sl_value
                        
                print(f"PositionAnalyzer: Symbol {position.symbol} -> Instrument {main_instrument} -> SL {sl_value} -> Final SL {result['sl_staly']}")
            else:
                print(f"PositionAnalyzer: Symbol {position.symbol} -> Nie znaleziono mapowania lub brak wartości SL")
        
        return result
    
    def validate_position_for_calculation(self, position: Position) -> Dict[str, bool]:
        """
        Sprawdza czy pozycja jest odpowiednia do obliczeń TP
        
        Args:
            position: Obiekt pozycji
        
        Returns:
            Słownik z wynikami walidacji dla różnych typów SL
        """
        result = {
            'sl_recznie': False,
            'sl_baza': False,
            'sl_staly': True  # SL stały zawsze można obliczyć
        }
        
        # Sprawdź sl_recznie
        if position.sl_recznie is not None and position.sl_recznie > 0:
            result['sl_recznie'] = True
        
        # Sprawdź sl z bazy
        if position.sl is not None and position.sl > 0:
            result['sl_baza'] = True
        
        return result
    
    def filter_positions_by_instrument(self, positions: List[Position], instruments: List[str]) -> List[Position]:
        """
        Filtruje pozycje według listy instrumentów
        
        Args:
            positions: Lista pozycji
            instruments: Lista dopuszczalnych instrumentów
        
        Returns:
            Przefiltrowana lista pozycji
        """
        if not instruments:
            return positions
        
        return [pos for pos in positions if pos.symbol in instruments]
    
    def get_unique_instruments(self, positions: List[Position]) -> List[str]:
        """
        Zwraca listę unikalnych instrumentów z pozycji
        
        Args:
            positions: Lista pozycji
        
        Returns:
            Lista unikalnych nazw instrumentów
        """
        instruments = set()
        for position in positions:
            if position.symbol:
                instruments.add(position.symbol)
        
        return sorted(list(instruments))
    
    def get_positions_by_tickets(self, tickets: List[str]) -> List[Position]:
        """
        Pobiera pozycje dla konkretnych ticketów
        
        Args:
            tickets: Lista ticketów do pobrania
        
        Returns:
            Lista obiektów Position
        """
        if not tickets:
            return []
        
        print(f"PositionAnalyzer: Pobieram pozycje dla {len(tickets)} ticketów")
        
        try:
            # Używamy konkretnych kolumn potrzebnych do kalkulacji TP
            columns = "open_time, ticket, type, volume, symbol, open_price, sl, sl_recznie, setup"
            
            # Budujemy zapytanie z placeholderami dla ticketów
            placeholders = ','.join(['?' for _ in tickets])
            query = f"""
            SELECT {columns}
            FROM positions 
            WHERE ticket IN ({placeholders})
            ORDER BY open_time
            """
            
            # Konwertuj tickety na stringi dla zapytania
            ticket_params = [str(ticket) for ticket in tickets]
            
            rows = self._execute_query(query, ticket_params)
            print(f"PositionAnalyzer: Znaleziono {len(rows)} wierszy w bazie dla ticketów")
            
            # Debug - sprawdź pierwsze pozycje
            if rows:
                print(f"PositionAnalyzer: Przykładowy wiersz: {rows[0]}")
            
            positions = []
            found_tickets = set()
            
            for row in rows:
                position = self._row_to_position(row)
                positions.append(position)
                found_tickets.add(str(position.ticket))
                print(f"PositionAnalyzer: Dodano pozycję {position.ticket} (symbol: {repr(position.symbol)})")
            
            # Sprawdź czy wszystkie tickety zostały znalezione
            missing_tickets = set(str(t) for t in tickets) - found_tickets
            if missing_tickets:
                print(f"PositionAnalyzer: Nie znaleziono ticketów: {missing_tickets}")
            
            print(f"PositionAnalyzer: Końcowo zwrócono {len(positions)} pozycji")
            return positions
            
        except Exception as e:
            print(f"Błąd podczas pobierania pozycji dla ticketów: {e}")
            import traceback
            traceback.print_exc()
            return []
