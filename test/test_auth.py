from test.conftest import GROUP_ID, REGISTERED_USER_ID, UNREGISTERED_USER_ID, reply_list_is_valid
from application.models import UserAuth, UserRegister

def test_auth(app):
    """
    WHEN user asks for login link
    THEN app should:
        - create login link
        - associate a temporary UserRegister entry
        - send the login link to user
    """
    # GIVEN
    # any system state, but I will take unregistered user as default
    USER_ID = UNREGISTERED_USER_ID

    # WHEN 
    reply = app.config['MASTERMIND'].query_reply("auth", USER_ID, GROUP_ID)

    # THEN
    assert reply_list_is_valid(reply)

    elem = "\n\n\n".join(reply)
    assert all([keyword in elem for keyword in ['login form', 'http', 'goddard-space-center.herokuapp.com']])

    assert (user_register := UserRegister.query.filter_by(user_id=USER_ID).first()) is not None
    assert user_register.m in elem

def test_deauth_valid(app):
    """
    GIVEN a user has their credentials in database
    WHEN that user requests deauthorization
    THEN app should delete credentials and report that credentials has been deleted
    """
    # GIVEN
    USER_ID = REGISTERED_USER_ID

    # WHEN
    reply = app.config['MASTERMIND'].query_reply("deauth", USER_ID, GROUP_ID)

    # THEN
    assert reply_list_is_valid(reply)
    
    elem = "\n\n\n".join(reply)
    assert all([keyword in elem for keyword in ['detail', 'deleted']])

    assert UserAuth.query.filter_by(user_id=USER_ID).first() is None

def test_deauth_invalid(app):
    """
    GIVEN a user hasn't registered auth before at all
    WHEN that user tried to call deauth
    THEN app should tell them it has no credentials of it
    """
    # GIVEN
    USER_ID = UNREGISTERED_USER_ID

    # WHEN
    reply = app.config['MASTERMIND'].query_reply("deauth", USER_ID, GROUP_ID)

    # THEN
    assert reply_list_is_valid(reply)

    elem = "\n\n\n".join(reply)
    assert "failed" in elem