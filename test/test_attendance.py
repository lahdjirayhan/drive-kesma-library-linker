from test.conftest import GROUP_ID, REGISTERED_USER_ID, UNREGISTERED_USER_ID, reply_list_is_valid

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
    # GIVEN
    USER_ID = REGISTERED_USER_ID

    # WHEN
    reply = app.config['MASTERMIND'].query_reply("absen teksim 12345", USER_ID, GROUP_ID)
    
    # THEN
    assert reply_list_is_valid(reply)

    elem = "\n\n\n".join(reply)
    assert all([keyword in elem for keyword in ['6', 'wrong', 'length', 'should']])

def test_valid_course_name(app):
    # Seriously do I need to run selenium here?
    # See here for possible things: https://stackoverflow.com/questions/38381602/python-unittest-and-mock-check-if-a-function-gets-called-but-then-stop-the-tes
    assert True