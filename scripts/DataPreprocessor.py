from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import numpy as np


class DataPreprocessor:

    def __init__(self, df, time_steps=30, test_size=0.15, val_size=0.1765):
        self.df = df
        self.time_steps = time_steps
        self.test_size = test_size
        self.val_size = val_size
        self.train = None
        self.val = None
        self.test = None
        self.scaler = MinMaxScaler()

    def preprocess(self):
        df_ml = self.df.drop(['timestamp', 'open', 'high', 'low', 'volume', 'day_of_week', 'hour_of_day', 'rsi'],axis=1)

        # Fill missing values with the mean
        df_ml['close'].fillna(df_ml['close'].mean(), inplace=True)
        df_ml['sma15'].fillna(df_ml['sma15'].mean(), inplace=True)
        df_ml['sma60'].fillna(df_ml['sma60'].mean(), inplace=True)

        # Split the data into train and test sets
        train_val, test = train_test_split(df_ml, test_size=self.test_size, shuffle=False)

        # Split the remaining data into train and validation sets
        train, val = train_test_split(train_val, test_size=self.val_size, shuffle=False)

        # Scale the data
        self.scaler.fit(train[['close', 'sma15', 'sma60']])
        train[['close_scaled', 'sma15_scaled', 'sma60_scaled']] = self.scaler.transform(train[['close', 'sma15', 'sma60']])
        val[['close_scaled', 'sma15_scaled', 'sma60_scaled']] = self.scaler.transform(val[['close', 'sma15', 'sma60']])
        test[['close_scaled', 'sma15_scaled', 'sma60_scaled']] = self.scaler.transform(test[['close', 'sma15', 'sma60']])

        # Create sequences for the input and output variables
        X_train, y_train = self.create_sequences(train[['close_scaled', 'sma15_scaled', 'sma60_scaled']], train['close_scaled'])
        X_val, y_val = self.create_sequences(val[['close_scaled', 'sma15_scaled', 'sma60_scaled']], val['close_scaled'])
        X_test, y_test = self.create_sequences(test[['close_scaled', 'sma15_scaled', 'sma60_scaled']], test['close_scaled'])

        # Reshape the data
        X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], X_train.shape[2])
        X_test = X_test.reshape(X_test.shape[0], X_test.shape[1], X_test.shape[2])
        X_val = X_val.reshape(X_val.shape[0], X_val.shape[1], X_val.shape[2])

        self.train = {'X': X_train, 'y': y_train}
        self.val = {'X': X_val, 'y': y_val}
        self.test = {'X': X_test, 'y': y_test}

    def create_sequences(self, X, y):
        Xs, ys = [], []
        for i in range(len(X) - self.time_steps):
            Xs.append(X.iloc[i:(i + self.time_steps), :].values)
            ys.append(y.iloc[i + self.time_steps])
        return np.array(Xs), np.array(ys)
