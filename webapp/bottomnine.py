import subprocess

import redis
from flask import Blueprint, render_template, jsonify

bottom_nine = Blueprint("main", __name__)

from webapp import app

REDIS_ENDPOINT = app.config["REDIS_ENDPOINT"]
REDIS_PORT = app.config["REDIS_PORT"]
REDIS_PASSWORD = app.config["REDIS_PASSWORD"]

conn = redis.Redis(REDIS_ENDPOINT, REDIS_PORT, password=REDIS_PASSWORD)


@bottom_nine.route("/")
def main():
    return render_template("bottom_nine.html", logged_in=False)


@bottom_nine.route("/top/<username>")
def get_top_posts(username):
    proc = subprocess.Popen(["python", "./background/makegrid.py", username],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out = proc.stdout.read(3)

    return jsonify({
        "message": out,
        "error": ""
    })


@bottom_nine.route("/progress/<username>")
def get_progress(username):
    key = username

    if not conn.exists(key):
        return jsonify({
            "error": "user not being scanned",
            "status": 404
        }), 404

    progress = conn.get(key)

    if progress == "done":
        return jsonify({
            "progress": "100.0%",
        })
    else:
        progress = "{0:.1f}%".format(eval(progress)*100)

        return jsonify({
            "progress": progress
        })
