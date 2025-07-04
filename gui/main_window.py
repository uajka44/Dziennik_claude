"""
Główne okno aplikacji z menu i zakładkami
"""
import tkinter as tk
from tkinter import ttk, messagebox
from gui.data_viewer import DataViewer
from gui.tp_calculator import TPCalculatorWindow
from database.connection import get_current_database_info


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
