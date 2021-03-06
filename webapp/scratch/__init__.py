import json
import logging

import requests
from authlib.client import OAuth2Session
from flask import request, session, Blueprint, render_template, redirect, url_for, abort

scratch = Blueprint("scratch", __name__)

from webapp import app, conn
from webapp.scratch.api import api as scratch_api

import random

log = logging.getLogger("bottomnine")
log.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler("bottomnine.log")
fh.setLevel(logging.DEBUG)

log.addHandler(fh)

# config

CLIENT_ID = app.config["CLIENT_ID"]
CLIENT_SECRET = app.config["CLIENT_SECRET"]

AUTH_URL = app.config["AUTH_URL"]
ACCESS_TOKEN_URL = app.config["ACCESS_TOKEN_URL"]

DISCORD_API_PREFIX = "https://discordapp.com/api/v6"


def random_pin(digits):
    return "".join([str(random.randrange(1, 10))] + [str(random.randrange(10)) for _ in range(digits - 1)])


@scratch.route("/")
def main():
    if "token" not in session:
        return render_template("scratch.html", logged_in=False)

    user_data = requests.get(DISCORD_API_PREFIX + "/users/@me", headers={
        "Authorization": session["token"]
    })

    # token no longer valid
    if user_data.status_code == 403:
        del session["token"]
        # reload
        return redirect(url_for("scratch.main"))

    user_data = user_data.json()

    # tell user if they're already verified
    scratch_user = conn.get("scratch:verified.{}".format(user_data["id"]))
    if scratch_user:
        scratch_user = json.loads(scratch_user)

    pin = random_pin(6)

    conn.set("scratch:verifying.{}".format(user_data["id"]), pin, ex=300)

    return render_template("scratch.html", logged_in=True, user_data=user_data, pin=pin, scratch_user=scratch_user)

@scratch.route("/docs/")
def api_docs():
    return render_template("scratch_API_docs.html")

@scratch.route("/cancel")
def cancel_login():
    del session["token"]
    # reload
    return redirect(url_for("scratch.main"))


@scratch.route("/discord")
def auth_url():
    oa2_session = OAuth2Session(CLIENT_ID, CLIENT_SECRET, scope="identify",
                                redirect_uri=url_for("scratch.oauth_complete",
                                                     _external=True))

    uri, state = oa2_session.create_authorization_url(AUTH_URL)

    session["state"] = state

    return redirect(uri)


@scratch.route("/discord/oa2comp")
def oauth_complete():
    state = session["state"]

    if "code" not in request.args:
        abort(403)

    oa2_session = OAuth2Session(CLIENT_ID, CLIENT_SECRET, state=state, scope="identify",
                                redirect_uri=url_for("scratch.oauth_complete",
                                                     _external=True))

    access_token = oa2_session.fetch_access_token(ACCESS_TOKEN_URL,
                                                  authorization_response=request.url)

    session["token"] = "Bearer " + access_token["access_token"]

    log.info("authorized user")

    return redirect(url_for("scratch.main"))
