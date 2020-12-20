# Selenium-related custom exceptions:
class LoginFailedError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__("Login to presensi ITS failed.")

class CourseNotFoundError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__("Course with name specified was not found.")
        
class ScheduleNotFoundError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__("No schedule with today's date.")

class TodayEntryAttendedError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__("Today's entry has been attended.")

class TodayEntryNotActionableError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__("Today's entry is neither HADIR or ALPA.")

class NoUnattendedEntryError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__("All entries are already HADIR.")

class WrongSpecificationError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__("A misspecification of matkul and/or absen happened.")

# Flask-SQLAlchemy-related custom exceptions:
class AuthorizationRetrievalError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__("Something wrong with retrieving the authorization from database.")