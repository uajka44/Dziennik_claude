"""
Navigation handler dla okien edycji - obsługuje przechodzenie między pozycjami
"""
from database.connection import execute_query
from config.field_definitions import COLUMNS


class EditNavigationHandler:
    """Handler nawigacji między pozycjami w oknie edycji"""
    
    def __init__(self, data_viewer):
        """
        Args:
            data_viewer: Instancja DataViewer dla dostępu do aktualnych filtrów
        """
        self.data_viewer = data_viewer
        self._current_positions = []
        self._current_index = -1
        
    def refresh_positions(self):
        """Odświeża listę pozycji na podstawie aktualnych filtrów w DataViewer"""
        try:
            # Pobierz aktualne filtry z DataViewer
            start_date = self.data_viewer.start_date_entry.get()
            end_date = self.data_viewer.end_date_entry.get()
            
            from utils.date_utils import date_range_to_unix
            start_unix, end_unix = date_range_to_unix(start_date, end_date)
            
            # Pobierz wybrane symbole
            selected_symbols = self.data_viewer.instruments_dropdown.get_selected()
            
            if not selected_symbols:
                self._current_positions = []
                return
            
            # Sprawdź czy wszystkie są wybrane
            all_symbols_count = len(self.data_viewer.instruments_dropdown.items)
            all_selected = len(selected_symbols) == all_symbols_count
            
            columns_str = ", ".join(COLUMNS)
            
            if all_selected:
                # Wszystkie instrumenty
                query = f"""
                SELECT {columns_str}
                FROM positions 
                WHERE open_time BETWEEN ? AND ?
                ORDER BY open_time
                """
                rows = execute_query(query, (start_unix, end_unix))
            else:
                # Wybrane instrumenty - uwzględnij oba formaty (z i bez \x00)
                expanded_symbols = []
                for clean_symbol in selected_symbols:
                    expanded_symbols.append(clean_symbol)
                    expanded_symbols.append(clean_symbol + '\x00')
                
                placeholders = ", ".join(["?" for _ in expanded_symbols])
                query = f"""
                SELECT {columns_str}
                FROM positions 
                WHERE open_time BETWEEN ? AND ? AND symbol IN ({placeholders})
                ORDER BY open_time
                """
                params = [start_unix, end_unix] + expanded_symbols
                rows = execute_query(query, params)
            
            # Konwertuj na listę z ticket jako kluczem
            self._current_positions = []
            for row in rows:
                ticket_index = COLUMNS.index("ticket")
                ticket = row[ticket_index]
                # Normalizuj ticket (usuń białe znaki, null charactery)
                if ticket is not None:
                    clean_ticket = str(ticket).strip().rstrip('\x00')
                    self._current_positions.append({
                        'ticket': clean_ticket,
                        'original_ticket': ticket,  # Zachowaj oryginał
                        'values': row
                    })
            
            print(f"[NavigationHandler] Odświeżono {len(self._current_positions)} pozycji")
            
            # Debug - wyświetl pierwsze kilka ticketów
            if len(self._current_positions) > 0:
                debug_tickets = [pos['ticket'] for pos in self._current_positions[:3]]
                print(f"[NavigationHandler] Pierwsze tickety: {debug_tickets}")
            
        except Exception as e:
            print(f"[NavigationHandler] Błąd odświeżania pozycji: {e}")
            self._current_positions = []
    
    def find_current_index(self, ticket):
        """Znajduje indeks aktualnej pozycji na podstawie ticket"""
        # Bardzo agresywna normalizacja ticket
        def normalize_ticket(t):
            if t is None:
                return ""
            # Konwertuj na string, usuń wszystkie możliwe białe znaki i znaki specjalne
            s = str(t).strip().rstrip('\x00').rstrip('\0')
            # Usuń też wszystkie niewidoczne znaki
            s = ''.join(char for char in s if char.isprintable())
            return s
        
        target_ticket = normalize_ticket(ticket)
        
        print(f"[NavigationHandler] Szukam ticket: '{target_ticket}' (długość: {len(target_ticket)})")
        print(f"[NavigationHandler] Oryginalny ticket: {repr(ticket)}")
        
        for i, pos in enumerate(self._current_positions):
            pos_ticket = normalize_ticket(pos['ticket'])
            
            if i < 3:  # Debug tylko pierwsze 3
                print(f"[NavigationHandler] Porówniuję [{i}]: '{pos_ticket}' == '{target_ticket}' ? (dł.: {len(pos_ticket)})")
                print(f"[NavigationHandler] Oryginalny pos: {repr(pos['ticket'])}")
            
            if pos_ticket == target_ticket:
                self._current_index = i
                print(f"[NavigationHandler] ✅ Znaleziono pozycję {ticket} na indeksie {i}")
                return i
        
        # Jeśli nadal nie znaleziono, sprawdź czy może to kwestia typu int vs string
        try:
            target_as_int = int(target_ticket)
            for i, pos in enumerate(self._current_positions):
                pos_ticket = normalize_ticket(pos['ticket'])
                try:
                    pos_as_int = int(pos_ticket)
                    if pos_as_int == target_as_int:
                        self._current_index = i
                        print(f"[NavigationHandler] ✅ Znaleziono przez porównanie int: {ticket} na indeksie {i}")
                        return i
                except ValueError:
                    continue
        except ValueError:
            pass
        
        # Debug - wyświetl wszystkie dostępne tickety
        available_tickets = [normalize_ticket(pos['ticket']) for pos in self._current_positions]
        print(f"[NavigationHandler] ❌ BŁĄD: Nie znaleziono ticket: '{target_ticket}'")
        print(f"[NavigationHandler] Dostępne tickety: {available_tickets[:5]}...")  # Tylko pierwsze 5
        
        self._current_index = -1
        return -1
    
    def navigate_next(self, current_ticket):
        """Przechodzi do następnej pozycji"""
        self.refresh_positions()
        current_index = self.find_current_index(current_ticket)
        
        if current_index == -1:
            print(f"[NavigationHandler] Nie znaleziono aktualnej pozycji: {current_ticket}")
            return
        
        next_index = current_index + 1
        if next_index >= len(self._current_positions):
            print("[NavigationHandler] To jest ostatnia pozycja")
            return
        
        next_position = self._current_positions[next_index]
        print(f"[NavigationHandler] Przechodzenie do następnej pozycji: {next_position['ticket']}")
        
        # Otwórz następną pozycję
        self._open_position(next_position)
    
    def navigate_prev(self, current_ticket):
        """Przechodzi do poprzedniej pozycji"""
        self.refresh_positions()
        current_index = self.find_current_index(current_ticket)
        
        if current_index == -1:
            print(f"[NavigationHandler] Nie znaleziono aktualnej pozycji: {current_ticket}")
            return
        
        prev_index = current_index - 1
        if prev_index < 0:
            print("[NavigationHandler] To jest pierwsza pozycja")
            return
        
        prev_position = self._current_positions[prev_index]
        print(f"[NavigationHandler] Przechodzenie do poprzedniej pozycji: {prev_position['ticket']}")
        
        # Otwórz poprzednią pozycję
        self._open_position(prev_position)
    
    def _open_position(self, position):
        """Otwiera pozycję w oknie edycji"""
        try:
            # Przygotuj values w formacie odpowiednim dla EditDialog
            from utils.date_utils import format_time_for_display
            from utils.formatting import format_profit_points, format_checkbox_value
            from config.field_definitions import TEXT_FIELDS, CHECKBOX_FIELDS
            
            values = list(position['values'])
            display_values = []
            
            for i, col in enumerate(COLUMNS):
                value = values[i]
                
                if col == "open_time":
                    display_values.append(format_time_for_display(value))
                elif col == "profit_points":
                    display_values.append(format_profit_points(value))
                elif col in [field.name for field in CHECKBOX_FIELDS]:
                    display_values.append(format_checkbox_value(value))
                else:
                    display_values.append(value or "")
            
            # Callback do aktualizacji widoku
            def on_save_callback(updated_values):
                # Znajdź odpowiedni element w treeview i zaktualizuj
                for item in self.data_viewer.tree.get_children():
                    item_values = self.data_viewer.tree.item(item, "values")
                    ticket_col_index = COLUMNS.index("ticket")
                    if item_values[ticket_col_index] == str(position['ticket']):
                        self.data_viewer.tree.item(item, values=tuple(updated_values))
                        break
            
            # Otwórz nowe okno edycji
            self.data_viewer.edit_manager.open_edit_window(
                parent=self.data_viewer.parent,
                ticket=position['ticket'],
                values=tuple(display_values),
                callback=on_save_callback,
                navigation_handler=self,
                save_current_first=False  # Już zapisane w _save_changes_silent
            )
            
        except Exception as e:
            print(f"[NavigationHandler] Błąd otwierania pozycji: {e}")
