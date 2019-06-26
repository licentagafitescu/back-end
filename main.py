import json
import uuid
import base64
from flask_cors import CORS
import requests
from authlib.flask.client import OAuth
from flask import Flask, redirect, session, jsonify, request
from werkzeug.contrib.cache import SimpleCache

import repository
import prediction
import time

app = Flask(__name__)
app.config.from_pyfile("app.cfg")
CORS(app)
oauth = OAuth(app)
cache = SimpleCache()


def save_request_token(token):
    cache.set(session.get("current_user",""),token)



def fetch_request_token():
    token = cache.get(session.get("current_user", ""))
    return token


def fetch_flickr_token():
    token = repository.get_token_by_id(session.get("current_user", ""))
    return token


oauth.register(
    name='flickr',
    client_id=app.config['FLICKR_CLIENT_ID'],
    client_secret=app.config['FLICKR_CLIENT_SECRET'],
    request_token_url=app.config['FLICKR_REQUEST_TOKEN_URL'],
    request_token_params=app.config['FLICKR_REQUEST_TOKEN_PARAMS'],
    access_token_url=app.config['FLICKR_ACCESS_TOKEN_URL'],
    access_token_params=app.config['FLICKR_ACCESS_TOKEN_PARAMS'],
    authorize_url=app.config['FLICKR_AUTHORIZE_URL'],
    api_base_url=app.config['FLICKR_API_BASE_URL'],
    client_kwargs=None,
    save_request_token=save_request_token,
    fetch_request_token=fetch_request_token,
    fetch_token=fetch_flickr_token,
)


@app.route("/")
def hello():
    similar_words("church")
    return "A"


@app.route('/addImage', methods=['POST', 'GET'])
def addImage():
    user = request.json['user']
    session["current_user"] = user
    name = request.json['name']
    originalImage = request.json['file']
    option = request.json['option']
    image_labels = prediction.predict(originalImage)
    image_labels = [x[1] for x in image_labels if x[2] > 0.2]
    t = time.time()
    if option == 'Profile':
        cached = False
        returned_images = []
        for label in image_labels:
            cached_response = cache.get(label + "+me")
            if cached_response is not None:
                returned_images.extend(cached_response)
                cached = True
        if not cached:
            images = get_photos_of_contact("me")
            captioned_images = []
            for image in images:
                captioned_images.append(get_labels(image))
            returned_images = []
            for label in image_labels:
                print(similar_images(label, captioned_images, "me"))
                returned_images.extend(similar_images(label, captioned_images, "me"))
    elif option == 'Contacts':
        returned_images = similar_images_with_search(image_labels, "contacts")
    else:
        returned_images = similar_images_with_search(image_labels, "all")
    print(returned_images)
    data = {
        "labels": image_labels,
        "images": returned_images
    }
    print("Total timp: ", time.time() - t)
    return jsonify(json.dumps(data)), 200, {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
    }


def similar_images_with_search(image_labels, mode):
    searched_images = []
    cached = False
    returned_images = []
    for label in image_labels:
        cached_response = cache.get(label + "+" + mode)
        if cached_response is not None:
            returned_images.extend(cached_response)
            cached = True
    if not cached:
        for label in image_labels:
            searched_images = searched_images + search_photos(mode, label)
        captioned_images = []
        for image in searched_images:
            captioned_images.append(get_labels(image))
        returned_images = []
        for label in image_labels:
            returned_images.extend(similar_images(label, captioned_images, mode))
    return returned_images


@app.route("/login")
def login():
    user_id = uuid.uuid4()
    user_id = str(user_id)
    session["current_user"] = user_id
    redirect_uri = "http://localhost:5000/authorize"
    return oauth.flickr.authorize_redirect(redirect_uri)


@app.route('/authorize')
def authorize():
    token = oauth.flickr.authorize_access_token()
    repository.add_token(session.get("current_user", ""), token)
    redirect_url = "http://localhost:4200/#/login/"
    redirect_url = redirect_url + session.get("current_user", "")
    return redirect(redirect_url)


