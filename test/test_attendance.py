from test.conftest import GROUP_ID, REGISTERED_USER_ID, UNREGISTERED_USER_ID, reply_list_is_valid

def test_no_credentials_in_db(app):
    """
    GIVEN user has no credentials stored in db
    WHEN user asks for attendance recording
    THEN app replies with "Failed to retrieve authorization from database" ish
    """
    # GIVEN
    USER_ID = UNREGISTERED_USER_ID
    
    # WHEN
    reply = app.config['MASTERMIND'].query_reply("absen ansur 123123", USER_ID, GROUP_ID)

    # THEN
    assert reply_list_is_valid(reply)
    
    elem = '\n\n\n'.join(reply)
    assert all([keyword in elem.lower() for keyword in ['failed', 'authorization']])

def test_no_course_name(app):
    """
    GIVEN user already has valid credentials in db
    WHEN user sends absen but without course name
    THEN app should send them list of possible course names and abbreviations
    """
    # GIVEN
    USER_ID = REGISTERED_USER_ID

    # WHEN
    reply = app.config['MASTERMIND'].query_reply("absen", USER_ID, GROUP_ID)

    # THEN
    assert reply_list_is_valid(reply)

    elem = "\n\n\n".join(reply)
    assert all([keyword in elem for keyword in ['abbreviation', 'course', 'known']])

def test_invalid_course_name(app):
    """
    GIVEN user already has valid credentials in db
    WHEN user sends absen with invalid/unknown course abbreviation
    THEN app should reply with appropriate unknown course error
    """
    # GIVEN
    USER_ID = REGISTERED_USER_ID

    # WHEN
    reply = app.config['MASTERMIND'].query_reply("absen invalidcoursename 123123", USER_ID, GROUP_ID)
    
    # THEN
    assert reply_list_is_valid(reply)

    elem = "\n\n\n".join(reply)
    assert "not recognized" in elem

def test_attendance_code_not_six_digits(app):
    """
    GIVEN user is registered
    WHEN user asks to record attendance but code is not six digits
    THEN app tells them error
    """
    # GIVEN
    USER_ID = REGISTERED_USER_ID

    # WHEN
    reply = app.config['MASTERMIND'].query_reply("absen teksim 12345", USER_ID, GROUP_ID)
    
    # THEN
    assert reply_list_is_valid(reply)

    elem = "\n\n\n".join(reply)
    assert all([keyword in elem for keyword in ['6', 'wrong', 'length', 'should']])

def test_valid_course_name(app, mocker):
    """
    GIVEN user is registered
    WHEN user asks to record attendance on valid course name
    THEN app should go run selenium
    """
    # mock the attendance recording API
    mocked_run_attendance = mocker.patch(
        'application.attendance.absen.run_attendance',
        return_value=["SUCCESS, THIS IS MOCK REPLY"]
    )

    # GIVEN
    USER_ID = REGISTERED_USER_ID

    # WHEN
    reply = app.config['MASTERMIND'].query_reply("absen teksim 123456", USER_ID, GROUP_ID)
    
    # THEN
    assert reply_list_is_valid(reply)

    elem = "\n\n\n".join(reply)
    assert "SUCCESS" in elem

    mocked_run_attendance.assert_called_once()
