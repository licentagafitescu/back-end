import os
import pickle

import numpy as np
from google.cloud import logging
from tensorflow.python.keras.applications.nasnet import  decode_predictions
import tensorflow as tf

class MyPredictor(object):
  def __init__(self, model, preprocessor):
    self._model = model
    self._preprocessor = preprocessor

  def predict(self, instances, **kwargs):
    inputs = np.asarray(instances)
    client = logging.Client()
    logger = client.logger('log_name')
    logger.log_text("input", inputs)
    preprocessed_inputs = self._preprocessor.preprocess(inputs)

    outputs = self._model.predict(preprocessed_inputs)
    return decode_predictions(outputs, top=3)[0]

  @classmethod
  def from_path(cls, model_dir):
    model_path = os.path.join(model_dir, 'model.h5')
    model = tf.keras.models.load_model(model_path)

    preprocessor_path = os.path.join(model_dir, 'preprocessor.pkl')
    with open(preprocessor_path, 'rb') as f:
      preprocessor = pickle.load(f)

    return cls(model, preprocessor)
