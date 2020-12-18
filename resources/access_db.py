from decouple import config
from linebot.models import TextSendMessage

from .utils import Messenger
from .utils import encrypt_fernet, decrypt_fernet, derive_key
from .models import UserAuth

# Flask-SQLAlchemy-related custom exceptions:
class AuthorizationRetrievalError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__("Something wrong with retrieving the authorization from database.")

KEYWORD_AUTHORIZE = "auth"
KEYWORD_DEAUTHORIZE = "deauth"

def access_database_from_line(unparsed_text, db, user_id):
    messenger = Messenger()
    try:
        splitlist = unparsed_text.split(" ", 2)
        keyword = splitlist[0]
        u = splitlist[1]
        p = splitlist[2]
    except IndexError as error:
        messenger.add_reply(TextSendMessage("Error: missing either NRP or password."))
        return messenger
    
    if keyword == KEYWORD_AUTHORIZE:
        # Add to database
        u_enc = encrypt_fernet(u, user_id)
        p_enc = encrypt_fernet(p, user_id)
        
        userauth = UserAuth.query.filter_by(user_id=user_id).first()
        if userauth is None:
            db.session.add(UserAuth(user_id, u_enc, p_enc))
            db.session.commit()
            messenger.add_reply(TextSendMessage(
                "User details added successfully!"
            ))
        else:
            userauth.u = u_enc
            userauth.p = p_enc
            db.session.commit()
            messenger.add_reply(TextSendMessage(
                "User details updated successfully!"
            ))
        
    elif keyword == KEYWORD_DEAUTHORIZE:
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
    userauth = UserAuth.query.filter_by(user_id=user_id).first()
    if userauth is None:
        raise AuthorizationRetrievalError
    
    u = decrypt_fernet(userauth.u, user_id)
    p = decrypt_fernet(userauth.p, user_id)
    return u, p