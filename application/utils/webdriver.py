import logging
import datetime
import timeit
from decouple import config
from selenium import webdriver

LOCAL_ENVIRONMENT = config('LOCAL_ENVIRONMENT', cast=bool, default=False)
GECKODRIVER_PATH = config('GECKODRIVER_PATH', cast=str, default='')
CHROMEDRIVER_PATH = config('CHROMEDRIVER_PATH', cast=str, default='')
GOOGLE_CHROME_BIN_PATH = config("GOOGLE_CHROME_BIN", cast=str, default='')
# MOZILLA_FIREFOX_BIN_PATH can be specified too if Firefox is not in default installation path (Program Files)

module_logger = logging.getLogger(__name__)
module_logger.setLevel(logging.INFO)

def build_driver():
    start = timeit.default_timer()
    if LOCAL_ENVIRONMENT:
        op = webdriver.FirefoxOptions()
        op.add_argument("--disable-dev-shm-usage")
        op.add_argument("--no-sandbox")
        driver = webdriver.Firefox(executable_path=GECKODRIVER_PATH, options=op)
    else:
        op = webdriver.ChromeOptions()
        op.add_argument('--headless')
        op.add_argument('--incognito')
        op.add_argument("--disable-dev-shm-usage")
        op.add_argument("--no-sandbox")
        op.binary_location = GOOGLE_CHROME_BIN_PATH
        driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, options=op)
    end = timeit.default_timer()
    module_logger.info("Webdriver start time:{}".format(datetime.timedelta(seconds = end-start)))
    return driver