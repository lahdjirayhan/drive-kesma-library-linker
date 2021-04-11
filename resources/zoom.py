import logging
import furl
import uuid
from decouple import config
import timeit
from datetime import datetime, timedelta
from babel.dates import format_date, format_time, format_datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from linebot.models import TextSendMessage
from .utils import Messenger
from .utils.course import MATKUL_ABBREVIATIONS, CLASSROOM_COURSE_TO_ID_DICT
from .access_db import fetch_credentials
from .exceptions import (
    AuthorizationRetrievalError,
    WrongSpecificationError
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# https://stackoverflow.com/questions/36408496/python-logging-handler-to-append-to-list
# Both answers combined
class ListHandler(logging.Handler):
    def __init__(self, *args, message_list, **kwargs):
        logging.Handler.__init__(self, *args, **kwargs)
        self.setFormatter(logging.Formatter('%(message)s'))
        self.message_list = message_list
    def emit(self, record):
        self.message_list.append(record.getMessage())

LOCAL_ENVIRONMENT = config('LOCAL_ENVIRONMENT', default=False, cast=bool)
GECKODRIVER_PATH = config('GECKODRIVER_PATH', default='', cast=str)
CHROMEDRIVER_PATH = config('CHROMEDRIVER_PATH', default='', cast=str)

LOGIN_WITH_MYITS_BUTTON = '//*[@title="Masuk dengan myITS"]'

USERNAME_FORM = '//*[@id="username"]'
NEXT_BUTTON = '//*[@id="continue"]'
PASSWORD_FORM = '//*[@id="password"]'
SIGNIN_BUTTON = '//*[@id="login"]'

JOIN_BUTTON = '//button[contains(text(), "Join Meeting")]'

class ClassroomZoomHandler:
    def __init__(self, course_id, username, password):
        # WEBDRIVER RELATED ATTRIBUTES
        self.local = LOCAL_ENVIRONMENT
        self.options = self.make_options()
        self.driver = None
        self.wait = None

        # ZOOM/CLASSROOM/COURSE RELATED ATTRIBUTES
        self.USERNAME = username
        self.PASSWORD = password
        self.LOGIN_LINK = "https://classroom.its.ac.id/auth/oidc"
        self.COURSE_HOME_LINK = "https://classroom.its.ac.id/course/view.php?id=" + str(course_id)
        self.potential_mod_zoom_links = []
        self.most_recent_zoom_link = "NO LINK"

        # LOGGING/LINE CHAT RELATED ATTRIBUTES
        self.message_list = []
        self.logger = None  # pylint is angry about some attributes not defined in init.
        self.setup_logger()

    def setup_logger(self):
        self.logger = logging.getLogger(__name__ + "." + str(uuid.uuid4()))
        self.logger.setLevel(logging.INFO) # DEBUG will print Selenium's debug logs, quite annoying
        self.logger.addHandler(ListHandler(message_list=self.message_list))
        # Side note regarding logging: Heroku logs already contain date and time.
        # Consider logging the logger name to identify and pin down bad things in the future.

        # Another side note regarding logging: How can I separate log level for LINE chat and for Heroku logs?
    
    def make_options(self):
        if self.local:
            op = webdriver.FirefoxOptions()
            op.add_argument("--disable-dev-shm-usage")
            op.add_argument("--no-sandbox")
        else:
            op = webdriver.ChromeOptions()
            op.add_argument('--headless')
            op.add_argument("--disable-dev-shm-usage")
            op.add_argument("--no-sandbox")
            op.binary_location = config("GOOGLE_CHROME_BIN")
        return op



    def start_webdriver(self):
        self.logger.info("Initializing webdriver.")
        if self.local:
            self.driver = webdriver.Firefox(executable_path=GECKODRIVER_PATH, options=self.options)
            self.wait = WebDriverWait(self.driver, 13)
        else:
            self.driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, options=self.options)
            self.wait = WebDriverWait(self.driver, 5)
        
        browser_name = self.driver.capabilities.get('browserName', 'NO_BROWSER_NAME').upper()
        browser_version = self.driver.capabilities.get('browserVersion', 'NO_BROWSER_VERSION')
        platform_name = self.driver.capabilities.get('platformName', 'NO_PLATFORM_NAME').upper()
        platform_version = self.driver.capabilities.get('platformVersion', 'NO_PLATFORM_VERSION')
        
        self.logger.info(
            "Webdriver initialized: {} {} on {} {}.".format(
                browser_name, browser_version, platform_name, platform_version
            )
        )
    
    def do_navigate_to_login_page_from_landing_page(self):
        # Not currently used because there's always an 'element click intercepted' error.
        try:
            self.wait.until(EC.element_to_be_clickable((By.XPATH, LOGIN_WITH_MYITS_BUTTON)))
        except TimeoutException:
            self.logger.error("Unable to load login page. Detail: LOGIN_WITH_MYITS_BUTTON not detected.")
            raise
        
        self.driver.find_element_by_xpath(LOGIN_WITH_MYITS_BUTTON).click()
        # Note to self: LOGIN_WITH_MYITS_BUTTON is either detected or not by wait.until
        # So find_element_by_xpath does not require catching NoSuchElementException

    def do_login(self):
        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, USERNAME_FORM)))
        except TimeoutException:
            self.logger.error("Unable to load login page. Detail: USERNAME_FORM not detected.")
            raise
        try:
            self.driver.find_element_by_xpath(USERNAME_FORM).clear()
            self.driver.find_element_by_xpath(USERNAME_FORM).send_keys(self.USERNAME)
            self.driver.find_element_by_xpath(NEXT_BUTTON).click()
            self.driver.find_element_by_xpath(PASSWORD_FORM).clear()
            self.driver.find_element_by_xpath(PASSWORD_FORM).send_keys(self.PASSWORD)
            self.driver.find_element_by_xpath(SIGNIN_BUTTON).click()
        except NoSuchElementException:
            self.logger.error("Unable to perform login. Detail: Unable to navigate login page using the provided XPATHs.")
            raise

    def get_potential_mod_zoom_links(self):
        potential_elements = self.driver.find_elements_by_partial_link_text("Zoom meeting")
        self.potential_mod_zoom_links = [(elem.get_attribute('href'), elem.text)
                                         for elem in potential_elements][::-1] # Reverse, most recent is first
        self.logger.info(
            "{} meetings found as potential candidate for actual Zoom link.".format(
                len(self.potential_mod_zoom_links)
            )
        )
    
    def get_most_recent_zoom_link_from_all_potentials(self):
        # main_window_handle = self.driver.current_window_handle
        for link, text in self.potential_mod_zoom_links:
            meeting_title = text.split("\n")[0]
            self.logger.info("Checking link for meeting: {}".format(meeting_title))
            self.driver.get(link)
            try:
                # self.wait.until(EC.presence_of_element_located((By.XPATH, JOIN_BUTTON))) # If not found, waits for 10 sec. Not nice. Redo.
                self.driver.find_element_by_xpath(JOIN_BUTTON).click()
                # https://stackoverflow.com/a/32580581/11316205
                # new_window_handle = next((i for i in self.driver.current_window_handle if i != main_window_handle), None)
                # new_window_handle = self.driver.window_handles[-1]
                # self.driver.switch_to.window(new_window_handle)
            except NoSuchElementException:
                # Zoom join button not found
                self.logger.error("Zoom join button not found.")
                # self.driver.close()
                # self.driver.switch_to.window(main_window_handle)
                continue
            
            try:
                self.wait.until(EC.title_contains("Launch Meeting"))
            except TimeoutException:
                self.logger.error("Unable to load 'Launch Meeting' page. Detail: title does not contain 'Launch Meeting'.")
                raise

            self.most_recent_zoom_link = furl.furl(self.driver.current_url).remove('uname').url
            self.logger.info("Zoom link found.")
            return

        self.logger.error("No zoom link is found.")
    
    def perform_action_obtain_zoom_link(self):
        self.start_webdriver()
        try:
            self.driver.get(self.LOGIN_LINK)
            self.do_login()
            self.driver.get(self.COURSE_HOME_LINK)
            self.get_potential_mod_zoom_links()
            self.get_most_recent_zoom_link_from_all_potentials()
        except Exception as e:
            self.logger.warning("Program encountered an error while obtaining the zoom link.")
            self.logger.error(e)
        finally:
            self.driver.quit()
            self.logger.info("Webdriver shut down.")

            # After all that very confusing logger setup, my Messenger class can simply
            # use 1) add_chats method or 2) add_chat using \n joins, using this message list.
            # for message in self.logger.handlers[0].message_list:
            #     print(message)

