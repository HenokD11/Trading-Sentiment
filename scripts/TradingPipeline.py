import pandas as pd
import numpy as np
from tensorflow.keras.callbacks import EarlyStopping, CSVLogger
import ccxt
import random
# reproducible 
np.random.seed(42)
random.seed(42)

import sys, os
sys.path.insert(0, '../scripts/')

from trade_old import Trading, Trader
from trader_model import LSTMModel
from DataPreprocessor import DataPreprocessor

csv_logger = CSVLogger('logs/training.log', append=True, separator=',')

callbacks=[EarlyStopping(monitor='val_loss', patience=3, mode='min'), csv_logger]

exchange = ccxt.binance()

# Step 1: Fetch the data
trading = Trading(exchange=exchange, symbol='BTC/USDT', timeFrame='5m', limit=1000)
trading.get_data(from_date='2022-07-21 00:00:00')
print("Data fetched successfully")


# Step 2: Preprocess the data
preprocessor = DataPreprocessor(trading.df, time_steps=30, test_size=0.15, val_size=0.1765)
preprocessor.preprocess()
print("Data preprocessed successfully")


# Step 3: Train the model
input_shape = (16, 30, 3)  # (batch_size, time_steps, input_dim)
output_shape = (16, 30, 1)  # (batch_size, time_steps, output_dim)

model = LSTMModel(input_shape=input_shape, output_shape=output_shape)
history = model.model.fit(preprocessor.train['X'], preprocessor.train['y'], epochs=10, batch_size=16, callbacks=callbacks, shuffle=False, validation_data=(preprocessor.val['X'], preprocessor.val['y']))
# model.train(preprocessor.train['X'], preprocessor.train['y'], preprocessor.val['X'], preprocessor.val['y'])

# evaluate the model on the test set
test_loss, test_accuracy = model.evaluate(preprocessor.test['X'], preprocessor.test['y'])

# print the test loss and accuracy
print('Test loss:', test_loss)
print('Test accuracy:', test_accuracy)

# Save the entire model
model.model.save('../model/{from_date}-Lstm_autoencoder.h5')
print("Model trained and saved successfully")
