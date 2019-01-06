import json
import logging

import requests
from authlib.client import OAuth2Session
from flask import request, session, Blueprint, render_template, redirect, url_for, abort, jsonify

scratch = Blueprint("scratch", __name__)

from webapp import app, conn
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

API_PREFIX = "https://discordapp.com/api/v6"

PROJECT_ID = "277359774"


def check_for_pin(pin):
    """Check for PIN in project comments and return username if verified."""

    comments = requests.get("https://api.scratch.mit.edu/projects/{}/comments?offset=0&limit=20".format(PROJECT_ID),
                            headers={
                                "Origin": "https://scratch.mit.edu",
                                "Referer": "https://scratch.mit.edu/projects/{}/".format(PROJECT_ID)
                            }).json()

    for comment in comments:
        if comment["content"] == str(pin):
            return {
                "id": comment["author"]["id"],
                "username": comment["author"]["username"]
            }

    return None


def random_pin(digits):
    return "".join([str(random.randrange(1, 10))] + [str(random.randrange(10)) for _ in range(digits - 1)])


@scratch.route("/")
def main():
    if "token" not in session:
        return render_template("scratch.html", logged_in=False)

    user_data = requests.get(API_PREFIX + "/users/@me", headers={
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


@scratch.route("/verified/")
def verified_yet():
    if "pin" not in request.args or "id" not in request.args:
        return jsonify({
            "verified": False,
            "error": "PIN and ID must be specified."
        }), 400

    pin = int(request.args["pin"])

    account_id = request.args["id"]

    expected = int(conn.get("scratch:verifying.{}".format(account_id)))

    if pin != expected:
        return jsonify({
            "verified": False,
            "error": "Invalid PIN or account ID."
        }), 400

    scratch_user = check_for_pin(pin)

    if scratch_user is not None:
        conn.set("scratch:verified.{}".format(account_id), json.dumps(scratch_user))
        conn.delete("scratch:verifying.{}".format(account_id))

        log.info("verified {}".format(scratch_user["username"]))

        return jsonify({
            "verified": True,
            "username": scratch_user["username"]
        }), 200

    return jsonify({
        "verified": False
    }), 200