def find_zoom_link_from_line(unparsed_text, user_id):
    start = timeit.default_timer()
    messenger = Messenger()
    matkul = unparsed_text
    try:
        try:
            matkul_proper_name = MATKUL_ABBREVIATIONS[matkul]
        except KeyError:
            messenger.add_reply(TextSendMessage("Matkul name is wrong or not recognized!"))
            raise WrongSpecificationError
        
        matkul_id = CLASSROOM_COURSE_TO_ID_DICT[matkul_proper_name]

        try:
            u, p = fetch_credentials(user_id)
        except AuthorizationRetrievalError:
            messenger.add_reply(TextSendMessage("Unable to retrieve authorization details associated with this LINE account."))
            raise

        zoom_handler = ClassroomZoomHandler(matkul_id, u, p)
        zoom_handler.perform_action_obtain_zoom_link()

        replies = [
            TextSendMessage('\n'.join(zoom_handler.message_list)),
            TextSendMessage(zoom_handler.most_recent_zoom_link)
        ]

        messenger.add_replies(replies)
    except Exception as error:
        logger.error("An exception in find_zoom_link_from_line:\n{}".format(error))
    
    logger.info("Time elapsed in executing request: {}".format(str(timedelta(seconds = timeit.default_timer() - start))))
    return messenger