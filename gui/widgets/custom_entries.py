"""
Niestandardowe pola wprowadzania danych
"""
import tkinter as tk
from tkinter import ttk


class SetupEntry(ttk.Entry):
    """Entry z obsługą skrótów dla pola Setup"""
    
    def __init__(self, parent, shortcuts, **kwargs):
        super().__init__(parent, **kwargs)
        self.shortcuts = shortcuts
        self.bind("<Tab>", self._on_tab)
        self.bind("<FocusOut>", self._on_focus_out)

    def _expand_shortcut(self):
        """Rozszerza skrót na pełną wartość"""
        current_value = self.get().strip()
        if current_value in self.shortcuts:
            expanded_value = self.shortcuts[current_value]
            self.delete(0, tk.END)
            self.insert(0, expanded_value)

    def _on_tab(self, event):
        """Obsługa zdarzenia Tab"""
        self._expand_shortcut()
        # Pozwalamy zdarzeniu Tab kontynuować normalne działanie
        return

    def _on_focus_out(self, event):
        """Obsługa zdarzenia utraty fokusa"""
        self._expand_shortcut()


class NumericEntry(ttk.Entry):
    """Entry akceptujące tylko liczby"""
    
    def __init__(self, parent, allow_decimal=True, allow_negative=False, **kwargs):
        super().__init__(parent, **kwargs)
        self.allow_decimal = allow_decimal
        self.allow_negative = allow_negative
        
        # Rejestracja walidacji
        vcmd = (self.register(self._validate), '%P')
        self.config(validate='key', validatecommand=vcmd)
    
    def _validate(self, value):
        """Walidacja wprowadzanych danych"""
        if value == "":
            return True
        
        # Sprawdzenie znaku minus
        if value.startswith('-'):
            if not self.allow_negative:
                return False
            value = value[1:]  # Usuń minus do dalszej walidacji
        
        # Sprawdzenie kropki dziesiętnej
        if '.' in value:
            if not self.allow_decimal:
                return False
            # Może być tylko jedna kropka
            if value.count('.') > 1:
                return False
            # Po kropce muszą być cyfry lub nic
            parts = value.split('.')
            if len(parts[1]) > 0 and not parts[1].isdigit():
                return False
            value = parts[0]  # Sprawdź część przed kropką
        
        # Sprawdzenie czy reszta to cyfry
        return value.isdigit() or value == ""
    
    def get_float(self):
        """Zwraca wartość jako float lub None jeśli puste/nieprawidłowe"""
        try:
            value = self.get().strip()
            if value == "":
                return None
            return float(value)
        except ValueError:
            return None
    
    def set_float(self, value):
        """Ustawia wartość float"""
        self.delete(0, tk.END)
        if value is not None:
            self.insert(0, str(value))


class ReadOnlyText(tk.Text):
    """Widget Text tylko do odczytu z lepszym wyglądem"""
    
    def __init__(self, parent, **kwargs):
        # Usuń height i width z kwargs jeśli są, żeby uniknąć konfliktów
        default_kwargs = {
            'state': 'disabled',
            'wrap': tk.WORD,
            'bg': '#f0f0f0',
            'relief': 'flat',
            'borderwidth': 1
        }
        default_kwargs.update(kwargs)
        
        super().__init__(parent, **default_kwargs)
    
    def set_text(self, text):
        """Ustawia tekst w widget"""
        self.config(state='normal')
        self.delete('1.0', tk.END)
        self.insert('1.0', text)
        self.config(state='disabled')
    
    def append_text(self, text):
        """Dodaje tekst na końcu"""
        self.config(state='normal')
        self.insert(tk.END, text)
        self.config(state='disabled')
