====================== Backtest Set File Generator ======================

This tool reads your pair data and config, fills a MetaTrader-style .set template, and writes one output file per CSV row into the output folder.
Follow below steps to customize the output set file.

-------------------------------------------------------------------------------
1. Update trading pairs and Tip / Dip (pair_data.csv)
-------------------------------------------------------------------------------

Edit config/pair_data.csv (or the path set in csv_file inside config.yaml).

Required columns:
  Instrument   Trading symbol, e.g. NZDCAD (used in the output filename).
  Year         Calendar year for that row (used in the filename pattern).
  Tip (High)   Upper bound of the range for that pair/year (template: price high).
  Dip (Low)    Lower bound of the range for that pair/year (template: price low).

-------------------------------------------------------------------------------
2. Update config.yaml for main trading and risk parameters
-------------------------------------------------------------------------------
  spread
    Broker spread value(points in unit). You can use a string such as "15".

  open_order_buffer_pct
    Percent of the range (Tip minus Dip) kept as a buffer at each end of the band,
    which is used to computes open-buy and open-sell thresholds from Tip, Dip, 
    and this percentage. Example: 30 means 30% of the range is applied from the 
    dip side and from the tip side.

  equity_assumption
    Equity assumption (defaul 10000). Correlate with real equity to make a leverage.
    Equity assumption 20000 and real equity 10000 means 2X leverage.

  real_equity
    Real equity (defaul 10000)

  tep_var
    Take profit percentage. Backtest end when the profit reach this percentage.

  take_profit_ratio
    Percentage the SRM EA recorded as take profit point. Eg. Top Boundary (TB)
    is $100, buy-in price is $50, take profit ratio set as 2. SRM EA marks 
    (50+100*2%) = $52 as take profit point.

  pullback_ratio
    When take profit point has recorded, the percentage the SRM EA actually make
    a "take profit" action. Eg. Top Boundary (TB) is $100, $52 is the take profit
    point, pullback ratio is 1. When the price fall to (52-100*1%) = $51, EA take
    profit here.

  drop_ratio
    Percentage the SRM EA recorded as drop point. Eg. Top Boundary (TB) is $100,
    buy-in price is $50, drop ratio is 2. SRM EA marks (50-100*2%) = $48 as drop
    point.

  brounce_ratio
    When drop point has recorded, the percentage the SRM EA actually make a  
    "raise" action. Eg. Top Boundary (TB) is $100, $48 is the drop point, brounce 
    ratio is 1. When the price fall to (48+100*1%) = $48, EA raise money to 
    buy/sell more.

-------------------------------------------------------------------------------
3. Generate the .set files
-------------------------------------------------------------------------------

Double-click run.bat to generate the result set file.

Dependencies: Python 3 and PyYAML. Install once with:
  pip install -r requirements.txt

===============================================================================
