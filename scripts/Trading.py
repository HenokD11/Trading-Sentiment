import pandas as pd
import pandas_ta as ta
from datetime import datetime
import os

class Trading:

    def __init__(self, exchange, symbol, timeFrame, limit):
        self.exchange = exchange
        self.symbol = symbol
        self.timeFrame = timeFrame
        self.limit = limit
        self.df = pd.DataFrame()

    def get_data(self):
        # Fetch historical OHLCV data
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeFrame, limit=self.limit)
        self.df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        # Convert timestamp to datetime and set as index
        self.df['time'] = pd.to_datetime(self.df['timestamp'], unit='ms')

        # Calculate indicators
        self.df['sma15'] = self.df['close'].rolling(window=15).mean()
        self.df['sma60'] = self.df['close'].rolling(window=60).mean()
        self.df['rsi'] = ta.momentum.RSIIndicator(self.df['close'].values, 14)

class Trader:

    def __init__(self, starting_capital, name):
        self.name = name
        self.timegenerated = datetime.now().strftime("%Y%m%d-%H%M%S")

        self.starting_capital = starting_capital
        self.capital = starting_capital
        self.trades = pd.DataFrame(
            columns=[
                'Trade ID',
                'Actif',
                'Timestamp',
                'Trade',
                'Price',
                'Nombre',
                'Capital',
                'Type',
                'Name'])
        self.trades1 = pd.DataFrame(
            columns=[
                'Trade ID',
                'Actif',
                'Type',
                'Timestamp Entry',
                'Price',
                'Nombre',
                'Timestamp Exit',
                'Price',
                'Capital',
                'Name'])
        self.nb = 0.
        self.actif = 0.
        self.pActif = starting_capital
        self.lastAction = "Close"
        self.posPrice = 0
        self.pos = 0
        self.trade = pd.DataFrame()
        self.tradeID = 1

    def calculate_statistics(self):
        long_count = 0
        short_count = 0
        long_capital = 0
        short_capital = 0
        overall_profit_loss = 0
        print(self.name)
        print(self.trades)

        for x, trade in self.trades.iterrows():
            #print ("X : " + str(x) + " Trader : " + self.name)
            if (trade['Type'] == "Long"):
                long_count += 1
                long_capital += trade['Capital'] + trade['Actif']

            if (trade['Type'] == "Short"):
                short_count += 1
                short_capital += trade['Capital'] + trade['Actif']
        overall_profit_loss = long_capital + short_capital

        statistics = {
            'Trader': self.name,
            'long_count': long_count,
            'short_count': short_count,
            'long_capital': long_capital,
            'short_capital': short_capital,
            'profit_loss': overall_profit_loss
        }

        return statistics

    def writeTrade(self, tradeID, actif, timestamp, dir, price, nb, capital, type):
        self.trade = {
            'Trade ID': tradeID,
            'Actif': actif,
            'Timestamp': timestamp,
            'Trade': dir,
            'Price': price,
            'Nombre': nb,
            'Capital': capital,
            'Type': type,
            'Name': self.name
            }
        self.trades = self.trades.append(self.trade, ignore_index=True)

    def writeTrade1(self, tradeID, actif, direction, timestamp_entry, price_entry, nb, timestamp_exit, price_exit, capital):
        self.trade = {
            'Trade ID': tradeID,
            'Actif': actif,
            'Direction': direction,
            'Timestamp Entry': timestamp_entry,
            'Price Entry': price_entry,
            'Nombre': nb,
            'Timestamp Exit': timestamp_exit,
            'Price Exit': price_exit,
            'Capital': capital,
            'Name': self.name
        }
        self.trades1 = self.trades1.append(self.trade, ignore_index=True)

    def enter_trade(self, direction, price):
        if direction == "Long":
            self.pos = self.capital / price
            self.posPrice = price
            self.capital = 0
            self.lastAction = "Enter Long"
            self.nb = self.pos
            self.actif = self.pos * price

        elif direction == "Short":
            self.pos = -self.capital / price
            self.posPrice = price
            self.capital = 0
            self.lastAction = "Enter Short"
            self.nb = -self.pos
            self.actif = -self.pos * price

        self.writeTrade(self.tradeID, self.actif, direction, datetime.now(), price, self.nb, self.capital, "Entry")
        self.tradeID += 1

    def exit_trade(self, direction, price):
        if direction == "Long":
            capital = self.pos * price
            profit = capital - self.actif
            self.capital = self.capital + capital
            self.lastAction = "Exit Long"
            self.pos = 0
            self.posPrice = 0
            self.nb = 0
            self.actif = 0

        elif direction == "Short":
            capital = -self.pos * price
            profit = capital + self.actif
            self.capital = self.capital + capital
            self.lastAction = "Exit Short"
            self.pos = 0
            self.posPrice = 0
            self.nb = 0
            self.actif = 0

        self.writeTrade(self.tradeID, capital, direction, datetime.now(), price, self.nb, self.capital, "Exit")
        self.writeTrade1(self.tradeID, capital, direction, self.trades.tail(1)['Timestamp'].values[0],
                        self.trades.tail(1)['Price'].values[0], self.nb, datetime.now(), price, self.capital)
        self.tradeID += 1

    def strategy(self, df):
        for index, row in df.iterrows():
            if self.pos == 0:
                if row['sma15'] > row['sma60'] and row['rsi'] > 50:
                    self.enter_trade("Long", row['close'])
                elif row['sma15'] < row['sma60'] and row['rsi'] < 50:
                    self.enter_trade("Short", row['close'])

            elif self.pos > 0:
                if row['sma15'] < row['sma60'] and row['rsi'] < 50:
                    self.exit_trade("Long", row['close'])

            elif self.pos < 0:
                if row['sma15'] > row['sma60'] and row['rsi'] > 50:
                    self.exit_trade("Short", row['close']) 


               
