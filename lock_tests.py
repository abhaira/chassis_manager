import unittest
import lock
import os


class LockCreation(unittest.TestCase):

    def test_fresh_lock(self):
        lck = lock.Lock()
        self.assertEqual(lck.type(), lock.LockType.FREE)
        self.assertEqual(lck.owners(), [])
        self.assertEqual(lck.waiters(), [])
        self.assertEqual(lck.history(), [])


class LockPersistenceTest(unittest.TestCase):
    def setUp(self) -> None:
        lock.lock_file_path = os.getcwd()

    def tearDown(self) -> None:
        os.remove(lock._get_lock_file_path())

    def test_type_persistence(self):
        lck = lock.Lock()
        lck.change_lock_type(lock.LockType.EXCLUSIVE)
        lck.save_lock()
        lck.load_lock()
        self.assertEqual(lck.type(), lock.LockType.EXCLUSIVE)

    def test_owners_persistence(self):
        lck = lock.Lock()
        test_name = "ramu"
        test_email = "ramu.kaka@pavilion.io"
        lck.add_lock_owner(test_name, test_email)
        lck.save_lock()
        lck.load_lock()
        self.assertEqual(len(lck.owners()), 1)
        owner = lck.owners()[0]
        self.assertEqual(owner["Name"], test_name)
        self.assertEqual(owner["Email"], test_email)

    def test_waiters_persistence(self):
        lck = lock.Lock()
        test_email = "ramu.kaka@pavilion.io"
        lck.add_to_waiting_queue(test_email, True)
        lck.save_lock()
        lck.load_lock()
        self.assertEqual(len(lck.waiters()), 1)
        waiters = lck.waiters()[0]
        self.assertEqual(waiters["Email"], test_email)
        self.assertEqual(waiters["Notify"], True)

    def test_history_persistence(self):
        lck = lock.Lock()
        test_email = "ramu.kaka@pavilion.io"
        test_action = "Locked"
        lck.add_history(test_email, test_action)
        lck.save_lock()
        lck.load_lock()
        self.assertEqual(len(lck.history()), 1)
        action = lck.history()[0]
        self.assertEqual(action["Email"], test_email)
        self.assertEqual(action["Action"], test_action)


class MaxHistoryTest(unittest.TestCase):

    def test_max_history(self):
        lck = lock.Lock()
        test_email = "ramu.kaka@pavilion.io"
        test_action = "Locked"
        offset = 20

        for x in range(lock.max_history + offset):
            lck.add_history(f"{test_email}{x!s}", test_action)

        self.assertEqual(len(lck.history()), lock.max_history)

        first_history = lck.history()[0]
        self.assertEqual(first_history["Email"], f"{test_email}{offset!s}")


class LockTest(unittest.TestCase):

    def test_exclusive_lock(self):
        lck = lock.Lock()
        test_name = "ramu"
        test_email = "ramu.kaka@pavilion.io"

        success, error = lck.lock(lock._lock_type_to_name(lock.LockType.EXCLUSIVE), test_name, test_email)
        self.assertEqual(success, True)
        self.assertEqual(error, None)
        self.assertEqual(lck.is_lock_owner(test_email), True)

        success, error = lck.lock(lock._lock_type_to_name(lock.LockType.EXCLUSIVE), test_name, test_email)
        self.assertEqual(success, False)
        self.assertEqual(error, lock.ErrAlreadyOwner)

        test_email = "gullu.kale@pavilion.io"
        success, error = lck.lock(lock._lock_type_to_name(lock.LockType.EXCLUSIVE), test_name, test_email)
        self.assertEqual(success, False)
        self.assertEqual(error, lock.ErrNotAvailable)

    def test_shared_lock(self):
        lck = lock.Lock()
        test_name = "ramu"
        test_email = "ramu.kaka@pavilion.io"

        success, error = lck.lock(lock._lock_type_to_name(lock.LockType.SHARED), test_name, test_email)
        self.assertEqual(success, True)
        self.assertEqual(error, None)

        success, error = lck.lock(lock._lock_type_to_name(lock.LockType.SHARED), test_name, test_email)
        self.assertEqual(success, False)
        self.assertEqual(error, lock.ErrAlreadyOwner)
        self.assertEqual(lck.is_lock_owner(test_email), True)

        test_name = "gullu"
        test_email = "gullu.kale@pavilion.io"
        self.assertEqual(lck.is_lock_owner(test_email), False)

        success, error = lck.lock(lock._lock_type_to_name(lock.LockType.SHARED), test_name, test_email)
        self.assertEqual(success, True)
        self.assertEqual(error, None)
        self.assertEqual(lck.is_lock_owner(test_email), True)

    def test_exclusive_unlock(self):
        lck = lock.Lock()
        test_name = "ramu"
        test_email = "ramu.kaka@pavilion.io"

        lck.unlock(test_email)
        self.assertEqual(lck.is_lock_owner(test_email), False)

        success, error = lck.lock(lock._lock_type_to_name(lock.LockType.EXCLUSIVE), test_name, test_email)
        self.assertEqual(success, True)
        self.assertEqual(error, None)
        self.assertEqual(lck.is_lock_owner(test_email), True)

        lck.unlock(test_email)
        self.assertEqual(lck.is_lock_owner(test_email), False)



if __name__ == '__main__':
    runner = unittest.main()
