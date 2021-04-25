import sys
import timeit
import logging
import traceback
from datetime import timedelta
from selenium.common.exceptions import WebDriverException, NoSuchElementException

from application.utils.course import MATKUL_ABBREVIATIONS
from application.utils.log_handler import ListHandler
from application.utils.webdriver import build_driver
from application.auth.access_db import fetch_credentials
from application.exceptions import AuthorizationRetrievalError, WrongSpecificationError

from .absen_POM import LoginPage, DashboardPage, TimetablePage

module_logger = logging.getLogger(__name__)
module_logger.setLevel(logging.DEBUG)

def absen_from_line(unparsed_text, user_id):
    start_time = timeit.default_timer()
    message_list = []   
    try:
        course_name, attendance_code = preprocess_chat_absen(unparsed_text)
        username, password = fetch_credentials(user_id)
    except (WrongSpecificationError, AuthorizationRetrievalError) as error:
        module_logger.debug(str(error))
        message_list.append(str(error))
    else:
        reply = run_attendance(username, password, course_name, attendance_code, user_id)
        message_list.extend(reply)
    
    module_logger.info("Time elapsed in executing request: {}".format(str(timedelta(seconds = timeit.default_timer() - start_time))))
    return message_list

def preprocess_chat_absen(unparsed_text):
    try:
        splitlist = unparsed_text.split(' ', 1)
        matkul = splitlist[0]
        kode_absen = splitlist[1]
    except IndexError:
        raise WrongSpecificationError("Either missing course name or attendance code.")
    
    try:
        matkul_proper_name = MATKUL_ABBREVIATIONS[matkul]
    except KeyError:
        raise WrongSpecificationError("Course name ({}) is wrong or not recognized!".format(matkul))
    
    if not kode_absen.isnumeric():
        raise WrongSpecificationError("Attendance code ({}) should contain numbers only.".format(kode_absen))
    
    if len(kode_absen) != 6:
        raise WrongSpecificationError("Attendance code ({}) has wrong length. It should contain exactly 6 digits.".format(kode_absen))
    
    return matkul_proper_name, kode_absen

def run_attendance(username, password, course_name, attendance_code, user_id):
    message_list = []
    
    logger = logging.getLogger(__name__ + "." + user_id)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(ListHandler(message_list=message_list))
    
    try:
        _run_attendance(username, password, course_name, attendance_code, logger)
    except Exception:
        # The general idea of catching Exception here is to make sure
        # program does not break because of something that is related to
        # Selenium trying to do its job. This is a necessity, albeit one
        # might argue it's an evil one. Note to self: why not catch
        # WebDriverException instead?
        exc_type, exc_value, _ = sys.exc_info()

        # Is this good idea?
        if exc_type is NoSuchElementException:
            logger.error("NoSuchElementException encountered. This could be a signal that the webpage design has changed and provided selectors has been obsolete. The operation is likely failed.")
        elif isinstance(exc_value, WebDriverException):
            logger.error("The operation is likely failed due to a webdriver exception.")
        else:
            logger.error("The operation is likely failed due to an unspecified exception.")
        logger.debug(traceback.format_exc())
        
    return message_list

def _run_attendance(username, password, course_name, attendance_code, logger):
    login_link = 'https://presensi.its.ac.id'
    dashboard_link = 'https://presensi.its.ac.id/dashboard'

    with build_driver() as driver:
        login_page = LoginPage(driver, logger, login_link)
        login_failed = not login_page.do_login(username, password)
        if login_failed:
            return
        
        dashboard_page = DashboardPage(driver, logger, dashboard_link)
        course_name_not_found = not (timetable_link := dashboard_page.get_course_link(course_name))
        if course_name_not_found:
            return

        timetable_page = TimetablePage(driver, logger, timetable_link)
        timetable_page.do_attendance(attendance_code)

    return