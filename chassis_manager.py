import configparser
import socket
import lock
import os
import subprocess
import gsheet

config_file_path = "./"
config_file_name = "/chm_config.conf"


def _build_email_body(chassis_name, chassis_ip):
    if chassis_name is None or chassis_name == '':
        chassis_name = 'Chassis'

    msg = f"""Subject: Chassis '{chassis_name!s}' is free now.
    
    Hi, 
    
    The chassis '{chassis_name!s}' [{chassis_ip!s}], that you were waiting for, is free now. 
    Please hope on to the machine and lock it. 
    
    Your friendly, 
    Chassis Manager
    """

    return msg


def _get_config_file_path():
    return config_file_path + config_file_name


def _get_default_name():
    return socket.gethostname()


def _get_default_ip():
    return socket.gethostbyname(socket.gethostname())


def _is_git_directory(path):
    return subprocess.call(['git', '-C', path, 'status'], stderr=subprocess.STDOUT, stdout=open(os.devnull, 'w')) == 0


def _git_init(path):
    return subprocess.call(['git', '-C', path, 'init'], stderr=subprocess.STDOUT, stdout=open(os.devnull, 'w')) == 0


def _is_git_installed():
    return subprocess.call(['git', '--version'], stderr=subprocess.STDOUT, stdout=open(os.devnull, 'w')) == 0


def _git_install_command():
    return subprocess.call(['yum', 'install', 'git', '-y'], stderr=subprocess.STDOUT, stdout=open(os.devnull, 'w')) == 0


def _install_git():
    if _is_git_installed():
        return True

    dns_file_path = os.Path("/etc/resolv.conf")
    file_created = False

    if not dns_file_path.is_file():
        file_created = True
        with open("/etc/resolv.conf", "w") as dns_file:
            dns_file.write("nameserver 8.8.8.8\n")

    success = _git_install_command()

    if file_created:
        os.remove("/etc/resolv.conf")

    return success


"""
******************************
******* Chassis Manager ******
******************************
"""


def init_git_repo(path):
    if not _install_git():
        return False, "Could not install 'git'"

    if _is_git_directory(path):
        return False, "Already a git repository"

    return _git_init(path), None


class ChassisManager:
    def __init__(self, name=None, ip=None):
        self._lock = lock.Lock()
        self._config = configparser.ConfigParser()
        self._config.read(_get_config_file_path())

        self._chassis_name = _get_default_name()
        self._chassis_ip = _get_default_ip()

        if 'Chassis' in self._config:
            if 'ip' in self._config['Chassis']:
                self._chassis_ip = self._config['Chassis']['ip']

            if 'name' in self._config['Chassis']:
                self._chassis_name = self._config['Chassis']['name']

        if name is not None and name != '':
            self._chassis_name = name

        if ip is not None and ip != '':
            self._chassis_ip = ip


        self._gsheet = gsheet.GSheet(self._chassis_name, self._chassis_ip)
        self._update_gsheet()

    def _update_gsheet(self):
        return self._gsheet.update_info(self._lock.lock_name(), self._lock.owners(), self._lock.waiters())

    def lock(self, lock_name, email, name, wait):
        success, error = self._lock.lock(lock_name, name, email)

        if success:
            return self._update_gsheet()

        if error in [lock.ErrNotAvailable, lock.ErrOnlySharedAllowed] and wait:
            self._lock.add_to_waiting_queue(email, True)

            success, error = self._update_gsheet()
            if not success:
                return False, error

        return False, error

    def print_lock_history(self):
        self._lock.print_history()

    def print_lock_owners(self):
        self._lock.print_owners()

    def unlock(self, email):
        success, error = self._lock.unlock(email)
        if not success:
            return success, error, 0

        if self._lock.type() == lock.LockType.FREE and len(self._lock.waiters()):
            notified = self._lock.notify_waiters(_build_email_body(self._chassis_name, self._chassis_ip))
            success, error = self._update_gsheet()
            return success, error, notified

        success, error = self._update_gsheet()
        return success, error, 0

    def ch_init(self, name, ip):
        self._chassis_name = name
        self._chassis_ip = ip

        self._config['Chassis'] = {
            'name': name,
            'ip': ip
        }

        with open(_get_config_file_path(), "w") as config_file:
            self._config.write(config_file)

        self._gsheet = gsheet.GSheet(self._chassis_name, self._chassis_ip)
        return self._update_gsheet()
