from application.models import UserAuth, UserRegister
import os
import tempfile
import pathlib

import pytest

from application import create_app, db

# HELPER CONSTANTS, FOR USE IN TESTS
REGISTERED_USER_ID   = "U03Feb22Jul"
UNREGISTERED_USER_ID = "U01Jan01Jan"
GROUP_ID             = "C03May03May"

class TestConfiguration:
    "Test configuration, so I can configure the flask app in testing situations"
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    def __init__(self, uri):
        self.SQLALCHEMY_DATABASE_URI = uri

@pytest.fixture
def app():
    """This fixture yields an app instance
    
    not a client instance, because I would want to just test directly against
    mastermind query_reply, bypassing the webhook handling entirely.
    """
    # Making test database handle
    db_handle, db_path = tempfile.mkstemp(suffix=".db")
    db_uri = "sqlite:///" + db_path

    # Making testconfiguration object
    test_config_object = TestConfiguration(db_uri)
    
    # Making app instance
    app_instance = create_app(config_object=test_config_object)

    # Making tables, preparing database
    with app_instance.app_context():
        db.create_all()
        db.session.add(UserAuth(REGISTERED_USER_ID, "jumbled_username", "jumbled_password"))
        db.session.commit()

    try:
        # Yield app instance
        with app_instance.app_context():
            with app_instance.test_request_context(base_url="https://goddard-space-center.herokuapp.com", path="/callback"):
                yield app_instance
    finally:
        # Closing database handle, deleting all temporary files
        # Note to self: this finally block sometimes is not run. As to why, I don't / can't know for sure.
        # Generator function not destroyed is probably the cause.
        cleanup_drivelinker_path()
        os.close(db_handle)
        os.unlink(db_path)

def cleanup_drivelinker_path():
    """Helper function to wipe out drivelinker credentials after use"""
    drive_linker_path = pathlib.Path(__file__).parent.parent.joinpath("application/drive_linker")
    drive_linker_path.joinpath("mycreds.txt").unlink(missing_ok=True)
    drive_linker_path.joinpath("client_secrets.json").unlink(missing_ok=True)

def reply_list_is_valid(reply) -> bool:
    """Helper: asserts conditions for a valid reply list, and returns True if all asserts pass

    otherwise it will raise AssertionError somewhere in the way
    """
    # Reply has to be a list
    assert isinstance(reply, list)

    # Elements in reply has to be string (text) or dict (flex, image, idk for future use)
    assert all(isinstance(elem, str) for elem in reply if not isinstance(elem, dict))
    
    # I want to be able to assert this function
    return True