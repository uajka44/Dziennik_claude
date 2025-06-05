"""
GUI dla kalkulatora Take Profit
"""
import tkinter as tk
from tkinter import ttk, messagebox
from gui.widgets.date_picker import DateRangePicker, InstrumentSelector, StopLossSelector
from gui.widgets.custom_entries import NumericEntry
from calculations.tp_calculator import TPCalculator
from config.database_config import AVAILABLE_INSTRUMENTS
from utils.formatting import format_points, format_price
import threading


class TPCalculatorWindow:
    """Okno kalkulatora Take Profit"""
    
    def __init__(self, parent):
        self.parent = parent
        self.calculator = TPCalculator()
        self.results = []
        
        # Tworzenie okna
        self.window = tk.Toplevel(parent)
        self.window.title("Kalkulator maksymalnego Take Profit")
        self.window.geometry("1200x800")
        self.window.resizable(True, True)
        
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """Tworzy wszystkie widgety okna"""
        
        # Główna ramka z przewijaniem
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # === SEKCJA PARAMETRÓW ===
        params_frame = ttk.LabelFrame(main_frame, text="Parametry kalkulacji")
        params_frame.pack(fill="x", pady=(0, 10))
        
        # Zakres dat
        self.date_picker = DateRangePicker(params_frame)
        self.date_picker.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Instrumenty
        self.instrument_selector = InstrumentSelector(params_frame, AVAILABLE_INSTRUMENTS)
        self.instrument_selector.grid(row=0, column=1, padx=10, pady=10, sticky="nw")
        
        # Stop Loss
        self.sl_selector = StopLossSelector(params_frame)
        self.sl_selector.grid(row=1, column=0, padx=10, pady=10, sticky="nw")
        
        # === SEKCJA BREAK EVEN ===
        be_frame = ttk.LabelFrame(params_frame, text="Break Even")
        be_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nw")
        
        # BE Prog
        ttk.Label(be_frame, text="Próg BE:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.be_prog_entry = NumericEntry(be_frame, width=10, allow_decimal=True)
        self.be_prog_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(be_frame, text="pkt").grid(row=0, column=2, padx=2, pady=5)
        
        # BE Offset
        ttk.Label(be_frame, text="Offset BE:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.be_offset_entry = NumericEntry(be_frame, width=10, allow_decimal=True)
        self.be_offset_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(be_frame, text="pkt").grid(row=1, column=2, padx=2, pady=5)
        
        # === SEKCJA DODATKOWE ===
        additional_frame = ttk.LabelFrame(params_frame, text="Dodatkowe parametry")
        additional_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        # Spread
        ttk.Label(additional_frame, text="Spread:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.spread_entry = NumericEntry(additional_frame, width=10, allow_decimal=True)
        self.spread_entry.insert(0, "0")
        self.spread_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(additional_frame, text="pkt").grid(row=0, column=2, padx=2, pady=5)
        
        # Checkbox szczegółowe logi
        self.detailed_logs_var = tk.BooleanVar()
        self.detailed_logs_cb = ttk.Checkbutton(
            additional_frame, 
            text="Szczegółowe logi (analiza świeczka po świeczce)", 
            variable=self.detailed_logs_var
        )
        self.detailed_logs_cb.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        
        # Checkbox zapisz do bazy
        self.save_to_db_var = tk.BooleanVar()
        self.save_to_db_cb = ttk.Checkbutton(
            additional_frame, 
            text="Zapisz wyniki do bazy danych", 
            variable=self.save_to_db_var
        )
        self.save_to_db_cb.grid(row=1, column=3, padx=20, pady=5)
        
        # === PRZYCISKI ===
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=10)
        
        self.calculate_button = ttk.Button(
            buttons_frame, 
            text="Oblicz", 
            command=self._start_calculation
        )
        self.calculate_button.pack(side="left", padx=5)
        
        self.export_button = ttk.Button(
            buttons_frame, 
            text="Eksportuj wyniki", 
            command=self._export_results,
            state="disabled"
        )
        self.export_button.pack(side="left", padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(buttons_frame, mode='indeterminate')
        self.progress.pack(side="right", padx=5)
        
        # === SEKCJA WYNIKÓW ===
        results_frame = ttk.LabelFrame(main_frame, text="Wyniki kalkulacji")
        results_frame.pack(fill="both", expand=True, pady=10)
        
        # Tabela wyników
        self._create_results_table(results_frame)
        
        # Podsumowanie
        self._create_summary_section(results_frame)
    
    def _create_results_table(self, parent):
        """Tworzy tabelę wyników"""
        
        # Ramka dla tabeli
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Kolumny tabeli
        columns = [
            "ticket", "symbol", "type", "open_time", "open_price", 
            "setup", "tp_sl_staly", "tp_sl_recznie", "tp_sl_be"
        ]
        
        # Scrollbary
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal")
        
        # Treeview
        self.results_tree = ttk.Treeview(
            table_frame, 
            columns=columns,
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )
        
        v_scrollbar.config(command=self.results_tree.yview)
        h_scrollbar.config(command=self.results_tree.xview)
        
        # Konfiguracja kolumn
        self.results_tree.column("#0", width=0, stretch=tk.NO)
        
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
            self.results_tree.column(col, width=config["width"], anchor=tk.CENTER)
            self.results_tree.heading(col, text=config["text"])
        
        # Umieszczenie w grid
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        self.results_tree.pack(fill="both", expand=True)
    
    def _create_summary_section(self, parent):
        """Tworzy sekcję podsumowania"""
        
        summary_frame = ttk.LabelFrame(parent, text="Podsumowanie")
        summary_frame.pack(fill="x", padx=5, pady=5)
        
        # Labels dla statystyk
        stats_frame = ttk.Frame(summary_frame)
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        # Wiersz 1
        ttk.Label(stats_frame, text="Pozycji ogółem:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.total_positions_label = ttk.Label(stats_frame, text="0")
        self.total_positions_label.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(stats_frame, text="Udanych obliczeń:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.successful_calcs_label = ttk.Label(stats_frame, text="0")
        self.successful_calcs_label.grid(row=0, column=3, padx=5, pady=2)
        
        # Wiersz 2 - średnie
        ttk.Label(stats_frame, text="Średni TP (SL stały):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.avg_tp_staly_label = ttk.Label(stats_frame, text="0.0 pkt")
        self.avg_tp_staly_label.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(stats_frame, text="Średni TP (SL ręczne):").grid(row=1, column=2, padx=5, pady=2, sticky="w")
        self.avg_tp_recznie_label = ttk.Label(stats_frame, text="0.0 pkt")
        self.avg_tp_recznie_label.grid(row=1, column=3, padx=5, pady=2)
        
        ttk.Label(stats_frame, text="Średni TP (BE):").grid(row=1, column=4, padx=5, pady=2, sticky="w")
        self.avg_tp_be_label = ttk.Label(stats_frame, text="0.0 pkt")
        self.avg_tp_be_label.grid(row=1, column=5, padx=5, pady=2)
        
        # Wiersz 3 - maksymalne
        ttk.Label(stats_frame, text="Max TP (SL stały):").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.max_tp_staly_label = ttk.Label(stats_frame, text="0.0 pkt")
        self.max_tp_staly_label.grid(row=2, column=1, padx=5, pady=2)
        
        ttk.Label(stats_frame, text="Max TP (SL ręczne):").grid(row=2, column=2, padx=5, pady=2, sticky="w")
        self.max_tp_recznie_label = ttk.Label(stats_frame, text="0.0 pkt")
        self.max_tp_recznie_label.grid(row=2, column=3, padx=5, pady=2)
        
        ttk.Label(stats_frame, text="Max TP (BE):").grid(row=2, column=4, padx=5, pady=2, sticky="w")
        self.max_tp_be_label = ttk.Label(stats_frame, text="0.0 pkt")
        self.max_tp_be_label.grid(row=2, column=5, padx=5, pady=2)
    
    def _setup_layout(self):
        """Konfiguruje układ okna"""
        # Ustawienia domyślne
        self.instrument_selector.select_all()  # Zaznacz wszystkie instrumenty
        self.sl_selector.sl_staly_var.set(True)  # Zaznacz SL stały
        self.sl_selector.sl_staly_entry.set_float(10.0)  # Domyślny SL stały 10 pkt
        self.sl_selector._toggle_sl_staly_entry()  # Włącz pole SL stały
        
        self.be_prog_entry.set_float(10.0)  # Domyślny BE prog 10 pkt
        self.be_offset_entry.set_float(1.0)  # Domyślny BE offset 1 pkt
    
    def _start_calculation(self):
        """Rozpoczyna kalkulację w osobnym wątku"""
        
        # Walidacja parametrów
        if not self._validate_parameters():
            return
        
        # Wyłącz przycisk i pokaż progress
        self.calculate_button.config(state="disabled")
        self.progress.start()
        
        # Uruchom kalkulację w osobnym wątku
        thread = threading.Thread(target=self._perform_calculation)
        thread.daemon = True
        thread.start()
    
    def _validate_parameters(self) -> bool:
        """Waliduje parametry przed kalkulacją"""
        
        # Sprawdź wybrane instrumenty
        instruments = self.instrument_selector.get_selected_instruments()
        if not instruments:
            messagebox.showerror("Błąd", "Wybierz przynajmniej jeden instrument")
            return False
        
        # Sprawdź wybrane typy SL
        sl_types = self.sl_selector.get_selected_sl_types()
        if not any(sl_types.values()):
            messagebox.showerror("Błąd", "Wybierz przynajmniej jeden typ Stop Loss")
            return False
        
        # Sprawdź SL stały jeśli wybrany
        if sl_types['sl_staly']:
            sl_staly = self.sl_selector.get_sl_staly_value()
            if sl_staly is None or sl_staly <= 0:
                messagebox.showerror("Błąd", "Podaj prawidłową wartość SL stałego")
                return False
        
        # Sprawdź spread
        spread = self.spread_entry.get_float()
        if spread is None or spread < 0:
            messagebox.showerror("Błąd", "Podaj prawidłową wartość spread'u")
            return False
        
        return True
    
    def _perform_calculation(self):
        """Wykonuje kalkulację (uruchamiane w osobnym wątku)"""
        try:
            print("Rozpoczynam kalkulację...")
            
            # Pobierz parametry
            start_date, end_date = self.date_picker.get_date_range()
            instruments = self.instrument_selector.get_selected_instruments()
            sl_types = self.sl_selector.get_selected_sl_types()
            sl_staly_value = self.sl_selector.get_sl_staly_value()
            be_prog = self.be_prog_entry.get_float()
            be_offset = self.be_offset_entry.get_float()
            spread = self.spread_entry.get_float() or 0
            save_to_db = self.save_to_db_var.get()
            detailed_logs = self.detailed_logs_var.get()  # Nowy parametr
            
            print(f"Parametry: daty={start_date}-{end_date}, instrumenty={instruments}")
            print(f"SL typy: {sl_types}, SL stały: {sl_staly_value}")
            
            # Wykonaj kalkulację
            print("Wywołuję kalkulator...")
            self.results = self.calculator.calculate_tp_for_date_range(
                start_date=start_date,
                end_date=end_date,
                instruments=instruments,
                sl_types=sl_types,
                sl_staly_value=sl_staly_value,
                be_prog=be_prog,
                be_offset=be_offset,
                spread=spread,
                save_to_db=save_to_db,
                detailed_logs=detailed_logs  # Przekazujemy nową opcję
            )
            
            print(f"Kalkulacja zakończona. Wyników: {len(self.results)}")
            
            # Zaktualizuj GUI w głównym wątku
            self.window.after(0, self._update_results_display)
            
        except Exception as e:
            import traceback
            error_msg = f"Błąd kalkulacji: {str(e)}\n\nSzczegóły:\n{traceback.format_exc()}"
            print(error_msg)
            # Pokaż błąd w głównym wątku
            self.window.after(0, lambda: messagebox.showerror("Błąd kalkulacji", error_msg))
            self.window.after(0, self._calculation_finished)
    
    def _update_results_display(self):
        """Aktualizuje wyświetlanie wyników"""
        print(f"GUI: Aktualizuję wyświetlanie. Wyników: {len(self.results)}")
        
        # Wyczyść tabelę
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Wypełnij tabelę wynikami
        for i, result in enumerate(self.results):
            print(f"GUI: Przetwarzam wynik {i+1}: ticket={result.ticket}")
            print(f"     TP stały: {result.max_tp_sl_staly}, TP ręczne: {result.max_tp_sl_recznie}, TP BE: {result.max_tp_sl_be}")
            
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
            print(f"     Wartości do tabeli: {values}")
            self.results_tree.insert("", "end", values=values)
        
        print(f"GUI: Dodano {len(self.results)} wierszy do tabeli")
        
        # Aktualizuj podsumowanie
        self._update_summary()
        
        # Włącz przycisk eksportu
        if self.results:
            self.export_button.config(state="normal")
            print("GUI: Włączyłem przycisk eksportu")
        
        # Zakończ kalkulację
        self._calculation_finished()
    
    def _update_summary(self):
        """Aktualizuje sekcję podsumowania"""
        print("GUI: Aktualizuję podsumowanie...")
        summary = self.calculator.get_calculation_summary(self.results)
        print(f"GUI: Podsumowanie: {summary}")
        
        self.total_positions_label.config(text=str(summary['total_positions']))
        self.successful_calcs_label.config(text=str(summary['successful_calculations']))
        
        self.avg_tp_staly_label.config(text=f"{summary['avg_tp_sl_staly']:.1f} pkt")
        self.avg_tp_recznie_label.config(text=f"{summary['avg_tp_sl_recznie']:.1f} pkt")
        self.avg_tp_be_label.config(text=f"{summary['avg_tp_sl_be']:.1f} pkt")
        
        self.max_tp_staly_label.config(text=f"{summary['max_tp_sl_staly']:.1f} pkt")
        self.max_tp_recznie_label.config(text=f"{summary['max_tp_sl_recznie']:.1f} pkt")
        self.max_tp_be_label.config(text=f"{summary['max_tp_sl_be']:.1f} pkt")
        
        print("GUI: Podsumowanie zaktualizowane")
    
    def _calculation_finished(self):
        """Wykonywane po zakończeniu kalkulacji"""
        self.progress.stop()
        self.calculate_button.config(state="normal")
        
        # Zamknij połączenia z bazy danych w analizatorach
        try:
            self.calculator.close_connection()
            self.calculator.candle_analyzer.close_connection()
            self.calculator.position_analyzer.close_connection()
        except:
            pass
    
    def _format_time(self, unix_timestamp):
        """Formatuje timestamp do wyświetlenia"""
        from utils.date_utils import format_time_for_display
        return format_time_for_display(unix_timestamp)
    
    def _export_results(self):
        """Eksportuje wyniki do pliku CSV"""
        if not self.results:
            messagebox.showwarning("Uwaga", "Brak wyników do eksportu")
            return
        
        from tkinter import filedialog
        import csv
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Zapisz wyniki jako..."
        )
        
        if filename:
            try:
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
                    for result in self.results:
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
