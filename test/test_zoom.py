from test.conftest import GROUP_ID, REGISTERED_USER_ID, UNREGISTERED_USER_ID, reply_list_is_valid

def test_no_credential_in_db(app):
    """
    GIVEN user has no credentials stored in db
    WHEN user asks for zoom finding
    THEN app replies with "Failed to retrieve authorization from database" ish
    """
    # GIVEN
    USER_ID = UNREGISTERED_USER_ID
    
    # WHEN
    reply = app.config['MASTERMIND'].query_reply("zoom ansur", USER_ID, GROUP_ID)

    # THEN
    assert reply_list_is_valid(reply)
    
    elem = '\n\n\n'.join(reply)
    assert all([keyword in elem.lower() for keyword in ['failed', 'authorization']])

def test_no_course_name(app):
    """
    WHEN user asks for zoom course list (chat without specifying course)
    THEN app replies with zoom course list
    """
    # GIVEN
    # Any system state, actually
    USER_ID = UNREGISTERED_USER_ID

    # WHEN
    reply = app.config['MASTERMIND'].query_reply("zoom", USER_ID, GROUP_ID)

    # THEN
    assert reply_list_is_valid(reply)

    elem = "\n\n\n".join(reply)
    assert all([keyword in elem for keyword in ['abbreviation', 'course', 'known']])

def test_invalid_course_name(app):
    """
    GIVEN user is registered in db
    WHEN user asks for zoomfinding but with an invalid course name
    THEN app replies with course not recognized message
    """
    # GIVEN
    USER_ID = REGISTERED_USER_ID

    # WHEN
    reply = app.config['MASTERMIND'].query_reply("zoom invalidcoursename", USER_ID, GROUP_ID)
    
    # THEN
    assert reply_list_is_valid(reply)

    elem = "\n\n\n".join(reply)
    assert "not recognized" in elem

def test_valid_course_name(app, mocker):
    """
    GIVEN user is registered
    WHEN user asks to find zoom for a valid course name
    THEN app should go run selenium
    """
    # mock the zoom-finding API
    mocked_run_find_zoom_link = mocker.patch(
        'application.zoom.zoom.run_find_zoom_link',
        return_value=["SUCCESS, THIS IS MOCK REPLY"]
    )

    # GIVEN
    USER_ID = REGISTERED_USER_ID

    # WHEN
    reply = app.config['MASTERMIND'].query_reply("zoom statof", USER_ID, GROUP_ID)
    
    # THEN
    assert reply_list_is_valid(reply)

    elem = "\n\n\n".join(reply)
    assert "SUCCESS" in elem

    mocked_run_find_zoom_link.assert_called_once()