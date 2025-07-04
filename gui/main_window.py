"""
Główne okno aplikacji z menu i zakładkami
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from gui.data_viewer import DataViewer
from gui.tp_calculator import TPCalculatorWindow
from database.connection import get_current_database_info, execute_query
from config.database_config import AVAILABLE_INSTRUMENTS
from database.migration.sl_opening_migrator import get_sl_migrator
from config.setup_config import get_setup_config


class MainWindow:
    """Główne okno aplikacji"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Dziennik Transakcji - AI 3.0")
        
        # Manager konfiguracji okien
        from gui.window_config import WindowConfigManager
        self.window_config = WindowConfigManager()
        
        # Zastosuj konfigurację głównego okna
        self.window_config.apply_window_config(self.root, "main_window")
        
        # Zapisz konfigurację przy zamykaniu
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Tworzenie menu
        self._create_menu()
        
        # Tworzenie głównych zakładek
        self._create_notebook()
        
        # Sprawdzenie połączenia z bazą danych
        self._check_database_connection()
    
    def _create_menu(self):
        """Tworzy menu główne"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menu Plik
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Plik", menu=file_menu)
        file_menu.add_command(label="Eksportuj dane...", command=self._export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Zamknij", command=self.root.quit)
        
        # Menu Narzędzia
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Narzędzia", menu=tools_menu)
        tools_menu.add_command(label="Kalkulator TP", command=self._open_tp_calculator)
        tools_menu.add_command(label="Tickety instrumentów", command=self._open_instrument_tickets)
        tools_menu.add_separator()
        tools_menu.add_command(label="Ustawienia", command=self._open_settings)
        
        # Menu Pomoc
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Pomoc", menu=help_menu)
        help_menu.add_command(label="O programie", command=self._show_about)
    
    def _create_notebook(self):
        """Tworzy notebook z zakładkami"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Zakładka: Przeglądarka transakcji
        self.data_viewer_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.data_viewer_frame, text="Przeglądarka transakcji")
        
        # Inicjalizacja przeglądarki danych
        self.data_viewer = DataViewer(self.data_viewer_frame)
        
        # Można dodać więcej zakładek tutaj w przyszłości
        # self.analytics_frame = ttk.Frame(self.notebook)
        # self.notebook.add(self.analytics_frame, text="Analityka")
    
    def _check_database_connection(self):
        """Sprawdza połączenie z bazą danych"""
        try:
            from database.connection import get_db_connection
            db = get_db_connection()
            # Test połączenia
            db.execute_query("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            
            # Dodaj status bar z informacją o aktualnej bazie
            db_info = get_current_database_info()
            self.status_bar = ttk.Label(
                self.root, 
                text=db_info,
                relief=tk.SUNKEN,
                anchor=tk.W
            )
            self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
            
        except Exception as e:
            messagebox.showerror(
                "Błąd bazy danych", 
                f"Nie można połączyć się z bazą danych:\n{e}"
            )
    
    def _open_tp_calculator(self):
        """Otwiera okno kalkulatora TP"""
        try:
            TPCalculatorWindow(self.root)
        except Exception as e:
            messagebox.showerror(
                "Błąd", 
                f"Nie można otworzyć kalkulatora TP:\n{e}"
            )
    
    def _open_instrument_tickets(self):
        """Otwiera okno mapowania ticketów instrumentów"""
        try:
            from gui.instrument_tickets import InstrumentTicketsWindow
            InstrumentTicketsWindow(self.root)
        except Exception as e:
            messagebox.showerror(
                "Błąd", 
                f"Nie można otworzyć okna ticketów instrumentów:\n{e}"
            )
    
    def _export_data(self):
        """Eksportuje dane z aktualnej zakładki"""
        current_tab = self.notebook.select()
        tab_text = self.notebook.tab(current_tab, "text")
        
        if tab_text == "Przeglądarka transakcji":
            # Deleguj eksport do data_viewer
            self.data_viewer.export_current_data()
        else:
            messagebox.showinfo("Informacja", "Eksport niedostępny dla tej zakładki")
    
    def _open_settings(self):
        """Otwiera okno ustawień"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Ustawienia")
        settings_window.geometry("500x400")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Główny notebook dla sekcji ustawień
        settings_notebook = ttk.Notebook(settings_window)
        settings_notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # === ZAKIŁADKA: OKNA ===
        window_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(window_frame, text="Okna")
        
        # Sekcja konfiguracji okien
        window_config_frame = ttk.LabelFrame(window_frame, text="Konfiguracja okien")
        window_config_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(window_config_frame, 
                 text="Resetuj pozycje i rozmiary okien:").pack(pady=5)
        
        button_frame = ttk.Frame(window_config_frame)
        button_frame.pack(pady=5)
        
        ttk.Button(button_frame, 
                  text="Reset okna edycji", 
                  command=lambda: self._reset_window_config("edit_dialog")).pack(side="left", padx=5)
        
        ttk.Button(button_frame, 
                  text="Reset głównego okna", 
                  command=lambda: self._reset_window_config("main_window")).pack(side="left", padx=5)
        
        ttk.Button(button_frame, 
                  text="Reset wszystkich", 
                  command=lambda: self._reset_window_config(None)).pack(side="left", padx=5)
        
        # === ZAKIŁADKA: MONITOR ===
        monitor_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(monitor_frame, text="Monitor")
        
        # Dodaj ustawienia monitora
        self._create_monitor_settings(monitor_frame)
        
        # === ZAKIĄDKA: DIAGNOSTYKA ===
        diagnostics_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(diagnostics_frame, text="Diagnostyka")
        
        # Dodaj narzędzia diagnostyczne
        self._create_diagnostics_settings(diagnostics_frame)
        
        # === ZAKIĄDKA: SETUP ===
        setup_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(setup_frame, text="Setup")
        
        # Dodaj ustawienia setupów
        self._create_setup_settings(setup_frame)
        
        # Przycisk zamknij
        ttk.Button(settings_window, 
                  text="Zamknij", 
                  command=settings_window.destroy).pack(pady=10)
    
    def _create_monitor_settings(self, parent_frame):
        """Tworzy sekcję ustawień monitora"""
        try:
            from monitoring.order_monitor import get_order_monitor
            monitor = get_order_monitor()
            
            # Status monitora
            status_frame = ttk.LabelFrame(parent_frame, text="Status monitora")
            status_frame.pack(fill="x", padx=10, pady=10)
            
            status = monitor.get_status()
            status_text = "🟢 Włączony" if status['is_running'] else "🔴 Wyłączony"
            
            self.monitor_status_label = ttk.Label(status_frame, text=f"Status: {status_text}", 
                                                  font=("Arial", 10, "bold"))
            self.monitor_status_label.pack(pady=10)
            
            # Ustawienia monitora
            config_frame = ttk.LabelFrame(parent_frame, text="Konfiguracja")
            config_frame.pack(fill="x", padx=10, pady=10)
            
            # Interwał sprawdzania
            ttk.Label(config_frame, text="Interwał sprawdzania (sekundy):").pack(pady=5)
            
            interval_frame = ttk.Frame(config_frame)
            interval_frame.pack(pady=5)
            
            self.interval_var = tk.IntVar(value=status['check_interval'])
            interval_spinner = tk.Spinbox(interval_frame, from_=5, to=300, 
                                        textvariable=self.interval_var, width=10)
            interval_spinner.pack(side="left", padx=5)
            
            ttk.Button(interval_frame, text="Zastosuj", 
                      command=lambda: self._apply_monitor_interval(monitor)).pack(side="left", padx=5)
            
            # Przyciski kontrolne
            control_frame = ttk.LabelFrame(parent_frame, text="Kontrola")
            control_frame.pack(fill="x", padx=10, pady=10)
            
            button_control_frame = ttk.Frame(control_frame)
            button_control_frame.pack(pady=10)
            
            if status['is_running']:
                ttk.Button(button_control_frame, text="Zatrzymaj monitor", 
                          command=lambda: self._stop_monitor(monitor)).pack(side="left", padx=5)
            else:
                ttk.Button(button_control_frame, text="Uruchom monitor", 
                          command=lambda: self._start_monitor(monitor)).pack(side="left", padx=5)
            
            ttk.Button(button_control_frame, text="Test dźwięku", 
                      command=self._test_monitor_sound).pack(side="left", padx=5)
            
            # Informacje
            info_frame = ttk.LabelFrame(parent_frame, text="Informacje")
            info_frame.pack(fill="x", padx=10, pady=10)
            
            ttk.Label(info_frame, 
                     text=f"Znanych ticketów: {status['known_tickets_count']}").pack(padx=10, pady=2)
            ttk.Label(info_frame, 
                     text=f"Aktywnych callbacków: {status['callbacks_count']}").pack(padx=10, pady=2)
            
        except Exception as e:
            ttk.Label(parent_frame, 
                     text=f"Błąd ładowania ustawień monitora: {e}", 
                     foreground="red").pack(padx=10, pady=10)
    
    def _apply_monitor_interval(self, monitor):
        """Stosuje nowy interwał monitora"""
        try:
            interval = self.interval_var.get()
            monitor.set_check_interval(interval)
            messagebox.showinfo("Sukces", f"Ustawiono interwał: {interval} sekund")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można ustawić interwału: {e}")
    
    def _start_monitor(self, monitor):
        """Uruchamia monitor"""
        try:
            interval = self.interval_var.get()
            monitor.set_check_interval(interval)
            monitor.start_monitoring()
            self.monitor_status_label.config(text="Status: 🟢 Włączony")
            messagebox.showinfo("Sukces", "Monitor uruchomiony")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można uruchomić monitora: {e}")
    
    def _stop_monitor(self, monitor):
        """Zatrzymuje monitor"""
        try:
            monitor.stop_monitoring()
            self.monitor_status_label.config(text="Status: 🔴 Wyłączony")
            messagebox.showinfo("Sukces", "Monitor zatrzymany")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zatrzymać monitora: {e}")
    
    def _test_monitor_sound(self):
        """Testuje dźwięk monitora"""
        try:
            import winsound
            winsound.Beep(800, 200)
            messagebox.showinfo("Test dźwięku", "Dźwięk został odegrany!")
        except ImportError:
            try:
                import os
                os.system('printf "\a"; sleep 0.1; printf "\a"')
                messagebox.showinfo("Test dźwięku", "Dźwięk został odegrany!")
            except:
                messagebox.showwarning("Test dźwięku", "Brak obsługi dźwięku na tym systemie")
    
    def _reset_window_config(self, window_name):
        """Resetuje konfigurację okien"""
        try:
            self.window_config.reset_window_config(window_name)
            
            if window_name:
                messagebox.showinfo("Sukces", f"Zresetowano konfigurację okna: {window_name}")
            else:
                messagebox.showinfo("Sukces", "Zresetowano konfigurację wszystkich okien")
                
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zresetować konfiguracji: {e}")
    
    def _create_diagnostics_settings(self, parent_frame):
        """Tworzy sekcję ustawień diagnostyki"""
        # Sekcja narzędzi diagnostycznych
        diagnostics_tools_frame = ttk.LabelFrame(parent_frame, text="Narzędzia diagnostyczne")
        diagnostics_tools_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(diagnostics_tools_frame, 
                 text="Narzędzia do analizy i diagnostyki bazy danych:").pack(pady=(10, 5))
        
        # Kontener dla przycisków z tooltipami
        buttons_frame = ttk.Frame(diagnostics_tools_frame)
        buttons_frame.pack(pady=10)
        
        # Przycisk Diagnostyka symbolów
        diag_symbols_frame = ttk.Frame(buttons_frame)
        diag_symbols_frame.pack(fill="x", pady=2)
        
        diag_symbols_btn = ttk.Button(
            diag_symbols_frame,
            text="Diagnostyka symbolów",
            command=self._show_symbol_diagnostics
        )
        diag_symbols_btn.pack(side="left", padx=5)
        
        # Ikonka pytajnika z tooltipem
        help_btn1 = ttk.Button(
            diag_symbols_frame,
            text="?",
            width=3,
            command=lambda: self._show_tooltip(
                "Analiza wszystkich symbolów w bazie danych z wykrywaniem problemów i niezgodności."
            )
        )
        help_btn1.pack(side="left", padx=2)
        
        # Przycisk Quick diagnostyka
        quick_diag_frame = ttk.Frame(buttons_frame)
        quick_diag_frame.pack(fill="x", pady=2)
        
        quick_diag_btn = ttk.Button(
            quick_diag_frame,
            text="Quick diagnostyka (konsola)",
            command=self._quick_diagnostics
        )
        quick_diag_btn.pack(side="left", padx=5)
        
        help_btn2 = ttk.Button(
            quick_diag_frame,
            text="?",
            width=3,
            command=lambda: self._show_tooltip(
                "Szybka diagnostyka symbolów wypisywana do konsoli (terminala).\n"
                "Przydatne do szybkiego sprawdzenia stanu bazy."
            )
        )
        help_btn2.pack(side="left", padx=2)
        
        # Przycisk Przywróć z backupu
        restore_frame = ttk.Frame(buttons_frame)
        restore_frame.pack(fill="x", pady=2)
        
        restore_btn = ttk.Button(
            restore_frame,
            text="Przywróć z backupu",
            command=self._restore_from_backup
        )
        restore_btn.pack(side="left", padx=5)
        
        help_btn3 = ttk.Button(
            restore_frame,
            text="?",
            width=3,
            command=lambda: self._show_tooltip(
                "Przywraca dane SL (opening) z backupu do pustych rekordów.\n"
                "Nadpisuje puste wartości sl_opening w tabeli positions.\n"
                "Bezpieczne - nie nadpisuje istniejących danych."
            )
        )
        help_btn3.pack(side="left", padx=2)
        
        # Informacja o bezpieczeństwie
        info_frame = ttk.LabelFrame(parent_frame, text="Informacje")
        info_frame.pack(fill="x", padx=10, pady=10)
        
        info_text = (
            "Wszystkie operacje diagnostyczne są bezpieczne i nie modyfikują danych\n"
            "bez potwierdzenia. Funkcja 'Przywróć z backupu' modyfikuje tylko\n"
            "puste rekordy i nie nadpisuje istniejących danych."
        )
        
        ttk.Label(info_frame, text=info_text, foreground="blue").pack(padx=10, pady=10)
    
    def _show_tooltip(self, message):
        """Pokazuje tooltip z informacją o funkcji"""
        messagebox.showinfo("Informacja", message)
    
    def _show_symbol_diagnostics(self):
        """Pokazuje diagnostykę symbolów z bazy danych"""
        try:
            # Pobierz wszystkie symbole z bazy (nie unikalne)
            query = "SELECT symbol, COUNT(*) as count FROM positions GROUP BY symbol ORDER BY symbol"
            rows = execute_query(query)
            
            # Stwórz okno diagnostyczne
            diag_window = tk.Toplevel(self.root)
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
                    content += f"  ⚠️ BRAK DOPASOWANIA w AVAILABLE_INSTRUMENTS\n"
                
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
    
    def _restore_from_backup(self):
        """Uruchamia przywracanie danych z backupu"""
        try:
            # Pobranie migratora
            sl_migrator = get_sl_migrator()
            
            # Pokaż okno potwierdzenia
            result = messagebox.askyesno(
                "Przywracanie z backupu",
                "Czy chcesz przywrócić dane SL (opening) z backupu?\n\n"
                "To nadpisze puste wartości sl_opening w tabeli positions."
            )
            
            if result:
                print("[MainWindow] Uruchamianie przywracania z backupu...")
                restored_count = sl_migrator.restore_from_backup()
                
                if restored_count > 0:
                    messagebox.showinfo(
                        "Sukces", 
                        f"Przywrócono {restored_count} rekordów z backupu!\n\n"
                        f"Odśwież dane w przegladarce transakcji aby zobaczyć zmiany."
                    )
                else:
                    messagebox.showinfo(
                        "Informacja", 
                        "Brak danych do przywracania lub wszystkie już są zaktualizowane."
                    )
                    
        except Exception as e:
            print(f"[MainWindow] Błąd przywracania z backupu: {e}")
            messagebox.showerror("Błąd", f"Nie udało się przywrócić z backupu:\n{e}")
    
    def _create_setup_settings(self, parent_frame):
        """Tworzy sekcję ustawień setupów"""
        # Pobierz manager setupów
        self.setup_config = get_setup_config()
        
        # Główny kontener z scrollbarem
        canvas_frame = ttk.Frame(parent_frame)
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Canvas z scrollbarem dla dużej ilości setupów
        canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Nagłówek
        header_frame = ttk.LabelFrame(scrollable_frame, text="Skróty Setupów")
        header_frame.pack(fill="x", padx=5, pady=5)
        
        info_label = ttk.Label(
            header_frame,
            text="Skonfiguruj skróty klawiszowe dla setupów. Nacisnij Tab lub kliknij poza pole aby rozwinąć skrót.",
            foreground="blue"
        )
        info_label.pack(padx=10, pady=5)
        
        # Lista setupów
        self.setups_frame = ttk.LabelFrame(scrollable_frame, text="Lista setupów")
        self.setups_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Nagłówki kolumn
        headers_frame = ttk.Frame(self.setups_frame)
        headers_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(headers_frame, text="Skrót", width=10).pack(side="left", padx=2)
        ttk.Label(headers_frame, text="Nazwa setupu", width=20).pack(side="left", padx=2)
        ttk.Label(headers_frame, text="Opis", width=30).pack(side="left", padx=2)
        ttk.Label(headers_frame, text="Akcje", width=15).pack(side="left", padx=2)
        
        # Kontener na wiersze setupów
        self.setup_rows_frame = ttk.Frame(self.setups_frame)
        self.setup_rows_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Załaduj istniejące setupy
        self._load_setup_rows()
        
        # Przycisk dodaj nowy setup
        add_frame = ttk.LabelFrame(scrollable_frame, text="Dodaj nowy setup")
        add_frame.pack(fill="x", padx=5, pady=5)
        
        add_row_frame = ttk.Frame(add_frame)
        add_row_frame.pack(padx=10, pady=10)
        
        ttk.Label(add_row_frame, text="Skrót:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.new_shortcut_entry = ttk.Entry(add_row_frame, width=10)
        self.new_shortcut_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(add_row_frame, text="Nazwa:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.new_name_entry = ttk.Entry(add_row_frame, width=20)
        self.new_name_entry.grid(row=0, column=3, padx=5, pady=2)
        
        ttk.Label(add_row_frame, text="Opis:").grid(row=0, column=4, padx=5, pady=2, sticky="w")
        self.new_desc_entry = ttk.Entry(add_row_frame, width=30)
        self.new_desc_entry.grid(row=0, column=5, padx=5, pady=2)
        
        ttk.Button(
            add_row_frame,
            text="Dodaj",
            command=self._add_new_setup
        ).grid(row=0, column=6, padx=10, pady=2)
        
        # Przyciski akcji
        action_frame = ttk.LabelFrame(scrollable_frame, text="Akcje")
        action_frame.pack(fill="x", padx=5, pady=5)
        
        action_buttons_frame = ttk.Frame(action_frame)
        action_buttons_frame.pack(padx=10, pady=10)
        
        ttk.Button(
            action_buttons_frame,
            text="Odśwież",
            command=self._refresh_setup_list
        ).pack(side="left", padx=5)
        
        ttk.Button(
            action_buttons_frame,
            text="Test skrótów",
            command=self._test_setup_shortcuts
        ).pack(side="left", padx=5)
    
    def _load_setup_rows(self):
        """Załadowuje wiersze z setupami"""
        # Wyczyść istniejące wiersze
        for widget in self.setup_rows_frame.winfo_children():
            widget.destroy()
        
        # Załaduj setupy z konfiguracji
        shortcuts = self.setup_config.get_shortcuts()
        
        for shortcut, data in shortcuts.items():
            self._create_setup_row(shortcut, data["name"], data.get("description", ""))
    
    def _create_setup_row(self, shortcut, name, description):
        """Tworzy wiersz dla jednego setupu"""
        row_frame = ttk.Frame(self.setup_rows_frame)
        row_frame.pack(fill="x", pady=1)
        
        # Entry dla skrótu
        shortcut_entry = ttk.Entry(row_frame, width=10)
        shortcut_entry.insert(0, shortcut)
        shortcut_entry.pack(side="left", padx=2)
        
        # Entry dla nazwy
        name_entry = ttk.Entry(row_frame, width=20)
        name_entry.insert(0, name)
        name_entry.pack(side="left", padx=2)
        
        # Entry dla opisu
        desc_entry = ttk.Entry(row_frame, width=30)
        desc_entry.insert(0, description)
        desc_entry.pack(side="left", padx=2)
        
        # Przyciski akcji
        action_frame = ttk.Frame(row_frame)
        action_frame.pack(side="left", padx=5)
        
        # Przycisk zapisz
        save_btn = ttk.Button(
            action_frame,
            text="Zapisz",
            width=8,
            command=lambda: self._save_setup_row(
                shortcut, shortcut_entry, name_entry, desc_entry, row_frame
            )
        )
        save_btn.pack(side="left", padx=2)
        
        # Przycisk usuń
        delete_btn = ttk.Button(
            action_frame,
            text="Usuń",
            width=8,
            command=lambda: self._delete_setup_row(shortcut, row_frame)
        )
        delete_btn.pack(side="left", padx=2)
    
    def _save_setup_row(self, original_shortcut, shortcut_entry, name_entry, desc_entry, row_frame):
        """Zapisuje zmiany w wierszu setupu"""
        try:
            new_shortcut = shortcut_entry.get().strip()
            new_name = name_entry.get().strip()
            new_desc = desc_entry.get().strip()
            
            if not new_shortcut or not new_name:
                messagebox.showerror("Błąd", "Skrót i nazwa są wymagane!")
                return
            
            # Jeśli skrót się zmienił, usuń stary
            if new_shortcut != original_shortcut:
                self.setup_config.remove_setup(original_shortcut)
            
            # Dodaj/zaktualizuj setup
            success = self.setup_config.add_setup(new_shortcut, new_name, new_desc)
            
            if success:
                messagebox.showinfo("Sukces", f"Setup '{new_shortcut}' → '{new_name}' zapisany!")
                self._refresh_setup_list()
            else:
                messagebox.showerror("Błąd", "Nie udało się zapisać setupu")
                
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd zapisu: {e}")
    
    def _delete_setup_row(self, shortcut, row_frame):
        """Usuwa setup"""
        result = messagebox.askyesno(
            "Potwierdź usunięcie",
            f"Czy na pewno chcesz usunąć setup '{shortcut}'?"
        )
        
        if result:
            success = self.setup_config.remove_setup(shortcut)
            if success:
                messagebox.showinfo("Sukces", f"Setup '{shortcut}' usunięty!")
                self._refresh_setup_list()
            else:
                messagebox.showerror("Błąd", "Nie udało się usunąć setupu")
    
    def _add_new_setup(self):
        """Dodaje nowy setup"""
        try:
            shortcut = self.new_shortcut_entry.get().strip()
            name = self.new_name_entry.get().strip()
            desc = self.new_desc_entry.get().strip()
            
            if not shortcut or not name:
                messagebox.showerror("Błąd", "Skrót i nazwa są wymagane!")
                return
            
            # Sprawdź czy skrót już istnieje
            shortcuts = self.setup_config.get_shortcuts()
            if shortcut in shortcuts:
                messagebox.showerror("Błąd", f"Skrót '{shortcut}' już istnieje!")
                return
            
            success = self.setup_config.add_setup(shortcut, name, desc)
            
            if success:
                messagebox.showinfo("Sukces", f"Setup '{shortcut}' → '{name}' dodany!")
                # Wyczyść pola
                self.new_shortcut_entry.delete(0, tk.END)
                self.new_name_entry.delete(0, tk.END)
                self.new_desc_entry.delete(0, tk.END)
                self._refresh_setup_list()
            else:
                messagebox.showerror("Błąd", "Nie udało się dodać setupu")
                
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd dodawania: {e}")
    
    def _refresh_setup_list(self):
        """Odświeża listę setupów"""
        self.setup_config.load_config()  # Przeładuj z pliku
        self._load_setup_rows()
    
    def _test_setup_shortcuts(self):
        """Testuje działanie skrótów setupu"""
        test_window = tk.Toplevel(self.root)
        test_window.title("Test skrótów Setup")
        test_window.geometry("500x300")
        
        # Instrukcja
        instruction_frame = ttk.LabelFrame(test_window, text="Instrukcja")
        instruction_frame.pack(fill="x", padx=10, pady=10)
        
        instruction_text = (
            "Wpisz skrót w polu poniżej i naciśnij Tab lub kliknij poza pole.\n"
            "Skrót powinien się automatycznie rozwinąć do pełnej nazwy setupu."
        )
        ttk.Label(instruction_frame, text=instruction_text).pack(padx=10, pady=10)
        
        # Pole testowe
        test_frame = ttk.LabelFrame(test_window, text="Test")
        test_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(test_frame, text="Wpisz skrót:").pack(pady=5)
        
        from gui.widgets.custom_entries import SetupEntry
        test_entry = SetupEntry(test_frame, width=30)
        test_entry.pack(pady=10)
        
        # Lista dostępnych skrótów
        shortcuts_frame = ttk.LabelFrame(test_window, text="Dostępne skróty")
        shortcuts_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        shortcuts_text = tk.Text(shortcuts_frame, height=8, wrap=tk.WORD)
        shortcuts_scroll = ttk.Scrollbar(shortcuts_frame, orient="vertical", command=shortcuts_text.yview)
        shortcuts_text.configure(yscrollcommand=shortcuts_scroll.set)
        
        shortcuts_text.pack(side="left", fill="both", expand=True)
        shortcuts_scroll.pack(side="right", fill="y")
        
        # Wypełnij listę skrótów
        shortcuts = self.setup_config.get_shortcuts()
        shortcuts_content = "Dostępne skróty:\n\n"
        for shortcut, data in sorted(shortcuts.items()):
            shortcuts_content += f"'{shortcut}' → '{data['name']}'\n"
            if data.get('description'):
                shortcuts_content += f"    {data['description']}\n"
            shortcuts_content += "\n"
        
        shortcuts_text.insert("1.0", shortcuts_content)
        shortcuts_text.config(state="disabled")
        
        # Przycisk zamknij
        ttk.Button(test_window, text="Zamknij", command=test_window.destroy).pack(pady=10)
    
    def _show_about(self):
        """Pokazuje informacje o programie"""
        about_text = """Dziennik Transakcji AI 3.0

Aplikacja do zarządzania dziennikiem transakcji tradingowych
z zaawansowanymi funkcjami analizy i kalkulacji.

Funkcjonalności:
• Przeglądanie i edycja transakcji
• Kalkulator maksymalnego Take Profit
• Analiza wyników z uwzględnieniem Break Even
• Eksport danych do CSV
• Zapis wyników do bazy danych

Wersja: 3.0
Data: 2025"""
        
        messagebox.showinfo("O programie", about_text)
    
    def _on_closing(self):
        """Obsługuje zamknięcie aplikacji"""
        try:
            # Zapisz konfigurację głównego okna
            self.window_config.save_window_config(self.root, "main_window")
            print("[MainWindow] Zapisano konfigurację okna")
        except Exception as e:
            print(f"[MainWindow] Błąd zapisu konfiguracji: {e}")
        
        # Zamknij aplikację
        self.root.quit()
        self.root.destroy()
