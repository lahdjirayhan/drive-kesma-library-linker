from typing import Any, List, Tuple
from application.attendance import absen_from_line
from application.auth import access_database_from_line
from application.zoom import find_zoom_link_from_line
from application.drive_linker import browse_library_from_line

class Mastermind:
    """
    Temporary docstring:

    Mastermind is an entity that holds business logic, i.e.
    LINE bot gets a chat -> LINE bot 'asks' Mastermind what to do about it ->
    Mastermind processes the chat -> Mastermind tells LINE bot what to say back
    LINE bot replies to user.

    Permissions/capabilities:
    - Drive instance (yes), to obtain e-book links
    - Database access (yes), to do zoomfinding and attendance
    - Reply/bot control (no), only provides replies in form of list of str/dict
    """
    def __init__(self, drive, db):
        self.drive = drive
        self.db = db
        self.identifiers = [
            "auth", "deauth",
            "absen",
            "zoom",
            "ebook", "soal"
        ]
    
    def query_reply(self, received_text: str, user_id: str, group_id: str) -> List:
        key, rest_of_the_chat = self._preprocess_split_to_keyword_and_argument(received_text)
        if key == "absen":
            return absen_from_line(rest_of_the_chat, user_id)
        if key in ["auth", "deauth"]:
            return access_database_from_line(key, self.db, user_id)
        if key == "zoom":
            return find_zoom_link_from_line(rest_of_the_chat, user_id)
        if key in ['ebook', 'soal']:
            if rest_of_the_chat == '':
                return browse_library_from_line(self.drive, key, None, user_id)
            return browse_library_from_line(self.drive, key, rest_of_the_chat, user_id)

        return []
    
    def _preprocess_split_to_keyword_and_argument(self, text: str) -> Tuple[Any, Any]:
        """Splits text into keyword and argument
        Checks if first word is keyword identifier.
        If yes, return key and argument
        If no, return None and None
        """
        stripped_text = text.strip()
        key, _, argument = stripped_text.partition(" ")
        if key in self.identifiers:
            return key, argument
        return None, None
