import numpy as np
import copy
import timeit
from datetime import timedelta
import json
import os
from decouple import config
import humanize

from ..utils import Messenger

from linebot.models import TextSendMessage, FlexSendMessage

kesma_library_folder_id = config("KESMA_LIBRARY_FOLDER_ID", default=os.environ.get("KESMA_LIBRARY_FOLDER_ID"))
class DriveLinker:
    def __init__(self, home_folder = kesma_library_folder_id):
        self.drive = None
        self.home_folder = home_folder
        self.current_folder = home_folder
        self.current_condition = {} # Refer to create_condition
        self.current_filelist = None
        self.current_show_string = ""
        
        self.keyword_home = "/home"
        self.keyword_help = "/help"
    
    # This method has to exist to signal Master that this class NEEDS a GoogleDrive instance
    # See Master.add_game
    def set_drive(self, drive):
        self.drive = drive
    
    def start_game(self):
        messenger = Messenger()
        self.set_filelist_and_condition(self.home_folder)
        self.update_show_string()
        messenger.add_reply(TextSendMessage(
            self.current_show_string
        ))
        return messenger
    
    def end_game(self):
        messenger = Messenger()
        messenger.add_reply(TextSendMessage(
            "Drive Linker service is offline now."
        ))
        return messenger
    
    def set_filelist_and_condition(self, folder_id):
        query = "'" + folder_id + "' in parents and trashed=false"
        results = self.drive.ListFile({'q': query}).GetList()
        folders = []
        files = []
        for item in results:
            if item['mimeType'] == "application/vnd.google-apps.folder":
                folders.append(item)
            else:
                files.append(item)
        folders = sorted(folders, key = lambda k: k['title'])
        files = sorted(files, key = lambda k: k['title'])
        self.current_filelist = [*folders, *files]
        
        self.current_condition = {}
        for i in range(len(self.current_filelist)):
            self.current_condition[str(i+1)] = self.current_filelist[i]
    
    def update_show_string(self):
        # Two pass is inefficient but readable
        show_string = ""
        show_string += "FOLDERS" "\n"
        for i in self.current_condition:
            if self.current_condition[i]['mimeType'] == "application/vnd.google-apps.folder":
                show_string += (i + ". ")
                show_string += (self.current_condition[i]['title'] + "\n")
        show_string += "\n"
        show_string += "FILES" "\n"
        for i in self.current_condition:
            if self.current_condition[i]['mimeType'] != "application/vnd.google-apps.folder":
                show_string += (i + ". ")
                show_string += (self.current_condition[i]['title'] + "\n")
        
        self.current_show_string = show_string
    
    def move_to_folder(self, folder_id):
        messenger = Messenger()
        self.current_folder = folder_id
        self.set_filelist_and_condition(folder_id)
        self.update_show_string()
        messenger.add_reply(TextSendMessage(
            self.current_show_string
        ))
        
        return messenger
    
    def move_to_home(self):
        return self.move_to_folder(self.home_folder)
        
    def get_help_string(self):
        messenger = Messenger()
        messenger.add_reply(TextSendMessage(
            ("Useful phrases:\n" +
             "- " + self.keyword_home + ": to get back to home folder (Kesma Library).\n" +
             "- " + self.keyword_help + ": to display this help.")
        ))
        
        return messenger
    
    def parse_and_reply(self, received_text, user_id, display_name, group_id):
        # Incoming inputs: numbers/choices/keywords
        # Given outputs: links (if file is chosen) or text (if folder is chosen, or other things)
        
        if received_text == self.keyword_home:
            return self.move_to_home()
        
        if received_text == self.keyword_help:
            return self.get_help_string()
        
        messenger = Messenger()
        try:
            object_in_question = self.current_condition[received_text]
        except KeyError as error:
            return messenger

        if object_in_question['mimeType'] == "application/vnd.google-apps.folder":
            next_folder_id = object_in_question['id']
            return self.move_to_folder(next_folder_id)
        else:
            file_download_id = object_in_question['webContentLink']
            messenger.add_reply(TextSendMessage(
                object_in_question['title'] + "\n" + file_download_id + "\n" + humanize.naturalsize(object_in_question['fileSize'])
            ))
            messenger.add_reply(TextSendMessage(
                self.current_show_string
            ))
            return messenger
