"""
Analiza świeczek dla kalkulacji TP
"""
import sqlite3
from database.queries import CandleQueries
from config.database_config import DB_PATH
from database.models import Candle
from utils.date_utils import unix_to_datetime, get_day_end_unix
from typing import List, Optional


class CandleAnalyzer:
    """Klasa do analizy danych świeczkowych"""
    
    def __init__(self):
        self.candle_queries = CandleQueries()
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
    
    def _find_table_name(self, instrument: str) -> Optional[str]:
        """Znajduje prawdziwą nazwę tabeli dla instrumentu"""
        try:
            # Sprawdź najpierw bezpośrednio
            if self._table_exists_simple(instrument):
                return instrument
            
            # Pobierz wszystkie tabele z danymi świeczkymi
            all_tables_query = "SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%cash%' OR name LIKE '%XAUUSD%')"
            all_tables = self._execute_query(all_tables_query)
            
            normalized_target = instrument.lower().replace('\x00', '').strip()
            
            for row in all_tables:
                table_name = row[0]
                normalized_table = table_name.lower().replace('\x00', '').strip()
                
                if normalized_table == normalized_target:
                    print(f"CandleAnalyzer: Znaleziono tabelę '{table_name}' dla instrumentu '{instrument}'")
                    return table_name
            
            print(f"CandleAnalyzer: Nie znaleziono tabeli dla instrumentu '{instrument}'")
            return None
            
        except Exception as e:
            print(f"CandleAnalyzer: Błąd przy szukaniu tabeli dla {instrument}: {e}")
            return None
    
    def _table_exists_simple(self, table_name: str) -> bool:
        """Prosta funkcja sprawdzająca istnienie tabeli"""
        try:
            query = self.candle_queries.check_table_exists()
            result = self._execute_query(query, (table_name,))
            return len(result) > 0
        except Exception:
            return False
    
    def get_candles_for_position(self, instrument: str, open_time: int) -> List[Candle]:
        """
        Pobiera świeczki dla pozycji od świeczki przed otwarciem do końca dnia
        
        Args:
            instrument: Nazwa instrumentu (np. "GER40.cash " lub "ger40.cash")
            open_time: Unix timestamp otwarcia pozycji
        
        Returns:
            Lista obiektów Candle
        """
        # Znajdź prawdziwą nazwę tabeli
        real_table_name = self._find_table_name(instrument)
        if not real_table_name:
            return []
        
        print(f"CandleAnalyzer: Używam tabeli '{real_table_name}' dla instrumentu '{instrument}'")
        
        # Pobierz świeczki od 60 sekund przed otwarciem pozycji do końca dnia
        # To zapewni że mamy świeczkę otwarcia pozycji jako pierwszą w obliczeniach
        start_time = open_time - 60  # 60 sekund wcześniej
        end_time = get_day_end_unix(open_time)
        print(f"CandleAnalyzer: Pobieranie świeczek od {start_time} (60s przed {open_time}) do {end_time}")
        
        try:
            query = self.candle_queries.get_candles_by_time_range(real_table_name)
            rows = self._execute_query(query, (start_time, end_time))
            print(f"CandleAnalyzer: Znaleziono {len(rows)} świeczek")
            
            candles = []
            for row in rows:
                candle = Candle(
                    time=row[0],
                    open=row[1],
                    high=row[2],
                    low=row[3],
                    close=row[4],
                    tick_volume=row[5] if len(row) > 5 else None,
                    spread=row[6] if len(row) > 6 else None,
                    real_volume=row[7] if len(row) > 7 else None
                )
                candles.append(candle)
            
            return candles
            
        except Exception as e:
            print(f"CandleAnalyzer: Błąd podczas pobierania świeczek dla {real_table_name}: {e}")
            return []
    
    def _table_exists(self, table_name: str) -> bool:
        """Sprawdza czy tabela istnieje w bazie danych"""
        try:
            query = self.candle_queries.check_table_exists()
            result = self._execute_query(query, (table_name,))
            exists = len(result) > 0
            
            if not exists:
                # Jeśli tabela nie istnieje, sprawdź jakie tabele są dostępne
                all_tables_query = "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%cash%' OR name LIKE '%XAUUSD%'"
                all_tables = self._execute_query(all_tables_query)
                available_tables = [row[0] for row in all_tables]
                print(f"CandleAnalyzer: Tabela '{table_name}' nie istnieje. Dostępne tabele z danymi: {available_tables}")
                
                # Spróbuj znaleźć pasującą tabelę (case-insensitive)
                for available_table in available_tables:
                    if available_table.lower().replace('\x00', '').strip() == table_name.lower():
                        print(f"CandleAnalyzer: Znaleziono pasującą tabelę: '{available_table}' dla '{table_name}'")
                        return True
            
            return exists
        except Exception as e:
            print(f"CandleAnalyzer: Błąd przy sprawdzaniu tabeli {table_name}: {e}")
            return False
    
    def calculate_max_tp_basic(self, candles: List[Candle], position_type: int, 
                              open_price: float, stop_loss: float, spread: float = 0, detailed_logs: bool = False) -> Optional[float]:
        """
        Oblicza maksymalny TP dla podstawowego scenariusza (bez BE)
        
        Algorytm:
        1. Idzie po kolejnych świeczkach od otwarcia pozycji
        2. Na każdej świeczce sprawdza czy cena uderzyła w SL
        3. Jeśli nie - sprawdza maksymalny zysk na tej świeczce
        4. Zapisuje maksymalny zysk jeśli jest większy od poprzedniego
        5. Kończy gdy cena uderzy w SL lub skończą się świeczki
        
        Args:
            candles: Lista świeczek
            position_type: 0 = buy, 1 = sell
            open_price: Cena otwarcia pozycji
            stop_loss: Poziom stop loss
            spread: Spread w punktach
        
        Returns:
            Maksymalny TP w punktach lub None jeśli pozycja została zamknięta na SL
        """
        if not candles:
            if detailed_logs:
                print("CandleAnalyzer: Brak świeczek do analizy")
            return None
        
        if detailed_logs:
            print(f"CandleAnalyzer: Rozpoczynam obliczenia TP:")
            print(f"  - Pozycja: {'BUY' if position_type == 0 else 'SELL'}")
            print(f"  - Cena otwarcia: {open_price}")
            print(f"  - Stop Loss: {stop_loss}")
            print(f"  - Spread: {spread}")
            print(f"  - Liczba świeczek: {len(candles)}")
        
        max_profit = 0.0
        is_buy = (position_type == 0)
        spread_adjustment = spread  # Spread już w punktach
        
        for i, candle in enumerate(candles):
            if detailed_logs:
                print(f"\nCandleAnalyzer: Świeczka {i+1}/{len(candles)}")
                print(f"  - OHLC: O={candle.open}, H={candle.high}, L={candle.low}, C={candle.close}")
            
            if i == 0:
                # Pierwsza świeczka - sprawdzamy czy maksymalna strata przekroczyła SL
                if detailed_logs:
                    print(f"  - Pierwsza świeczka, sprawdzam czy udażyła w SL")
                
                if is_buy:
                    # Dla BUY: sprawdzamy czy low uderzyło w SL
                    if candle.low <= stop_loss + spread_adjustment:
                        if detailed_logs:
                            print(f"  - SL uderzony przez low ({candle.low} <= {stop_loss + spread_adjustment})")
                            print(f"  - Pozycja od razu wybita na pierwszej świeczce - TP = 0")
                        return 0.0  # Została wybita, ale TP = 0 (nie None!)
                    
                    # Jeśli SL nie został uderzony, sprawdź zysk na close
                    profit = candle.close - open_price
                    if detailed_logs:
                        print(f"  - SL nie uderzony, zysk na close: {candle.close} - {open_price} = {profit}")
                    
                    if profit > max_profit:
                        max_profit = profit
                        if detailed_logs:
                            print(f"  - Nowy maksymalny zysk: {max_profit}")
                        
                else:  # sell
                    # Dla SELL: sprawdzamy czy high uderzyło w SL
                    if candle.high >= stop_loss - spread_adjustment:
                        print(f"  - SL uderzony przez high ({candle.high} >= {stop_loss - spread_adjustment})")
                        print(f"  - Pozycja od razu wybita na pierwszej świeczce - TP = 0")
                        return 0.0  # Została wybita, ale TP = 0 (nie None!)
                    
                    # Jeśli SL nie został uderzony, sprawdź zysk na close
                    profit = open_price - candle.close
                    print(f"  - SL nie uderzony, zysk na close: {open_price} - {candle.close} = {profit}")
                    
                    if profit > max_profit:
                        max_profit = profit
                        print(f"  - Nowy maksymalny zysk: {max_profit}")
                        
            else:
                # Kolejne świeczki - możemy sprawdzać extrema (high/low)
                print(f"  - Kolejna świeczka, sprawdzam extrema")
                
                if is_buy:
                    # Sprawdź czy low uderzyło w SL
                    if candle.low <= stop_loss + spread_adjustment:
                        print(f"  - SL uderzony przez low ({candle.low} <= {stop_loss + spread_adjustment})")
                        print(f"  - Pozycja zamknięta, zwracam maksymalny zysk: {max_profit}")
                        return max_profit
                    
                    # Sprawdź maksymalny zysk na tej świeczce (high)
                    profit = candle.high - open_price
                    print(f"  - Potencjalny zysk na high: {candle.high} - {open_price} = {profit}")
                    
                    if profit > max_profit:
                        max_profit = profit
                        print(f"  - Nowy maksymalny zysk: {max_profit}")
                        
                else:  # sell
                    # Sprawdź czy high uderzyło w SL
                    if candle.high >= stop_loss - spread_adjustment:
                        print(f"  - SL uderzony przez high ({candle.high} >= {stop_loss - spread_adjustment})")
                        print(f"  - Pozycja zamknięta, zwracam maksymalny zysk: {max_profit}")
                        return max_profit
                    
                    # Sprawdź maksymalny zysk na tej świeczce (low)
                    profit = open_price - candle.low
                    print(f"  - Potencjalny zysk na low: {open_price} - {candle.low} = {profit}")
                    
                    if profit > max_profit:
                        max_profit = profit
                        print(f"  - Nowy maksymalny zysk: {max_profit}")
        
        print(f"\nCandleAnalyzer: Koniec świeczek, końcowy maksymalny zysk: {max_profit}")
        return max_profit
    
    def calculate_max_tp_with_be(self, candles: List[Candle], position_type: int,
                                open_price: float, initial_sl: float, be_prog: float,
                                be_offset: float, spread: float = 0, detailed_logs: bool = False) -> Optional[float]:
        """
        Oblicza maksymalny TP z uwzględnieniem przesuwania SL na BE
        
        Args:
            candles: Lista świeczek
            position_type: 0 = buy, 1 = sell
            open_price: Cena otwarcia pozycji
            initial_sl: Początkowy stop loss
            be_prog: Próg zysku do przesunięcia SL (w punktach)
            be_offset: Przesunięcie SL względem ceny otwarcia (w punktach)
            spread: Spread w punktach
        
        Returns:
            Maksymalny TP w punktach lub None jeśli pozycja została zamknięta na SL
        """
        if not candles:
            return None
        
        print(f"\n=== ROZPOCZYNAM OBLICZENIA TP Z BREAK EVEN ====")
        print(f"Pozycja: {'BUY' if position_type == 0 else 'SELL'}, Próg BE: {be_prog}, Offset: {be_offset}")
        
        max_profit = 0.0
        is_buy = (position_type == 0)
        be_triggered = False
        current_sl = initial_sl
        
        # Konwersje (1 punkt = 1.0)
        spread_adjustment = spread  # Spread już w punktach
        be_prog_price = be_prog  # BE prog już w punktach
        be_offset_price = be_offset  # BE offset już w punktach
        
        # Oblicz nowy SL po przesunięciu
        if is_buy:
            new_sl_after_be = open_price + be_offset_price
        else:
            new_sl_after_be = open_price - be_offset_price
        
        print(f"Mam {len(candles)} świeczek do analizy BE")
        
        for i, candle in enumerate(candles):
            print(f"\nCandleAnalyzer BE: Świeczka {i+1}/{len(candles)}")
            print(f"  - OHLC: O={candle.open}, H={candle.high}, L={candle.low}, C={candle.close}")
            print(f"  - Aktualny SL: {current_sl}, BE aktywne: {be_triggered}")
            
            if i == 0:
                # Pierwsza świeczka
                print(f"  - Pierwsza świeczka BE")
                if is_buy:
                    # Sprawdź czy uderzył w aktualny SL
                    if candle.low <= current_sl + spread_adjustment:
                        print(f"  - SL uderzony na pierwszej świeczce, zwrócić 0")
                        return 0.0
                    
                    # Sprawdź czy osiągnął próg BE na close
                    profit_close = candle.close - open_price
                    print(f"  - Zysk na close: {profit_close:.1f} pkt")
                    
                    if not be_triggered and profit_close >= be_prog_price:
                        be_triggered = True
                        current_sl = new_sl_after_be
                        print(f"  *** BE AKTYWOWANE! Zysk {profit_close:.1f} >= {be_prog_price}, SL przesunięty na {current_sl} ***")
                    
                    profit = profit_close
                    max_profit = max(max_profit, profit)
                    
                else:  # sell
                    if candle.high >= current_sl - spread_adjustment:
                        print(f"  - SL uderzony na pierwszej świeczce, zwrócić 0")
                        return 0.0
                    
                    profit_close = open_price - candle.close
                    print(f"  - Zysk na close: {profit_close:.1f} pkt")
                    
                    if not be_triggered and profit_close >= be_prog_price:
                        be_triggered = True
                        current_sl = new_sl_after_be
                        print(f"  *** BE AKTYWOWANE! Zysk {profit_close:.1f} >= {be_prog_price}, SL przesunięty na {current_sl} ***")
                    
                    profit = profit_close
                    max_profit = max(max_profit, profit)
            else:
                # Kolejne świeczki
                print(f"  - Kolejna świeczka BE")
                if is_buy:
                    # Sprawdź próg BE przed sprawdzeniem SL
                    be_activated_this_candle = False
                    if not be_triggered:
                        profit_high = candle.high - open_price
                        print(f"  - Zysk na high: {profit_high:.1f} pkt")
                        if profit_high >= be_prog_price:
                            be_triggered = True
                            be_activated_this_candle = True
                            current_sl = new_sl_after_be
                            print(f"  *** BE AKTYWOWANE! Zysk na high {profit_high:.1f} >= {be_prog_price}, SL przesunięty na {current_sl} ***")
                            print(f"  - Przesunięty SL będzie sprawdzany od następnej świeczki")
                    
                    # Sprawdź czy uderzył w aktualny SL (ale tylko jeśli BE nie zostało właśnie aktywowane)
                    if not be_activated_this_candle and candle.low <= current_sl + spread_adjustment:
                        if be_triggered:
                            print(f"  *** NOWY SL UDERZONY! Low {candle.low} <= {current_sl + spread_adjustment}, TP = {max_profit:.1f} ***")
                        else:
                            print(f"  - Oryginalny SL uderzony przez low, TP = {max_profit:.1f}")
                        return max_profit
                    elif be_activated_this_candle:
                        print(f"  - BE właśnie aktywowane, pomijam sprawdzenie SL na tej świeczce")
                    
                    profit = candle.high - open_price
                    if profit > max_profit:
                        max_profit = profit
                        print(f"  - NOWY maksymalny zysk: {max_profit:.1f} pkt")
                    else:
                        max_profit = max(max_profit, profit)
                        
                else:  # sell
                    # Sprawdź próg BE przed sprawdzeniem SL
                    be_activated_this_candle = False
                    if not be_triggered:
                        profit_low = open_price - candle.low
                        print(f"  - Zysk na low: {profit_low:.1f} pkt")
                        if profit_low >= be_prog_price:
                            be_triggered = True
                            be_activated_this_candle = True
                            current_sl = new_sl_after_be
                            print(f"  *** BE AKTYWOWANE! Zysk na low {profit_low:.1f} >= {be_prog_price}, SL przesunięty na {current_sl} ***")
                            print(f"  - Przesunięty SL będzie sprawdzany od następnej świeczki")
                    
                    if not be_activated_this_candle and candle.high >= current_sl - spread_adjustment:
                        if be_triggered:
                            print(f"  *** NOWY SL UDERZONY! High {candle.high} >= {current_sl - spread_adjustment}, TP = {max_profit:.1f} ***")
                        else:
                            print(f"  - Oryginalny SL uderzony przez high, TP = {max_profit:.1f}")
                        return max_profit
                    elif be_activated_this_candle:
                        print(f"  - BE właśnie aktywowane, pomijam sprawdzenie SL na tej świeczce")
                    
                    profit = open_price - candle.low
                    if profit > max_profit:
                        max_profit = profit
                        print(f"  - NOWY maksymalny zysk: {max_profit:.1f} pkt")
                    else:
                        max_profit = max(max_profit, profit)
        
        return max_profit
    
    def has_sufficient_data(self, instrument: str, open_time: int) -> bool:
        """
        Sprawdza czy są dostępne wystarczające dane świeczkowe
        
        Args:
            instrument: Nazwa instrumentu
            open_time: Unix timestamp otwarcia pozycji
        
        Returns:
            True jeśli są dane, False jeśli brak
        """
        # Znajdź prawdziwą nazwę tabeli
        real_table_name = self._find_table_name(instrument)
        if not real_table_name:
            return False
        
        try:
            # Sprawdź czy jest przynajmniej jedna świeczka od 60 sekund przed otwarciem
            start_time = open_time - 60
            query = self.candle_queries.get_candles_from_time(real_table_name)
            rows = self._execute_query(query, (start_time,))
            result = len(rows) > 0
            print(f"CandleAnalyzer: Tabela {real_table_name} ma {len(rows)} świeczek od {start_time}")
            return result
        except Exception as e:
            print(f"CandleAnalyzer: Błąd przy sprawdzaniu danych dla {real_table_name}: {e}")
            return False
