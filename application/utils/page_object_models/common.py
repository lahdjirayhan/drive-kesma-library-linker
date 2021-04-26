# THIS FILE IS AN ATTEMPT TO REFORM absen.py IN drive-kesma-library-linker
# Instead of one gigantic/monolithic function, I am trying to use what is known as
# Page Object Model, i.e. there will be separate classes that represent
# LoginPage (presensi.its.ac.id), HomePage (presensi.its.ac.id after login),
# AttendanceListPage (presensi.its.ac.id/blahblahcourseidandwhatnot), and so on.

# I suspect that the operation which carries out ATTENDANCE will be familiarly known as
# "Testing", as if I'm testing the operationals of presensi.its.ac.id site. I suspect, and
# am not sure. It's counterintuitive as what I'm doing is not TESTING, but
# INTERACTING with the webpage while GUARANTEEING fail-safe mechanisms so that
# my web app don't crash.

# Note to self: at the time of writing (14th of April) the methods on these POMs don't have
# mechanism to catch NoSuchElementException, which is kinda expected to happen sooner or later,
# and when it happens, I don't want to be caught extremely off-guard. One way to handle this is to
# introduce Page Elements, i.e. making a button or form or div its own Page Element class.
# That way, I can override the .find_element() method to incorporate a simple try-catch block
# along with some boolean return value. The current implementation only make classes for pages,
# not page elements. Relevant reference for this approach might include (please read hard, don't skim):
# https://selenium-python.readthedocs.io/page-objects.html
# https://www.maestralsolutions.com/using-custom-web-element-models-in-selenium-testing-framework/
# Alternative solution: wrap run_attendance to catch NoSuchElementException, see below.

import logging
import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.remote.remote_connection import LOGGER as selenium_logger
from urllib3.connectionpool import log as urllib3_logger

# Suppress selenium debug logs by elevating them to INFO level
selenium_logger.setLevel(logging.INFO)
urllib3_logger.setLevel(logging.INFO)

class BasePage(object):
    """
    Base class which all Page objects can inherit from.
    """

    def __init__(self, driver_instance, logger_instance, url):
        self.driver = driver_instance
        self.wait = WebDriverWait(self.driver, 5) # Note to self: enable configurable wait for use in local vs Heroku
        self.logger = logger_instance
        
        self.driver.get(url)
        self.prepare_selectors()
    
    def prepare_selectors(self):
        pass
    
    def fill_form_value(self, form_locator, text):
        form_field = self.driver.find_element(*form_locator)
        form_field.clear()
        form_field.send_keys(text)
    
    def click_button(self, button_locator):
        self.driver.find_element(*button_locator).click()
        
    def wait_until_presence_of_element_located(self, element_locator):
        try: self.wait.until(EC.presence_of_element_located(element_locator))
        except TimeoutException: return False
        return True
    
    def wait_until_title_contains(self, text):
        try: self.wait.until(EC.title_contains(text))
        except TimeoutException: return False
        return True
    
    def wait_until_element_clickable(self, element_locator):
        try: self.wait.until(EC.element_to_be_clickable(element_locator))
        except TimeoutException: return False
        return True
    
    def sleep(self, seconds=0.3):
        """Short time sleeping for waiting super-fast but not instantaneous operations."""
        time.sleep(seconds)

class LoginPage(BasePage):
    """
    Methods to operate in login page, i.e. my.its.ac.id/blahblah
    """
    def prepare_selectors(self):
        self.USERNAME_FORM = By.ID, 'username'
        self.NEXT_BUTTON   = By.ID, 'continue'
        self.PASSWORD_FORM = By.ID, 'password'
        self.SIGNIN_BUTTON = By.ID, 'login'
    
    def do_login(self, username, password, text_to_wait_in_title_to_confirm_login_success = "Dashboard"):
        self.fill_form_value(self.USERNAME_FORM, username)
        self.click_button(self.NEXT_BUTTON)
        self.fill_form_value(self.PASSWORD_FORM, password)
        self.click_button(self.SIGNIN_BUTTON)

        if (login_successful:= self.wait_until_title_contains(text_to_wait_in_title_to_confirm_login_success)):
            self.logger.info("Login successful.")
        else:
            self.logger.info("Login failed.")
        
        return login_successful

class DashboardPage(BasePage):
    """
    Methods to operate in dashboard page, i.e. right after login.

    Fortunately, presensi.its.ac.id and classroom.its.ac.id dashboards
    have almost exactly similar structure, so have this class in common.
    """
    def prepare_selectors(self):
        self.COURSE_LINKS = By.CSS_SELECTOR, "h5>a"
    
    def get_course_link(self, course_name):
        a_tags = self.get_potential_course_links()
        for entry in a_tags:
            if course_name in entry.text:
                self.logger.info("Course {} is found.".format(course_name))
                self.logger.debug((course_link := entry.get_attribute('href')))
                return course_link
        self.logger.info("Course {} is not found.".format(course_name))
        return None
    
    def get_potential_course_links(self):
        self.wait_until_presence_of_element_located(self.COURSE_LINKS)
        return self.driver.find_elements(*self.COURSE_LINKS)
