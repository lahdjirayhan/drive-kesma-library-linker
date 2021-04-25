from datetime import datetime, timedelta
from babel.dates import format_date

from selenium.webdriver.common.by import By

from .common import BasePage

class TimetablePage(BasePage):
    """
    Methods to operate in presensi.its.ac.id course-specific timetable page.
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
