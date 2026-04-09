# robo-advisor

A webpage showing the mNAV fluctuation over time (updated daily) for MSTR, the flagship DATCO. Daily Bitcoin valuation is pulled with CoinGecko API, and MSTR market cap pulled from Yahoo Finance with yfinance Python package.

Historical mNAV data is taken from [bitcoinquant.co](https://bitcoinquant.co/company/MSTR), daily Github Action pulls the aforementioned values and calculates new mNAV data.