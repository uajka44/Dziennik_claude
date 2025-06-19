"""
Okno konfiguracji ticketów instrumentów - mapowanie różnych nazw na główne instrumenty
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from config.database_config import DB_PATH


class InstrumentTicketsWindow:
    """Okno do zarządzania mapowaniem ticketów instrumentów"""
    
    def __init__(self, parent):
        self.parent = parent
        self.config_file = os.path.join(os.path.dirname(DB_PATH), "instrument_tickets.json")
        
        # Domyślna konfiguracja instrumentów
        self.default_instruments = {
            "DAX": ["ger40.cash", "germany40", "dax40", "ger40"],
            "NASDAQ": ["us100.cash", "us100", "nq100", "nasdaq100", "nas100"],
            "DJ": ["us30.cash", "us30", "dow30", "dj30", "dow jones"],
            "GOLD": ["xauusd", "gold", "złoto", "au"],
            "BTC": ["btcusd", "bitcoin", "btc", "crypto"]
        }
        
        # Domyślne aktywne instrumenty
        self.default_active_instruments = {
            "DAX": True,
            "NASDAQ": True, 
            "DJ": True,
            "GOLD": True,
            "BTC": False  # BTC domyślnie wyłączony
        }
        
        # Załaduj konfigurację
        self.instruments_config, self.active_instruments = self._load_config()
        
        # Tworzenie okna
        self.window = tk.Toplevel(parent)
        self.window.title("Tickety instrumentów")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        
        # Wyśrodkuj okno względem rodzica
        self._center_window()
        
        self._create_widgets()
        self._load_data()
    
    def _center_window(self):
        """Wyśrodkowuje okno względem okna rodzica"""
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Pobierz pozycję i rozmiar okna rodzica
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Oblicz pozycję dla wyśrodkowania
        window_width = 800
        window_height = 600
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def _create_widgets(self):
        """Tworzy wszystkie widgety okna"""
        
        # Główna ramka
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # === NAGŁÓWEK ===
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 10))
        
        title_label = ttk.Label(
            header_frame, 
            text="Mapowanie ticketów instrumentów",
            font=("Arial", 14, "bold")
        )
        title_label.pack()
        
        description_label = ttk.Label(
            header_frame,
            text="Skonfiguruj różne nazwy ticketów dla głównych instrumentów.\n" +
                 "Zaznacz checkbox aby aktywować instrument w kalkulatorze TP.\n" +
                 "Oddzielaj nazwy przecinkami. Przykład: ger40.cash, germany40, dax40",
            justify="center"
        )
        description_label.pack(pady=(5, 0))
        
        # === LISTA INSTRUMENTÓW ===
        instruments_frame = ttk.LabelFrame(main_frame, text="Instrumenty i ich tickety")
        instruments_frame.pack(fill="both", expand=True, pady=10)
        
        # Ramka z przewijaniem
        canvas_frame = ttk.Frame(instruments_frame)
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Canvas i scrollbar
        self.canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Słownik do przechowywania widgetów
        self.instrument_widgets = {}
        
        # === PRZYCISKI ===
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=10)
        
        # Przycisk dodaj instrument
        add_button = ttk.Button(
            buttons_frame,
            text="Dodaj nowy instrument",
            command=self._add_new_instrument
        )
        add_button.pack(side="left", padx=(0, 10))
        
        # Przycisk resetuj
        reset_button = ttk.Button(
            buttons_frame,
            text="Przywróć domyślne",
            command=self._reset_to_defaults
        )
        reset_button.pack(side="left", padx=(0, 10))
        
        # Przyciski zapisz/anuluj
        save_button = ttk.Button(
            buttons_frame,
            text="Zapisz",
            command=self._save_config
        )
        save_button.pack(side="right", padx=(10, 0))
        
        cancel_button = ttk.Button(
            buttons_frame,
            text="Anuluj",
            command=self.window.destroy
        )
        cancel_button.pack(side="right")
    
    def _create_instrument_row(self, instrument_name, tickets_list):
        """Tworzy wiersz dla jednego instrumentu"""
        
        # Główna ramka dla instrumentu
        instrument_frame = ttk.Frame(self.scrollable_frame)
        instrument_frame.pack(fill="x", pady=5, padx=5)
        
        # Checkbox aktywacji instrumentu
        is_active = self.active_instruments.get(instrument_name, True)
        checkbox_var = tk.BooleanVar(value=is_active)
        checkbox = ttk.Checkbutton(
            instrument_frame,
            variable=checkbox_var
        )
        checkbox.pack(side="left", padx=(0, 5))
        
        # Etykieta z nazwą instrumentu
        name_label = ttk.Label(
            instrument_frame,
            text=f"{instrument_name}:",
            font=("Arial", 10, "bold"),
            width=12
        )
        name_label.pack(side="left", padx=(0, 10))
        
        # Pole tekstowe z ticketami
        tickets_text = ", ".join(tickets_list)
        tickets_entry = tk.Text(
            instrument_frame,
            height=2,
            wrap=tk.WORD,
            font=("Arial", 9)
        )
        tickets_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        tickets_entry.insert("1.0", tickets_text)
        
        # Przycisk usuń (tylko dla niestandardowych instrumentów)
        if instrument_name not in self.default_instruments:
            remove_button = ttk.Button(
                instrument_frame,
                text="Usuń",
                width=8,
                command=lambda: self._remove_instrument(instrument_name)
            )
            remove_button.pack(side="right")
        
        # Zachowaj referencje do widgetów
        self.instrument_widgets[instrument_name] = {
            'frame': instrument_frame,
            'checkbox_var': checkbox_var,
            'entry': tickets_entry
        }
    
    def _load_data(self):
        """Ładuje dane instrumentów do interfejsu"""
        # Wyczyść istniejące widgety
        for widgets in self.instrument_widgets.values():
            widgets['frame'].destroy()
        self.instrument_widgets.clear()
        
        # Utwórz wiersze dla wszystkich instrumentów
        for instrument_name, tickets_list in sorted(self.instruments_config.items()):
            self._create_instrument_row(instrument_name, tickets_list)
    
    def _add_new_instrument(self):
        """Dodaje nowy instrument"""
        dialog = AddInstrumentDialog(self.window)
        if dialog.result:
            instrument_name = dialog.result['name']
            tickets = dialog.result['tickets']
            
            # Sprawdź czy instrument już istnieje
            if instrument_name in self.instruments_config:
                messagebox.showerror(
                    "Błąd",
                    f"Instrument '{instrument_name}' już istnieje!"
                )
                return
            
            # Dodaj nowy instrument
            self.instruments_config[instrument_name] = tickets
            self.active_instruments[instrument_name] = True  # Nowe instrumenty domyślnie aktywne
            self._load_data()
    
    def _remove_instrument(self, instrument_name):
        """Usuwa instrument (tylko niestandardowe)"""
        if instrument_name in self.default_instruments:
            messagebox.showerror(
                "Błąd",
                f"Nie można usunąć domyślnego instrumentu '{instrument_name}'!"
            )
            return
        
        result = messagebox.askyesno(
            "Potwierdzenie",
            f"Czy na pewno chcesz usunąć instrument '{instrument_name}'?"
        )
        
        if result:
            del self.instruments_config[instrument_name]
            if instrument_name in self.active_instruments:
                del self.active_instruments[instrument_name]
            self._load_data()
    
    def _reset_to_defaults(self):
        """Przywraca domyślną konfigurację"""
        result = messagebox.askyesno(
            "Potwierdzenie",
            "Czy na pewno chcesz przywrócić domyślną konfigurację?\n" +
            "Wszystkie niestandardowe zmiany zostaną utracone!"
        )
        
        if result:
            self.instruments_config = self.default_instruments.copy()
            self.active_instruments = self.default_active_instruments.copy()
            self._load_data()
    
    def _save_config(self):
        """Zapisuje konfigurację"""
        try:
            # Pobierz dane z widgetów
            new_config = {}
            new_active = {}
            
            for instrument_name, widgets in self.instrument_widgets.items():
                tickets_text = widgets['entry'].get("1.0", "end-1c")
                is_active = widgets['checkbox_var'].get()
                
                # Parsuj tickety (usuń puste, wytrymuj)
                tickets = [
                    ticket.strip() 
                    for ticket in tickets_text.split(",")
                    if ticket.strip()
                ]
                
                if tickets:  # Tylko jeśli są jakieś tickety
                    new_config[instrument_name] = tickets
                    new_active[instrument_name] = is_active
            
            # Zapisz do plików
            self.instruments_config = new_config
            self.active_instruments = new_active
            self._write_config()
            
            messagebox.showinfo(
                "Sukces",
                "Konfiguracja została zapisana pomyślnie!"
            )
            
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror(
                "Błąd",
                f"Nie można zapisać konfiguracji:\n{e}"
            )
    
    def _load_config(self):
        """Ładuje konfigurację z pliku"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Pobierz konfigurację instrumentów
                config = data.get('instruments', {})
                active = data.get('active_instruments', {})
                
                # Sprawdź czy wszystkie domyślne instrumenty istnieją
                for instrument, tickets in self.default_instruments.items():
                    if instrument not in config:
                        config[instrument] = tickets
                    if instrument not in active:
                        active[instrument] = self.default_active_instruments.get(instrument, True)
                
                return config, active
            else:
                return self.default_instruments.copy(), self.default_active_instruments.copy()
                
        except Exception as e:
            print(f"Błąd podczas ładowania konfiguracji: {e}")
            return self.default_instruments.copy(), self.default_active_instruments.copy()
    
    def _write_config(self):
        """Zapisuje konfigurację do pliku"""
        try:
            # Utwórz katalog jeśli nie istnieje
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Przygotuj dane do zapisu
            data = {
                'instruments': self.instruments_config,
                'active_instruments': self.active_instruments
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise Exception(f"Nie można zapisać pliku konfiguracji: {e}")


class AddInstrumentDialog:
    """Dialog do dodawania nowego instrumentu"""
    
    def __init__(self, parent):
        self.result = None
        
        # Tworzenie okna
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Dodaj nowy instrument")
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Wyśrodkuj względem rodzica
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        x = parent_x + (parent_width - 400) // 2
        y = parent_y + (parent_height - 200) // 2
        self.dialog.geometry(f"400x200+{x}+{y}")
        
        self._create_widgets()
        
        # Czekaj na zamknięcie
        self.dialog.wait_window()
    
    def _create_widgets(self):
        """Tworzy widgety dialogu"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Nazwa instrumentu
        ttk.Label(main_frame, text="Nazwa instrumentu:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.name_entry = ttk.Entry(main_frame, width=30)
        self.name_entry.grid(row=0, column=1, sticky="ew", pady=(0, 5))
        
        # Tickety
        ttk.Label(main_frame, text="Tickety (oddzielone przecinkami):").grid(row=1, column=0, sticky="nw", pady=(0, 5))
        self.tickets_text = tk.Text(main_frame, height=4, width=30)
        self.tickets_text.grid(row=1, column=1, sticky="ew", pady=(0, 10))
        
        # Przyciski
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(buttons_frame, text="OK", command=self._ok_clicked).pack(side="left", padx=(0, 10))
        ttk.Button(buttons_frame, text="Anuluj", command=self._cancel_clicked).pack(side="left")
        
        # Konfiguracja grid
        main_frame.columnconfigure(1, weight=1)
        
        # Focus na pierwszym polu
        self.name_entry.focus()
    
    def _ok_clicked(self):
        """Obsługa przycisku OK"""
        name = self.name_entry.get().strip()
        tickets_text = self.tickets_text.get("1.0", "end-1c")
        
        if not name:
            messagebox.showerror("Błąd", "Podaj nazwę instrumentu!")
            return
        
        tickets = [
            ticket.strip() 
            for ticket in tickets_text.split(",")
            if ticket.strip()
        ]
        
        if not tickets:
            messagebox.showerror("Błąd", "Podaj przynajmniej jeden ticket!")
            return
        
        self.result = {
            'name': name.upper(),  # Nazwy instrumentów wielką literą
            'tickets': tickets
        }
        
        self.dialog.destroy()
    
    def _cancel_clicked(self):
        """Obsługa przycisku Anuluj"""
        self.dialog.destroy()
