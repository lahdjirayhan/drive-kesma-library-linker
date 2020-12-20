import os
import time
import timeit
from decouple import config
from babel.dates import format_date, format_time, format_datetime
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from linebot.models import TextSendMessage
from .utils import Messenger
from .models import UserAuth
from .access_db import fetch_credentials, AuthorizationRetrievalError

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


nse_exception_text = "NoSuchElementException encountered ({code}). Dev-only: refer to source code."

# Absen engine, "the big code"
def absen(matkul, kode_presensi, username, password):
    messenger = Messenger()
    
    # It is saddening that I have to use Chrome. RIP geckodriver + heroku.
    driver = webdriver.Chrome(executable_path = os.environ.get("CHROMEDRIVER_PATH"), options = _op)
    wait = WebDriverWait(driver, 13)
    
    try:
        
        # INITIAL WEBPAGE LOAD AND LOGIN
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
            print(nse_exception_text.format(code=0))
            messenger.add_reply(TextSendMessage(nse_exception_text.format(code=0)))
            raise
        
        # VERIFY LOGIN
        try:
            wait.until(EC.title_contains("Dashboard"))
            print("Login successful.")
            messenger.add_reply(TextSendMessage("Login successful."))
        except TimeoutException:
            print("Login unsuccessful.")
            messenger.add_reply(TextSendMessage("Login unsuccessful."))
            raise LoginFailedError
        
        # LOCATE LIST OF COURSE NAMES
        try:
            wait.until(EC.visibility_of_element_located((By.TAG_NAME, 'li')))
            list_of_li = driver.find_elements_by_tag_name('li')
        except TimeoutException:
            print("Fail to get list of courses.")
            messenger.add_reply(TextSendMessage("Fail to get list of courses."))
            raise
        except NoSuchElementException:
            print(nse_exception_text.format(code=1))
            messenger.add_reply(TextSendMessage(nse_exception_text.format(code=1)))
            raise
        
        # SELECT INFERRED COURSE
        try:
            for entry in list_of_li:
                print(entry.find_element_by_tag_name('a').text)
                print(entry.find_element_by_tag_name('a').get_attribute('href'))
                if matkul in entry.find_element_by_tag_name('a').text:
                    print(matkul, "found!")
                    already_found = True
                    driver.get(entry.find_element_by_tag_name('a').get_attribute('href'))
                    break
            raise CourseNotFoundError
        except CourseNotFoundError:
            print("Course with the name specified was not found.")
            messenger.add_reply(TextSendMessage("Course with the name specified not found."))
            raise
        except NoSuchElementException:
            print(nse_exception_text.format(code=2))
            messenger.add_reply(TextSendMessage(nse_exception_text.format(code=2)))
            raise
        
        # RETRIEVE TABLE OF COURSE SCHEDULE ENTRIES
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, '//table')))
            time.sleep(0.5)
            table = driver.find_element_by_xpath('//table')
            course_entries = table.find_elements_by_xpath('.//tbody[@class !=""]')
            course_dates = [entry.find_element_by_xpath('.//tr/td[2]/p[1]').text for entry in course_entries]
            course_statuses = [entry.find_element_by_xpath('.//td[@class = "jenis-hadir-mahasiswa"]').text for entry in course_entries]
        except TimeoutException:
            print("Fail to get list of schedules.")
            messenger.add_reply(TextSendMessage("Fail to get list of schedules."))
            raise
        except NoSuchElementException:
            print(nse_exception_text.format(code=3))
            messenger.add_reply(TextSendMessage(nse_exception_text.format(code=3)))
            raise

        try:
            schedule_not_found = False
            no_unattended_entry = False
            selected_entry = None
            today_date = format_date(datetime.now() + timedelta(hours = 7), 'EEEE, d MMMM y', locale = "id")
            try:
                selected_entry = course_entries[course_dates.index(today_date)]
            except ValueError:
                # today_date not in course_dates raises ValueError
                raise ScheduleNotFoundError
        except ScheduleNotFoundError:
            try:
                most_recent_alpa_index = len(course_statuses) - course_statuses[::-1].index("ALPA") - 1
                selected_entry = course_entries[most_recent_alpa_index]
            except ValueError:
                # ALPA not in course_statuses raises ValueError
                no_unattended_entry = True
            schedule_not_found = True
        finally:
            schedule_traversing_reports = []
            try:
                selected_date = selected_entry.find_element_by_xpath('.//tr/td[2]/p[1]').text
            except AttributeError:
                # selected_entry being None will raise AttributeError
                selected_date = None
            for i in range(len(course_entries)):
                schedule_traversing_reports.append(' '.join([course_dates[i], course_statuses[i]]))
                if course_dates[i] == selected_date:
                    schedule_traversing_reports[-1] = ' '.join(["[X]", schedule_traversing_reports[-1], "[X]"])
            
            schedule_traversing_report_string = '\n'.join(schedule_traversing_reports)
            messenger.add_reply(TextSendMessage(schedule_traversing_report_string))

            # EXPLANATION ABOUT WHICH ENTRY IS SELECTED
            if no_unattended_entry:
                messenger.add_reply(TextSendMessage(
                    "There is no entry marked as ALPA."
                ))
                # Reraise NoUnattendedEntryError as the previous one is lost
                # This is to exit the large try-except block,
                # as opposed to using return.
                raise NoUnattendedEntryError
            elif schedule_not_found:
                messenger.add_reply(TextSendMessage(
                    "There is no entry with today's date, so most recent entry marked as ALPA is selected."
                ))
            else:
                messenger.add_reply(TextSendMessage(
                    "There is an entry with today's date, so that entry is selected."
                ))
        
        # INFER ACTION ON ENTRY
        try:
            if selected_entry.find_element_by_xpath('.//td[@class = "jenis-hadir-mahasiswa"]').text == "HADIR":
                raise TodayEntryAttendedError
            elif selected_entry.find_element_by_xpath('.//td[@class = "jenis-hadir-mahasiswa"]').text != "ALPA":
                raise TodayEntryNotActionableError

        except NoSuchElementException:
            print(nse_exception_text.format(code=5))
            messenger.add_reply(TextSendMessage(nse_exception_text.format(code=5)))
            raise
        except TodayEntryAttendedError:
            print("Today's entry is already attended.")
            messenger.add_reply(TextSendMessage("Today's entry is already attended."))
            raise
        except TodayEntryNotActionableError:
            print("Today's entry is neither HADIR nor ALPA.")
            messenger.add_reply(TextSendMessage("Today's entry is neither HADIR nor ALPA."))
            raise
        
        # BRING UP PRESENSI WIDGET AND DO ABSENSI
        try:
            selected_entry.find_element_by_xpath('.//*[contains(@data-target, "#modal-hadir")]').click()
        except NoSuchElementException:
            print(nse_exception_text.format(code=6))
            messenger.add_reply(TextSendMessage(nse_exception_text.format(code=6)))
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
            print(nse_exception_text.format(code=7))
            messenger.add_reply(TextSendMessage(nse_exception_text.format(code=7)))
            raise
        
        # VERIFY PRESENSI
        time.sleep(0.8) # Wait for classroom to register presensi
        try:
            alert_text = driver.find_element_by_xpath('.//div[@role = "alert"]').text
            
            # Take only text, not with the x sign that somehow is there with the text.
            alert_text = alert_text.rsplit('\n', 2)[-1]
        except NoSuchElementException:
            alert_text = "Tidak ada pemberitahuan berhasil/gagal di webpage."
        finally:            
            print(alert_text)
            messenger.add_reply(TextSendMessage(alert_text))
            
            # Make absensi status to be sent first rather than last.
            # Is it good thing?
            # messenger.reply_array.append(messenger.reply_array.pop(0))
    except Exception as error:
        print("An exception in absen:\n{}".format(error))
    
    driver.quit()
    return messenger

# The gateway, sanity checker, wrapper. Moved from Master to reflect
# what absen is all about: not a class, but rather a function
# (one call to return the results and that's it).
def absen_from_line(unparsed_text, user_id):
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
        
        if not kode_absen.isnumeric():
            messenger.add_reply(TextSendMessage("Kode presensi should contain numbers only."))
            raise WrongSpecificationError
        
        if len(kode_absen) != 6:
            messenger.add_reply(TextSendMessage("Kode presensi has wrong length. It should contain exactly 6 digits."))
            raise WrongSpecificationError
        
        # Retrieve account details from database.
        try:
            u, p = fetch_credentials(user_id)
        except AuthorizationRetrievalError:
            messenger.add_reply(TextSendMessage("Unable to retrieve authorization details associated with this LINE account."))
            raise
        except:
            raise
        
        try:
            messenger.add_replies(absen(matkul_proper_name, kode_absen, u, p).reply_array)
        except:
            raise

    except Exception as error:
        print("An exception in absen_from_line:\n{}".format(error))
    
    print("Time elapsed in executing request:", timedelta(seconds = timeit.default_timer() - start))
    return messenger
