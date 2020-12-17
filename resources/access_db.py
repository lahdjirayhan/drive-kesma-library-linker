from decouple import config
from cryptography.fernet import Fernet
from linebot.models import TextSendMessage

from .utils import Messenger
from .models import UserAuth

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
        p_enc = Fernet(config("FERNET_KEY").encode()).encrypt(p.encode()).decode()
        
        userauth = UserAuth.query.filter_by(user_id=user_id).first()
        if userauth is None:
            db.session.add(UserAuth(user_id, u, p_enc))
            db.session.commit()
            messenger.add_reply(TextSendMessage(
                "User added successfully!\n"
                "NRP: {u}\n"
                "Pass: {p}\n"
                "\n"
                "Delete the chats containing your authentication details "
                "because it is sensitive information and may be read accidentally "
                "by another person near you.".format(u=u, p=p)
            ))
        else:
            userauth.u = u
            userauth.p = p_enc
            db.session.commit()
            messenger.add_reply(TextSendMessage(
                "User details updated successfully!\n"
                "NRP: {u}\n"
                "Pass: {p}\n"
                "\n"
                "Delete the chats containing your authentication details "
                "because it is sensitive information and may be read accidentally "
                "by another person near you.".format(u=u, p=p)
            ))
        
    elif keyword == KEYWORD_DEAUTHORIZE:
        UserAuth.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        messenger.add_reply(TextSendMessage(
            "User details deleted successfully!\n"
            "NRP: {u}\n"
            "Pass: {p}\n"
            "\n"
            "Delete the chats containing your authentication details "
            "because it is sensitive information and may be read accidentally "
            "by another person near you.".format(u=u, p=p)
        ))
    else:
        messenger.add_reply(TextSendMessage(
            "Error: command unknown"
        ))
    
    return messenger
