# General exception regarding incorrect argument specifications:
class WrongSpecificationError(Exception):
    def __init__(self, msg="A misspecification command happened.", *args, **kwargs):
        super().__init__(msg, *args, **kwargs)

# Selenium-related custom exceptions:
class LoginFailedError(Exception):
    def __init__(self, msg="Login to presensi ITS failed.", *args, **kwargs):
        super().__init__(msg, *args, **kwargs)

class CourseNotFoundError(Exception):
    def __init__(self, msg="Course with name specified was not found.", *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
        
class ScheduleNotFoundError(Exception):
    def __init__(self, msg="No schedule with today's date.", *args, **kwargs):
        super().__init__(msg, *args, **kwargs)

class TodayEntryAttendedError(Exception):
    def __init__(self, msg="Today's entry has been attended.", *args, **kwargs):
        super().__init__(msg, *args, **kwargs)

class TodayEntryNotActionableError(Exception):
    def __init__(self, msg="Today's entry is neither HADIR or ALPA.", *args, **kwargs):
        super().__init__(msg, *args, **kwargs)

class NoUnattendedEntryError(Exception):
    def __init__(self, msg="All entries are already HADIR.", *args, **kwargs):
        super().__init__(msg, *args, **kwargs)

# Flask-SQLAlchemy-related custom exceptions:
class AuthorizationRetrievalError(Exception):
    def __init__(self, msg="Failed to retrieve authorization from database.", *args, **kwargs):
        super().__init__(msg, *args, **kwargs)