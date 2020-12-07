import os
import time
import timeit
from babel.dates import format_date, format_time, format_datetime
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from linebot.models import TextSendMessage
from .utils import Messenger

# Custom exceptions:
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

class NoUnattendedEntryError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__("All other entries have been attended.")

class WrongSpecificationError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__("A misspecification of matkul and/or absen happened.")

# Custom-defined helpers
def make_matkul_abbreviation():
  abbrevs = {
    ("teksim", "teknik simulasi"): "Teknik Simulasi",
    ("ad", "andat", "analisis data"): "Analisis Data",
    ("mm", "manmut", "manajemen mutu"): "Manajemen Mutu",
    ("sml", "statistical machine learning"): "Statistical Machine Learning",
    ("ofstat", "offstat", "statof", "statoff", "statistika ofisial"): "Statistika Ofisial",
    ("ekon", "ekono", "ekonom", "ekonometrika"): "Ekonometrika"
  }
  result = {}
  for k, v in abbrevs.items():
    for key in k:
      result[key] = v
  return result

matkul_abbreviations = make_matkul_abbreviation()

def make_options():
    op = webdriver.ChromeOptions()
    op.add_argument("--headless")
    op.add_argument("--disable-dev-shm-usage")
    op.add_argument("--no-sandbox")
    op.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    return op

_op = make_options()

presensi_site = 'https://presensi.its.ac.id'

username_form = '//*[@id="username"]'
next_button = '//*[@id="continue"]'
password_form = '//*[@id="password"]'
signin_button = '//*[@id="login"]'
kode_presensi_form = '//*[@id="kode_akses_mhs"]'
simpan_button = '//*[@id="submit-hadir-mahasiswa"]'

