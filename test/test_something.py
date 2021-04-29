def test_no_keyword_chat(app):
    reply = app.config['MASTERMIND'].query_reply("^", "", "")

    assert isinstance(reply, list)
    assert len(reply) > 0
    assert all(isinstance(element, str) for element in reply)

def test_wrong_course_name(app):
    reply = app.config["MASTERMIND"].query_reply("^wrong_name", "", "")

    assert len(reply) > 0

    msg = reply[0]
    assert "not recognized" in msg