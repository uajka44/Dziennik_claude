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
        
        # Filtr Usuń 007 - Magic Number
        ttk.Label(self.filter_frame, text="Usuń 007:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        # Checkbox do usuwania trejdów z magic_number = 7
        self.remove_007_filter_var = tk.BooleanVar(value=False)  # Domyślnie odznaczony
        self.remove_007_checkbox = ttk.Checkbutton(
            self.filter_frame,
            text="Usuń 007",
            variable=self.remove_007_filter_var,
            command=self.load_data
        )
        self.remove_007_checkbox.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Przyciski diagnostyczne i narzędzia zostały przeniesione do menu Narzędzia -> Ustawienia
        
        # === SEKCJA WYBORU DAT ===
        self.date_frame = ttk.LabelFrame(self.parent, text="Zakres dat")
        self.date_frame.pack(fill="x", padx=10, pady=10)
        
        # Pola do wyboru dat z kalendarza
        ttk.Label(self.date_frame, text="Data początkowa:").grid(row=0, column=0, padx=5, pady=5)
        self.start_date_entry = DateEntry(
            self.date_frame, width=12, background='darkblue',
            foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
            year=date.today().year, month=date.today().month, day=date.today().day
        )
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.date_frame, text="Data końcowa:").grid(row=1, column=0, padx=5, pady=5)
        self.end_date_entry = DateEntry(
            self.date_frame, width=12, background='darkblue',
            foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
            year=date.today().year, month=date.today().month, day=date.today().day
        )
        self.end_date_entry.grid(row=1, column=1, padx=5, pady=5)

        # Przyciski
        self.search_button = ttk.Button(self.date_frame, text="Wyszukaj", command=self.load_data)
        self.search_button.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        
        self.today_button = ttk.Button(self.date_frame, text="Dzisiaj", command=self._set_today)
        self.today_button.grid(row=2, column=2, padx=5, pady=5)
        
        # Przyciski nawigacji po dniach
        self.prev_day_button = ttk.Button(self.date_frame, text="Prev", command=self._prev_day)
        self.prev_day_button.grid(row=2, column=3, padx=5, pady=5)
        
        self.next_day_button = ttk.Button(self.date_frame, text="Next", command=self._next_day)
        self.next_day_button.grid(row=2, column=4, padx=5, pady=5)

        # === SEKCJA PODSUMOWANIA ===
        ttk.Separator(self.date_frame, orient="horizontal").grid(row=3, column=0, columnspan=5, sticky="ew", pady=5)

        self.summary_frame = ttk.Frame(self.date_frame)
        self.summary_frame.grid(row=4, column=0, columnspan=5, sticky="ew", padx=5, pady=5)

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
            
            # Warunek dla filtra Usuń 007
            remove_007_filter_active = self.remove_007_filter_var.get()
            if remove_007_filter_active:
                # Jeśli filtr "Usuń 007" jest zaznaczony, ukryj trejdy z magic_number = 7
                where_conditions.append("(magic_number IS NULL OR magic_number != ?)")
                base_params.append(7)
                print("Filtr 'Usuń 007' aktywny - ukrywam trejdy z magic_number = 7")
            else:
                # Jeśli filtr "Usuń 007" jest odznaczony, pokazuj wszystkie trejdy
                print("Filtr 'Usuń 007' nieaktywny - pokazuję wszystkie trejdy")
            
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
