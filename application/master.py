from typing import Any, List, Tuple
from application.attendance import absen_from_line
from application.auth import access_database_from_line
from application.zoom import find_zoom_link_from_line
from application.drive_linker import browse_library_from_line

source_code_link = "https://github.com/lahdjirayhan/drive-kesma-library-linker"

MASTERMIND_GENERAL_HELP_STRING = f"""Hello! Here are what this bot can do:

1. RECORD YOUR ATTENDANCE
Using the keyword "absen", you can make this bot record your attendance in Presensi.

2. FIND YOUR CLASS ZOOM LINK
Using keyword "zoom", you can make this bot find your class' zoom link in Classroom.

3. PROVIDE LINKS TO PAST EXAMS AND E-BOOKS IN HIMASTA-ITS KESMA LIBRARY
Using keyword "ebook" and "soal", you will get direct download links of past exams and ebooks that are contained within HIMASTA-ITS Kesma Library.

NOTE: "absen" and "zoom" require your credentials.

4. REMEMBER YOUR CREDENTIALS
Using keyword "auth", you can tell this bot about your credentials. Using keyword "deauth", you can make this bot forgets your credentials.
Credentials are used to log in to Presensi and Classroom.

Further information may be found in this bot's source code:
{source_code_link}

Enjoy this bot's functionalities!
"""

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
            "ebook", "soal",
            "help"
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
        if key == "help":
            return [MASTERMIND_GENERAL_HELP_STRING]

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
