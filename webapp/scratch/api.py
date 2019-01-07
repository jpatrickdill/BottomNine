import json
import logging

import requests
from authlib.client import OAuth2Session
from flask import request, session, Blueprint, render_template, redirect, url_for, abort, jsonify

api = Blueprint("scratch.api", __name__)

from webapp import app, conn
import random

log = logging.getLogger("bottomnine")
log.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler("bottomnine.log")
fh.setLevel(logging.DEBUG)

log.addHandler(fh)

# config

PROJECT_ID = "277359774"

DISCORD_API_PREFIX = "https://discordapp.com/api/v6"


# /


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


@api.route("/verified/")
def verified_yet():
    if "pin" not in request.args or "id" not in request.args:
        return jsonify({
            "verified": False,
            "error": "PIN and ID must be specified."
        }), 400

    pin = int(request.args["pin"])

    account_id = request.args["id"]

    if pin is None or account_id is None:
        return jsonify({
            "verified": False,
            "error": "Invalid PIN or account ID."
        }), 400

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


@api.route("/unverify")
def unverify():
    if "token" not in session:
        return redirect(url_for("scratch.main"))

    user_data = requests.get(DISCORD_API_PREFIX + "/users/@me", headers={
        "Authorization": session["token"]
    })

    # token no longer valid
    if user_data.status_code == 403:
        del session["token"]
        # reload-
        return redirect(url_for("scratch.main"))

    user_data = user_data.json()

    # tell user if they're already verified
    conn.delete("scratch:verified.{}".format(user_data["id"]))

    return redirect(url_for("scratch.main"))


@api.route("/user/<int:discord_id>")
def get_user(discord_id):
    """Return Scratch user info from Discord ID"""

    scratch_user = conn.get("scratch:verified.{}".format(discord_id))
    if not scratch_user:
        return jsonify({
            "verified": False
        }), 404

    scratch_user = json.loads(scratch_user)

    return jsonify({
        "user": scratch_user,
        "verified": True
    }), 200
