"""
Przeglądarka danych transakcji (zrefaktoryzowana wersja oryginalnego DatabaseViewer)
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
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


class CheckboxDropdown:
    """Rozwijana lista z checkboxami"""
    
    def __init__(self, parent, callback=None):
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
        
        self.display_var = tk.StringVar(value="Symbole")
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
        
        self._create_widgets()
        self._setup_layout()
    
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
        
        # Przyciski diagnostyczne
        ttk.Button(
            self.filter_frame, 
            text="Diagnostyka symbolów", 
            command=self._show_symbol_diagnostics
        ).grid(row=1, column=0, padx=5, pady=5)
        
        ttk.Button(
            self.filter_frame, 
            text="Quick diagnostyka (konsola)", 
            command=self._quick_diagnostics
        ).grid(row=1, column=1, padx=5, pady=5)
        
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

        # === SEKCJA PODSUMOWANIA ===
        ttk.Separator(self.date_frame, orient="horizontal").grid(row=3, column=0, columnspan=3, sticky="ew", pady=5)

        self.summary_frame = ttk.Frame(self.date_frame)
        self.summary_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        ttk.Label(self.summary_frame, text="Suma profitu:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.total_profit_label = ttk.Label(self.summary_frame, text="0.00")
        self.total_profit_label.grid(row=0, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(self.summary_frame, text="Liczba transakcji:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.transactions_count_label = ttk.Label(self.summary_frame, text="0")
        self.transactions_count_label.grid(row=1, column=1, padx=5, pady=2, sticky="w")

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
    
    def load_data(self):
        """Ładuje dane z bazy danych dla podanego zakresu dat i wybranych instrumentów"""
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
                return
            
            # Sprawdź czy wszystkie są wybrane
            all_symbols_count = len(self.instruments_dropdown.items)
            all_selected = len(selected_symbols) == all_symbols_count
            
            # Dynamiczne generowanie zapytania SQL
            columns_str = ", ".join(COLUMNS)
            
            if all_selected:
                # Wszystkie instrumenty
                query = self.position_queries.get_positions_by_date_range(columns_str)
                rows = execute_query(query, (start_unix, end_unix))
            else:
                # Wybrane instrumenty - uwzględnij oba formaty (z i bez \x00)
                expanded_symbols = []
                for clean_symbol in selected_symbols:
                    expanded_symbols.append(clean_symbol)  # Oryginalny format
                    expanded_symbols.append(clean_symbol + '\x00')  # Format z null character
                
                placeholders = ", ".join(["?" for _ in expanded_symbols])
                query = f"""
                SELECT {columns_str}
                FROM positions 
                WHERE open_time BETWEEN ? AND ? AND symbol IN ({placeholders})
                ORDER BY open_time
                """
                params = [start_unix, end_unix] + expanded_symbols
                rows = execute_query(query, params)
            
            print(f"Pobrano {len(rows)} transakcji dla wybranych filtrów")
            print(f"Wybrane symbole: {selected_symbols if not all_selected else 'wszystkie'}")
            if not all_selected:
                print(f"Rozszerzone symbole (z \\x00): {expanded_symbols}")

            # Przygotowanie zmiennych do obliczenia sumy profitu
            total_profit = 0.0
            transaction_count = len(rows)

            # Wypełnianie tabeli danymi
            for row in rows:
                display_values = []
                for i, col in enumerate(COLUMNS):
                    value = row[i]

                    if col == "open_time":
                        display_values.append(format_time_for_display(value))
                    elif col == "profit_points":
                        adjusted_value = value / 100 if value is not None else None
                        if adjusted_value is not None:
                            total_profit += adjusted_value
                        display_values.append(format_profit_points(value))
                    elif col in [field.name for field in CHECKBOX_FIELDS]:
                        display_values.append(format_checkbox_value(value))
                    else:
                        display_values.append(value or "")

                self.tree.insert("", "end", values=tuple(display_values))

            # Aktualizacja etykiet z podsumowaniem
            self.total_profit_label.config(text=f"{total_profit:.2f}")
            self.transactions_count_label.config(text=f"{transaction_count}")

            if not rows:
                messagebox.showinfo("Informacja", "Brak danych dla podanych filtrów.")
                self.total_profit_label.config(text="0.00")
                self.transactions_count_label.config(text="0")

        except Exception as e:
            print(f"Błąd bazy danych: {e}")
            messagebox.showerror("Błąd bazy danych", f"Wystąpił błąd podczas ładowania danych: {e}")
    
    def edit_item(self, event):
        """Obsługuje edycję elementu po podwójnym kliknięciu"""
        selected_items = self.tree.selection()
        if not selected_items:
            return

        selected_item = selected_items[0]
        values = self.tree.item(selected_item, "values")

        if not values:
            return

        # Tworzenie okna dialogowego do edycji
        edit_dialog = tk.Toplevel(self.parent)
        edit_dialog.title("Edytuj dane")
        edit_dialog.geometry("500x800")

        # Ramka do edycji
        edit_frame = ttk.Frame(edit_dialog, padding=10)
        edit_frame.pack(fill="both", expand=True)

        # Wartości do przechowywania wyników edycji
        entry_widgets = {}
        checkbox_vars = {}

        # Wyświetlenie daty (nie edytowalna)
        ttk.Label(edit_frame, text="Data i czas:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(edit_frame, text=values[0]).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Tworzenie kontrolek do edycji dla pól tekstowych
        row_index = 1
        for i, field in enumerate(TEXT_FIELDS):
            ttk.Label(edit_frame, text=f"{field.display_name}:").grid(
                row=row_index, column=0, padx=5, pady=5, sticky="w"
            )

            value = values[i + 1] if i + 1 < len(values) else ""

            if field.field_type == "multiline":
                entry = tk.Text(edit_frame, width=30, height=5)
                entry.grid(row=row_index, column=1, padx=5, pady=5, sticky="ew")
                entry.insert("1.0", value)
                if not field.editable:
                    entry.config(state="disabled")
            elif field.name == "setup":
                entry = SetupEntry(edit_frame, SETUP_SHORTCUTS, width=30)
                entry.grid(row=row_index, column=1, padx=5, pady=5, sticky="ew")
                entry.insert(0, value)
                if not field.editable:
                    entry.config(state="readonly")
            else:
                entry = ttk.Entry(edit_frame, width=30)
                entry.grid(row=row_index, column=1, padx=5, pady=5, sticky="ew")
                entry.insert(0, value)
                if not field.editable:
                    entry.config(state="readonly")

            entry_widgets[field.name] = entry
            row_index += 1

        # Separator
        ttk.Separator(edit_frame, orient="horizontal").grid(
            row=row_index, column=0, columnspan=2, sticky="ew", pady=10
        )
        row_index += 1

        # Checkboxy
        checkbox_label_frame = ttk.LabelFrame(edit_frame, text="Opcje")
        checkbox_label_frame.grid(row=row_index, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        checkbox_frame = ttk.Frame(checkbox_label_frame)
        checkbox_frame.pack(fill="both", expand=True, padx=5, pady=5)

        checkboxes_per_row = 3
        for i, field in enumerate(CHECKBOX_FIELDS):
            col = i % checkboxes_per_row
            row = i // checkboxes_per_row

            field_index = len(TEXT_FIELDS) + i + 1
            checkbox_value = (values[field_index] == "✓") if field_index < len(values) else False

            var = tk.IntVar(value=1 if checkbox_value else 0)
            checkbox = ttk.Checkbutton(checkbox_frame, text=field.display_name, variable=var)
            checkbox.grid(row=row, column=col, padx=10, pady=5, sticky="w")

            checkbox_vars[field.name] = var

        # Funkcja zapisująca zmiany
        def save_changes():
            try:
                new_values = {}
                
                # Pobieranie wartości z pól tekstowych
                for field_name, widget in entry_widgets.items():
                    field = ALL_FIELDS[field_name]
                    if field.field_type == "multiline":
                        new_values[field_name] = widget.get("1.0", "end-1c")
                    else:
                        new_values[field_name] = widget.get()

                # Pobieranie wartości z checkboxów
                for field_name, var in checkbox_vars.items():
                    new_values[field_name] = var.get()

                # Pobierz ticket jako klucz do aktualizacji
                ticket = values[COLUMNS.index("ticket")]

                # Przygotowanie zapytania SQL
                updateable_fields = []
                update_values = []

                for field_name, value in new_values.items():
                    field = ALL_FIELDS.get(field_name)
                    if field and field.editable:
                        updateable_fields.append(f"{field_name} = ?")
                        update_values.append(value)

                if updateable_fields:
                    update_query = f"""
                    UPDATE positions 
                    SET {", ".join(updateable_fields)}
                    WHERE ticket = ?
                    """
                    update_values.append(ticket)

                    execute_update(update_query, tuple(update_values))

                    # Aktualizacja widoku tabeli
                    updated_values = list(values)
                    
                    for i, field in enumerate(TEXT_FIELDS):
                        if field.name in new_values:
                            updated_values[i + 1] = new_values[field.name]

                    for i, field in enumerate(CHECKBOX_FIELDS):
                        if field.name in new_values:
                            field_index = len(TEXT_FIELDS) + i + 1
                            updated_values[field_index] = "✓" if new_values[field.name] == 1 else ""

                    self.tree.item(selected_item, values=tuple(updated_values))

                edit_dialog.destroy()

            except Exception as e:
                messagebox.showerror("Błąd bazy danych", f"Nie można zaktualizować danych: {e}")

        # Przyciski zapisz/anuluj
        button_frame = ttk.Frame(edit_dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Zapisz", command=save_changes).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Anuluj", command=edit_dialog.destroy).grid(row=0, column=1, padx=5)
    
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
