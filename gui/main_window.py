"""
Główne okno aplikacji z menu i zakładkami
"""
import tkinter as tk
from tkinter import ttk, messagebox
from gui.data_viewer import DataViewer
from gui.tp_calculator import TPCalculatorWindow
from config.database_config import DB_PATH


class MainWindow:
    """Główne okno aplikacji"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Dziennik Transakcji - AI 3.0")
        self.root.geometry("1600x900")
        
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
        self.data_viewer = DataViewer(self.data_viewer_frame, DB_PATH)
        
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
            
            # Dodaj status bar
            self.status_bar = ttk.Label(
                self.root, 
                text=f"Połączono z bazą danych: {DB_PATH}",
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
        messagebox.showinfo("Informacja", "Ustawienia będą dostępne w przyszłej wersji")
    
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
