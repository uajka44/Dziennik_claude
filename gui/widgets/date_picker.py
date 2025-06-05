"""
Komponenty kalendarza i wyboru dat
"""
import tkinter as tk
from tkinter import ttk
from datetime import date
from tkcalendar import DateEntry


class DateRangePicker(ttk.Frame):
    """Widget do wyboru zakresu dat"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Data początkowa
        ttk.Label(self, text="Data początkowa:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.start_date_entry = DateEntry(
            self, 
            width=12, 
            background='darkblue',
            foreground='white', 
            borderwidth=2, 
            date_pattern='yyyy-mm-dd',
            year=date.today().year, 
            month=date.today().month, 
            day=date.today().day
        )
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=5)

        # Data końcowa
        ttk.Label(self, text="Data końcowa:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.end_date_entry = DateEntry(
            self, 
            width=12, 
            background='darkblue',
            foreground='white', 
            borderwidth=2, 
            date_pattern='yyyy-mm-dd',
            year=date.today().year, 
            month=date.today().month, 
            day=date.today().day
        )
        self.end_date_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Przycisk "Dzisiaj"
        self.today_button = ttk.Button(self, text="Dzisiaj", command=self.set_today)
        self.today_button.grid(row=0, column=2, padx=5, pady=5)
    
    def set_today(self):
        """Ustawia daty na dzisiejszy dzień"""
        today = date.today()
        self.start_date_entry.set_date(today)
        self.end_date_entry.set_date(today)
    
    def get_start_date(self):
        """Zwraca datę początkową jako string YYYY-MM-DD"""
        return self.start_date_entry.get()
    
    def get_end_date(self):
        """Zwraca datę końcową jako string YYYY-MM-DD"""
        return self.end_date_entry.get()
    
    def get_date_range(self):
        """Zwraca zakres dat jako tuple (start, end)"""
        return self.get_start_date(), self.get_end_date()
    
    def set_date_range(self, start_date, end_date):
        """Ustawia zakres dat"""
        if isinstance(start_date, str):
            # Konwersja z string na date object
            year, month, day = map(int, start_date.split('-'))
            start_date = date(year, month, day)
        
        if isinstance(end_date, str):
            year, month, day = map(int, end_date.split('-'))
            end_date = date(year, month, day)
        
        self.start_date_entry.set_date(start_date)
        self.end_date_entry.set_date(end_date)


class InstrumentSelector(ttk.LabelFrame):
    """Widget do wyboru instrumentów"""
    
    def __init__(self, parent, instruments, **kwargs):
        super().__init__(parent, text="Instrumenty", **kwargs)
        
        self.instruments = instruments
        self.checkboxes = {}
        self.variables = {}
        
        # Tworzenie checkboxów dla każdego instrumentu
        for i, instrument in enumerate(instruments):
            var = tk.BooleanVar()
            checkbox = ttk.Checkbutton(
                self, 
                text=instrument, 
                variable=var
            )
            checkbox.grid(row=i//2, column=i%2, padx=5, pady=2, sticky="w")
            
            self.checkboxes[instrument] = checkbox
            self.variables[instrument] = var
    
    def get_selected_instruments(self):
        """Zwraca listę wybranych instrumentów"""
        return [instrument for instrument, var in self.variables.items() if var.get()]
    
    def set_selected_instruments(self, selected_instruments):
        """Ustawia wybrane instrumenty"""
        for instrument, var in self.variables.items():
            var.set(instrument in selected_instruments)
    
    def select_all(self):
        """Zaznacza wszystkie instrumenty"""
        for var in self.variables.values():
            var.set(True)
    
    def deselect_all(self):
        """Odznacza wszystkie instrumenty"""
        for var in self.variables.values():
            var.set(False)


class StopLossSelector(ttk.LabelFrame):
    """Widget do wyboru typów stop loss"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Typy Stop Loss", **kwargs)
        
        # Checkbox dla sl_recznie
        self.sl_recznie_var = tk.BooleanVar()
        self.sl_recznie_cb = ttk.Checkbutton(
            self, 
            text="SL ręczne (z bazy)", 
            variable=self.sl_recznie_var
        )
        self.sl_recznie_cb.grid(row=0, column=0, columnspan=2, padx=5, pady=2, sticky="w")
        
        # Checkbox dla sl z bazy
        self.sl_baza_var = tk.BooleanVar()
        self.sl_baza_cb = ttk.Checkbutton(
            self, 
            text="SL z bazy", 
            variable=self.sl_baza_var
        )
        self.sl_baza_cb.grid(row=1, column=0, columnspan=2, padx=5, pady=2, sticky="w")
        
        # Checkbox dla sl stałego + pole input
        self.sl_staly_var = tk.BooleanVar()
        self.sl_staly_cb = ttk.Checkbutton(
            self, 
            text="SL stały:", 
            variable=self.sl_staly_var,
            command=self._toggle_sl_staly_entry
        )
        self.sl_staly_cb.grid(row=2, column=0, padx=5, pady=2, sticky="w")
        
        from .custom_entries import NumericEntry
        self.sl_staly_entry = NumericEntry(
            self, 
            width=10,
            allow_decimal=True,
            allow_negative=False
        )
        self.sl_staly_entry.grid(row=2, column=1, padx=5, pady=2, sticky="w")
        self.sl_staly_entry.config(state='disabled')
        
        ttk.Label(self, text="pkt").grid(row=2, column=2, padx=2, pady=2)
    
    def _toggle_sl_staly_entry(self):
        """Przełącza dostępność pola SL stały"""
        if self.sl_staly_var.get():
            self.sl_staly_entry.config(state='normal')
        else:
            self.sl_staly_entry.config(state='disabled')
    
    def get_selected_sl_types(self):
        """Zwraca słownik z wybranymi typami SL"""
        return {
            'sl_recznie': self.sl_recznie_var.get(),
            'sl_baza': self.sl_baza_var.get(),
            'sl_staly': self.sl_staly_var.get()
        }
    
    def get_sl_staly_value(self):
        """Zwraca wartość SL stałego"""
        if self.sl_staly_var.get():
            return self.sl_staly_entry.get_float()
        return None
