import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dropout, RepeatVector, TimeDistributed, Dense

class LSTMModel:
    def __init__(self, input_shape, output_shape, learning_rate=0.0001, epsilon=1e-08, decay=0.01):
        self.input_shape = input_shape
        self.output_shape = output_shape
        self.learning_rate = learning_rate
        self.epsilon = epsilon
        self.decay = decay
        self.model = self.build_model()

    def build_model(self):
        model = Sequential()
        model.add(LSTM(128, input_shape=(self.input_shape[1], self.input_shape[2])))
        model.add(Dropout(rate=0.2))

        model.add(RepeatVector(self.output_shape[1]))
        model.add(LSTM(128, return_sequences=True))

        model.add(Dropout(rate=0.2))
        model.add(TimeDistributed(Dense(self.output_shape[2])))

        learning_rate_fn = tf.keras.optimizers.schedules.ExponentialDecay(

            initial_learning_rate=self.learning_rate,
            decay_steps=10000,
            decay_rate= self.decay,
            staircase=True
            
        )

        optimizer = tf.optimizers.Adam(learning_rate=learning_rate_fn)

        model.compile(optimizer=optimizer, loss='mae')
        model.summary()
        return model