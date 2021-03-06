import time
from io import BytesIO

import numpy as np
import base64
import tensorflow as tf
from keras.applications.nasnet import NASNetMobile
from keras.applications.nasnet import preprocess_input, decode_predictions
from keras.preprocessing import image

global model, graph
model = NASNetMobile(weights="imagenet")
graph = tf.get_default_graph()


def predict(image_response):
    image_response = base64.b64decode(image_response)
    t = time.time()
    img = image.load_img(BytesIO(image_response), target_size=(224, 224))
    img = image.img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img = preprocess_input(img)

    with graph.as_default():
        preds = model.predict(img)
        print(time.time() - t)
        # decode the results into a list of tuples (class, description, probability)
        # (one such list for each sample in the batch)
        print(decode_predictions(preds))
        return decode_predictions(preds,top=3)[0]