#!/usr/bin/env python
"""
Test skrypt do sprawdzenia czy nowy układ TP działa
"""

import tkinter as tk
from tkinter import ttk

def create_test_window():
    """Tworzy testowe okno z nowym układem TP"""
    root = tk.Tk()
    root.title("Test układu TP")
    root.geometry("1000x600")
    
    # Główny kontener
    main_frame = ttk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Lewa strona - główna tabela
    left_frame = ttk.LabelFrame(main_frame, text="Główna tabela")
    left_frame.pack(side="left", fill="both", expand=True)
    
    # Przykładowa tabela
    tree = ttk.Treeview(left_frame)
    tree["columns"] = ("ticket", "symbol", "profit")
    tree.column("#0", width=0, stretch=tk.NO)
    tree.column("ticket", width=80)
    tree.column("symbol", width=100)
    tree.column("profit", width=80)
    
    tree.heading("ticket", text="Ticket")
    tree.heading("symbol", text="Symbol")
    tree.heading("profit", text="Profit")
    
    # Przykładowe dane
    tree.insert("", "end", values=("12345", "GER40", "15.5"))
    tree.insert("", "end", values=("12346", "US100", "22.0"))
    tree.insert("", "end", values=("12347", "XAUUSD", "-10.0"))
    
    tree.pack(fill="both", expand=True, padx=5, pady=5)
    
    # Prawa strona - kalkulator TP
    right_frame = ttk.LabelFrame(main_frame, text="Kalkulator TP", width=300)
    right_frame.pack(side="right", fill="y", padx=(10, 0))
    right_frame.pack_propagate(False)
    
    # Ustawienia
    settings_frame = ttk.LabelFrame(right_frame, text="Ustawienia")
    settings_frame.pack(fill="x", padx=5, pady=5)
    
    # Spread
    spread_frame = ttk.Frame(settings_frame)
    spread_frame.pack(fill="x", padx=5, pady=2)
    ttk.Label(spread_frame, text="Spread:").pack(side="left")
    spread_var = tk.DoubleVar(value=1.0)
    ttk.Entry(spread_frame, textvariable=spread_var, width=8).pack(side="right")
    
    # Przycisk
    ttk.Button(right_frame, text="Oblicz TP", 
               command=lambda: print("Oblicz TP kliknięte!")).pack(padx=5, pady=5, fill="x")
    
    # Tabela wyników TP
    tp_tree = ttk.Treeview(right_frame, height=10)
    tp_tree["columns"] = ("ticket", "tp", "status")
    tp_tree.column("#0", width=0, stretch=tk.NO)
    tp_tree.column("ticket", width=70)
    tp_tree.column("tp", width=70)
    tp_tree.column("status", width=100)
    
    tp_tree.heading("ticket", text="Ticket")
    tp_tree.heading("tp", text="TP")
    tp_tree.heading("status", text="Status")
    
    # Przykładowe dane TP
    tp_tree.insert("", "end", values=("12345", "25.5", "Obliczono"))
    tp_tree.insert("", "end", values=("12346", "SL Hit", "Stop Loss"))
    
    tp_tree.pack(fill="both", expand=True, padx=5, pady=5)
    
    return root

if __name__ == "__main__":
    print("Tworzenie testowego okna układu TP...")
    root = create_test_window()
    print("Uruchamianie aplikacji testowej...")
    root.mainloop()
    print("Aplikacja testowa zamknięta.")
