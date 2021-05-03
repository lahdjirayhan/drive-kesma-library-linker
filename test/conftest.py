from application.auth.access_db import add_userauth
from application.models import db

import os
import tempfile
import pathlib

import pytest

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
def db_uri():
    """This fixture yields the temporary database URI"""
    db_handle, db_path = tempfile.mkstemp(suffix=".db")
    db_uri = "sqlite:///" + db_path
    yield db_uri
    os.close(db_handle)
    os.unlink(db_path)

@pytest.fixture
def app_instance(db_uri):
    """This fixture yields app instance without app context"""
    from application import create_app

    test_config_object = TestConfiguration(db_uri)
    app_instance = create_app(config_object=test_config_object)
    yield app_instance

@pytest.fixture
def app(app_instance):
    """This fixture yields an app instance
    
    not a client instance, because I would want to just test directly against
    mastermind query_reply, bypassing the webhook handling entirely.
    """
    # Making tables, preparing database
    with app_instance.app_context():
        db.create_all()
        add_userauth(db, REGISTERED_USER_ID, 'jumbled_username', 'jumbled_password')

    # Yield app instance with app and test request contexts (READY TO USE)
    with app_instance.app_context():
        with app_instance.test_request_context(base_url="https://goddard-space-center.herokuapp.com", path="/callback"):
            yield app_instance

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