# Absen engine, "the big code"
def absen(matkul, kode_presensi, username = os.environ.get("RAYHAN_INTEGRA_USERNAME"), password = os.environ.get("RAYHAN_INTEGRA_PASSWORD")):
    messenger = Messenger()
    
    # It is saddening that I have to use Chrome. RIP geckodriver + heroku.
    driver = webdriver.Chrome(executable_path = os.environ.get("CHROMEDRIVER_PATH"), options = _op)
    wait = WebDriverWait(driver, 13)
    
    try:
        
        try:
            driver.get(presensi_site)
            wait.until(EC.presence_of_element_located((By.XPATH, username_form)))
            time.sleep(0.5)
            driver.find_element_by_xpath(username_form).clear()
            time.sleep(0.5)
            driver.find_element_by_xpath(username_form).send_keys(username)
            time.sleep(0.5)
            driver.find_element_by_xpath(next_button).click()
            wait.until(EC.visibility_of_element_located((By.XPATH, password_form)))
            driver.find_element_by_xpath(password_form).send_keys(password)
            time.sleep(0.5)
            driver.find_element_by_xpath(signin_button).click()
        except TimeoutException:
            print("Initial webpage load failed")
            messenger.add_reply(TextSendMessage("Initial webpage load failed"))
            raise
        except NoSuchElementException:
            print("NoSuchElementException encountered (0). Dev-only: refer to source code.")
            messenger.add_reply(TextSendMessage("NoSuchElementException encountered (0). Dev-only: refer to source code."))
            raise
            
        try:
            wait.until(EC.title_contains("Dashboard"))
            print("Login successful")
            messenger.add_reply(TextSendMessage("Login successful"))
        except TimeoutException:
            print("Login unsuccessful")
            messenger.add_reply(TextSendMessage("Login unsuccessful"))
            raise LoginFailedError

        try:
            wait.until(EC.visibility_of_element_located((By.TAG_NAME, 'li')))
            list_of_li = driver.find_elements_by_tag_name('li')
        except TimeoutException:
            print("Fail to get list of courses")
            messenger.add_reply(TextSendMessage("Fail to get list of courses"))
            raise
        except NoSuchElementException:
            print("NoSuchElementException encountered (1). Dev-only: refer to source code.")
            messenger.add_reply(TextSendMessage("NoSuchElementException encountered (1). Dev-only: refer to source code."))
            raise

        try:
            already_found = False
            for entry in list_of_li:
                print(entry.find_element_by_tag_name('a').text)
                print(entry.find_element_by_tag_name('a').get_attribute('href'))
                if matkul in entry.find_element_by_tag_name('a').text:
                    print(matkul, "found!")
                    already_found = True
                    driver.get(entry.find_element_by_tag_name('a').get_attribute('href'))
                    break

            if not already_found:
                raise CourseNotFoundError
        except CourseNotFoundError:
            print("Course with the name specified was not found.")
            messenger.add_reply(TextSendMessage("Course with the name specified not found."))
            raise
        except NoSuchElementExceptionError:
            print("NoSuchElementException encountered (2). Dev-only: refer to source code.")
            messenger.add_reply(TextSendMessage("NoSuchElementException encountered (2). Dev-only: refer to source code."))
            raise

        try:
            wait.until(EC.presence_of_element_located((By.XPATH, '//table')))
            time.sleep(0.5)
            table = driver.find_element_by_xpath('//table')
            course_entries = table.find_elements_by_xpath('.//tbody[@class !=""]')
        except TimeoutException:
            print("Fail to get list of schedules")
            messenger.add_reply(TextSendMessage("Fail to get list of schedules"))
            raise
        except NoSuchElementException:
            print("NoSuchElementException encountered (3). Dev-only: refer to source code.")
            messenger.add_reply(TextSendMessage("NoSuchElementException encountered (3). Dev-only: refer to source code."))
            raise

        today_date = format_date(datetime.now(), 'EEEE, d MMMM y', locale = "id")
        print(today_date)
        schedule_traversing_report = ""
        course_entries.reverse()
        try:
            today_entry = None
            already_found = False
            for entry in course_entries:
                course_entry_string = (entry.find_element_by_xpath('.//tr/td[2]/p[1]').text + " " +
                                       entry.find_element_by_xpath('.//td[@class = "jenis-hadir-mahasiswa"]').text)
                print(course_entry_string)
                schedule_traversing_report += (course_entry_string + '\n')
                if entry.find_element_by_xpath('.//tr/td[2]/p[1]').text == today_date:
                    today_entry = entry
                    already_found = True
                    print("Matched date!")
                    schedule_traversing_report += "Matched date!\n"
                    break
                    
            if not already_found:
                raise ScheduleNotFoundError
        except ScheduleNotFoundError:
            print("No matching date is found.")
            schedule_traversing_report += "No matching date is found.\n"
            for entry in course_entries:
                if entry.find_element_by_xpath('.//td[@class = "jenis-hadir-mahasiswa"]').text == "ALPA":
                    today_entry = entry
                    print("Found alpa entry!", entry.find_element_by_xpath('.//tr/td[2]/p[1]').text)
                    schedule_traversing_report += ('Found alpa entry at' + entry.find_element_by_xpath('.//tr/td[2]/p[1]').text + '!\n')
                    break
            
            if today_entry is None:
                print("No alpa entry is found!")
                schedule_traversing_report += "No alpa entry is found!\n"
                raise NoUnattendedEntry
        except NoSuchElementException:
            print("NoSuchElementException encountered (4). Dev-only: refer to source code.")
            messenger.add_reply(TextSendMessage("NoSuchElementException encountered (4). Dev-only: refer to source code."))
            raise
        finally:
            messenger.add_reply(TextSendMessage(schedule_traversing_report))
        
        try:
            if today_entry.find_element_by_xpath('.//td[@class = "jenis-hadir-mahasiswa"]').text != "ALPA":
                raise TodayEntryAttendedError
        except NoSuchElementException:
            print("NoSuchElementException encountered (5). Dev-only: refer to source code.")
            messenger.add_reply(TextSendMessage("NoSuchElementException encountered (5). Dev-only: refer to source code."))
            raise
        except TodayEntryAttendedError:
            print("Today's entry is already attended.")
            messenger.add_reply(TextSendMessage("Today's entry is already attended."))
            raise
        
        try:
            today_entry.find_element_by_xpath('.//*[contains(@data-target, "#modal-hadir")]').click()
        except NoSuchElementException:
            print("NoSuchElementException encountered (5b). Dev-only: refer to source code.")
            messenger.add_reply(TextSendMessage("NoSuchElementException encountered (5b). Dev-only: refer to source code."))
            raise
        
        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, kode_presensi_form)))
            driver.find_element_by_xpath(kode_presensi_form).send_keys(kode_presensi)
            time.sleep(0.5)
            driver.find_element_by_xpath(simpan_button).click()
        except TimeoutException:
            print("Fail to get widget box for kode presensi.")
            messenger.add_reply(TextSendMessage("Fail to get widget box for kode presensi."))
            raise
        except NoSuchElementException:
            print("NoSuchElementException encountered (6). Dev-only: refer to source code.")
            messenger.add_reply(TextSendMessage("NoSuchElementException encountered (6). Dev-only: refer to source code."))
            raise
            
        time.sleep(1) # Wait for classroom to register presensi
        try:
            alert_text = driver.find_element_by_xpath('.//div[@role = "alert"]').text
        except NoSuchElementException:
            alert_text = "No alerts available."
        print(alert_text)
        messenger.add_reply(TextSendMessage(alert_text))
    except:
        pass
    
    driver.quit()
    return messenger

# The gateway, sanity checker, wrapper. Moved from Master to reflect
# what absen is all about: not a class, but rather a function
# (one call to return the results and that's it).
def absen_from_line(unparsed_text):
    # Input sanity check: reduces burden on Selenium running.
    # Time-reporting, more accurate and "whole" now. Decorator is infeasible
    # because it stops stack trace on the wrapper.
    start = timeit.default_timer()
    messenger = Messenger()
    try:
        splitlist = unparsed_text.rstrip().rsplit(" ", 1)
        try:
            matkul = splitlist[0]
            kode_absen = splitlist[1]
        except IndexError:
            messenger.add_reply(TextSendMessage("Either missing matkul name or kode absen."))
            raise WrongSpecificationError
        
        try:
            matkul_proper_name = matkul_abbreviations[matkul]
        except KeyError as error:
            messenger.add_reply(TextSendMessage("Matkul name is wrong or not recognized!"))
            raise WrongSpecificationError
        
        if not kode_presensi.isnumeric():
            messenger.add_reply(TextSendMessage("Kode presensi should contain numbers only."))
            raise WrongSpecificationError
        
        if len(kode_presensi) != 6:
            messenger.add_reply(TextSendMessage("Kode presensi has wrong length. It should contain exactly 6 digits."))
            raise WrongSpecificationError
        
        messenger.add_replies(absen(matkul_proper_name, kode_absen).reply_array)
        print("Time elapsed in executing request:", timedelta(seconds = timeit.default_timer() - start))
    except:
        pass
    return messenger
