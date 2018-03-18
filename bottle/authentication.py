from bottle import (get, post, route, response, run, redirect, request,
                    static_file, ServerAdapter, default_app)
import os
import uuid

import pw_store
import shared_cfg


def new_session():
    """Make a new session key, add to the response a cookie with the session
    key and return the new session key"""

    key = str(uuid.uuid4())

    response.set_cookie(shared_cfg.SESSION_COOKIE_NAME, key, secure=True)

    return key


def confirm_password_form(retry):
    form = '<form action="/first-time-setup" method="post">'
    if retry:
        form += "Entered passwords did not match. Please try again.</br>"
    form += '''
                Password database does not exist. Creating new one.</br>
                Password: <input name="password" type="password"/> </br>
                Re-enter Password: <input name="password2" type="password" />
                <input value="Create" type="submit" />
                </form>
            '''
    return form


@get('/first-time-setup')
def first_time_setup(retry=""):
    if not shared_cfg.pw_store:
        if not os.path.exists(shared_cfg.pw_store_filename):
            return confirm_password_form(False)
    return redirect("/")


@get('/first-time-setup-retry')
def first_time_setup_retry():
    if not shared_cfg.pw_store:
        if not os.path.exists(shared_cfg.pw_store_filename):
            return confirm_password_form(True)
    return redirect("/")


@post('/first-time-setup')
def do_first_time_setup():
    password = request.forms.get('password')
    password2 = request.forms.get('password2')
    if password == password2:
        shared_cfg.cv.acquire()
        shared_cfg.pw_store = pw_store.open_pw_store(password, shared_cfg.pw_store_filename)
        if shared_cfg.pw_store:
            shared_cfg.master_password = password
            shared_cfg.session_key = new_session()
        else:
            shared_cfg.master_password = None
        shared_cfg.cv.release()
        return redirect("/")
    else:
        return redirect("/first-time-setup-retry")


def change_master_password_form(bad_master, mismatch):
    form = '<form action="/change-master-password" method="post">'
    if bad_master:
        form += "Entered master password was incorrect. Please try again.</br>"
    if mismatch:
        form += "New passwords did not match. Please try again.</br>"
    form += '''
                Changing master password.</br>
                Existing Password: <input name="existing_password" type="password"/> </br>
                New Password: <input name="new_password" type="password"/> </br>
                Re-enter New Password: <input name="new_password_confirm" type="password" />
                <input value="Create" type="submit" />
                </form>
            '''
    return form


@get('/change-master-password')
def change_master_password():
    if shared_cfg.is_session_valid(request):
        return change_master_password_form(False, False)
    return redirect("/")


@get('/change-master-password-retry-bad-master')
def change_master_password_retry_bad_master():
    if shared_cfg.is_session_valid(request):
        return change_master_password_form(True, False)
    return redirect("/")


@get('/change-master-password-retry-mismatch')
def change_master_password_retry_mismatch():
    if shared_cfg.is_session_valid(request):
        return change_master_password_form(False, True)
    return redirect("/")


@post('/change-master-password')
def change_master_password():
    if shared_cfg.is_session_valid(request):
        existing_password = request.forms.get('existing_password')
        new_password = request.forms.get('new_password')
        new_password_confirm = request.forms.get('new_password_confirm')
        if existing_password != shared_cfg.master_password:
            return redirect("/change-master-password-retry-bad-master")
        if new_password != new_password_confirm:
            return redirect("/change-master-password-retry-mismatch")
        shared_cfg.cv.acquire()
        shared_cfg.master_password = new_password
        pw_store.save_pw_store(shared_cfg.pw_store, new_password, shared_cfg.pw_store_filename)
        shared_cfg.cv.release()
    return redirect("/")


def enter_password_form(retry):
    form = '<form action="/login" method="post">'
    if retry:
        form += "Entered password didn't work. Please try again.</br>"
    form += '''
                Password: <input name="password" type="password" />
                <input value="Login" type="submit" />
                </form>
            '''
    return form


@get('/login-retry')
def login_retry():
    if not shared_cfg.pw_store:
        if not os.path.exists(shared_cfg.pw_store_filename):
            return redirect("/first-time-setup")
        return enter_password_form(True)
    return redirect("/")


@get('/login')
def login():
    if not shared_cfg.pw_store:
        if not os.path.exists(shared_cfg.pw_store_filename):
            return redirect("/first-time-setup")
        return enter_password_form(False)
    return redirect("/")


@post('/login')
def do_login():
    password = request.forms.get('password')
    shared_cfg.cv.acquire()
    shared_cfg.pw_store = pw_store.open_pw_store(password, shared_cfg.pw_store_filename)
    if shared_cfg.pw_store:
        shared_cfg.master_password = password
        shared_cfg.session_key = new_session()
    else:
        shared_cfg.master_password = None
    shared_cfg.cv.release()
    if not shared_cfg.pw_store:
        return redirect("/login-retry")
    else:
        return redirect("/")
