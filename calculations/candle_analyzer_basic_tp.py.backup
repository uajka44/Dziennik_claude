    def calculate_max_tp_basic(self, candles: List[Candle], position_type: int, 
                              open_price: float, stop_loss: float, spread: float = 0) -> Optional[float]:
        """
        Oblicza maksymalny TP dla podstawowego scenariusza (bez BE)
        
        Algorytm:
        1. Idzie po kolejnych świeczkach od otwarcia pozycji
        2. Na każdej świeczce sprawdza czy cena uderzyła w SL
        3. Jeśli nie - sprawdza maksymalny zysk na tej świeczce
        4. Zapisuje maksymalny zysk jeśli jest większy od poprzedniego
        5. Kończy gdy cena uderzy w SL lub skończą się świeczki
        
        Args:
            candles: Lista świeczek
            position_type: 0 = buy, 1 = sell
            open_price: Cena otwarcia pozycji
            stop_loss: Poziom stop loss
            spread: Spread w punktach
        
        Returns:
            Maksymalny TP w punktach lub None jeśli pozycja została zamknięta na SL
        """
        if not candles:
            print("CandleAnalyzer: Brak świeczek do analizy")
            return None
        
        print(f"CandleAnalyzer: Rozpoczynam obliczenia TP:")
        print(f"  - Pozycja: {'BUY' if position_type == 0 else 'SELL'}")
        print(f"  - Cena otwarcia: {open_price}")
        print(f"  - Stop Loss: {stop_loss}")
        print(f"  - Spread: {spread}")
        print(f"  - Liczba świeczek: {len(candles)}")
        
        max_profit = 0.0
        is_buy = (position_type == 0)
        spread_adjustment = spread  # Spread już w punktach
        
        for i, candle in enumerate(candles):
            print(f"\nCandleAnalyzer: Świeczka {i+1}/{len(candles)}")
            print(f"  - OHLC: O={candle.open}, H={candle.high}, L={candle.low}, C={candle.close}")
            
            if i == 0:
                # Pierwsza świeczka - nie znamy przebiegu, więc sprawdzamy tylko close
                print(f"  - Pierwsza świeczka, sprawdzam tylko close")
                
                if is_buy:
                    # Sprawdź czy low uderzyło w SL
                    if candle.low <= stop_loss + spread_adjustment:
                        print(f"  - SL uderzony przez low ({candle.low} <= {stop_loss + spread_adjustment})")
                        return None  # Pozycja zamknięta na SL
                    
                    # Sprawdź zysk na close
                    profit = candle.close - open_price
                    print(f"  - Zysk na close: {candle.close} - {open_price} = {profit}")
                    
                    if profit > max_profit:
                        max_profit = profit
                        print(f"  - Nowy maksymalny zysk: {max_profit}")
                        
                else:  # sell
                    # Sprawdź czy high uderzyło w SL
                    if candle.high >= stop_loss - spread_adjustment:
                        print(f"  - SL uderzony przez high ({candle.high} >= {stop_loss - spread_adjustment})")
                        return None  # Pozycja zamknięta na SL
                    
                    # Sprawdź zysk na close
                    profit = open_price - candle.close
                    print(f"  - Zysk na close: {open_price} - {candle.close} = {profit}")
                    
                    if profit > max_profit:
                        max_profit = profit
                        print(f"  - Nowy maksymalny zysk: {max_profit}")
                        
            else:
                # Kolejne świeczki - możemy sprawdzać extrema (high/low)
                print(f"  - Kolejna świeczka, sprawdzam extrema")
                
                if is_buy:
                    # Sprawdź czy low uderzyło w SL
                    if candle.low <= stop_loss + spread_adjustment:
                        print(f"  - SL uderzony przez low ({candle.low} <= {stop_loss + spread_adjustment})")
                        print(f"  - Pozycja zamknięta, zwracam maksymalny zysk: {max_profit}")
                        return max_profit
                    
                    # Sprawdź maksymalny zysk na tej świeczce (high)
                    profit = candle.high - open_price
                    print(f"  - Potencjalny zysk na high: {candle.high} - {open_price} = {profit}")
                    
                    if profit > max_profit:
                        max_profit = profit
                        print(f"  - Nowy maksymalny zysk: {max_profit}")
                        
                else:  # sell
                    # Sprawdź czy high uderzyło w SL
                    if candle.high >= stop_loss - spread_adjustment:
                        print(f"  - SL uderzony przez high ({candle.high} >= {stop_loss - spread_adjustment})")
                        print(f"  - Pozycja zamknięta, zwracam maksymalny zysk: {max_profit}")
                        return max_profit
                    
                    # Sprawdź maksymalny zysk na tej świeczce (low)
                    profit = open_price - candle.low
                    print(f"  - Potencjalny zysk na low: {open_price} - {candle.low} = {profit}")
                    
                    if profit > max_profit:
                        max_profit = profit
                        print(f"  - Nowy maksymalny zysk: {max_profit}")
        
        print(f"\nCandleAnalyzer: Koniec świeczek, końcowy maksymalny zysk: {max_profit}")
        return max_profit
