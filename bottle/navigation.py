from bottle import (post, redirect, request, route, template)
import logging

import shared_cfg
import manage_passwords

log = logging.getLogger(__name__)


@route('/lock')
def lock():
    if shared_cfg.validate_session(request):
        log.debug("Locking the whole thing down")
        shared_cfg.lock_store()
        return template("locked.html")
    return redirect("/")


@route('/activate')
def activate():
    if shared_cfg.validate_session(request):
        log.debug("Activating the device")
        shared_cfg.activate_keyboard_mode()
        return template("keyboard-mode.html")
    return redirect("/")


@route('/master-pass')
def master_pass():
    if shared_cfg.validate_session(request):
        log.debug("Changing master password")
        return redirect("/change-master-password")
    return redirect("/")


@route('/manage')
def manage():
    if shared_cfg.validate_session(request):
        log.debug("Managing passwords")
        return manage_passwords.manage_path("=")
    return redirect("/")


@post('/footer')
def handle_main_menu_post():
    log.debug("Handling main menu post")
    if shared_cfg.validate_session(request):
        if request.forms.get("lock"):
            return redirect("/lock")
        elif request.forms.get("activate"):
            return redirect("/activate")
        elif request.forms.get("master_pass"):
            return redirect("/master-pass")
        elif request.forms.get("manage"):
            return redirect("/manage")
    return redirect("/")