@app.route('/profile')
def flickr_profile():
    id = request.args.get('id')
    print(id)
    session["current_user"] = id
    profile = get_profile()
    profile_info = dict()
    iconfarm = profile.get("person", {}).get("iconfarm")
    iconserver = profile.get("person", {}).get("iconserver")
    nsid = profile.get("person", {}).get("nsid")
    name = profile.get("person", {}).get("realname", {}).get("_content", "")
    if int(iconserver) <= 0:
        buddyicon = "https://www.flickr.com/images/buddyicon.gif"
    else:
        buddyicon = "http://farm{}.staticflickr.com/{}/buddyicons/{}.jpg".format(iconfarm,
                                                                                 iconserver,
                                                                                 nsid)
    profile_info["name"] = name
    profile_info["buddyicon"] = buddyicon
    return jsonify(json.dumps(profile_info)), 200, {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
    }


def get_profile():
    request_url = app.config["FLICKR_API_BASE_URL"] + "rest?"
    parameters = dict()
    parameters["method"] = "flickr.people.getInfo"
    parameters["nojsoncallback"] = 1
    parameters["format"] = "json"
    parameters["api_key"] = app.config["FLICKR_CLIENT_ID"]
    parameters["user_id"] = repository.get_token_by_id(session["current_user"]).get("user_nsid", "")
    resp = requests.get(request_url, parameters)
    return resp.json()


def get_photos_of_contact(contact):
    api_key = app.config["FLICKR_CLIENT_ID"]
    method = "flickr.people.getPhotos"
    response_format = "json"
    request_url = "rest?method={}&api_key={}&user_id={}&format={}&nojsoncallback={}".format(method, api_key, contact,
                                                                                            response_format, 1)
    response = oauth.flickr.get(request_url).json()
    photo_list = []
    for photo in response.get("photos", {}).get("photo", []):
        photo_list.append(photo_to_url(photo))
    return photo_list


def search_photos(mode, text):
    api_key = app.config["FLICKR_CLIENT_ID"]
    method = "flickr.photos.search"
    media = "photos"
    sort = "relevance"
    response_format = "json"
    if mode == "me":
        request_url = "rest?method={}&api_key={}&format={}&nojsoncallback={}" \
                      "&text={}&user_id={}&media={}&sort={}".format(method,
                                                                    api_key,
                                                                    response_format,
                                                                    1,
                                                                    text,
                                                                    mode,
                                                                    media,
                                                                    sort)
    elif mode == "contacts":
        request_url = "rest?method={}&api_key={}&format={}&nojsoncallback={}" \
                      "&text={}&contacts={}&media={}&sort={}".format(method,
                                                                     api_key,
                                                                     response_format,
                                                                     1,
                                                                     text,
                                                                     "all",
                                                                     media,
                                                                     sort)
    else:
        request_url = "rest?method={}&api_key={}&format={}&nojsoncallback={}" \
                      "&text={}&media={}&sort={}".format(method,
                                                         api_key,
                                                         response_format,
                                                         1,
                                                         text,
                                                         media,
                                                         sort)
    response = oauth.flickr.get(request_url).json()
    photo_list = []
    for photo in response.get("photos", {}).get("photo", []):
        photo_list.append(photo_to_url(photo))
    print(len(photo_list))
    return photo_list


def photo_to_url(photo):
    data = dict()
    data["farm-id"] = photo.get("farm", "")
    data["server-id"] = photo.get("server")
    data["id"] = photo.get("id")
    data["secret"] = photo.get("secret")
    photo_url = "https://farm{farm-id}.staticflickr.com/{server-id}/{id}_{secret}.jpg".format(**data)
    return photo_url


def get_labels(image):
    response = requests.get(image)
    response = response.content
    response = base64.b64encode(response).decode()
    labels = prediction.predict(response)
    labels = [x[1] for x in labels if x[2] > 0.2]
    return (image, labels)


def similar_images(label, image_list, mode):
    similar_images = set()
    for image, labels in image_list:
        if label in labels:
            similar_images.add(image)
    similar_images = list(similar_images)
    cache.set(label + "+" + mode, similar_images, timeout=3 * 60 * 60)
    return similar_images


def similar_words(label):
    if ' ' in label:
        label.replace(" ", "+")
    url = "https://api.datamuse.com/words?rel_syn=" + label
    response = requests.get(url).json()
    similar_words = []
    for word_structure in response:
        similar_words.append(word_structure["word"])
    if len(similar_words) > 3:
        similar_words = similar_words[0:3]
    return similar_words


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=5000)
