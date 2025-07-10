"""
Przeglądarka danych transakcji (zrefaktoryzowana wersja oryginalnego DatabaseViewer)
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, timedelta
import csv
from tkcalendar import DateEntry
from config.field_definitions import (
    TEXT_FIELDS, CHECKBOX_FIELDS, ALL_FIELDS, COLUMNS, 
    COLUMN_HEADERS, COLUMN_WIDTHS, COLUMN_ALIGNMENTS, SETUP_SHORTCUTS
)
from config.database_config import AVAILABLE_INSTRUMENTS
from database.connection import execute_query, execute_update
from database.queries import PositionQueries
from gui.widgets.custom_entries import SetupEntry
from utils.date_utils import date_range_to_unix, format_time_for_display
from utils.formatting import format_profit_points, format_checkbox_value
from database.migration.sl_opening_migrator import get_sl_migrator
from monitoring.order_monitor import get_order_monitor
from config.monitor_config import DEFAULT_MONITOR_SETTINGS
from config.setup_config import get_setup_config


class CheckboxDropdown:
    """Rozwijana lista z checkboxami"""
    
    def __init__(self, parent, callback=None, default_text="Symbole"):
        self.parent = parent
        self.callback = callback
        self.is_open = False
        self.items = {}
        self.variables = {}
        
        # Główny frame
        self.main_frame = ttk.Frame(parent)
        
        # Przycisk rozwijający
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill="x")
        
        self.display_var = tk.StringVar(value=default_text)
        self.dropdown_button = ttk.Button(
            self.button_frame,
            textvariable=self.display_var,
            command=self._toggle_dropdown,
            width=20
        )
        self.dropdown_button.pack(side="left", fill="x", expand=True)
        
        # Strzałka
        self.arrow_label = ttk.Label(self.button_frame, text="▼", width=3)
        self.arrow_label.pack(side="right")
        
        # Popup z checkboxami
        self.popup = None
        
    def add_item(self, key, text, checked=True):
        """Dodaje element do listy"""
        var = tk.BooleanVar(value=checked)
        self.variables[key] = var
        self.items[key] = {
            'text': text,
            'var': var,
            'checkbox': None
        }
        var.trace('w', self._on_item_changed)
        
    def _toggle_dropdown(self):
        """Przełącza widoczność listy rozwijanej"""
        if self.is_open:
            self._close_dropdown()
        else:
            self._open_dropdown()
            
    def _open_dropdown(self):
        """Otwiera listę rozwijaną"""
        if self.popup:
            return
            
        self.is_open = True
        self.arrow_label.config(text="▲")
        
        # Twórz popup
        self.popup = tk.Toplevel(self.main_frame)
        self.popup.wm_overrideredirect(True)
        self.popup.wm_attributes("-topmost", True)
        
        # Pozycjonowanie
        x = self.dropdown_button.winfo_rootx()
        y = self.dropdown_button.winfo_rooty() + self.dropdown_button.winfo_height()
        self.popup.geometry(f"+{x}+{y}")
        
        # Frame dla checkboxów
        popup_frame = ttk.Frame(self.popup, relief="solid", borderwidth=1)
        popup_frame.pack(fill="both", expand=True, padx=1, pady=1)
        
        # "Wszystkie" checkbox
        self.all_var = tk.BooleanVar(value=True)
        all_cb = ttk.Checkbutton(
            popup_frame,
            text="Wszystkie",
            variable=self.all_var,
            command=self._on_all_changed
        )
        all_cb.pack(anchor="w", padx=5, pady=2)
        
        # Separator
        ttk.Separator(popup_frame, orient="horizontal").pack(fill="x", padx=5, pady=2)
        
        # Checkboxy dla poszczególnych elementów
        for key, item in self.items.items():
            cb = ttk.Checkbutton(
                popup_frame,
                text=item['text'],
                variable=item['var'],
                command=self._on_item_changed
            )
            cb.pack(anchor="w", padx=5, pady=1)
            item['checkbox'] = cb
            
        # Obsługa zamykania
        self.popup.bind("<FocusOut>", self._on_focus_out)
        self.popup.bind("<Button-1>", self._on_click_outside)
        self.popup.focus_set()
        
        # Aktualizuj tekst na przycisku
        self._update_display()
        
    def _close_dropdown(self):
        """Zamyka listę rozwijaną"""
        self.is_open = False
        self.arrow_label.config(text="▼")
        
        if self.popup:
            self.popup.destroy()
            self.popup = None
            
    def _on_focus_out(self, event):
        """Zamyka dropdown po utracie fokusu"""
        # Sprawdź czy focus nie przeszedł na element wewnątrz popup
        if event.widget == self.popup:
            self.main_frame.after(100, self._close_dropdown)
            
    def _on_click_outside(self, event):
        """Zamyka dropdown po kliknięciu poza nim"""
        pass  # Checkboxy mają własną obsługę
        
    def _on_all_changed(self):
        """Obsługa zmiany 'Wszystkie'"""
        all_checked = self.all_var.get()
        
        # Ustaw wszystkie checkboxy
        for item in self.items.values():
            item['var'].set(all_checked)
            
        self._update_display()
        if self.callback:
            self.callback()
            
    def _on_item_changed(self, *args):
        """Obsługa zmiany konkretnego elementu"""
        # Sprawdź czy wszystkie są zaznaczone
        all_checked = all(item['var'].get() for item in self.items.values())
        self.all_var.set(all_checked)
        
        self._update_display()
        if self.callback:
            self.callback()
            
    def _update_display(self):
        """Aktualizuje tekst na przycisku"""
        checked_count = sum(1 for item in self.items.values() if item['var'].get())
        total_count = len(self.items)
        
        if checked_count == 0:
            text = "Brak wybranych"
        elif checked_count == total_count:
            text = "Wszystkie"
        else:
            text = f"{checked_count}/{total_count} wybranych"
            
        self.display_var.set(text)
        
    def get_selected(self):
        """Zwraca listę wybranych kluczy"""
        return [key for key, item in self.items.items() if item['var'].get()]
        
    def grid(self, **kwargs):
        """Umieszcza widget w grid"""
        self.main_frame.grid(**kwargs)
        
    def pack(self, **kwargs):
        """Umieszcza widget przez pack"""
        self.main_frame.pack(**kwargs)


class DataViewer:
    """Przeglądarka danych transakcji"""
    
    def __init__(self, parent):
        self.parent = parent
        self.position_queries = PositionQueries()
        
        # Import edit managera i navigation handler
        from gui.edit_manager import EditWindowManager
        from gui.navigation_handler import EditNavigationHandler
        self.edit_manager = EditWindowManager()
        self.navigation_handler = EditNavigationHandler(self)
        
        # Inicjalizuj migrator
        self.sl_migrator = get_sl_migrator()
        
        # Inicjalizuj monitor nowych zleceń
        self.order_monitor = get_order_monitor()
        self.order_monitor.add_new_order_callback(self._on_new_order_detected)
        
        self._create_widgets()
        self._setup_layout()
        
        # Uruchom migrację przy starcie
        self._run_initial_migration()
        
        # Uruchom monitoring nowych zleceń (jeśli włączone)
        if DEFAULT_MONITOR_SETTINGS["auto_start"]:
            self._start_order_monitoring()
    
    def _create_widgets(self):
        """Tworzy wszystkie widgety"""
        
        # === SEKCJA FILTRÓW ===
        self.filter_frame = ttk.LabelFrame(self.parent, text="Filtry")
        self.filter_frame.pack(fill="x", padx=10, pady=10)
        
        # Filtr instrumentów - rozwijana lista z checkboxami
        ttk.Label(self.filter_frame, text="Instrumenty:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Custom rozwijana lista z checkboxami
        self.instruments_dropdown = CheckboxDropdown(self.filter_frame, callback=self.load_data)
        self.instruments_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Załaduj symbole i dodaj do dropdown
        self._load_available_symbols()
        
        # Filtr Setup - rozwijana lista z checkboxami
        ttk.Label(self.filter_frame, text="Setup:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        # Checkbox do włączania/wyłączania filtra Setup
        self.setup_filter_active_var = tk.BooleanVar(value=False)  # Domyślnie nieaktywny
        self.setup_filter_checkbox = ttk.Checkbutton(
            self.filter_frame,
            text="Aktywny",
            variable=self.setup_filter_active_var,
            command=self.load_data
        )
        self.setup_filter_checkbox.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Custom rozwijana lista z checkboxami dla setupów
        self.setup_dropdown = CheckboxDropdown(self.filter_frame, callback=self._on_setup_filter_change, default_text="Setupy")
        self.setup_dropdown.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        
        # Załaduj setupy i dodaj do dropdown
        self._load_available_setups()
        
        # Filtr Wątpliwe trejdy - lista rozwijana
        ttk.Label(self.filter_frame, text="Wątpliwe trejdy:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        # Lista rozwijana z opcjami filtrowania
        self.suspicious_trades_var = tk.StringVar(value="nieaktywny")  # Domyślnie nieaktywny
        self.suspicious_trades_combo = ttk.Combobox(
            self.filter_frame,
            textvariable=self.suspicious_trades_var,
            values=["nieaktywny", "tylko wątpliwe", "nie pokazuj wątpliwych"],
            state="readonly",
            width=20
        )
        self.suspicious_trades_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.suspicious_trades_combo.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        
        # Przyciski diagnostyczne i narzędzia zostały przeniesione do menu Narzędzia -> Ustawienia
        
        # === SEKCJA WYBORU DAT I PARAMETRÓW TP ===
        self.dates_and_tp_frame = ttk.Frame(self.parent)
        self.dates_and_tp_frame.pack(fill="x", padx=10, pady=10)
        
        # === RAMKA DAT (lewa strona) ===
        self.date_frame = ttk.LabelFrame(self.dates_and_tp_frame, text="Zakres dat")
        self.date_frame.pack(side="left", fill="y", padx=(0, 10))
        
        # Pola do wyboru dat z kalendarza
        ttk.Label(self.date_frame, text="Data początkowa:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.start_date_entry = DateEntry(
            self.date_frame, width=12, background='darkblue',
            foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
            year=date.today().year, month=date.today().month, day=date.today().day
        )
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.date_frame, text="Data końcowa:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.end_date_entry = DateEntry(
            self.date_frame, width=12, background='darkblue',
            foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
            year=date.today().year, month=date.today().month, day=date.today().day
        )
        self.end_date_entry.grid(row=1, column=1, padx=5, pady=5)

        # Przyciski
        self.search_button = ttk.Button(self.date_frame, text="Wyszukaj", command=self.load_data)
        self.search_button.grid(row=2, column=0, padx=5, pady=5)
        
        self.today_button = ttk.Button(self.date_frame, text="Dzisiaj", command=self._set_today)
        self.today_button.grid(row=2, column=1, padx=5, pady=5)
        
        # Przyciski nawigacji po dniach
        nav_frame = ttk.Frame(self.date_frame)
        nav_frame.grid(row=3, column=0, columnspan=2, pady=5)
        
        self.prev_day_button = ttk.Button(nav_frame, text="Prev", command=self._prev_day)
        self.prev_day_button.pack(side="left", padx=5)
        
        self.next_day_button = ttk.Button(nav_frame, text="Next", command=self._next_day)
        self.next_day_button.pack(side="left", padx=5)
        
        # === RAMKA PARAMETRÓW TP (prawa strona) ===
        self.tp_params_frame = ttk.LabelFrame(self.dates_and_tp_frame, text="Parametry TP")
        self.tp_params_frame.pack(side="left", fill="both", expand=True)
        
        # Konfiguracja kolumn dla równego rozkładu
        self.tp_params_frame.columnconfigure(0, weight=1)
        self.tp_params_frame.columnconfigure(1, weight=1)
        self.tp_params_frame.columnconfigure(2, weight=1)
        
        # Import potrzebnych komponentów
        from gui.widgets.custom_entries import NumericEntry
        from gui.widgets.date_picker import StopLossSelector
        
        # === TYPY STOP LOSS ===
        self.sl_selector = StopLossSelector(self.tp_params_frame)
        self.sl_selector.grid(row=0, column=0, padx=10, pady=10, sticky="nw")
        
        # === SPREAD ===
        spread_frame = ttk.LabelFrame(self.tp_params_frame, text="Spread")
        spread_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nw")
        
        ttk.Label(spread_frame, text="Spread:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.spread_entry = NumericEntry(spread_frame, width=10, allow_decimal=True)
        self.spread_entry.insert(0, "0")
        self.spread_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(spread_frame, text="pkt").grid(row=0, column=2, padx=2, pady=5)
        
        # === BREAK EVEN ===
        be_frame = ttk.LabelFrame(self.tp_params_frame, text="Break Even")
        be_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nw")
        
        # BE Prog
        ttk.Label(be_frame, text="Próg BE:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.be_prog_entry = NumericEntry(be_frame, width=10, allow_decimal=True)
        self.be_prog_entry.insert(0, "10.0")
        self.be_prog_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(be_frame, text="pkt").grid(row=0, column=2, padx=2, pady=5)
        
        # BE Offset
        ttk.Label(be_frame, text="Offset BE:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.be_offset_entry = NumericEntry(be_frame, width=10, allow_decimal=True)
        self.be_offset_entry.insert(0, "1.0")
        self.be_offset_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(be_frame, text="pkt").grid(row=1, column=2, padx=2, pady=5)
        
        # === DODATKOWE OPCJE ===
        options_frame = ttk.LabelFrame(self.tp_params_frame, text="Opcje")
        options_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
        # Checkbox szczegółowe logi
        self.detailed_logs_var = tk.BooleanVar()
        self.detailed_logs_cb = ttk.Checkbutton(
            options_frame, 
            text="Szczegółowe logi (analiza świeczka po świeczce)", 
            variable=self.detailed_logs_var
        )
        self.detailed_logs_cb.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Checkbox zapisz do bazy
        self.save_to_db_var = tk.BooleanVar()
        self.save_to_db_cb = ttk.Checkbutton(
            options_frame, 
            text="Zapisz wyniki do bazy danych", 
            variable=self.save_to_db_var
        )
        self.save_to_db_cb.grid(row=0, column=1, padx=20, pady=5, sticky="w")
        
        # Przycisk oblicz TP
        self.calculate_tp_button = ttk.Button(
            options_frame,
            text="Oblicz TP dla zakresu",
            command=self._calculate_tp_for_range
        )
        self.calculate_tp_button.grid(row=1, column=0, columnspan=2, padx=5, pady=10)

        # === SEKCJA PODSUMOWANIA ===
        summary_separator = ttk.Separator(self.date_frame, orient="horizontal")
        summary_separator.grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)

        self.summary_frame = ttk.Frame(self.date_frame)
        self.summary_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        ttk.Label(self.summary_frame, text="Suma profitu:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.total_profit_label = ttk.Label(self.summary_frame, text="0.00")
        self.total_profit_label.grid(row=0, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(self.summary_frame, text="Liczba transakcji:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.transactions_count_label = ttk.Label(self.summary_frame, text="0")
        self.transactions_count_label.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        # Dodajemy statystykę winrate
        ttk.Label(self.summary_frame, text="Wygrywające trejdy:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.winning_trades_label = ttk.Label(self.summary_frame, text="0")
        self.winning_trades_label.grid(row=2, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(self.summary_frame, text="Przegrywające trejdy:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.losing_trades_label = ttk.Label(self.summary_frame, text="0")
        self.losing_trades_label.grid(row=3, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(self.summary_frame, text="Winrate:").grid(row=4, column=0, padx=5, pady=2, sticky="w")
        self.winrate_label = ttk.Label(self.summary_frame, text="0.00%")
        self.winrate_label.grid(row=4, column=1, padx=5, pady=2, sticky="w")

        # === SEKCJA TABELI ===
        self.tree_frame = ttk.Frame(self.parent)
        self.tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Pasek przewijania pionowy i poziomy
        vscrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical")
        hscrollbar = ttk.Scrollbar(self.tree_frame, orient="horizontal")

        self.tree = ttk.Treeview(
            self.tree_frame, 
            yscrollcommand=vscrollbar.set, 
            xscrollcommand=hscrollbar.set
        )
        self.tree["columns"] = COLUMNS

        vscrollbar.config(command=self.tree.yview)
        hscrollbar.config(command=self.tree.xview)

        # Konfiguracja kolumn
        self.tree.column("#0", width=0, stretch=tk.NO)

        for col in COLUMNS:
            width = COLUMN_WIDTHS.get(col, 100)
            anchor = COLUMN_ALIGNMENTS.get(col, tk.W)
            self.tree.column(col, width=width, anchor=anchor)
            self.tree.heading(col, text=COLUMN_HEADERS.get(col, col), anchor=anchor)

        # Umieszczanie elementów
        vscrollbar.pack(side="right", fill="y")
        hscrollbar.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        # Obsługa edycji danych
        self.tree.bind("<Double-1>", self.edit_item)
        
        # Informacja o statusie edycji
        self.edit_status_frame = ttk.LabelFrame(self.parent, text="Status edycji")
        self.edit_status_frame.pack(fill="x", padx=10, pady=5)
        
        self.edit_status_label = ttk.Label(
            self.edit_status_frame, 
            text="🔴 Brak aktywnej edycji", 
            foreground="red"
        )
        self.edit_status_label.pack(padx=10, pady=5)
        
        # Sprawdzaj status co 1 sekundę
        self._update_edit_status()
        self.parent.after(1000, self._update_edit_status_loop)
    
    def _setup_layout(self):
        """Konfiguruje układ"""
        # Automatyczne załadowanie danych na dzisiaj
        self._set_today()
        self.load_data()
    
    def _load_available_symbols(self):
        """Pobiera unikalne symbole z bazy danych i dodaje do dropdown"""
        try:
            # Pobierz unikalne symbole z bazy - uporządkowane i oczyszczone
            query = "SELECT DISTINCT symbol FROM positions ORDER BY symbol"
            rows = execute_query(query)
            raw_symbols = [row[0] for row in rows if row[0]]  # Filtruj puste wartości
            
            # Grupuj symbole - usuń duplikaty spowodowane \x00
            clean_symbols = {}
            for symbol in raw_symbols:
                # Usuń \x00 z końca dla porównania
                clean_symbol = symbol.rstrip('\x00')
                if clean_symbol not in clean_symbols:
                    clean_symbols[clean_symbol] = []
                clean_symbols[clean_symbol].append(symbol)
            
            print(f"Znalezione symbole: {clean_symbols}")
            
            # Dodaj symbole do dropdown
            for clean_symbol, original_symbols in clean_symbols.items():
                self.instruments_dropdown.add_item(
                    clean_symbol, 
                    clean_symbol.upper(), 
                    checked=True
                )
                # Przechowuj również mapowanie do oryginalnych symbolów
                setattr(self, f'_original_symbols_{clean_symbol}', original_symbols)
                    
            print(f"Załadowano {len(clean_symbols)} unikalnych symbolów do dropdown: {list(clean_symbols.keys())}")
            
        except Exception as e:
            print(f"Błąd podczas ładowania symbolów: {e}")
            messagebox.showerror("Błąd", f"Nie można załadować symbolów z bazy: {e}")
    
    def _load_available_setups(self):
        """Pobiera dostępne setupy z konfiguracji i dodaje do dropdown"""
        try:
            # Pobierz setupy z nowego systemu konfiguracji
            setup_config = get_setup_config()
            setup_names = setup_config.get_setup_names()
            
            print(f"Znalezione setupy: {setup_names}")
            
            # Dodaj setupy do dropdown
            for setup_name in sorted(setup_names):
                self.setup_dropdown.add_item(
                    setup_name, 
                    setup_name,  # Wyświetla nazwę setupu (rgr, momo, etc.)
                    checked=True  # Domyślnie wszystkie zaznaczone
                )
                    
            print(f"Załadowano {len(setup_names)} setupów do dropdown: {setup_names}")
            
        except Exception as e:
            print(f"Błąd podczas ładowania setupów: {e}")
            messagebox.showerror("Błąd", f"Nie można załadować setupów: {e}")
    
    def _on_setup_filter_change(self):
        """Obsługuje zmianę w filtrze Setup"""
        # Zawsze przeładuj dane gdy zmieni się filtr Setup
        # (load_data sprawdzi czy filtr jest aktywny)
        self.load_data()
    

    def _show_symbol_diagnostics(self):
        """Pokazuje diagnostykę symbolów z bazy danych"""
        try:
            # Pobierz wszystkie symbole z bazy (nie unikalne)
            query = "SELECT symbol, COUNT(*) as count FROM positions GROUP BY symbol ORDER BY symbol"
            rows = execute_query(query)
            
            # Stwórz okno diagnostyczne
            diag_window = tk.Toplevel(self.parent)
            diag_window.title("Diagnostyka symbolów")
            diag_window.geometry("600x400")
            
            # Text widget z scrollbarem
            text_frame = ttk.Frame(diag_window)
            text_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD)
            scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Analiza symbolów
            content = "=== DIAGNOSTYKA SYMBOLÓW Z BAZY DANYCH ===\n\n"
            content += f"Znaleziono {len(rows)} unikalnych symbolów:\n\n"
            
            for symbol, count in rows:
                # Szczegółowa analiza symbolu
                repr_symbol = repr(symbol)  # Pokaże ukryte znaki
                length = len(symbol) if symbol else 0
                
                content += f"Symbol: {symbol}\n"
                content += f"  Reprezentacja: {repr_symbol}\n"
                content += f"  Długość: {length} znaków\n"
                content += f"  Liczba transakcji: {count}\n"
                
                # Sprawdź czy pasuje do AVAILABLE_INSTRUMENTS
                matches = []
                for avail in AVAILABLE_INSTRUMENTS:
                    if symbol and (symbol.lower() == avail.lower() or symbol.upper() == avail.upper()):
                        matches.append(avail)
                
                if matches:
                    content += f"  Pasuje do: {matches}\n"
                else:
                    content += f"  \u26a0\ufe0f BRAK DOPASOWANIA w AVAILABLE_INSTRUMENTS\n"
                
                content += "\n"
            
            content += "\n=== AVAILABLE_INSTRUMENTS (konfiguracja) ===\n\n"
            for instr in AVAILABLE_INSTRUMENTS:
                content += f"  {instr}\n"
            
            # Wyświetl treść
            text_widget.insert("1.0", content)
            text_widget.config(state="disabled")  # Tylko do odczytu
            
            # Przyciski
            button_frame = ttk.Frame(diag_window)
            button_frame.pack(fill="x", padx=10, pady=10)
            
            def save_to_file():
                """Zapisuje diagnostykę do pliku"""
                try:
                    from tkinter import filedialog
                    filename = filedialog.asksaveasfilename(
                        defaultextension=".txt",
                        filetypes=[("Pliki tekstowe", "*.txt"), ("Wszystkie pliki", "*.*")],
                        title="Zapisz diagnostykę jako..."
                    )
                    
                    if filename:
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(content)
                        messagebox.showinfo("Sukces", f"Diagnostyka zapisana do:\n{filename}")
                except Exception as e:
                    messagebox.showerror("Błąd", f"Nie można zapisać pliku: {e}")
            
            def copy_to_clipboard():
                """Kopiuje diagnostykę do schowka"""
                try:
                    diag_window.clipboard_clear()
                    diag_window.clipboard_append(content)
                    messagebox.showinfo("Sukces", "Diagnostyka skopiowana do schowka!")
                except Exception as e:
                    messagebox.showerror("Błąd", f"Nie można skopiować do schowka: {e}")
            
            # Dodaj przyciski
            ttk.Button(button_frame, text="Zapisz do pliku", command=save_to_file).pack(side="left", padx=5)
            ttk.Button(button_frame, text="Kopiuj do schowka", command=copy_to_clipboard).pack(side="left", padx=5)
            ttk.Button(button_frame, text="Zamknij", command=diag_window.destroy).pack(side="right", padx=5)
            
            # Dodaj również wydruk do konsoli
            print("\n" + "="*60)
            print(content)
            print("="*60 + "\n")
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd diagnostyki: {e}")
    
    def _quick_diagnostics(self):
        """Szybka diagnostyka - tylko wydruk do konsoli"""
        try:
            print("\n" + "="*80)
            print("QUICK DIAGNOSTYKA SYMBOLÓW - WYNIKI W KONSOLI")
            print("="*80)
            
            # Pobierz symbole z bazy
            query = "SELECT symbol, COUNT(*) as count FROM positions GROUP BY symbol ORDER BY symbol"
            rows = execute_query(query)
            
            print(f"\nZnaleziono {len(rows)} unikalnych symbolów w bazie:\n")
            
            for symbol, count in rows:
                print(f"Symbol: '{symbol}'")
                print(f"  repr(): {repr(symbol)}")
                print(f"  len(): {len(symbol) if symbol else 0}")
                print(f"  transakcje: {count}")
                
                # Sprawdź dopasowania
                matches = []
                for avail in AVAILABLE_INSTRUMENTS:
                    if symbol and (symbol.lower() == avail.lower() or symbol.upper() == avail.upper()):
                        matches.append(avail)
                
                if matches:
                    print(f"  STATUS: ✅ PASUJE do {matches}")
                else:
                    print(f"  STATUS: ❌ BRAK DOPASOWANIA!")
                print()
            
            print("AVAILABLE_INSTRUMENTS z konfiguracji:")
            for instr in AVAILABLE_INSTRUMENTS:
                print(f"  '{instr}'")
            
            print("\n" + "="*80)
            print("KONIEC DIAGNOSTYKI - skopiuj powyższe wyniki")
            print("="*80 + "\n")
            
            messagebox.showinfo("Diagnostyka", "Wyniki wyświetlone w konsoli!\nSkopiuj z okna terminala.")
            
        except Exception as e:
            print(f"Błąd quick diagnostyki: {e}")
            messagebox.showerror("Błąd", f"Błąd diagnostyki: {e}")
    
    def _set_today(self):
        """Ustawia daty na dzisiejszy dzień"""
        today = date.today()
        self.start_date_entry.set_date(today)
        self.end_date_entry.set_date(today)
    
    def _prev_day(self):
        """Przesuwa datę początkową o jeden dzień wstecz i ustawia datę końcową jako datę początkową"""
        current_start_date = self.start_date_entry.get_date()  # get_date() zwraca obiekt date
        new_date = current_start_date - timedelta(days=1)
        
        self.start_date_entry.set_date(new_date)
        self.end_date_entry.set_date(new_date)
        
        # Automatycznie załaduj dane dla nowej daty
        self.load_data()
    
    def _next_day(self):
        """Przesuwa datę początkową o jeden dzień do przodu i ustawia datę końcową jako datę początkową"""
        current_start_date = self.start_date_entry.get_date()  # get_date() zwraca obiekt date
        new_date = current_start_date + timedelta(days=1)
        
        self.start_date_entry.set_date(new_date)
        self.end_date_entry.set_date(new_date)
        
        # Automatycznie załaduj dane dla nowej daty
        self.load_data()
    
    def _run_initial_migration(self):
        """Uruchamia migrację SL opening przy starcie aplikacji"""
        try:
            print("[DataViewer] Uruchamianie migracji SL opening...")
            migrated_count = self.sl_migrator.run_migration()
            
            # Pokaż status migracji
            status = self.sl_migrator.get_migration_status()
            print(f"[DataViewer] Status migracji: {status}")
            
            if migrated_count > 0:
                print(f"[DataViewer] Zmigrowano {migrated_count} rekordów SL opening")
                
        except Exception as e:
            print(f"[DataViewer] Błąd migracji przy starcie: {e}")
    
    def _restore_from_backup(self):
        """Uruchamia przywracanie danych z backupu"""
        try:
            # Pokaż okno potwierdzenia
            result = messagebox.askyesno(
                "Przywracanie z backupu",
                "Czy chcesz przywrócić dane SL (opening) z backupu?\n\n"
                "To nadpisze puste wartości sl_opening w tabeli positions."
            )
            
            if result:
                print("[DataViewer] Uruchamianie przywracania z backupu...")
                restored_count = self.sl_migrator.restore_from_backup()
                
                if restored_count > 0:
                    messagebox.showinfo(
                        "Sukces", 
                        f"Przywrócono {restored_count} rekordów z backupu!\n\n"
                        f"Odśwież dane (przycisk Wyszukaj) aby zobaczyć zmiany."
                    )
                    # Automatycznie odśwież dane
                    self.load_data()
                else:
                    messagebox.showinfo(
                        "Informacja", 
                        "Brak danych do przywracania lub wszystkie już są zaktualizowane."
                    )
                    
        except Exception as e:
            print(f"[DataViewer] Błąd przywracania z backupu: {e}")
            messagebox.showerror("Błąd", f"Nie udało się przywrócić z backupu:\n{e}")
    
    def _start_order_monitoring(self):
        """Uruchamia monitoring nowych zleceń"""
        try:
            self.order_monitor.set_check_interval(DEFAULT_MONITOR_SETTINGS["check_interval"])
            self.order_monitor.start_monitoring()
        except Exception as e:
            print(f"[DataViewer] Błąd uruchamiania monitora: {e}")
    
    def _on_new_order_detected(self, order_data: dict):
        """Callback wywoływany gdy zostanie wykryte nowe zlecenie"""
        try:
            ticket = order_data['ticket']
            symbol = order_data['symbol']
            
            # Tu możesz dodać dodatkowe akcje w przyszłości:
            # - Automatyczne odświeżenie tabeli
            # - Powiadomienia na ekranie  
            # - Zapisywanie do logów
            # - Integracja z zewnętrznymi systemami
            
            print(f"[DataViewer] 📨 Wykryto nowe zlecenie: #{ticket} ({symbol})")
            
        except Exception as e:
            print(f"[DataViewer] Błąd obsługi nowego zlecenia: {e}")
    
    def load_data(self):
        """Ładuje dane z bazy danych dla podanego zakresu dat i wybranych instrumentów"""
        # Uruchom migrację przed każdym wyszukiwaniem
        try:
            migrated_count = self.sl_migrator.run_migration()
            if migrated_count > 0:
                print(f"[DataViewer] Zmigrowano dodatkowo {migrated_count} rekordów SL opening")
        except Exception as e:
            print(f"[DataViewer] Błąd migracji przy wyszukiwaniu: {e}")
        
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()

        try:
            start_unix, end_unix = date_range_to_unix(start_date, end_date)
        except ValueError:
            messagebox.showerror("Błąd", "Nieprawidłowy format daty. Użyj formatu YYYY-MM-DD.")
            return

        # Czyszczenie tabeli
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            # Sprawdzenie które instrumenty są wybrane z dropdown
            selected_symbols = self.instruments_dropdown.get_selected()
            
            if not selected_symbols:
                # Jeśli żaden nie jest zaznaczony, nie pokazuj nic
                self.total_profit_label.config(text="0.00")
                self.transactions_count_label.config(text="0")
                self.winning_trades_label.config(text="0")
                self.losing_trades_label.config(text="0")
                self.winrate_label.config(text="0.00%")
                return
            
            # Sprawdź czy wszystkie są wybrane
            all_symbols_count = len(self.instruments_dropdown.items)
            all_selected = len(selected_symbols) == all_symbols_count
            
            # Dynamiczne generowanie zapytania SQL
            columns_str = ", ".join(COLUMNS)
            
            # Podstawowe parametry
            base_params = [start_unix, end_unix]
            
            # Buduj warunki WHERE
            where_conditions = ["open_time BETWEEN ? AND ?"]
            
            # Warunek dla instrumentów
            if not all_selected:
                # Wybrane instrumenty - uwzględnij oba formaty (z i bez \x00)
                expanded_symbols = []
                for clean_symbol in selected_symbols:
                    expanded_symbols.append(clean_symbol)  # Oryginalny format
                    expanded_symbols.append(clean_symbol + '\x00')  # Format z null character
                
                placeholders = ", ".join(["?" for _ in expanded_symbols])
                where_conditions.append(f"symbol IN ({placeholders})")
                base_params.extend(expanded_symbols)
            
            # Warunek dla Setup (jeśli filtr jest aktywny)
            setup_filter_active = self.setup_filter_active_var.get()
            if setup_filter_active:
                selected_setups = self.setup_dropdown.get_selected()
                if selected_setups:
                    # Dodaj warunek dla setupów
                    setup_placeholders = ", ".join(["?" for _ in selected_setups])
                    where_conditions.append(f"setup IN ({setup_placeholders})")
                    base_params.extend(selected_setups)
                    print(f"Filtr Setup aktywny - wybrane setupy: {selected_setups}")
                else:
                    print("Filtr Setup aktywny ale brak wybranych setupów - zwracam puste wyniki")
                    # Jeśli filtr aktywny ale nic nie wybrano, zwróć puste wyniki
                    self.total_profit_label.config(text="0.00")
                    self.transactions_count_label.config(text="0")
                    self.winning_trades_label.config(text="0")
                    self.losing_trades_label.config(text="0")
                    self.winrate_label.config(text="0.00%")
                    return
            
            # Warunek dla filtra Wątpliwe trejdy
            suspicious_filter = self.suspicious_trades_var.get()
            if suspicious_filter == "tylko wątpliwe":
                # Pokazuj tylko trejdy z magic_number = 7
                where_conditions.append("magic_number = ?")
                base_params.append(7)
                print("Filtr 'Wątpliwe trejdy' - pokazuję tylko wątpliwe (magic_number = 7)")
            elif suspicious_filter == "nie pokazuj wątpliwych":
                # Ukryj trejdy z magic_number = 7
                where_conditions.append("(magic_number IS NULL OR magic_number != ?)")
                base_params.append(7)
                print("Filtr 'Wątpliwe trejdy' - ukrywam wątpliwe (magic_number = 7)")
            else:  # nieaktywny
                # Nie dodawaj żadnych warunków - pokazuj wszystkie trejdy
                print("Filtr 'Wątpliwe trejdy' - nieaktywny, pokazuję wszystkie trejdy")
            
            # Złóż zapytanie
            where_clause = " AND ".join(where_conditions)
            query = f"""
            SELECT {columns_str}
            FROM positions 
            WHERE {where_clause}
            ORDER BY open_time
            """
            
            rows = execute_query(query, base_params)
            
            print(f"Pobrano {len(rows)} transakcji dla wybranych filtrów")
            print(f"Wybrane symbole: {selected_symbols if not all_selected else 'wszystkie'}")
            if not all_selected:
                print(f"Rozszerzone symbole (z \\x00): {expanded_symbols}")

            # Przygotowanie zmiennych do obliczenia sumy profitu i statystyk
            total_profit = 0.0
            transaction_count = len(rows)
            winning_trades = 0
            losing_trades = 0

            # Wypełnianie tabeli danymi
            for row in rows:
                display_values = []
                current_profit = None
                
                for i, col in enumerate(COLUMNS):
                    value = row[i]

                    if col == "open_time":
                        display_values.append(format_time_for_display(value))
                    elif col == "profit_points":
                        adjusted_value = value / 100 if value is not None else None
                        current_profit = adjusted_value
                        if adjusted_value is not None:
                            total_profit += adjusted_value
                        display_values.append(format_profit_points(value))
                    elif col in [field.name for field in CHECKBOX_FIELDS]:
                        display_values.append(format_checkbox_value(value))
                    else:
                        display_values.append(value or "")
                
                # Obliczanie statystyk winrate na podstawie profitu
                if current_profit is not None:
                    if current_profit > 0:
                        winning_trades += 1
                    elif current_profit < 0:
                        losing_trades += 1
                    # Ignorujemy transakcje z profilem = 0 (Break Even)

                self.tree.insert("", "end", values=tuple(display_values))

            # Obliczanie winrate
            total_counted_trades = winning_trades + losing_trades
            winrate = (winning_trades / total_counted_trades * 100) if total_counted_trades > 0 else 0.0

            # Aktualizacja etykiet z podsumowaniem
            self.total_profit_label.config(text=f"{total_profit:.2f}")
            self.transactions_count_label.config(text=f"{transaction_count}")
            self.winning_trades_label.config(text=f"{winning_trades}")
            self.losing_trades_label.config(text=f"{losing_trades}")
            self.winrate_label.config(text=f"{winrate:.2f}%")

            if not rows:
                messagebox.showinfo("Informacja", "Brak danych dla podanych filtrów.")
                self.total_profit_label.config(text="0.00")
                self.transactions_count_label.config(text="0")
                self.winning_trades_label.config(text="0")
                self.losing_trades_label.config(text="0")
                self.winrate_label.config(text="0.00%")

        except Exception as e:
            print(f"Błąd bazy danych: {e}")
            messagebox.showerror("Błąd bazy danych", f"Wystąpił błąd podczas ładowania danych: {e}")
    
    def edit_item(self, event):
        """Obsługuje edycję elementu po podwójnym kliknięciu - używa EditWindowManager"""
        selected_items = self.tree.selection()
        if not selected_items:
            return

        selected_item = selected_items[0]
        values = self.tree.item(selected_item, "values")

        if not values:
            return

        # Pobierz ticket z wartości
        try:
            ticket = values[COLUMNS.index("ticket")]
            print(f"[DataViewer] Próba otwarcia edycji dla ticket: {ticket}")
        except (ValueError, IndexError) as e:
            print(f"[DataViewer] Błąd pobierania ticket: {e}")
            messagebox.showerror("Błąd", "Nie można pobrać numeru ticket")
            return

        # Podświetl klikniętą pozycję - NOWE!
        self.highlight_ticket(ticket)

        # Callback do aktualizacji widoku po zapisaniu
        def on_save_callback(updated_values):
            """Aktualizuje widok tabeli po zapisaniu zmian"""
            self.tree.item(selected_item, values=tuple(updated_values))
            print(f"[DataViewer] Zaktualizowano widok dla ticket: {ticket}")

        # Sprawdź czy okno edycji jest już otwarte
        save_current_first = self.edit_manager.is_editing()
        
        if save_current_first:
            print(f"[DataViewer] Okno edycji już otwarte - zapisuję poprzednie przed otwarciem nowego")
        
        # Otwórz okno edycji przez manager
        self.edit_manager.open_edit_window(
            parent=self.parent,
            ticket=ticket,
            values=values,
            callback=on_save_callback,
            navigation_handler=self.navigation_handler,
            save_current_first=save_current_first
        )
    
    def _update_edit_status(self):
        """Aktualizuje status edycji w interfejsie"""
        try:
            if self.edit_manager.is_editing():
                ticket = self.edit_manager.get_current_ticket()
                self.edit_status_label.config(
                    text=f"🟢 Edytowane: ticket {ticket}",
                    foreground="green"
                )
            else:
                self.edit_status_label.config(
                    text="🔴 Brak aktywnej edycji",
                    foreground="red"
                )
        except Exception as e:
            print(f"[DataViewer] Błąd aktualizacji statusu: {e}")
    
    def _update_edit_status_loop(self):
        """Pętla aktualizacji statusu co sekundę"""
        self._update_edit_status()
        self.parent.after(1000, self._update_edit_status_loop)
    
    def export_current_data(self):
        """Eksportuje aktualnie wyświetlane dane do CSV"""
        # Pobierz wszystkie elementy z drzewa
        items = self.tree.get_children()
        if not items:
            messagebox.showwarning("Uwaga", "Brak danych do eksportu")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Eksportuj dane jako..."
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    
                    # Nagłówki
                    headers = [COLUMN_HEADERS.get(col, col) for col in COLUMNS]
                    writer.writerow(headers)
                    
                    # Dane
                    for item in items:
                        values = self.tree.item(item, "values")
                        writer.writerow(values)
                
                messagebox.showinfo("Sukces", f"Dane zostały wyeksportowane do:\n{filename}")
                
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można zapisać pliku:\n{e}")
    
    def highlight_ticket(self, ticket):
        """Podświetla (zaznacza) pozycję z podanym ticket w tabeli"""
        try:
            # Normalizuj ticket do porównania
            def normalize_ticket(t):
                if t is None:
                    return ""
                s = str(t).strip().rstrip('\x00').rstrip('\0')
                s = ''.join(char for char in s if char.isprintable())
                return s
            
            target_ticket = normalize_ticket(ticket)
            ticket_col_index = COLUMNS.index("ticket")
            
            # Przejdź przez wszystkie elementy w tabeli
            for item in self.tree.get_children():
                item_values = self.tree.item(item, "values")
                if len(item_values) > ticket_col_index:
                    item_ticket = normalize_ticket(item_values[ticket_col_index])
                    
                    if item_ticket == target_ticket:
                        # Zaznacz element
                        self.tree.selection_set(item)
                        self.tree.focus(item)
                        
                        # Przewiń tabelu żeby element był widoczny
                        self.tree.see(item)
                        
                        print(f"[DataViewer] Podświetlono ticket: {ticket}")
                        return True
            
            print(f"[DataViewer] Nie znaleziono ticket do podświetlenia: {ticket}")
            return False
            
        except Exception as e:
            print(f"[DataViewer] Błąd podświetlania ticket: {e}")
            return False
    
    def _calculate_tp_for_range(self):
        """Oblicza TP dla aktualnie wyświetlanych pozycji (uwzględnia wszystkie filtry)"""
        try:
            print("[DataViewer] Rozpoczynam kalkulację TP dla przefiltrowanych danych...")
            
            # OPCJA A: Pobierz tickety z aktualnie wyświetlanych danych w tabeli
            displayed_tickets = []
            ticket_col_index = None
            
            # Znajdź indeks kolumny ticket
            from config.field_definitions import COLUMNS
            try:
                ticket_col_index = COLUMNS.index("ticket")
            except ValueError:
                messagebox.showerror("Błąd", "Nie znaleziono kolumny 'ticket' w tabeli")
                return
            
            # Pobierz wszystkie tickety z aktualnie wyświetlanej tabeli
            for item in self.tree.get_children():
                values = self.tree.item(item, "values")
                if len(values) > ticket_col_index:
                    ticket = values[ticket_col_index]
                    if ticket:  # Ignoruj puste tickety
                        displayed_tickets.append(str(ticket).strip())
            
            print(f"[DataViewer] Znaleziono {len(displayed_tickets)} pozycji w tabeli")
            
            if not displayed_tickets:
                messagebox.showwarning("Uwaga", "Brak pozycji w tabeli do obliczenia TP.\n\nUpewnij się, że:\n- Wybrano odpowiedni zakres dat\n- Filtry pozwalają na wyświetlenie pozycji")
                return
            
            print(f"[DataViewer] Pierwsze 5 ticketów: {displayed_tickets[:5]}")
            
            # Pobierz parametry SL
            sl_types = self.sl_selector.get_selected_sl_types()
            if not any(sl_types.values()):
                messagebox.showerror("Błąd", "Wybierz przynajmniej jeden typ Stop Loss")
                return
            
            sl_staly_values = self.sl_selector.get_sl_staly_values()
            
            # Pobierz parametry BE
            be_prog = self.be_prog_entry.get_float()
            be_offset = self.be_offset_entry.get_float()
            
            # Pobierz spread
            spread = self.spread_entry.get_float() or 0
            
            # Pobierz opcje
            detailed_logs = self.detailed_logs_var.get()
            save_to_db = self.save_to_db_var.get()
            
            print(f"[DataViewer] Parametry kalkulacji:")
            print(f"  - Liczba ticketów: {len(displayed_tickets)}")
            print(f"  - SL typy: {sl_types}")
            print(f"  - SL stały: {sl_staly_values}")
            print(f"  - BE: prog={be_prog}, offset={be_offset}")
            print(f"  - Spread: {spread}")
            print(f"  - Opcje: detailed_logs={detailed_logs}, save_to_db={save_to_db}")
            
            # Walidacja parametrów BE
            if sl_types.get('sl_staly', False) and be_prog is not None and be_offset is not None:
                if be_prog <= 0 or be_offset <= 0:
                    messagebox.showerror("Błąd", "Parametry Break Even muszą być dodatnie")
                    return
            
            # Walidacja spread
            if spread < 0:
                messagebox.showerror("Błąd", "Spread nie może być ujemny")
                return
            
            # Importuj i uruchom kalkulator
            from calculations.tp_calculator import TPCalculator
            
            print("[DataViewer] Uruchamianie kalkulatora TP dla ticketów...")
            calculator = TPCalculator()
            
            # Wyłącz przycisk na czas obliczeń
            self.calculate_tp_button.config(state="disabled", text="Obliczam...")
            
            # Wykonaj kalkulację dla konkretnych ticketów (NOWA METODA)
            results = calculator.calculate_tp_for_tickets(
                tickets=displayed_tickets,
                sl_types=sl_types,
                sl_staly_values=sl_staly_values,
                be_prog=be_prog,
                be_offset=be_offset,
                spread=spread,
                save_to_db=save_to_db,
                detailed_logs=detailed_logs
            )
            
            print(f"[DataViewer] Kalkulacja zakończona. Wyników: {len(results)}")
            
            # Pokaż informację o filtrach w wynikach
            active_filters = []
            if self.setup_filter_active_var.get():
                selected_setups = self.setup_dropdown.get_selected()
                active_filters.append(f"Setup: {', '.join(selected_setups)}")
            
            suspicious_filter = self.suspicious_trades_var.get()
            if suspicious_filter != "nieaktywny":
                active_filters.append(f"Wątpliwe trejdy: {suspicious_filter}")
            
            # Pokaż wyniki z informacją o filtrach
            self._show_tp_results(results, calculator, active_filters)
            
        except Exception as e:
            print(f"[DataViewer] Błąd kalkulacji TP: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Błąd kalkulacji", f"Nie można obliczyć TP:\n{e}")
        
        finally:
            # Przywróć przycisk
            self.calculate_tp_button.config(state="normal", text="Oblicz TP dla zakresu")
    
    def _show_tp_results(self, results, calculator, active_filters=None):
        """Pokazuje wyniki kalkulacji TP w osobnym oknie"""
        try:
            # Utwórz okno wyników
            filters_info = f" (z filtrami: {', '.join(active_filters)})" if active_filters else ""
            results_window = tk.Toplevel(self.parent)
            results_window.title(f"Wyniki kalkulacji TP - {len(results)} pozycji{filters_info}")
            results_window.geometry("1200x700")
            
            # Główna ramka
            main_frame = ttk.Frame(results_window)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # === INFO O FILTRACH ===
            if active_filters:
                info_frame = ttk.LabelFrame(main_frame, text="Aktywne filtry")
                info_frame.pack(fill="x", pady=(0, 10))
                
                info_text = "Kalkulacja uwzględnia tylko pozycje spełniające filtry: " + ", ".join(active_filters)
                ttk.Label(info_frame, text=info_text, foreground="blue", font=("Arial", 9)).pack(padx=10, pady=5)
            
            # === TABELA WYNIKÓW ===
            results_frame = ttk.LabelFrame(main_frame, text="Wyniki kalkulacji")
            results_frame.pack(fill="both", expand=True, pady=(0, 10))
            
            # Scrollbary
            v_scrollbar = ttk.Scrollbar(results_frame, orient="vertical")
            h_scrollbar = ttk.Scrollbar(results_frame, orient="horizontal")
            
            # Kolumny wyników
            columns = [
                "ticket", "symbol", "type", "open_time", "open_price", 
                "setup", "tp_sl_staly", "tp_sl_recznie", "tp_sl_be"
            ]
            
            # Treeview
            results_tree = ttk.Treeview(
                results_frame, 
                columns=columns,
                yscrollcommand=v_scrollbar.set,
                xscrollcommand=h_scrollbar.set
            )
            
            v_scrollbar.config(command=results_tree.yview)
            h_scrollbar.config(command=results_tree.xview)
            
            # Konfiguracja kolumn
            results_tree.column("#0", width=0, stretch=tk.NO)
            
            column_config = {
                "ticket": {"width": 80, "text": "Ticket"},
                "symbol": {"width": 100, "text": "Symbol"},
                "type": {"width": 60, "text": "Typ"},
                "open_time": {"width": 120, "text": "Czas otwarcia"},
                "open_price": {"width": 100, "text": "Cena otwarcia"},
                "setup": {"width": 100, "text": "Setup"},
                "tp_sl_staly": {"width": 100, "text": "TP (SL stały)"},
                "tp_sl_recznie": {"width": 100, "text": "TP (SL ręczne)"},
                "tp_sl_be": {"width": 100, "text": "TP (BE)"}
            }
            
            for col in columns:
                config = column_config[col]
                results_tree.column(col, width=config["width"], anchor=tk.CENTER)
                results_tree.heading(col, text=config["text"])
            
            # Wypełnij tabelę wynikami
            from utils.formatting import format_points, format_price
            
            for i, result in enumerate(results):
                values = (
                    result.ticket,
                    result.symbol,
                    result.position_type,
                    self._format_time(result.open_time),
                    format_price(result.open_price),
                    result.setup or "",
                    format_points(result.max_tp_sl_staly) if result.max_tp_sl_staly is not None else "",
                    format_points(result.max_tp_sl_recznie) if result.max_tp_sl_recznie is not None else "",
                    format_points(result.max_tp_sl_be) if result.max_tp_sl_be is not None else ""
                )
                results_tree.insert("", "end", values=values)
            
            # Umieszczenie elementów
            v_scrollbar.pack(side="right", fill="y")
            h_scrollbar.pack(side="bottom", fill="x")
            results_tree.pack(fill="both", expand=True)
            
            # === PODSUMOWANIE ===
            summary_frame = ttk.LabelFrame(main_frame, text="Podsumowanie")
            summary_frame.pack(fill="x", pady=10)
            
            # Oblicz statystyki
            summary = calculator.get_calculation_summary(results)
            
            # Wyświetl statystyki
            stats_frame = ttk.Frame(summary_frame)
            stats_frame.pack(fill="x", padx=10, pady=10)
            
            # Wiersz 1
            ttk.Label(stats_frame, text="Pozycji ogółem:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
            ttk.Label(stats_frame, text=str(summary['total_positions'])).grid(row=0, column=1, padx=5, pady=2)
            
            ttk.Label(stats_frame, text="Udanych obliczeń:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
            ttk.Label(stats_frame, text=str(summary['successful_calculations'])).grid(row=0, column=3, padx=5, pady=2)
            
            # Wiersz 2 - średnie
            ttk.Label(stats_frame, text="Średni TP (SL stały):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
            ttk.Label(stats_frame, text=f"{summary['avg_tp_sl_staly']:.1f} pkt").grid(row=1, column=1, padx=5, pady=2)
            
            ttk.Label(stats_frame, text="Średni TP (SL ręczne):").grid(row=1, column=2, padx=5, pady=2, sticky="w")
            ttk.Label(stats_frame, text=f"{summary['avg_tp_sl_recznie']:.1f} pkt").grid(row=1, column=3, padx=5, pady=2)
            
            ttk.Label(stats_frame, text="Średni TP (BE):").grid(row=1, column=4, padx=5, pady=2, sticky="w")
            ttk.Label(stats_frame, text=f"{summary['avg_tp_sl_be']:.1f} pkt").grid(row=1, column=5, padx=5, pady=2)
            
            # Wiersz 3 - maksymalne
            ttk.Label(stats_frame, text="Max TP (SL stały):").grid(row=2, column=0, padx=5, pady=2, sticky="w")
            ttk.Label(stats_frame, text=f"{summary['max_tp_sl_staly']:.1f} pkt").grid(row=2, column=1, padx=5, pady=2)
            
            ttk.Label(stats_frame, text="Max TP (SL ręczne):").grid(row=2, column=2, padx=5, pady=2, sticky="w")
            ttk.Label(stats_frame, text=f"{summary['max_tp_sl_recznie']:.1f} pkt").grid(row=2, column=3, padx=5, pady=2)
            
            ttk.Label(stats_frame, text="Max TP (BE):").grid(row=2, column=4, padx=5, pady=2, sticky="w")
            ttk.Label(stats_frame, text=f"{summary['max_tp_sl_be']:.1f} pkt").grid(row=2, column=5, padx=5, pady=2)
            
            # === PRZYCISKI ===
            buttons_frame = ttk.Frame(main_frame)
            buttons_frame.pack(fill="x", pady=10)
            
            # Przycisk eksportu
            def export_results():
                """Eksportuje wyniki do CSV"""
                filename = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                    title="Zapisz wyniki jako..."
                )
                
                if filename:
                    try:
                        import csv
                        with open(filename, 'w', newline='', encoding='utf-8') as file:
                            writer = csv.writer(file)
                            
                            # Nagłówki
                            headers = [
                                "Ticket", "Symbol", "Typ", "Czas otwarcia", "Cena otwarcia",
                                "Setup", "TP (SL stały)", "TP (SL ręczne)", "TP (BE)",
                                "SL stały", "SL ręczne", "BE prog", "BE offset", "Spread"
                            ]
                            writer.writerow(headers)
                            
                            # Dane
                            for result in results:
                                row = [
                                    result.ticket,
                                    result.symbol,
                                    result.position_type,
                                    self._format_time(result.open_time),
                                    result.open_price,
                                    result.setup or "",
                                    result.max_tp_sl_staly or "",
                                    result.max_tp_sl_recznie or "",
                                    result.max_tp_sl_be or "",
                                    result.sl_staly_value or "",
                                    result.sl_recznie_value or "",
                                    result.be_prog or "",
                                    result.be_offset or "",
                                    result.spread or ""
                                ]
                                writer.writerow(row)
                        
                        messagebox.showinfo("Sukces", f"Wyniki zostały zapisane do pliku:\n{filename}")
                        
                    except Exception as e:
                        messagebox.showerror("Błąd", f"Nie można zapisać pliku:\n{e}")
            
            ttk.Button(buttons_frame, text="Eksportuj wyniki", command=export_results).pack(side="left", padx=5)
            ttk.Button(buttons_frame, text="Zamknij", command=results_window.destroy).pack(side="right", padx=5)
            
            print(f"[DataViewer] Okno wyników utworzone z {len(results)} pozycjami")
            
        except Exception as e:
            print(f"[DataViewer] Błąd tworzenia okna wyników: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Błąd", f"Nie można pokazać wyników:\n{e}")
    
    def _format_time(self, unix_timestamp):
        """Formatuje timestamp do wyświetlenia"""
        from utils.date_utils import format_time_for_display
        return format_time_for_display(unix_timestamp)
