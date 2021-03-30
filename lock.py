import json
import smtplib
import ssl
import pathlib


from enum import Enum, auto
from pathlib import Path
from datetime import datetime

"""
******************************
******* Macros ***************
******************************
"""
lock_file_path = str(pathlib.Path(__file__).parent.absolute())
lock_file_name = "/.chm_lock.json"
max_history = 50

ErrNotAvailable = "Lock not available"
ErrOnlySharedAllowed = "Only Shared lock allowed"
ErrInternal = "Internal error"
ErrAlreadyOwner = "User already owns the lock"
ErrNotAnOwner = "User is not an owner"

"""
******************************
******* SMTP configurations **
******************************
"""
port = 465
smtp_server = "smtp.gmail.com"
sender_email = "x.y@pavilion.io"
password = "xyz"

"""
******************************
******* Global Types *********
******************************
"""


class LockType(Enum):
    FREE = auto()
    EXCLUSIVE = auto()
    SHARED = auto()


"""
******************************
******* Exceptions ***********
******************************
"""


class InvalidLock(Exception):
    pass


"""
******************************
******* Utility Functions ****
******************************
"""


def _lock_name_to_type(name):
    if name.lower() == "exclusive":
        return LockType.EXCLUSIVE

    if name.lower() == "shared":
        return LockType.SHARED

    if name.lower() == "free":
        return LockType.FREE

    raise InvalidLock(f"Invalid lock name '{name!s}'")


def _lock_type_to_name(lock_type):
    if lock_type == LockType.EXCLUSIVE:
        return "EXCLUSIVE"

    if lock_type == LockType.SHARED:
        return "SHARED"

    if lock_type == LockType.FREE:
        return "FREE"

    raise InvalidLock("Invalid lock type")


def _lock_type_to_action(lock_type):
    if lock_type == LockType.EXCLUSIVE:
        return "Exclusive lock"

    if lock_type == LockType.SHARED:
        return "Shared lock"

    if lock_type == LockType.FREE:
        return "Unlock"

    raise InvalidLock("Invalid lock type")


def _lock_file_exist():
    lock_file = Path(_get_lock_file_path())
    return lock_file.is_file()


def _get_lock_file_path():
    return lock_file_path + lock_file_name


def _send_email(receiver_email, message):
    try:
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)
            return True

    except Exception as e:
        pass
    return False


"""
******************************
******* The Lock *************
******************************
"""


class Lock:
    def __init__(self, data=None):
        self._lock_data = data

        if data is None:
            self.load_lock()

    def _fresh_lock(self):
        self._lock_data = {
            "Type": "FREE",
            "Owners": [],
            "Waiters": [],
            "History": []
        }

    def type(self):
        return _lock_name_to_type(self._lock_data["Type"])

    def lock_name(self):
        return self._lock_data["Type"]

    def owners(self):
        return self._lock_data["Owners"]

    def waiters(self):
        return self._lock_data["Waiters"]

    def history(self):
        return self._lock_data["History"]

    def change_lock_type(self, lock_type):
        self._lock_data["Type"] = _lock_type_to_name(lock_type)
        self.save_lock()

    def add_lock_owner(self, owner_name, owner_email):
        owners = self.owners()
        owners.append({
            "Name": owner_name,
            "Email": owner_email
        })
        self.save_lock()

    def print_owners(self):
        owners = self.owners()

        if not owners:
            print("Lock is free")
            return

        for a_owner in owners:
            print(f"{a_owner['Email']!s}")

    def remove_lock_owner(self, owner_email):
        owners = self.owners()

        for a_owner in owners:
            if a_owner['Email'] == owner_email:
                owners.remove(a_owner)

        self.save_lock()

    def is_lock_owner(self, email):
        owners = self.owners()

        for a_owner in owners:
            if a_owner['Email'] == email:
                return True

        return False

    def add_to_waiting_queue(self, email, notify):
        waiters = self.waiters()
        waiters.append({
            "Email": email,
            "Notify": notify
        })
        self.save_lock()

    def add_history(self, email, action):
        history = self.history()

        if len(history) == max_history:
            history.pop(0)

        history.append({
            "Time": str(datetime.now()),
            "Email": email,
            "Action": action
        })
        self.save_lock()

    def print_history(self):
        history = self.history()

        if not history:
            print("No history available")
            return

        for event in history:
            print(f"{event['Time']!s} \t {event['Email']!s} --> {event['Action']!s}")

    def save_lock(self):
        with open(_get_lock_file_path(), "w") as lock_file:
            json.dump(self._lock_data, lock_file)

    def load_lock(self):
        if not _lock_file_exist():
            self._fresh_lock()
            return

        with open(_get_lock_file_path()) as lock_file:
            self._lock_data = json.load(lock_file)

    def notify_waiters(self, msg):
        notified = 0
        waiters = self.waiters()

        for a_waiter in waiters:
            #if _send_email(a_waiter['Email'], msg):
            #    notified += 1
            waiters.remove(a_waiter)

        self.save_lock()
        return notified

    def lock(self, lock_name, owner_name, owner_email):
        lock_type = _lock_name_to_type(lock_name)
        current_lck_type = self.type()

        if current_lck_type == LockType.FREE:
            self.change_lock_type(lock_type)
            self.add_lock_owner(owner_name, owner_email)
            self.add_history(owner_email, _lock_type_to_action(lock_type))
            return True, None

        if current_lck_type == LockType.EXCLUSIVE:
            self.add_history(owner_email, "Queried")

            if self.is_lock_owner(owner_email):
                return False, ErrAlreadyOwner

            return False, ErrNotAvailable

        if current_lck_type == LockType.SHARED and lock_type == LockType.SHARED:
            if self.is_lock_owner(owner_email):
                self.add_history(owner_email, "Queried")
                return False, ErrAlreadyOwner

            self.add_lock_owner(owner_name, owner_email)
            self.add_history(owner_email, _lock_type_to_action(lock_type))

            return True, None

        if current_lck_type == LockType.SHARED and lock_type != LockType.SHARED:
            self.add_history(owner_email, "Queried")
            return False, ErrOnlySharedAllowed

        return False, ErrInternal

    def unlock(self, email):
        if not self.is_lock_owner(email):
            return False, ErrNotAnOwner

        current_lck_type = self.type()
        self.add_history(email, _lock_type_to_action(LockType.FREE))

        if current_lck_type == LockType.FREE:
            return True, None

        self.remove_lock_owner(email)

        if current_lck_type == LockType.SHARED and len(self.owners()):
            return True, None

        self.change_lock_type(LockType.FREE)
        return True, None
