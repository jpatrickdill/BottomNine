import logging
import platform
import subprocess

import redis
from flask import Blueprint, render_template, jsonify

bottom_nine = Blueprint("main", __name__)

from webapp import app

REDIS_ENDPOINT = app.config["REDIS_ENDPOINT"]
REDIS_PORT = app.config["REDIS_PORT"]
REDIS_PASSWORD = app.config["REDIS_PASSWORD"]

conn = redis.Redis(REDIS_ENDPOINT, REDIS_PORT, password=REDIS_PASSWORD)

log = logging.getLogger("bottomnine")
log.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler("bottomnine.log")
fh.setLevel(logging.DEBUG)

log.addHandler(fh)

# redis cache


# create console handler with a higher log level


python = "python3"
if platform.system() == "Windows":
    python = "python"


@bottom_nine.route("/")
def main():
    return render_template("bottom_nine.html", logged_in=False)


@bottom_nine.route("/top/<username>")
def get_top_posts(username):
    username = username.lower()

    proc = subprocess.Popen([python, "./background/scrape.py", username],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out = proc.stdout.read(3)

    return jsonify({
        "message": out,
        "error": ""
    })


@bottom_nine.route("/progress/<username>")
def get_progress(username):
    key = username.lower()

    if not conn.exists(key):
        return jsonify({
            "error": "user not being scanned",
            "status": 404
        }), 404

    progress = conn.get(key)

    if progress == "done":
        return jsonify({
            "progress": "100.0%",
            "finished": True,
            "status": 200
        })
    else:
        progress = "{0:.1f}%".format(eval(progress) * 100)

        return jsonify({
            "progress": progress,
            "finished": True if progress == "100.0%" else False,
            "status": 200
        })


@bottom_nine.route("/makegrid/<username>", methods=("POST",))
def make_image(username):
    username = username.lower()

    log.debug("make image request for {}".format(username))

    proc = subprocess.Popen([python, "./background/makegrid.py", username],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out = proc.stdout.read(3)

    if out == "404":
        return jsonify({
            "error": "user hasn't been scanned",
            "status": 404
        }), 404

    return jsonify({
        "message": "image being generated",
        "status": 200,
    })


@bottom_nine.route("/cdn/<username>")
def get_cdn_url(username):
    username = username.lower()
    key = "images.{}".format(username)

    log.debug("cdn requested for {}".format(username))

    if conn.exists(key):
        return jsonify({
            "exists": True,
            "url": conn.get(key)
        }), 200

    else:
        return jsonify({
            "exists": False,
        }), 200
