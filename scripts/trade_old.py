import pandas as pd
import ta
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

    def get_data(self, from_date=None):
        if from_date:
            from_ts = self.exchange.parse8601(from_date)
            ohlcv_list = []
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeFrame, since=from_ts, limit=self.limit)
            ohlcv_list.append(ohlcv)
            while True:
                from_ts = ohlcv[-1][0]
                new_ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeFrame, since=from_ts, limit=self.limit)
                ohlcv.extend(new_ohlcv)
                if len(new_ohlcv) != self.limit:
                    break
            self.df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        else:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeFrame, limit=self.limit)
            self.df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        # Convert timestamp to datetime and set as index
        self.df['time'] = pd.to_datetime(self.df['timestamp'], unit='ms')
        # Create additional features
        self.df['day_of_week'] = self.df['time'].dt.day_of_week
        self.df['hour_of_day'] = self.df['time'].dt.hour

        # Calculate indicators
        self.df['sma15'] = self.df['close'].rolling(window=15).mean()
        self.df['sma60'] = self.df['close'].rolling(window=60).mean()
        self.df['rsi'] = ta.momentum.rsi(self.df['close'].values, 14)


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
        self.trades = pd.concat([self.trades, pd.DataFrame(self.trade, index=[0])])

        self.addTrade = pd.DataFrame(self.trade, index=[1])

        fileName = str('./results/' + self.timegenerated + "_" + self.name + "_" + 'Trade_stats.csv')

        if not os.path.isfile(fileName):
            self.addTrade.to_csv(fileName, mode='a', index=False, header=True)
        else:
            self.addTrade.to_csv(fileName, mode='a', index=False, header=False)

        return self.trade

    def long(self, price, timestamp):
        dir = "Long"
        if self.lastAction == "Short":
            self.close(price, timestamp, "Long")
            dir = "Short -> Long"
        if self.pos <= 0:
            self.nb = self.capital / price
            self.posPrice = price
            self.pActif = self.actif
            self.actif = self.capital
            self.capital = 0
            self.pos = 1
            self.lastAction = "Long"
            return self.writeTrade(
                self.tradeID,
                self.actif,
                timestamp,
                dir,
                price,
                self.nb,
                self.capital,
                self.lastAction
            )

    def short(self, price, timestamp):
        dir = "Short"
        if self.lastAction == "Long":
            self.close(price, timestamp, "Short")
            dir = "Long -> Short"
        if self.pos >= 0:
            self.nb = self.capital / price
            self.posPrice = price
            self.pActif = self.actif
            self.actif = self.capital
            self.capital = 0
            self.pos = -1
            self.lastAction = "Short"
            return self.writeTrade(
                self.tradeID,
                self.actif,
                timestamp,
                dir,
                price,
                self.nb,
                self.capital,
                self.lastAction
            )

    def close(self, price, timestamp, reverse):
        if self.nb > 0:
            if reverse == "Long":
                self.lastAction = "Reverse Long"
                self.capital = self.actif + ((self.posPrice * self.nb) - (price * self.nb))
            if reverse == "Short":
                self.lastAction = "Reverse Short"
                self.capital = self.actif + ((price * self.nb) - (self.posPrice * self.nb))
            if reverse == "Close":
                if self.lastAction == "Long":
                    self.capital = self.actif + ((price * self.nb) - (self.posPrice * self.nb))
                if self.lastAction == "Short":
                    self.capital = self.actif + ((self.posPrice * self.nb) - (price * self.nb))
                self.lastAction = "Close"
            self.nb = 0
            self.pos = 0
            self.posPrice = 0
            self.pActif = self.actif
            self.actif = self.capital
            dir = "Close"
            self.tradeID = self.tradeID + 1

            #print(self.calculate_statistics())
            return self.writeTrade(
                self.tradeID-1,
                self.actif,
                timestamp,
                dir,
                price,
                self.nb,
                self.capital,
                self.lastAction
            )

    def isAlive(self):
        if self.actif > 0 or self.capital > 0:
            return True
        else:
            return False

    def getReward(self, act):
        reward = 0
        if act == 0 or act == 1:
            # if self.lastAction == "Reverse Long" or self.lastAction == "Reverse Short":
            #     reward = self.actif - self.pActif

            reward = reward + 50
        if act == 2:
            if self.actif > self.pActif:
                reward = 125
            else:
                reward = -100
        #if reward != 50:
        #    print ('Reward : ' + str(reward))
        return reward
