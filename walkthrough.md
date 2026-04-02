# Bank Nifty Algo Trading System (V2) Walkthrough

The Bank Nifty Algo V2 is a modular, price-action based trading system integrated with Zerodha Kite.

## System Architecture

The system is organized into several key modules for better maintainability and control:

- **Data Layer**: Fetches 5-minute candles and LTP from Zerodha.
- **Strategy Engine**: Implements the "Context + Level + Trigger + Confirmation" logic.
- **Risk Engine**: Enforces daily loss limits and trade caps.
- **Execution Layer**: Handles paper trading with exit monitoring (SL/Target).
- **Communication Layer**: Sends rich Telegram alerts and logs all signals/trades to CSV.

## Key Files

- [main.py](file:///Users/manojaaa/Desktop/Millionare! 2/BankNiftyV2/main.py): The entry point and 5-minute loop.
- [config.py](file:///Users/manojaaa/Desktop/Millionare! 2/BankNiftyV2/config.py): Strategy and Risk parameters.
- [engine.py](file:///Users/manojaaa/Desktop/Millionare! 2/BankNiftyV2/strategy/engine.py): Core signal logic.
- [paper.py](file:///Users/manojaaa/Desktop/Millionare! 2/BankNiftyV2/execution/paper.py): Paper trade management.

## How to Run

1. Ensure your [.env](file:///Users/manojaaa/Desktop/Millionare%21%202/TysonAlgo/.env) file has valid Kite credentials.
2. Install dependencies:
   ```bash
   pip install -r BankNiftyV2/requirements.txt
   ```
3. Run the system:
   ```bash
   chmod +x run_v2.sh
   ./run_v2.sh
   ```

## Trading Logic

- **Context**: Bullish if Price > VWAP, Bearish if Price < VWAP.
- **Chop Filter**: Skips trading if the range of the last 5 candles is too tight.
- **Trigger**: Dynamic scoring based on Engulfing patterns and Strong Candle Body.
- **Risk**: Halts trading for the day if loss exceeds ₹5000 or 3 trades are taken.

## Monitoring

Check Telegram for live signals and exit alerts. Detailed logs are available in:
- `BankNiftyV2/logs/signals.csv`
- `BankNiftyV2/logs/trades.csv`
