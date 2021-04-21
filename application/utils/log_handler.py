import logging

# https://stackoverflow.com/questions/36408496/python-logging-handler-to-append-to-list
# Both answers combined
class ListHandler(logging.Handler):
    def __init__(self, *args, message_list, **kwargs):
        logging.Handler.__init__(self, *args, **kwargs)
        self.setFormatter(logging.Formatter('%(message)s'))
        self.setLevel(logging.INFO)
        self.message_list = message_list
    def emit(self, record):
        self.message_list.append(record.getMessage())