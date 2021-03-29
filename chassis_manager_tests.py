import unittest
import chassis_manager
import os
import lock


class ChassisManagerCreationFromConfFileTest(unittest.TestCase):
    def setUp(self) -> None:
        chassis_manager.config_file_path = os.getcwd()

        with open(chassis_manager._get_config_file_path(), "a+") as config_file:
            config_file.write("[Chassis]\n")
            config_file.write("ip = 10.10.10.10\n")
            config_file.write("name = gullu\n")

    def tearDown(self) -> None:
        try:
            os.remove(chassis_manager._get_config_file_path())
            os.remove(lock._get_lock_file_path())
        except Exception as e:
            pass

    def test_chassis_manager(self):
        chm = chassis_manager.ChassisManager()
        self.assertEqual(chm._chassis_ip, "10.10.10.10")
        self.assertEqual(chm._chassis_name, "gullu")


class ChassisManagerLock(unittest.TestCase):
    def tearDown(self) -> None:
        try:
            os.remove(lock._get_lock_file_path())
        except Exception as e:
            pass

    def test_chm_lock(self):
        chm = chassis_manager.ChassisManager()
        success, error = chm.lock(lock._lock_type_to_name(lock.LockType.EXCLUSIVE),
                             "gullu.kale@gmail.com", "gullu", False)
        self.assertEqual(success, True)
        self.assertEqual(error, None)

        success, error = chm.lock(lock._lock_type_to_name(lock.LockType.EXCLUSIVE),
                               "pillu.kale@gmail.com", "pillu", False)
        self.assertEqual(success, False)
        self.assertEqual(error, lock.ErrNotAvailable)
        self.assertEqual(len(chm._lock.waiters()), 0)


class ChassisManagerUnlock(unittest.TestCase):
    def tearDown(self) -> None:
        try:
            os.remove(lock._get_lock_file_path())
        except Exception as e:
            pass

    def test_unlock(self):
        chm = chassis_manager.ChassisManager()
        success, error = chm.lock(lock._lock_type_to_name(lock.LockType.EXCLUSIVE),
                             "gullu.kale@gmail.com", "gullu", True)
        self.assertEqual(success, True)
        self.assertEqual(error, None)

        success, error = chm.lock(lock._lock_type_to_name(lock.LockType.EXCLUSIVE),
                               "pillu.kale@gmail.com", "pillu", False)
        self.assertEqual(success, False)
        self.assertEqual(error, lock.ErrNotAvailable)
        self.assertEqual(len(chm._lock.waiters()), 0)

        success, error, notified = chm.unlock("gullu.kale@gmail.com")
        self.assertEqual(success, True)
        self.assertEqual(error, None)
        self.assertEqual(len(chm._lock.waiters()), 0)


if __name__ == "__main__":
    runner = unittest.main()
