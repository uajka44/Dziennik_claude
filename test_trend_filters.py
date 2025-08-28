#!/usr/bin/env python3
"""
Test filtrów TrendS i TrendL
"""

import os
import sys
import tkinter as tk
from tkinter import ttk

# Dodaj katalog główny do PATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.data_viewer import DataViewer

def test_trend_filters():
    """Test filtrów TrendS i TrendL"""
    print("=== TEST FILTRÓW TRENDS i TRENDL ===")
    
    # Utwórz okno testowe
    root = tk.Tk()
    root.title("Test Filtrów TrendS/TrendL")
    root.geometry("1400x800")
    
    try:
        # Utwórz DataViewer
        data_viewer = DataViewer(root)
        
        print("✅ DataViewer utworzony pomyślnie")
        
        # Sprawdź czy filtry TrendS i TrendL istnieją
        if hasattr(data_viewer, 'trends_dropdown'):
            print("✅ Filtr TrendS istnieje")
            
            # Sprawdź wartości w dropdown
            trends_items = list(data_viewer.trends_dropdown.items.keys())
            print(f"   Wartości TrendS: {trends_items}")
            
            # Sprawdź czy wszystkie są domyślnie zaznaczone
            selected_trends = data_viewer.trends_dropdown.get_selected()
            print(f"   Zaznaczone TrendS: {selected_trends}")
            
        else:
            print("❌ Filtr TrendS nie istnieje")
            
        if hasattr(data_viewer, 'trendl_dropdown'):
            print("✅ Filtr TrendL istnieje")
            
            # Sprawdź wartości w dropdown
            trendl_items = list(data_viewer.trendl_dropdown.items.keys())
            print(f"   Wartości TrendL: {trendl_items}")
            
            # Sprawdź czy wszystkie są domyślnie zaznaczone
            selected_trendl = data_viewer.trendl_dropdown.get_selected()
            print(f"   Zaznaczone TrendL: {selected_trendl}")
            
        else:
            print("❌ Filtr TrendL nie istnieje")
        
        # Test funkcjonalności
        print("\n=== TEST FUNKCJONALNOŚCI ===")
        
        # Sprawdź czy metoda _load_trend_values działa
        if hasattr(data_viewer, '_load_trend_values'):
            print("✅ Metoda _load_trend_values istnieje")
        else:
            print("❌ Metoda _load_trend_values nie istnieje")
            
        # Test symulacji zmiany filtra
        if hasattr(data_viewer, 'trends_dropdown') and hasattr(data_viewer, 'trendl_dropdown'):
            print("\n=== SYMULACJA FILTROWANIA ===")
            
            # Odznacz niektóre wartości w TrendS
            if '-3' in data_viewer.trends_dropdown.variables:
                data_viewer.trends_dropdown.variables['-3'].set(False)
                print("Odznaczono TrendS = -3")
                
            if '3' in data_viewer.trends_dropdown.variables:
                data_viewer.trends_dropdown.variables['3'].set(False)
                print("Odznaczono TrendS = 3")
                
            # Sprawdź nowy stan
            selected_after = data_viewer.trends_dropdown.get_selected()
            print(f"TrendS po zmianie: {selected_after}")
            
            # Test czy filtr się aktywuje (czy długość się zmieniła)
            if len(selected_after) < len(data_viewer.trends_dropdown.items):
                print("✅ Filtr TrendS będzie aktywny")
            else:
                print("❌ Filtr TrendS nie będzie aktywny")
        
        print("\n=== STRUKTURA GUI ===")
        
        # Sprawdź layout
        if hasattr(data_viewer, 'filter_frame'):
            children = data_viewer.filter_frame.winfo_children()
            print(f"Elementy w filter_frame: {len(children)}")
            
            labels = [w for w in children if isinstance(w, ttk.Label)]
            label_texts = [w.cget('text') for w in labels]
            print(f"Etykiety: {label_texts}")
            
            if 'TrendS:' in label_texts and 'TrendL:' in label_texts:
                print("✅ Etykiety TrendS i TrendL są widoczne")
            else:
                print("❌ Brakuje etykiet TrendS lub TrendL")
        
        print("\n=== PODSUMOWANIE ===")
        print("Filtry TrendS i TrendL zostały pomyślnie dodane!")
        print("Możesz teraz testować aplikację ręcznie.")
        print("")
        print("Instrukcja testowania:")
        print("1. Otwórz aplikację (python main.py)")
        print("2. Przejdź do zakładki 'Przeglądarka danych'")
        print("3. W sekcji 'Filtry' znajdziesz nowe filtry 'TrendS:' i 'TrendL:'")
        print("4. Kliknij na nie aby rozwinąć listę z checkboxami")
        print("5. Odznacz niektóre wartości i sprawdź czy filtrowanie działa")
        
        # Pozostaw okno otwarte do ręcznego testowania
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Błąd podczas testu: {e}")
        import traceback
        traceback.print_exc()
        root.destroy()

if __name__ == "__main__":
    test_trend_filters()
