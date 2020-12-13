import time
from decouple import config
from multiprocessing import Lock
from multiprocessing.managers import BaseManager
from resources import MasterDriveHandler

master = MasterDriveHandler()

def get_mastermind():
    with lock:
        return master

manager = BaseManager(('', 37844), config("MANAGER_PASSWORD", default = "password").encode())
print("Manager server declared.")

manager.register('get_mastermind', get_mastermind)
manager.start()
print("Manager server started.")