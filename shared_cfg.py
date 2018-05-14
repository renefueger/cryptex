from datetime import datetime, timedelta
import logging
import threading
import uuid

import pw_store


class LockWrapper:
    """Wraps a lock object to make it easier to enable/disable the lock."""
    def __init__(self, enable):
        if enable:
            self.lock = threading.RLock()
        else:
            self.lock = None

    def acquire(self, block=False):
        if self.lock:
            return self.lock.acquire(block)
        else:
            return True

    def release(self):
        if self.lock:
            self.lock.release()


config_lock = LockWrapper(True)

SESSION_COOKIE_NAME = "cryptex-session-id"
ILLEGAL_NAME_CHARS = pw_store.ILLEGAL_NAME_CHARS


class Session:
    def __init__(self):
        self.key = None
        self.last_active_time = None
        self.timeout_seconds = 60 * 5
        self.path = "/"


session = None

keyboard_mode = False
master_password = None
pw_store_filename = "/home/pi/master_store.enc"
master_store = None


log = logging.getLogger(__name__)


def login(password):
    global config_lock, master_store, pw_store_filename, master_password

    config_lock.acquire()
    try:
        master_store = pw_store.open_pw_store(password, pw_store_filename)
        if master_store:
            master_password = password
        else:
            master_password = None
    finally:
        config_lock.release()
    return master_password is not None


def change_master_password(password):
    global config_lock, master_password, master_store, pw_store_filename

    config_lock.acquire()
    try:
        if master_store and master_password:
            master_password = password
            master_store.save(password, pw_store_filename)
    finally:
        config_lock.release()


def new_session(response):
    """Creates a new session and adds to the response a cookie with the session
    key"""
    global config_lock, session

    config_lock.acquire()
    try:
        session = Session()

        session.key = str(uuid.uuid4())
        response.set_cookie(SESSION_COOKIE_NAME, session.key, secure=True)
        session.last_active_time = datetime.now()
    finally:
        config_lock.release()

    log.debug("Creating new session with key '{0}'".format(session.key))


def validate_session(request):
    """ Returns True if there is a current session and its session ID matches
    the session ID of the passed-in request. If the session is valid, the
    session timeout will be reset. """
    global config_lock, session

    if not session:
        log.debug("Session invalid due to no session object")
        return False

    if not session.last_active_time:
        log.debug("Session invalid due to no last active time")
        return False

    if does_session_match(request.get_cookie(SESSION_COOKIE_NAME)):
        delta = datetime.now() - session.last_active_time
        log.debug("Session timeout delta: {0}".format(delta.total_seconds()))
        if delta.total_seconds() <= session.timeout_seconds:
            log.debug("Session valid; resetting timeout")
            config_lock.acquire()
            session.last_active_time = datetime.now()
            config_lock.release()
            return True

        log.debug("Session invalid due to timeout")
        config_lock.acquire()
        session = None
        config_lock.release()
    else:
        log.debug("Session invalid due to cookie mismatch")

    return False


def is_session_active():
    """ Returns True if there is an active session."""
    global session

    return session is not None


def does_session_match(cookie):
    global session

    return cookie and session and session.key and cookie == session.key


def is_in_keyboard_mode():
    global keyboard_mode

    return keyboard_mode


def add_entry(ent, ent_name):
    global config_lock, master_store, pw_store_filename, master_password, session

    config_lock.acquire()
    try:
        if master_store and master_password:
            master_store.add_entry(ent, ent_name, session.path)
            master_store.save(master_password, pw_store_filename)
    finally:
        config_lock.release()


def add_container(cont, cont_name):
    global config_lock, master_store, pw_store_filename, master_password, session

    config_lock.acquire()
    try:
        if master_store and master_password:
            master_store.add_container(cont, cont_name, session.path)
            master_store.save(master_password, pw_store_filename)
    finally:
        config_lock.release()


def change_session_path(path):
    global config_lock, session
    config_lock.acquire()
    session.path = path
    config_lock.release()


def get_entries_by_path(path):
    global master_store

    if master_store:
        return master_store.get_entries_by_path(path)

    return []


def get_containers_by_path(path):
    global master_store

    if master_store:
        return master_store.get_containers_by_path(path)

    return []


def save_pw_store():
    global config_lock, master_store, pw_store_filename, master_password

    config_lock.acquire()
    try:
        if master_store and master_password:
            master_store.save(master_password, pw_store_filename)
    finally:
        config_lock.release()


def activate_keyboard_mode():
    global config_lock, keyboard_mode, master_store, master_password, session

    config_lock.acquire()
    save_pw_store()
    master_password = None
    session = None
    keyboard_mode = True
    config_lock.release()


def lock_store():
    global config_lock, master_store, master_password, session

    config_lock.acquire()
    try:
        save_pw_store()
        master_store = None
        master_password = None
        session.key = None
    finally:
        config_lock.release()
