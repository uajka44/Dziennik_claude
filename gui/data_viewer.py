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
from database.connection import execute_query, execute_update
from database.queries import PositionQueries
from gui.widgets.custom_entries import SetupEntry
from utils.date_utils import date_range_to_unix, format_time_for_display
from utils.formatting import format_profit_points, format_checkbox_value


class DataViewer:
    """Przeglądarka danych transakcji"""
    
    def __init__(self, parent, db_path):
        self.parent = parent
        self.db_path = db_path
        self.position_queries = PositionQueries()
        
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """Tworzy wszystkie widgety"""
        
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
    
    def _set_today(self):
        """Ustawia daty na dzisiejszy dzień"""
        today = date.today()
        self.start_date_entry.set_date(today)
        self.end_date_entry.set_date(today)
    
    def load_data(self):
        """Ładuje dane z bazy danych dla podanego zakresu dat"""
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
            # Dynamiczne generowanie zapytania SQL na podstawie zdefiniowanych kolumn
            columns_str = ", ".join(COLUMNS)
            query = self.position_queries.get_positions_by_date_range(columns_str)
            rows = execute_query(query, (start_unix, end_unix))

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
                messagebox.showinfo("Informacja", "Brak danych dla podanego zakresu dat.")
                self.total_profit_label.config(text="0.00")
                self.transactions_count_label.config(text="0")

        except Exception as e:
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
