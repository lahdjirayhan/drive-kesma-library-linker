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
from datetime import datetime, timedelta
from babel.dates import format_date

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
    Methods to operate in login page (my.its.ac.id/blahblah) is all here.
    """
    def prepare_selectors(self):
        self.USERNAME_FORM = By.ID, 'username'
        self.NEXT_BUTTON   = By.ID, 'continue'
        self.PASSWORD_FORM = By.ID, 'password'
        self.SIGNIN_BUTTON = By.ID, 'login'
    
    def do_login(self, username, password):
        self.fill_form_value(self.USERNAME_FORM, username)
        self.click_button(self.NEXT_BUTTON)
        self.fill_form_value(self.PASSWORD_FORM, password)
        self.click_button(self.SIGNIN_BUTTON)
        
        login_successful = self.wait_until_title_contains('Dashboard')

        if login_successful:
            self.logger.info("Login successful.")
        else:
            self.logger.info("Login failed.")
        
        return login_successful

class DashboardPage(BasePage):
    """
    Methods to operate in dashboard page, i.e. presensi.its.ac.id after login.
    """
    def prepare_selectors(self):
        self.COURSE_LIST_ELEMENT = By.TAG_NAME, 'li'
    
    def get_course_link(self, course_name):
        self.sleep()
        list_of_li_elements = self.driver.find_elements(*self.COURSE_LIST_ELEMENT)
        for entry in list_of_li_elements:
            if course_name in entry.find_element(By.TAG_NAME, 'a').text:
                self.logger.info("Course {} is found.".format(course_name))
                self.logger.debug((course_link := entry.find_element(By.TAG_NAME, 'a').get_attribute('href')))
                return course_link
        self.logger.info("Course {} is not found.".format(course_name))
        return None

class TimetablePage(BasePage):
    """
    Methods to operate in timetable page, i.e. course-specific presensi, go here.
    """
    def prepare_selectors(self):
        self.KODE_PRESENSI_FORM = By.ID, 'kode_akses_mhs'
        self.SIMPAN_BUTTON = By.ID, 'submit-hadir-mahasiswa'
        self.ISI_PRESENSI_HADIR_BUTTON = By.XPATH, './/*[contains(@data-target, "#modal-hadir")]'
        self.NOTIFICATION_DIV = By.XPATH, './/div[@role = "alert"]'

        self.TIMETABLE_TABLE = By.TAG_NAME, 'table'
        self.TIMETABLE_CHILD_ELEMENT_ROW = By.XPATH, './/tbody[@class !=""]'
        self.TIMETABLE_ROW_CHILD_ELEMENT_DATE = By.XPATH, './/tr/td[2]/p[1]'
        self.TIMETABLE_ROW_CHILD_ELEMENT_STATUS = By.XPATH, './/td[@class = "jenis-hadir-mahasiswa"]'
            
    def do_attendance(self, attendance_code):
        if not (entry := self.find_desired_timetable_entry()):
            return
        self.bring_up_widget(entry)
        self.fill_form_value(self.KODE_PRESENSI_FORM, attendance_code)
        self.click_button(self.SIMPAN_BUTTON)
        
        self.wait_until_presence_of_element_located(self.NOTIFICATION_DIV)
        notification_alert_text = self.driver.find_element(*self.NOTIFICATION_DIV).text.rsplit('\n', 2)[-1]
        self.logger.info(notification_alert_text)
        
    def find_desired_timetable_entry(self):
        if not self.wait_until_presence_of_element_located(self.TIMETABLE_TABLE):
            return None
        table = self.driver.find_element(*self.TIMETABLE_TABLE)
        
        course_entries = [(
            entry,
            entry.find_element(*self.TIMETABLE_ROW_CHILD_ELEMENT_DATE).text,
            entry.find_element(*self.TIMETABLE_ROW_CHILD_ELEMENT_STATUS).text
        ) for entry in table.find_elements(*self.TIMETABLE_CHILD_ELEMENT_ROW)]

        if (selected_entry := self.find_today_timetable_entry(course_entries)):
            if selected_entry.find_element(*self.TIMETABLE_ROW_CHILD_ELEMENT_STATUS).text.upper() == "ALPA":
                self.logger.info("Today's entry is ALPA, performing attendance on today's entry.")
            elif selected_entry.find_element(*self.TIMETABLE_ROW_CHILD_ELEMENT_STATUS).text.upper() == "HADIR":
                self.logger.info("Today's entry is already attended (HADIR).")
            else:
                self.logger.info("Today's entry is not actionable. It's neither HADIR nor ALPA.")
        elif (selected_entry := self.find_most_recent_unattended_timetable_entry(course_entries)):
            self.logger.info("Can't find entry with today's date, selecting latest ALPA entry.")
        else:
            self.logger.info("There is no entry marked as ALPA.")
        
        traversal_report_per_line = []
        for entry, date, status in course_entries:
            marker = '[X]' if entry == selected_entry else ''
            traversal_report_per_line.append(' '.join([marker, status, date, marker]).strip())
        
        traversal_report = '\n'.join(traversal_report_per_line)
        self.logger.info(traversal_report)
        return selected_entry

    def find_today_timetable_entry(self, course_entries):
        today_date = format_date(datetime.now() + timedelta(hours = 7), 'EEEE, d MMMM y', locale = 'id') # Note to self: configure time-zone compensation, don't hardcode
        for entry, date, _ in course_entries[::-1]:
            if date == today_date:
                return entry
        return None

    def find_most_recent_unattended_timetable_entry(self, course_entries):
        for entry, _, status in course_entries[::-1]:
            if status == 'ALPA':
                return entry
        return None

    def bring_up_widget(self, entry):
        entry.find_element(*self.ISI_PRESENSI_HADIR_BUTTON).click()
        self.wait_until_element_clickable(self.KODE_PRESENSI_FORM)
