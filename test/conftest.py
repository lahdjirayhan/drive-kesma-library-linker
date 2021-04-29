import pytest
import pathlib

from application import create_app

@pytest.fixture
def app():
    app = create_app()
    yield app
    cleanup_drivelinker_path()

def cleanup_drivelinker_path():
    drive_linker_path = pathlib.Path(__file__).parent.parent.joinpath("application/drive_linker")
    drive_linker_path.joinpath("mycreds.txt").unlink(missing_ok=True)
    drive_linker_path.joinpath("client_secrets.json").unlink(missing_ok=True)