"""
Główny kalkulator Take Profit
"""
from typing import List, Dict, Optional, Tuple
from database.models import Position, TPCalculationResult
import sqlite3
from database.queries import TPCalculationQueries
from config.database_config import DB_PATH
from calculations.candle_analyzer import CandleAnalyzer
from calculations.position_analyzer import PositionAnalyzer
from utils.date_utils import unix_to_date_string
from datetime import datetime


class TPCalculator:
    """Główna klasa do obliczania maksymalnego Take Profit"""
    
    def __init__(self):
        self.candle_analyzer = CandleAnalyzer()
        self.position_analyzer = PositionAnalyzer()
        self.tp_queries = TPCalculationQueries()
        self._connection = None
        self._ensure_tp_table_exists()
    
    def _get_connection(self):
        """Zwraca połączenie dla aktualnego wątku"""
        if self._connection is None:
            self._connection = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30.0)
        return self._connection
    
    def _execute_update(self, query, params=None):
        """Wykonuje zapytanie UPDATE/INSERT z obsługą wątków"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.rowcount
        finally:
            cursor.close()
    
    def _ensure_tp_table_exists(self):
        """Tworzy tabelę wyników TP jeśli nie istnieje"""
        try:
            query = self.tp_queries.create_tp_results_table()
            self._execute_update(query)
        except Exception as e:
            print(f"Błąd podczas tworzenia tabeli TP: {e}")
    
    def close_connection(self):
        """Zamyka połączenie"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def calculate_tp_for_date_range(self, 
                                  start_date: str, 
                                  end_date: str,
                                  instruments: List[str],
                                  sl_types: Dict[str, bool],
                                  sl_staly_values: Optional[Dict[str, float]] = None,
                                  be_prog: Optional[float] = None,
                                  be_offset: Optional[float] = None,
                                  spread: float = 0,
                                  save_to_db: bool = False,
                                  detailed_logs: bool = False) -> List[TPCalculationResult]:
        """Oblicza maksymalny TP dla pozycji z zakresu dat"""
        print(f"TPCalculator: Rozpoczynam obliczenia dla {start_date} - {end_date}")
        print(f"TPCalculator: Instrumenty: {instruments}")
        
        # Pobierz pozycje
        print("TPCalculator: Pobieram pozycje...")
        positions = self.position_analyzer.get_positions_for_date_range(
            start_date, end_date, instruments
        )
        
        print(f"TPCalculator: Znaleziono {len(positions)} pozycji")
        
        if not positions:
            print("TPCalculator: Brak pozycji do analizy")
            return []
        
        results = []
        missing_data_positions = []
        
        for i, position in enumerate(positions):
            print()  # Pusta linijka przed każdą pozycją
            print(f"\033[94mTPCalculator: Analizuję pozycję {i+1}/{len(positions)}: {position.ticket}\033[0m")  # Niebieski kolor
            
            # Sprawdź dostępność danych świeczkowych
            if not self.candle_analyzer.has_sufficient_data(position.symbol, position.open_time):
                print(f"TPCalculator: Brak danych świeczkowych dla pozycji {position.ticket}")
                missing_data_positions.append(position.ticket)
                continue
            
            # Oblicz TP dla tej pozycji
            try:
                tp_result = self._calculate_tp_for_position(
                    position, sl_types, sl_staly_values, be_prog, be_offset, spread, detailed_logs
                )
                
                if tp_result:
                    tp_result.calculation_date = start_date if start_date == end_date else f"{start_date}_{end_date}"
                    results.append(tp_result)
                    print(f"TPCalculator: Pozycja {position.ticket} - wynik dodany")
                else:
                    print(f"TPCalculator: Pozycja {position.ticket} - brak wyniku")
                    
            except Exception as e:
                print(f"TPCalculator: Błąd przy obliczaniu pozycji {position.ticket}: {e}")
                import traceback
                traceback.print_exc()
        
        # Zapisz do bazy danych jeśli wymagane
        if save_to_db and results:
            print(f"TPCalculator: Zapisuję {len(results)} wyników do bazy")
            self._save_results_to_db(results)
        
        # Wyświetl komunikat o brakujących danych
        if missing_data_positions:
            print(f"TPCalculator: Brak danych świeczkowych dla pozycji: {', '.join(map(str, missing_data_positions))}")
        
        print(f"TPCalculator: Obliczenia zakończone. Wyników: {len(results)}")
        return results
    
    def _calculate_tp_for_position(self,
                                 position: Position,
                                 sl_types: Dict[str, bool],
                                 sl_staly_values: Optional[Dict[str, float]],
                                 be_prog: Optional[float],
                                 be_offset: Optional[float],
                                 spread: float,
                                 detailed_logs: bool = False) -> Optional[TPCalculationResult]:
        """
        Oblicza TP dla pojedynczej pozycji
        
        Args:
            position: Obiekt pozycji
            sl_types: Wybrane typy SL
            sl_staly_value: Wartość stałego SL
            be_prog: Próg BE
            be_offset: Offset BE
            spread: Spread
        
        Returns:
            Obiekt TPCalculationResult lub None
        """
        # Pobierz świeczki
        candles = self.candle_analyzer.get_candles_for_position(
            position.symbol, position.open_time
        )
        
        if not candles:
            return None
        
        # Pobierz stop lossy
        stop_losses = self.position_analyzer.get_position_stop_losses(
            position, sl_staly_values
        )
        print(f"TPCalculator: Stop losses dla pozycji {position.ticket}: {stop_losses}")
        
        # Inicjalizuj wynik
        result = TPCalculationResult(
            ticket=position.ticket,
            open_price=position.open_price,
            open_time=position.open_time,
            position_type=position.position_type_string,  # Użyj nowej właściwości
            symbol=position.symbol,
            setup=position.setup,
            spread=spread
        )
        print(f"TPCalculator: Pozycja {position.ticket}: typ={position.position_type_string}, open_price={position.open_price}, type_int={position.type_as_int}")
        
        # Oblicz TP dla sl_recznie
        if sl_types.get('sl_recznie', False) and stop_losses['sl_recznie'] is not None:
            print(f"TPCalculator: Obliczam TP dla sl_recznie = {stop_losses['sl_recznie']}")
            result.max_tp_sl_recznie = self.candle_analyzer.calculate_max_tp_basic(
                candles, position.type_as_int, position.open_price, 
                stop_losses['sl_recznie'], spread, detailed_logs
            )
            result.sl_recznie_value = stop_losses['sl_recznie']
            print(f"TPCalculator: Wynik TP sl_recznie: {result.max_tp_sl_recznie}")
        
        # Oblicz TP dla sl z bazy
        if sl_types.get('sl_baza', False) and stop_losses['sl_baza'] is not None:
            print(f"TPCalculator: Obliczam TP dla sl_baza = {stop_losses['sl_baza']}")
            result.max_tp_sl_recznie = self.candle_analyzer.calculate_max_tp_basic(
                candles, position.type_as_int, position.open_price,
                stop_losses['sl_baza'], spread, detailed_logs
            )
            print(f"TPCalculator: Wynik TP sl_baza: {result.max_tp_sl_recznie}")
        
        # Oblicz TP dla sl stałego
        if sl_types.get('sl_staly', False) and stop_losses['sl_staly'] is not None:
            print(f"TPCalculator: Obliczam TP dla sl_staly = {stop_losses['sl_staly']}")
            tp_result = self.candle_analyzer.calculate_max_tp_basic(
                candles, position.type_as_int, position.open_price,
                stop_losses['sl_staly'], spread, detailed_logs
            )
            result.max_tp_sl_staly = tp_result
            result.sl_staly_value = stop_losses['sl_staly']
            
            if tp_result is None:
                print(f"TPCalculator: Wynik TP sl_staly: None (błąd danych)")
            else:
                print(f"TPCalculator: Wynik TP sl_staly: {tp_result} ({'pozycja wybita' if tp_result == 0 else 'normalny zysk'})")
        
        # Oblicz TP z BE jeśli parametry podane
        if (be_prog is not None and be_offset is not None and 
            sl_types.get('sl_staly', False) and stop_losses['sl_staly'] is not None):
            
            print(f"TPCalculator: Obliczam TP z BE: prog={be_prog}, offset={be_offset}, initial_sl={stop_losses['sl_staly']}")
            print(f"*** WYWOŁUJĘ METODĘ BE Z KOMUNIKATAMI ***")
            result.max_tp_sl_be = self.candle_analyzer.calculate_max_tp_with_be(
                candles, position.type_as_int, position.open_price,
                stop_losses['sl_staly'], be_prog, be_offset, spread, detailed_logs
            )
            print(f"*** METODA BE ZAKOŃCZONA ***")
            result.be_prog = be_prog
            result.be_offset = be_offset
            print(f"TPCalculator: Wynik TP BE: {result.max_tp_sl_be}")
        
        return result
    
    def _save_results_to_db(self, results: List[TPCalculationResult]):
        """Zapisuje wyniki do bazy danych"""
        try:
            query = self.tp_queries.insert_tp_result()
            
            for result in results:
                params = (
                    result.ticket,
                    result.open_price,
                    result.open_time,
                    result.position_type,
                    result.symbol,
                    result.setup,
                    result.max_tp_sl_staly,
                    result.max_tp_sl_recznie,
                    result.max_tp_sl_be,
                    result.sl_staly_value,
                    result.sl_recznie_value,
                    result.be_prog,
                    result.be_offset,
                    result.spread,
                    result.calculation_date,
                    result.notes
                )
                
                self._execute_update(query, params)
                
        except Exception as e:
            print(f"Błąd podczas zapisywania wyników do bazy: {e}")
    
    def get_calculation_summary(self, results: List[TPCalculationResult]) -> Dict[str, any]:
        """
        Zwraca podsumowanie wyników kalkulacji
        
        Args:
            results: Lista wyników kalkulacji
        
        Returns:
            Słownik z podsumowaniem
        """
        if not results:
            return {
                'total_positions': 0,
                'successful_calculations': 0,
                'avg_tp_sl_staly': 0,
                'avg_tp_sl_recznie': 0,
                'avg_tp_sl_be': 0,
                'max_tp_sl_staly': 0,
                'max_tp_sl_recznie': 0,
                'max_tp_sl_be': 0
            }
        
        # Filtruj wyniki gdzie są dane (włącznie z 0.0)
        tp_staly_values = [r.max_tp_sl_staly for r in results if r.max_tp_sl_staly is not None]
        tp_recznie_values = [r.max_tp_sl_recznie for r in results if r.max_tp_sl_recznie is not None]
        tp_be_values = [r.max_tp_sl_be for r in results if r.max_tp_sl_be is not None]
        
        return {
            'total_positions': len(results),
            'successful_calculations': len([r for r in results if any([
                r.max_tp_sl_staly is not None, r.max_tp_sl_recznie is not None, r.max_tp_sl_be is not None
            ])]),
            'avg_tp_sl_staly': sum(tp_staly_values) / len(tp_staly_values) if tp_staly_values else 0,
            'avg_tp_sl_recznie': sum(tp_recznie_values) / len(tp_recznie_values) if tp_recznie_values else 0,
            'avg_tp_sl_be': sum(tp_be_values) / len(tp_be_values) if tp_be_values else 0,
            'max_tp_sl_staly': max(tp_staly_values) if tp_staly_values else 0,
            'max_tp_sl_recznie': max(tp_recznie_values) if tp_recznie_values else 0,
            'max_tp_sl_be': max(tp_be_values) if tp_be_values else 0,
            'positions_with_data': {
                'sl_staly': len(tp_staly_values),
                'sl_recznie': len(tp_recznie_values),
                'sl_be': len(tp_be_values)
            }
        }
