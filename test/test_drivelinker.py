from test.conftest import GROUP_ID, UNREGISTERED_USER_ID, reply_list_is_valid

def test_ebook_too_high_number(app):
    """
    WHEN user chat 'ebook' with too high of a number
    THEN app should tell user it's an error/unable to do that
    """
    # GIVEN
    USER_ID = UNREGISTERED_USER_ID

    # WHEN
    reply = app.config["MASTERMIND"].query_reply("ebook 1000", USER_ID, GROUP_ID)

    # THEN
    assert reply_list_is_valid(reply)

    elem = "\n\n\n".join(reply)
    assert "invalid folder number" in elem.lower()