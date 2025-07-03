# 🔔 Moduł Monitorowania Nowych Zleceń - Dokumentacja Rozwoju

## 📍 **Lokalizacja:**
- **Główny moduł:** `monitoring/order_monitor.py`
- **Konfiguracja:** `config/monitor_config.py`
- **Integracja:** `gui/data_viewer.py`

## 🎯 **Obecna funkcjonalność:**
- **Automatyczne sprawdzanie** bazy co X sekund (domyślnie 30s)
- **Detekcja nowych ticketów** przez porównanie ze znanymi
- **Powiadomienia dźwiękowe** przy nowych zleceniach
- **Interface ustawień** - włącz/wyłącz, zmiana interwału
- **Singleton pattern** - jeden monitor na aplikację

## 🔧 **Jak dodać nowe funkcje:**

### **1. Dodanie nowego typu powiadomienia:**
```python
# W order_monitor.py w metodzie _notify_new_order()

def _notify_new_order(self, order_data: dict):
    # Istniejące powiadomienia
    self._play_notification_sound()
    
    # 🆕 DODAJ TUTAJ:
    # self._show_desktop_notification(order_data)
    # self._send_email_notification(order_data) 
    # self._log_to_file(order_data)
    # self._update_external_api(order_data)
```

### **2. Dodanie nowego callback:**
```python
# W DataViewer._on_new_order_detected()

def _on_new_order_detected(self, order_data: dict):
    # 🆕 DODAJ AKCJE TUTAJ:
    
    # Automatyczne odświeżenie tabeli
    self.load_data()
    
    # Powiadomienie na ekranie
    self._show_popup_notification(order_data)
    
    # Zapis do pliku log
    self._log_new_order(order_data)
    
    # Integracja z MQL5
    self._notify_mql5(order_data)
```

### **3. Rozszerzenie konfiguracji:**
```python
# W config/monitor_config.py

DEFAULT_MONITOR_SETTINGS = {
    "enabled": True,
    "check_interval": 30,
    "play_sound": True,
    "show_console_log": True,
    "auto_start": True,
    
    # 🆕 NOWE OPCJE:
    "show_desktop_notifications": True,
    "auto_refresh_table": False,
    "send_email_alerts": False,
    "log_to_file": True,
    "webhook_url": "",
}
```

## 📋 **Przykłady rozszerzeń:**

### **A. Powiadomienia Windows (toast):**
```python
def _show_desktop_notification(self, order_data):
    try:
        import win10toast
        toaster = win10toast.ToastNotifier()
        toaster.show_toast(
            "Nowe Zlecenie",
            f"#{order_data['ticket']} - {order_data['symbol']}",
            duration=5
        )
    except ImportError:
        pass
```

### **B. Automatyczne odświeżenie tabeli:**
```python
def _on_new_order_detected(self, order_data: dict):
    # Odśwież tabelę jeśli nowe zlecenie z dzisiaj
    if self._is_today_order(order_data['open_time']):
        self.load_data()
```

### **C. Zapis do pliku log:**
```python
def _log_new_order(self, order_data: dict):
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("new_orders.log", "a") as f:
        f.write(f"{timestamp}: {order_data}\n")
```

## 🎯 **Gotowe punkty rozszerzenia:**

1. **`_notify_new_order()`** - dodawanie powiadomień
2. **`_on_new_order_detected()`** - akcje w GUI  
3. **`DEFAULT_MONITOR_SETTINGS`** - nowe opcje konfiguracji
4. **`_show_monitor_settings()`** - rozszerzenie interfejsu ustawień
5. **Callback system** - dodawanie nowych reakcji

## 💡 **Wskazówki implementacji:**

1. **Zawsze testuj** nowe funkcje z małym interwałem (5s)
2. **Używaj try/except** - monitor nie może crashować aplikacji
3. **Loguj wszystko** - ułatwia debugging
4. **Callback pattern** - łatwe dodawanie nowych reakcji
5. **Konfiguracja przez GUI** - użytkownik nie musi edytować kodu

---

**Autor:** Claude AI  
**Data:** Grudzień 2024  
**Wersja dokumentacji:** 1.0
