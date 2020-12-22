import uuid
from linebot.models import TextSendMessage
from flask import url_for, request

from .utils import Messenger
from .utils import encrypt_fernet, decrypt_fernet
from .models import UserAuth, UserRegister
from .exceptions import AuthorizationRetrievalError

KEYWORD_AUTHORIZE = "auth"
KEYWORD_DEAUTHORIZE = "deauth"

# Helper functions so access_database can be generalized
def add_userauth(db, user_id, u, p):
    u_enc = encrypt_fernet(u, user_id)
    p_enc = encrypt_fernet(p, user_id)
    db.session.add(UserAuth(user_id, u_enc, p_enc))
    db.session.commit()

def update_userauth(db, user_id, u, p):
    user_auth = UserAuth.query.filter_by(user_id=user_id).first()
    user_auth.u = encrypt_fernet(u, user_id)
    user_auth.p = encrypt_fernet(p, user_id)
    db.session.commit()

def delete_userauth(db, user_id):
    UserAuth.query.filter_by(user_id=user_id).delete()
    db.session.commit()

def access_database_from_line(unparsed_text, db, user_id):
    messenger = Messenger()
    keyword = unparsed_text
    
    if keyword == KEYWORD_AUTHORIZE:
        # Generate link for authorization page
        m = str(uuid.uuid4())
        db.session.add(UserRegister(m, user_id))
        db.session.commit()

        link = request.url_root + url_for('authorize.authorize', secret_code=m)

        messenger.add_reply(TextSendMessage(
            "Please fill in this login form here to authenticate this bot to do your presensi:\n{}".format(link)
        ))
        
    elif keyword == KEYWORD_DEAUTHORIZE:
        # Remove from database
        UserAuth.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        messenger.add_reply(TextSendMessage(
            "User details deleted successfully!"
        ))
    else:
        messenger.add_reply(TextSendMessage(
            "Error: command unknown."
        ))
    
    return messenger

# Helper function to make it easier for the program to fetch credentials
def fetch_credentials(user_id):
    user_auth = UserAuth.query.filter_by(user_id=user_id).first()
    if user_auth is None:
        raise AuthorizationRetrievalError
    
    u = decrypt_fernet(user_auth.u, user_id)
    p = decrypt_fernet(user_auth.p, user_id)
    return u, p