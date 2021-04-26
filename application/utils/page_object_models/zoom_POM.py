import furl

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from .common import BasePage, DashboardPage

class ClassroomDashboardPage(DashboardPage):
    def prepare_selectors(self):
        self.COURSE_LINKS = By.CSS_SELECTOR, 'a.coursename'

class ModZoomPage(BasePage):
    """
    Methods to operate in classroom.its.ac.id/mod/zoom session-specific.
    """
    def prepare_selectors(self):
        self.JOIN_BUTTON = By.XPATH, '//button[contains(text(), "Join Meeting")]'
        # NOTE(Rayhan): How about meeting metadata i.e. date and time?
        # They should also go here and perhaps be reported.

    def get_zoom_link_from_button(self):
        try:
            self.driver.find_element(*self.JOIN_BUTTON).click()
        except NoSuchElementException:
            return None
        self.driver.switch_to.window(self.driver.window_handles[-1])
        return furl.furl(self.driver.current_url).remove('uname').url


class CourseHomePage(BasePage):
    """
    Methods to operate in classroom.its.ac.id/course/view.php?id course-specific.
    """
    def prepare_selectors(self):
        self.MOD_ZOOM_HYPERLINK_ELEMENT = By.PARTIAL_LINK_TEXT, "Zoom meeting"

    def do_find_zoom_link(self):
        traversal_report_per_line = []

        if (potential_mod_zoom_links := self.get_potential_mod_zoom_links()):
            traversal_report_per_line.append("COURSE SESSIONS CHECKED:")
            for element in potential_mod_zoom_links:
                mod_zoom_page = ModZoomPage(self.driver, self.logger, element[0])
                if (zoom_link := mod_zoom_page.get_zoom_link_from_button()):
                    traversal_report_per_line.append(
                        element[1].partition('\n')[0] + ": " + "LINK FOUND"
                    )
                    break
                
                traversal_report_per_line.append(
                    element[1].partition('\n')[0] + ": " + "no link."
                )
        
        traversal_report = '\n'.join(traversal_report_per_line)
        self.logger.info(traversal_report)
        if zoom_link:
            self.logger.info(zoom_link)

    def get_potential_mod_zoom_links(self):
        # NOTE(Rayhan): Implement typehinting?
        potential_elements = self.driver.find_elements(*self.MOD_ZOOM_HYPERLINK_ELEMENT)
        potential_mod_zoom_links = [(elem.get_attribute('href'), elem.text)
                                         for elem in potential_elements][::-1] # Reverse, most recent is first
        self.logger.info(
            "{} meetings found as potential candidate for actual Zoom link.".format(
                len(potential_mod_zoom_links)
            )
        )
        return potential_mod_zoom_links
