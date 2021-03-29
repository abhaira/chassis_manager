import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

auth_file = './Quickstart-fc30c03af78b.json'
sheet_name = "Chassis Info"
DATA_START_ROW = 2
COL_CHASSIS_NAME = 1
COL_CHASSIS_IP = 2
COL_CHASSIS_LOCK = 3
COL_CHASSIS_OWNERS = 4


class GSheet:
    def __init__(self, name, ip):
        creds = ServiceAccountCredentials.from_json_keyfile_name(auth_file, scope)
        client = gspread.authorize(creds)
        self._sheet = client.open(sheet_name).sheet1
        self._chassis_name = name
        self._chassis_ip = ip
        self._row = self._find_or_create_row()

    def _find_or_create_row(self):
        ret = self._find_row()

        if ret != -1:
            return ret

        self._sheet.append_row([self._chassis_name, self._chassis_ip])
        return self._find_row()

    def _find_row(self):
        try:
            return self._sheet.find(self._chassis_name, in_column=COL_CHASSIS_NAME).row
        except gspread.exceptions.CellNotFound:
            pass

        try:
            return self._sheet.find(self._chassis_ip, in_column=COL_CHASSIS_IP).row
        except gspread.exceptions.CellNotFound:
            pass

        return -1

    def update_info(self, lock, owners=None, waiters=None):
        if self._row == -1:
            return False, "chassis row not found"

        self._sheet.delete_rows(self._row)

        owners_list = ''
        waiters_list = ''

        if owners is not None:
            owners_list = ', '.join([owner['Email'] for owner in owners])

        if waiters is not None:
            waiters_list = ', '.join([waiter['Email'] for waiter in waiters])

        try:
            self._sheet.insert_row([self._chassis_name, self._chassis_ip, lock, owners_list, waiters_list], self._row)
        except Exception as e:
            return False, str(e)

        return True, None