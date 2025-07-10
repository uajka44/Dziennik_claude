#!/usr/bin/env python3
"""
Test sprawdzający poprawki w logice spread'u
"""

# Test pozycji SELL z spread'em
def test_sell_spread_logic():
    print("=== TEST POZYCJI SELL Z SPREAD'EM ===")
    
    # Przykład: pozycja SELL otwarta po 24610.06, SL stały 10 pkt
    open_price = 24610.06
    sl_points = 10
    spread = 1.0
    
    # Dla SELL: SL powinien być na open_price + sl_points = 24620.06
    stop_loss = open_price + sl_points
    print(f"Open price: {open_price}")
    print(f"SL points: {sl_points}")
    print(f"Stop Loss poziom: {stop_loss}")
    print(f"Spread: {spread}")
    
    # STARA (błędna) logika: 
    old_sl_with_spread = stop_loss + spread  # 24621.06
    print(f"STARA logika - SL z spread'em: {old_sl_with_spread} (BŁĘDNE!)")
    
    # NOWA (poprawna) logika dla SELL:
    new_sl_with_spread = stop_loss + spread  # To jest PRAWIDŁOWE dla SELL!
    print(f"NOWA logika - SL z spread'em: {new_sl_with_spread} (PRAWIDŁOWE dla SELL)")
    
    # Test świeczki
    test_candle_high = 24620.5
    
    print(f"\nTest świeczki z high = {test_candle_high}:")
    print(f"Czy high >= {new_sl_with_spread}? {test_candle_high >= new_sl_with_spread}")
    
    if test_candle_high >= new_sl_with_spread:
        print("SL uderzony - pozycja zamknięta")
    else:
        print("SL nie uderzony - pozycja dalej otwarta")

def test_buy_spread_logic():
    print("\n=== TEST POZYCJI BUY Z SPREAD'EM ===")
    
    # Przykład: pozycja BUY otwarta po 24610.06, SL stały 10 pkt
    open_price = 24610.06
    sl_points = 10
    spread = 1.0
    
    # Dla BUY: SL powinien być na open_price - sl_points = 24600.06
    stop_loss = open_price - sl_points
    print(f"Open price: {open_price}")
    print(f"SL points: {sl_points}")
    print(f"Stop Loss poziom: {stop_loss}")
    print(f"Spread: {spread}")
    
    # STARA (błędna) logika: 
    old_sl_with_spread = stop_loss + spread  # 24601.06 (BŁĘDNE!)
    print(f"STARA logika - SL z spread'em: {old_sl_with_spread} (BŁĘDNE!)")
    
    # NOWA (poprawna) logika dla BUY:
    new_sl_with_spread = stop_loss - spread  # 24599.06 (PRAWIDŁOWE!)
    print(f"NOWA logika - SL z spread'em: {new_sl_with_spread} (PRAWIDŁOWE dla BUY)")
    
    # Test świeczki
    test_candle_low = 24600.0
    
    print(f"\nTest świeczki z low = {test_candle_low}:")
    print(f"Czy low <= {new_sl_with_spread}? {test_candle_low <= new_sl_with_spread}")
    
    if test_candle_low <= new_sl_with_spread:
        print("SL uderzony - pozycja zamknięta")
    else:
        print("SL nie uderzony - pozycja dalej otwarta")

if __name__ == "__main__":
    test_sell_spread_logic()
    test_buy_spread_logic()
    
    print("\n=== PODSUMOWANIE POPRAWEK ===")
    print("1. Dla pozycji BUY: spread powinien być ODEJMOWANY od SL")
    print("   Powód: spread zwiększa koszt zamknięcia, więc faktyczny SL jest NIŻSZY")
    print("2. Dla pozycji SELL: spread powinien być DODAWANY do SL")
    print("   Powód: spread zwiększa koszt zamknięcia, więc faktyczny SL jest WYŻSZY")
    print("3. W kodzie poprawiono linie sprawdzające SL dla pozycji BUY")
    print("4. Dla pozycji SELL logika była już prawidłowa")
