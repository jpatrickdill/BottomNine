import subprocess

from flask import Blueprint, render_template, jsonify

bottom_nine = Blueprint("main", __name__)


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
