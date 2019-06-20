import time
from io import BytesIO

import numpy as np
import base64
import tensorflow as tf
from keras.models import load_model
from keras.applications.nasnet import preprocess_input, decode_predictions
from keras.preprocessing import image

global model, graph
model = load_model("model.h5")
graph = tf.get_default_graph()


def predict(image_response):
    image_response = base64.b64decode(image_response)
    t = time.time()
    img = image.load_img(BytesIO(image_response), target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)

    with graph.as_default():
        preds = model.predict(x)
        print(time.time() - t)
        # decode the results into a list of tuples (class, description, probability)
        # (one such list for each sample in the batch)
        print(decode_predictions(preds))
        return decode_predictions(preds,top=3)[0]