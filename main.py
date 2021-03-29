import argparse
import chassis_manager


def lock(args):
    lock = args.LOCK

    if lock is None or lock is False:
        return False

    lock_type = args.LOCK_TYPE
    name = args.NAME
    email = args.EMAIL
    notify = False

    if lock_type is None or name is None or email is None:
        if lock_type is None:
            print("Please specify the lock type")

        if name is None:
            print("Please specify your name")

        if email is None:
            print("Please specify your pavilion email address")

        return False

    if args.NOTIFY is not None:
        notify = args.NOTIFY

    chm = chassis_manager.ChassisManager()
    success, error = chm.lock(lock_type, email, name, notify)

    if not success:
        print(error)
        return False

    return True


def lock_history(args):
    history = args.LOCK_HISTORY

    if history is None or history is False:
        return False

    chm = chassis_manager.ChassisManager()
    chm.print_lock_history()

    return True


def lock_owners(args):
    owners = args.LOCK_OWNERS

    if owners is None or owners is False:
        return False

    chm = chassis_manager.ChassisManager()
    chm.print_lock_owners()

    return True


def unlock(args):
    unlock = args.UNLOCK

    if unlock is None or unlock is False:
        return False

    email = args.EMAIL

    if email is None:
        print("Please specify your pavilion email address")
        return False

    chm = chassis_manager.ChassisManager()
    success, error, notified = chm.unlock(email)

    if not success:
        print(error)
        return False

    print(f"{notified!s} waiters notified")

    return True


def git_init(args):
    git_repo = args.REPO_PATH

    if git_repo is None or git_repo == '':
        print("Please specify the directory path")
        return False

    success, error = chassis_manager.init_git_repo(git_repo)
    if not success:
        print(error)
        return False

    return True


def init(args):
    init = args.INIT

    if init is None or init is False:
        return False

    name = args.CHNAME
    ip = args.CHIP

    if name is None or ip is None:
        if name is None:
            print("Please specify the chassis name")

        if ip is None:
            print("Please specify the chassis ip")

        return False

    chm = chassis_manager.ChassisManager(name, ip)
    chm.ch_init(name, ip)
    return True


def parse_user_args():
    parser = argparse.ArgumentParser(description="chassis ownership manager")

    parser.add_argument('--lock', action='store_true', dest="LOCK", required=False,
                        help="If you want to lock the chassis")

    parser.add_argument('--unlock', action='store_true', dest="UNLOCK", required=False,
                        help="If you want to unlock the chassis")

    parser.add_argument('--lock-type', dest="LOCK_TYPE", required=False,
                        help="Lock type. Exclusive/Sharing")

    parser.add_argument('--notify', action='store_true', dest="NOTIFY", required=False,
                        help="You will be notified over email when the chassis is free")

    parser.add_argument('--lock-history', action='store_true', dest="LOCK_HISTORY", required=False,
                        help="print the lock history")

    parser.add_argument('--lock-owners', action='store_true', dest="LOCK_OWNERS", required=False,
                        help="print the lock owners")

    parser.add_argument('--email', dest="EMAIL", required=False,
                        help="Your pavilion email id")

    parser.add_argument('--name', dest="NAME", required=False,
                        help="Your name")

    parser.add_argument('--git-init', dest="REPO_PATH", required=False,
                        help="Initialize a path as a git repository")

    parser.add_argument('--init', action='store_true', dest="INIT", required=False,
                        help="Initialize chassis manager")

    parser.add_argument('--chname', dest="CHNAME", required=False,
                        help="Chassis name")

    parser.add_argument('--chip', dest="CHIP", required=False,
                        help="Chassis ip")

    return parser.parse_args()


"""
******************************
******* The Main *************
******************************
"""

if __name__ == "__main__":
    args = parse_user_args()

    if lock(args):
        print("Lock acquired successfully")
        exit(0)

    if lock_history(args):
        exit(0)

    if lock_owners(args):
        exit(0)

    if unlock(args):
        print("Lock released successfully")
        exit(0)

    if init(args):
        print("Chassis initialized successfully")
        exit(0)

    if git_init(args):
        print("Git repository initialized successfully")
        exit(0)

    exit(1)
