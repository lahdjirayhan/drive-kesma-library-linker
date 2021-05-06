import pytest
from test.conftest import GROUP_ID, UNREGISTERED_USER_ID, reply_list_is_valid

@pytest.mark.parametrize("received_chat, texts_that_should_exist",
[
    ("soal", ["1. ", "pengantar metode statistika"]), # Checking numbers and a valid/verified course name
    ("soal 1", ['drive.google.com', ".pdf"]),
    ("soal 0", ['invalid folder number']),
    ("soal 1000", ['invalid folder number'])
])
def test_soal(app, received_chat, texts_that_should_exist):
    """
    WHEN user chat received_chat (parametrized)
    THEN app should give user the appropriate reply (parametrized as well)
    """
    # GIVEN
    USER_ID = UNREGISTERED_USER_ID

    # THEN
    reply = app.config["MASTERMIND"].query_reply(received_chat, USER_ID, GROUP_ID)

    # THEN
    assert reply_list_is_valid(reply)

    elem = "\n\n\n".join(reply).lower()
    assert all([item in elem for item in texts_that_should_exist])