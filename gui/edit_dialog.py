"""
Dialog edycji transakcji - wydzielony z data_viewer.py
"""
import tkinter as tk
from tkinter import ttk, messagebox

from config.field_definitions import (
    TEXT_FIELDS, CHECKBOX_FIELDS, ALL_FIELDS, COLUMNS
)
from database.connection import execute_update
from gui.widgets.custom_entries import SetupEntry


class EditDialog:
    """Dialog do edycji pojedynczej transakcji"""
    
    def __init__(self, parent, ticket, values, on_save_callback=None, on_close_callback=None):
        """
        Args:
            parent: Okno rodzic
            ticket: Numer ticket edytowanej pozycji  
            values: Tuple z wartościami z treeview
            on_save_callback: Funkcja wywoływana po zapisaniu zmian
            on_close_callback: Funkcja wywoływana po zamknięciu okna
        """
        self.parent = parent
        self.ticket = ticket
        self.values = values
        self.on_save_callback = on_save_callback
        self.on_close_callback = on_close_callback
        
        # Dodatkowe callbacks dla nawigacji
        self.on_next_callback = None
        self.on_prev_callback = None
        
        # Tworzenie okna dialogowego
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Edytuj transakcję - Ticket: {ticket}")
        self.dialog.geometry("700x900")  # Większe okno
        self.dialog.minsize(650, 800)  # Minimalne rozmiary
        
        # Manager konfiguracji okien - PRZED zastosowaniem konfiguracji
        from gui.window_config import WindowConfigManager
        self.window_config = WindowConfigManager()
        
        # Zapobiegnij zamknięciu okna bez powiadomienia managera
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_window_delete)
        
        # Zastosuj konfigurację okna (pozycja i rozmiar)
        self.window_config.apply_window_config(self.dialog, "edit_dialog")
        
        # Widgets do przechowywania
        self.entry_widgets = {}
        self.checkbox_vars = {}
        
        self._create_widgets()
        
        # Focus na okno
        self.dialog.transient(parent)
        self.dialog.grab_set()
    
    def _create_widgets(self):
        """Tworzy wszystkie widgety dialogu"""
        
        # Główna ramka z paddingiem
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Nagłówek z informacją o ticket
        header_frame = ttk.LabelFrame(main_frame, text="Informacje o pozycji")
        header_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(header_frame, text=f"Ticket: {self.ticket}", 
                 font=("Arial", 10, "bold")).pack(padx=10, pady=5)
        ttk.Label(header_frame, text=f"Data i czas: {self.values[0]}").pack(padx=10, pady=5)
        
        # Scrollable frame dla formularza
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Ramka edycji wewnątrz scrollable_frame
        edit_frame = ttk.LabelFrame(scrollable_frame, text="Dane do edycji", padding=10)
        edit_frame.pack(fill="both", expand=True)
        
        # Tworzenie kontrolek do edycji dla pól tekstowych
        row_index = 0
        for i, field in enumerate(TEXT_FIELDS):
            ttk.Label(edit_frame, text=f"{field.display_name}:").grid(
                row=row_index, column=0, padx=5, pady=5, sticky="w"
            )

            value = self.values[i + 1] if i + 1 < len(self.values) else ""

            if field.field_type == "multiline":
                entry = tk.Text(edit_frame, width=35, height=5)  # Szersze pola
                entry.grid(row=row_index, column=1, padx=5, pady=5, sticky="ew")
                entry.insert("1.0", value)
                if not field.editable:
                    entry.config(state="disabled")
            elif field.name == "setup":
                entry = SetupEntry(edit_frame, width=35)  # Szersze pola - używa nowego systemu
                entry.grid(row=row_index, column=1, padx=5, pady=5, sticky="ew")
                entry.insert(0, value)
                if not field.editable:
                    entry.config(state="readonly")
            else:
                entry = ttk.Entry(edit_frame, width=35)  # Szersze pola
                entry.grid(row=row_index, column=1, padx=5, pady=5, sticky="ew")
                entry.insert(0, value)
                if not field.editable:
                    entry.config(state="readonly")

            self.entry_widgets[field.name] = entry
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
            checkbox_value = (self.values[field_index] == "✓") if field_index < len(self.values) else False

            var = tk.IntVar(value=1 if checkbox_value else 0)
            checkbox = ttk.Checkbutton(checkbox_frame, text=field.display_name, variable=var)
            checkbox.grid(row=row, column=col, padx=10, pady=5, sticky="w")

            self.checkbox_vars[field.name] = var

        # Konfiguracja grid dla edit_frame
        edit_frame.columnconfigure(1, weight=1)
        
        # Pack canvas i scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Przyciski na dole
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Lewa strona - nawigacja
        nav_frame = ttk.Frame(button_frame)
        nav_frame.pack(side="left", fill="x", expand=True)
        
        self.prev_button = ttk.Button(nav_frame, text="◀ Poprzednia", command=self._go_prev)
        self.prev_button.pack(side="left", padx=5)
        
        self.next_button = ttk.Button(nav_frame, text="Następna ▶", command=self._go_next)
        self.next_button.pack(side="left", padx=5)
        
        # Prawa strona - akcje
        action_frame = ttk.Frame(button_frame)
        action_frame.pack(side="right")
        
        ttk.Button(action_frame, text="Zapisz", command=self._save_changes).pack(side="left", padx=5)
        ttk.Button(action_frame, text="Anuluj", command=self._cancel).pack(side="left", padx=5)
        
        # Informacja o komunikacji z MQL5
        info_frame = ttk.LabelFrame(main_frame, text="Status")
        info_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Label(info_frame, 
                 text=f"🔗 MQL5 wie że edytujesz ticket: {self.ticket}",
                 foreground="green").pack(padx=10, pady=5)
    
    def _play_success_sound(self):
        """Odgrywa dźwięk sukcesu po zapisaniu"""
        try:
            import winsound
            # Odegraj systemowy dźwięk sukcesu
            winsound.MessageBeep(winsound.MB_OK)
        except ImportError:
            # Fallback dla systemów nie-Windows
            try:
                import os
                # Dla Linux/Mac
                os.system('printf "\a"')  # Terminal bell
            except:
                print("[EditDialog] 🔔 Zapisano (brak obsługi dźwięku)")
    
    def _save_changes(self):
        """Zapisuje zmiany do bazy danych"""
        try:
            new_values = {}
            
            # Pobieranie wartości z pól tekstowych
            for field_name, widget in self.entry_widgets.items():
                field = ALL_FIELDS[field_name]
                if field.field_type == "multiline":
                    new_values[field_name] = widget.get("1.0", "end-1c")
                else:
                    new_values[field_name] = widget.get()

            # Pobieranie wartości z checkboxów
            for field_name, var in self.checkbox_vars.items():
                new_values[field_name] = var.get()

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
                update_values.append(self.ticket)

                execute_update(update_query, tuple(update_values))
                
                print(f"[EditDialog] Zapisano zmiany dla ticket: {self.ticket}")

                # Wywołaj callback jeśli został podany
                if self.on_save_callback:
                    # Przygotuj zaktualizowane wartości dla callback
                    updated_values = list(self.values)
                    
                    for i, field in enumerate(TEXT_FIELDS):
                        if field.name in new_values:
                            updated_values[i + 1] = new_values[field.name]

                    for i, field in enumerate(CHECKBOX_FIELDS):
                        if field.name in new_values:
                            field_index = len(TEXT_FIELDS) + i + 1
                            updated_values[field_index] = "✓" if new_values[field.name] == 1 else ""
                    
                    self.on_save_callback(updated_values)

                # Odegraj dźwięk sukcesu zamiast okienka
                self._play_success_sound()
                print(f"[EditDialog] ✅ Zapisano zmiany dla ticket: {self.ticket}")
                self._close_dialog()

        except Exception as e:
            print(f"[EditDialog] Błąd zapisu: {e}")
            messagebox.showerror("Błąd bazy danych", f"Nie można zaktualizować danych: {e}")
    
    def _cancel(self):
        """Anuluje edycję i zamyka dialog"""
        self._close_dialog()
    
    def _go_next(self):
        """Przechodzi do następnej pozycji"""
        if self.on_next_callback:
            # Najpierw zapisz zmiany
            if self._save_changes_silent():
                self.on_next_callback()
    
    def _go_prev(self):
        """Przechodzi do poprzedniej pozycji"""
        if self.on_prev_callback:
            # Najpierw zapisz zmiany
            if self._save_changes_silent():
                self.on_prev_callback()
    
    def set_navigation_callbacks(self, next_callback, prev_callback):
        """Ustawia callback dla nawigacji"""
        self.on_next_callback = next_callback
        self.on_prev_callback = prev_callback
        
        # Aktywuj/dezaktywuj przyciski na podstawie dostępności callbacków
        self.next_button.config(state="normal" if next_callback else "disabled")
        self.prev_button.config(state="normal" if prev_callback else "disabled")
    
    def _save_changes_silent(self):
        """Zapisuje zmiany bez pokazywania komunikatu sukcesu"""
        try:
            new_values = {}
            
            # Pobieranie wartości z pól tekstowych
            for field_name, widget in self.entry_widgets.items():
                field = ALL_FIELDS[field_name]
                if field.field_type == "multiline":
                    new_values[field_name] = widget.get("1.0", "end-1c")
                else:
                    new_values[field_name] = widget.get()

            # Pobieranie wartości z checkboxów
            for field_name, var in self.checkbox_vars.items():
                new_values[field_name] = var.get()

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
                update_values.append(self.ticket)

                execute_update(update_query, tuple(update_values))
                
                print(f"[EditDialog] Cicho zapisano zmiany dla ticket: {self.ticket}")

                # Wywołaj callback jeśli został podany
                if self.on_save_callback:
                    # Przygotuj zaktualizowane wartości dla callback
                    updated_values = list(self.values)
                    
                    for i, field in enumerate(TEXT_FIELDS):
                        if field.name in new_values:
                            updated_values[i + 1] = new_values[field.name]

                    for i, field in enumerate(CHECKBOX_FIELDS):
                        if field.name in new_values:
                            field_index = len(TEXT_FIELDS) + i + 1
                            updated_values[field_index] = "✓" if new_values[field.name] == 1 else ""
                    
                    self.on_save_callback(updated_values)

                return True
            return True

        except Exception as e:
            print(f"[EditDialog] Błąd zapisu: {e}")
            messagebox.showerror("Błąd bazy danych", f"Nie można zaktualizować danych: {e}")
            return False
    
    def _on_window_delete(self):
        """Obsługuje zamknięcie okna przez X"""
        self._close_dialog()
    
    def _close_dialog(self):
        """Zamyka dialog i powiadamia manager"""
        # Zapisz konfigurację okna przed zamknięciem
        try:
            self.window_config.save_window_config(self.dialog, "edit_dialog")
        except Exception as e:
            print(f"[EditDialog] Błąd zapisu konfiguracji okna: {e}")
        
        if self.on_close_callback:
            self.on_close_callback()
        
        try:
            self.dialog.destroy()
        except:
            pass  # Okno mogło już być zniszczone
    
    def destroy(self):
        """Publiczna metoda do zamykania dialogu"""
        self._close_dialog()
    
    def update_content(self, new_ticket, new_values):
        """Aktualizuje zawartość okna dla nowej pozycji (używane przy nawigacji)"""
        self.ticket = new_ticket
        self.values = new_values
        
        # Aktualizuj tytuł okna
        self.dialog.title(f"Edytuj transakcję - Ticket: {new_ticket}")
        
        # Aktualizuj nagłówek
        # ... (tutaj można dodać aktualizację zawartości pól)
        
        # Aktualizuj komunikację z MQL5
        print(f"[EditDialog] Zaktualizowano zawartość dla ticket: {new_ticket}")
