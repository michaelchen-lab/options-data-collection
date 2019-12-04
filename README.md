# options-data-collection

This program collects end-of-day options data of all symbols daily. It collects data daily when NYSE closes each day.

- main.py --- Main program: Data collection; JSON parsing; outputting CSV file
- symbols.txt --- Contains all the symbols to collect options prices from
- tradier_sym_price.py --- Collects stock prices from tradier API
