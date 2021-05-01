import sys
import timeit
import logging
import traceback
from datetime import timedelta
from selenium.common.exceptions import WebDriverException, NoSuchElementException

from application.utils.course import COURSE_ABBREVIATION_HELP_STRING, MATKUL_ABBREVIATIONS
from application.utils.log_handler import ListHandler
from application.utils.webdriver import build_driver
from application.auth.access_db import fetch_credentials
from application.exceptions import AuthorizationRetrievalError, WrongSpecificationError

from application.utils.page_object_models import LoginPage, ClassroomDashboardPage, CourseHomePage

module_logger = logging.getLogger(__name__)
module_logger.setLevel(logging.DEBUG)

ZOOM_HELP_STRING = """This keyword is used to find zoom links in Classroom. To use, send this format:
zoom + (course abbreviation)

where course abbreviation is one of the known ones, listed as follows:

""" + COURSE_ABBREVIATION_HELP_STRING

def find_zoom_link_from_line(unparsed_text, user_id):
    start_time = timeit.default_timer()
    message_list = []
    
    if unparsed_text:
        try:
            course_name = preprocess_chat_zoom(unparsed_text)
            username, password = fetch_credentials(user_id)
        except (WrongSpecificationError, AuthorizationRetrievalError) as error:
            module_logger.debug(str(error))
            message_list.append(str(error))
        else:
            reply = run_find_zoom_link(username, password, course_name, user_id)
            message_list.extend(reply)
    else:
        message_list.append(ZOOM_HELP_STRING)
    
    module_logger.info("Time elapsed in executing request: {}".format(str(timedelta(seconds = timeit.default_timer() - start_time))))
    return message_list

def preprocess_chat_zoom(unparsed_text):
    try:
        course_name = unparsed_text
        course_proper_name = MATKUL_ABBREVIATIONS[course_name]
    except KeyError:
        raise WrongSpecificationError("Course name ({}) is wrong or not recognized!".format(course_name))
    
    return course_proper_name

def run_find_zoom_link(username, password, course_name, user_id):
    message_list = []

    logger = logging.getLogger(__name__ + "." + user_id)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(ListHandler(message_list=message_list))

    try:
        _run_find_zoom_link(username, password, course_name, logger)
    except Exception:
        exc_type, exc_value, _ = sys.exc_info()

        if exc_type is NoSuchElementException:
            logger.error("NoSuchElementException encountered. This could be a signal that the webpage design has changed and provided selectors has been obsolete. The operation is likely failed.")
        elif isinstance(exc_value, WebDriverException):
            logger.error("The operation is likely failed due to a webdriver exception.")
        else:
            logger.error("The operation is likely failed due to an unspecified exception.")
        logger.debug(traceback.format_exc())
        
    return message_list

def _run_find_zoom_link(username, password, course_name, logger):
    login_link = 'https://classroom.its.ac.id/auth/oidc'
    dashboard_link = 'https://classroom.its.ac.id/my'

    with build_driver() as driver:
        login_page = LoginPage(driver, logger, login_link)
        login_failed = not login_page.do_login(username, password)
        if login_failed:
            return
        
        dashboard_page = ClassroomDashboardPage(driver, logger, dashboard_link)
        course_name_not_found = not (course_page_link := dashboard_page.get_course_link(course_name))
        if course_name_not_found:
            return
        
        course_home_page = CourseHomePage(driver, logger, course_page_link)
        course_home_page.do_find_zoom_link()
    
    return
