from pony.orm import *
import models as models


@db_session
def add_token(user_id, token):
    try:
        token_db = models.User[token.get("user_nsid", "")]
        token_db.user_id = user_id
        token_db.oauth_token = token.get("oauth_token", "")
        token_db.oauth_token_secret = token.get("oauth_token_secret", "")
        commit()
        return True
    except ObjectNotFound:
        oauth_token = token.get("oauth_token", "")
        oauth_token_secret = token.get("oauth_token_secret", "")
        user_nsid = token.get("user_nsid", "")
        username = token.get("username", "")
        fullname = token.get("fullname", "")
        token_db = models.User(user_id=user_id, user_nsid=user_nsid, username=username,
                               oauth_token=oauth_token,
                               oauth_token_secret=oauth_token_secret,
                               fullname=fullname)
        try:
            commit()
            return token_db.user_id
        except TransactionIntegrityError:
            return False


@db_session
def get_token(user_nsid):
    try:
        token_view = dict()
        token = models.User[user_nsid]
        token_view["fullname"] = token.fullname
        token_view["username"] = token.username
        token_view["oauth_token"] = token.oauth_token
        token_view["oauth_token_secret"] = token.oauth_token_secret
        token_view["user_nsid"] = token.user_nsid
    except ObjectNotFound:
        token_view = None
    return token_view


@db_session
def get_token_by_id(user_id):
    token = models.User.get(user_id=user_id)
    if token is not None:
        token_view = dict()
        token_view["fullname"] = token.fullname
        token_view["username"] = token.username
        token_view["oauth_token"] = token.oauth_token
        token_view["oauth_token_secret"] = token.oauth_token_secret
        token_view["user_nsid"] = token.user_nsid
        return token_view
    else:
        return None


models.generate_mappings()
