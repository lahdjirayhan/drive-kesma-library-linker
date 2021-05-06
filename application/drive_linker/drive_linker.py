import timeit
import logging
from decouple import config
from datetime import timedelta
import humanize

from application.utils.log_handler import ListHandler
from application.exceptions import WrongSpecificationError

module_logger = logging.getLogger(__name__)
module_logger.setLevel(logging.DEBUG)

bank_soal_folder_id = config("BANK_SOAL_FOLDER_ID")
ebook_folder_id = config("EBOOK_FOLDER_ID")

def browse_library_from_line(drive, doctype, unparsed_rest_of_text, user_id):
    start_time = timeit.default_timer()
    message_list = []
    try:
        doctype, sorted_number = preprocess_chat_library(doctype, unparsed_rest_of_text)
    except WrongSpecificationError as error:
        module_logger.debug(str(error))
        message_list.append(str(error))
    else:
        reply = run_library(drive, doctype, sorted_number, user_id)
        message_list.extend(reply)
    
    module_logger.info("Time elapsed in executing request: {}".format(str(timedelta(seconds = timeit.default_timer() - start_time))))
    return message_list

def preprocess_chat_library(doctype, sorted_number):
    # Note to self: in hindsight this function may look weird.
    # But I try to make it consistent with other preprocess functions.
    if doctype not in ['ebook', 'soal']:
        raise WrongSpecificationError("Invalid folder name '{}'. Do you want to show ebook folder or bank soal folder?".format(doctype))
    
    if sorted_number is None: # If no sorted number, it means "show me all available subfolders" command.
        pass
    elif not (sorted_number.isdecimal() and int(sorted_number) > 0):
        raise WrongSpecificationError("Invalid folder number '{}'. Should give positive numeric value.".format(sorted_number))
    return doctype, sorted_number

def run_library(drive, doctype, sorted_number, user_id):
    message_list = []

    if doctype == "ebook":
        logger = logging.getLogger(__name__ + ".ebook." + user_id)
        home_folder = ebook_folder_id
    elif doctype == "soal":
        logger = logging.getLogger(__name__ + ".bank_soal." + user_id)
        home_folder = bank_soal_folder_id
    
    logger.setLevel(logging.DEBUG)
    logger.addHandler(ListHandler(message_list=message_list))

    drive_linker = DriveLinker(drive, logger, home_folder)
    reply = drive_linker.summarize_course_folder_with_this_sorted_number(sorted_number)
    
    message_list.append(reply)
    return message_list

class DriveLinker:
    """
    Methods that interact with drive, go here.
    """
    def __init__(self, drive_instance, logger_instance, home_folder):
        self.drive = drive_instance
        self.logger = logger_instance
        self.home_folder = home_folder
        self.directory_path_separator = " - "
    
    def summarize_course_folder_with_this_sorted_number(self, sorted_number):
        try:
            folder_id = self._get_folder_id_by_sorted_number(sorted_number)
        except IndexError as error:
            if len(error.args) == 2:
                return error.args[1]
            return "Invalid folder number {}.".format(sorted_number)
        
        if folder_id == self.home_folder:
            return self._summarize_home_folder_into_string(folder_id)
        else:
            return self._summarize_course_folder_into_string(folder_id)
    
    def _get_folder_id_by_sorted_number(self, subfolder_sorted_number):
        if subfolder_sorted_number is None:
            return self.home_folder
        
        actual_index = int(subfolder_sorted_number) - 1 # Python is 0-indexed, but showing the list to user is 1-indexed.
        subfolders, files = self._get_home_folder_contents()
        
        results = [*subfolders, *files]
        
        try:
            item_id = results[actual_index]['id']
        except IndexError as error:
            error.args = (
                *error.args,
                "Invalid folder number {}. Expected range 1 - {}.".format(int(subfolder_sorted_number), len(results))
            )
            raise error
        return item_id
    
    def _summarize_home_folder_into_string(self, folder_id):
        """Given a home folder's id, summarize it's contents
        
        This will NOT recursively summarize each subfolder. This function is intended to be used
        on a home folder, i.e. kesmalib/ebook
        """
        subfolders, files = self._get_home_folder_contents()
        
        str_list = [
            # List all subfolders
            *[str(index) + ". " + item['title'] for index, item in enumerate(subfolders, 1)],
            
            # An empty space to separate folder from files
            "",
            
            # List all files
            *[str(index) + ". " + item['title'] for index, item in enumerate(files, len(subfolders) + 1)],
        ]
        
        str_reply = "\n".join(str_list)
        return str_reply
    
    def _summarize_course_folder_into_string(self, folder_id, prepend_title=''):
        """Given a course folder's id, summarize its contents
        
        This will recursively summarize each subfolder. This function is intended to be used
        on a course folder, i.e. kesmalib/ebook/pms
        """
        subfolders, files = self._get_subfolders_and_files_separately(folder_id)
        
        str_list = [            
            # Summarize each subfolder
            *[self._summarize_course_folder_into_string(folder_id=folder['id'], prepend_title=folder['title']+self.directory_path_separator) for folder in subfolders],
            
            # Summarize this folder
            *[
                # Provide name, link, and size
                "\n".join([prepend_title + item['title'], item['webContentLink'], humanize.naturalsize(item['fileSize'])]) for item in files
            ]
        ]
        
        # Join with two newlines separating each entry
        str_reply = "\n\n".join(str_list)
        return str_reply
    
    def _get_home_folder_contents(self):
        """Given a home folder's id, obtain its contents and sort"""
        subfolders, files = self._get_subfolders_and_files_separately(self.home_folder)
        
        subfolders = sorted(subfolders, key = lambda item: item['title'])
        files = sorted(files, key = lambda item: item['title'])
        
        return subfolders, files
        
    def _get_subfolders_and_files_separately(self, folder_id):
        query = self._build_query(folder_id=folder_id)
        item_list = self.drive.ListFile(query).GetList()
        
        subfolders, files = self._separate_into_subfolders_and_files_based_on_mimetype(item_list)
        return subfolders, files
    
    def _separate_into_subfolders_and_files_based_on_mimetype(self, item_list):
        subfolders, files = [], []
        for item in item_list:
            if item['mimeType'] == "application/vnd.google-apps.folder":
                subfolders.append(item)
            else:
                files.append(item)
        
        return subfolders, files

    def _build_query(self, folder_id=None, search_by_title=None, exact_title=True):
        """
        Helper method to build query dict for pydrive ListFile method
        """
        # Folder query
        if folder_id is None:
            folder_id = self.home_folder
        folder_query = "'{}' in parents and trashed=false".format(folder_id)

        # Title query
        # I realize either one the following is not going to be used
        # but I'll leave here anyway for the meantime
        if search_by_title is not None:
            if exact_title:
                title_query = "title = '{}'".format(search_by_title)
            else:
                title_query = "title contains '{}'".format(search_by_title)
            full_query = " and ".join([folder_query, title_query])
        else:
            full_query = folder_query
        
        return {"q": full_query}
    
    def _get_title_by_id(self, folder_id):
        # NOTE(Rayhan) Unused at the moment
        return self.drive.CreateFile({"id": folder_id})['title'].upper()
