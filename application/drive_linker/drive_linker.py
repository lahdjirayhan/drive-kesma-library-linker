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
    elif not sorted_number.isdecimal():
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
    reply = drive_linker.summarize_directory_content_into_string(sorted_number)
    
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
    
    def summarize_directory_content_into_string(self, subfolder_sorted_number=None, subfolder_id=None, prepend_title=''):
        """
        Summarize the content of a directory specified by either its subfolder sort number or subfolder id.
        """
        try:
            subfolder_id = self.get_folder_id_by_sorted_number(subfolder_sorted_number) if subfolder_id is None else subfolder_id
        except IndexError:
            self.logger.info("Invalid folder number {}.".format(str(subfolder_sorted_number-1)))
            return ""
        
        query = self.build_query(folder_id=subfolder_id)
        item_list = self.drive.ListFile(query).GetList()

        folder_list = [item for item in item_list if item['mimeType'] == "application/vnd.google-apps.folder"]
        file_list = [item for item in item_list if item['mimeType'] != "application/vnd.google-apps.folder"]
        if subfolder_sorted_number is None and subfolder_id == self.home_folder:
            str_list = ['. '.join([str(index+1), item['title']]) for index, item in enumerate(folder_list)]
            str_reply = '\n'.join(str_list)
        else:
            str_list = [*[self.summarize_directory_content_into_string(subfolder_id=item['id'], prepend_title=item['title']+"/") for item in folder_list],
                        *['\n'.join([prepend_title + item['title'], item['webContentLink'], humanize.naturalsize(item['fileSize'])]) for item in file_list]]
            str_reply = '\n\n'.join(str_list)
        return str_reply
    
    def get_folder_id_by_sorted_number(self, subfolder_sorted_number=None):
        if subfolder_sorted_number is None:
            return self.home_folder
        
        actual_index = int(subfolder_sorted_number) - 1 # Python is 0-indexed, but showing the list to user is 1-indexed.
        query = self.build_query()
        results = self.drive.ListFile(query).GetList()

        try: item_id = results[actual_index]['id']
        except IndexError: raise # pylint is not happy about immediately raising, but I think this is better be left explicit that I'm catching/expecting an IndexError
        return item_id

    def build_query(self, folder_id=None, search_by_title=None, exact_title=True):
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
