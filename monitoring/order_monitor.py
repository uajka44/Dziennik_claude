"""
Monitor nowych zleceń - sprawdza bazę danych co X sekund w poszukiwaniu nowych pozycji
"""
import time
import threading
from datetime import datetime
from typing import Optional, Callable, Set
from database.connection import execute_query
from config.database_config import POSITIONS_TABLE


class NewOrderMonitor:
    """Monitor nowych zleceń tradingowych"""
    
    def __init__(self, check_interval: int = 30):
        """
        Args:
            check_interval: Interwał sprawdzania w sekundach (domyślnie 30s)
        """
        self.check_interval = check_interval
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Zbiór już znanych ticketów
        self.known_tickets: Set[int] = set()
        
        # Callbacks dla różnych zdarzeń
        self.on_new_order_callbacks = []  # List[Callable]
        self.on_error_callbacks = []      # List[Callable]
        
        # Inicjalizuj znane tickety przy starcie
        self._initialize_known_tickets()
    
    def _initialize_known_tickets(self):
        """Inicjalizuje zbiór już istniejących ticketów"""
        try:
            query = f"SELECT ticket FROM {POSITIONS_TABLE}"
            rows = execute_query(query)
            self.known_tickets = {row[0] for row in rows if row[0]}
            print(f"[OrderMonitor] Załadowano {len(self.known_tickets)} istniejących ticketów")
        except Exception as e:
            print(f"[OrderMonitor] Błąd inicjalizacji: {e}")
            self.known_tickets = set()
    
    def start_monitoring(self):
        """Uruchamia monitoring w osobnym wątku"""
        if self.is_running:
            print("[OrderMonitor] Monitor już działa")
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print(f"[OrderMonitor] Rozpoczęto monitoring (sprawdzanie co {self.check_interval}s)")
    
    def stop_monitoring(self):
        """Zatrzymuje monitoring"""
        self.is_running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        print("[OrderMonitor] Zatrzymano monitoring")
    
    def _monitor_loop(self):
        """Główna pętla monitorowania"""
        while self.is_running:
            try:
                self._check_for_new_orders()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"[OrderMonitor] Błąd w pętli monitorowania: {e}")
                self._notify_error(e)
                time.sleep(5)  # Krótka przerwa przed ponowieniem
    
    def _check_for_new_orders(self):
        """Sprawdza czy pojawiły się nowe zlecenia"""
        try:
            # Pobierz wszystkie aktualne tickety
            query = f"SELECT ticket, open_time, symbol, type, volume FROM {POSITIONS_TABLE}"
            rows = execute_query(query)
            
            current_tickets = {row[0] for row in rows if row[0]}
            
            # Znajdź nowe tickety
            new_tickets = current_tickets - self.known_tickets
            
            if new_tickets:
                print(f"[OrderMonitor] 🆕 Znaleziono {len(new_tickets)} nowych zleceń: {list(new_tickets)}")
                
                # Pobierz szczegóły nowych zleceń
                for ticket in new_tickets:
                    order_data = next((row for row in rows if row[0] == ticket), None)
                    if order_data:
                        self._notify_new_order({
                            'ticket': order_data[0],
                            'open_time': order_data[1],
                            'symbol': order_data[2],
                            'type': order_data[3],
                            'volume': order_data[4]
                        })
                
                # Aktualizuj zbiór znanych ticketów
                self.known_tickets.update(new_tickets)
        
        except Exception as e:
            print(f"[OrderMonitor] Błąd sprawdzania nowych zleceń: {e}")
            self._notify_error(e)
    
    def _notify_new_order(self, order_data: dict):
        """Powiadamia o nowym zleceniu"""
        try:
            # Odegraj dźwięk powiadomienia
            self._play_notification_sound()
            
            # Formatuj informacje o zleceniu
            ticket = order_data['ticket']
            symbol = order_data['symbol']
            order_type = "BUY" if order_data['type'] == 0 else "SELL" if order_data['type'] == 1 else "UNKNOWN"
            volume = order_data['volume']
            
            print(f"[OrderMonitor] 📊 NOWE ZLECENIE: #{ticket} | {symbol} | {order_type} | {volume} lot")
            
            # Wywołaj wszystkie zarejestrowane callbacks
            for callback in self.on_new_order_callbacks:
                try:
                    callback(order_data)
                except Exception as e:
                    print(f"[OrderMonitor] Błąd callback: {e}")
        
        except Exception as e:
            print(f"[OrderMonitor] Błąd powiadomienia: {e}")
    
    def _notify_error(self, error: Exception):
        """Powiadamia o błędzie"""
        for callback in self.on_error_callbacks:
            try:
                callback(error)
            except Exception as e:
                print(f"[OrderMonitor] Błąd error callback: {e}")
    
    def _play_notification_sound(self):
        """Odgrywa dźwięk powiadomienia o nowym zleceniu"""
        try:
            import winsound
            # Odegraj dźwięk powiadomienia (częstotliwość 800Hz przez 200ms)
            winsound.Beep(800, 200)
        except ImportError:
            # Fallback dla systemów nie-Windows
            try:
                import os
                # Podwójny terminal bell dla wyróżnienia
                os.system('printf "\a"; sleep 0.1; printf "\a"')
            except:
                print("[OrderMonitor] 🔔 NOWE ZLECENIE (brak obsługi dźwięku)")
    
    def add_new_order_callback(self, callback: Callable):
        """Dodaje callback wywoływany przy nowym zleceniu"""
        self.on_new_order_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable):
        """Dodaje callback wywoływany przy błędzie"""
        self.on_error_callbacks.append(callback)
    
    def set_check_interval(self, interval: int):
        """Ustawia nowy interwał sprawdzania"""
        self.check_interval = max(5, interval)  # Minimum 5 sekund
        print(f"[OrderMonitor] Ustawiono interwał sprawdzania: {self.check_interval}s")
    
    def get_status(self) -> dict:
        """Zwraca status monitora"""
        return {
            'is_running': self.is_running,
            'check_interval': self.check_interval,
            'known_tickets_count': len(self.known_tickets),
            'callbacks_count': len(self.on_new_order_callbacks)
        }


# Singleton instance
_monitor_instance: Optional[NewOrderMonitor] = None

def get_order_monitor() -> NewOrderMonitor:
    """Zwraca singleton instance monitora"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = NewOrderMonitor()
    return _monitor_instance
