from __future__ import print_function

import json
import platform
import subprocess
import sys
import re

import redis
import requests

# instagram profile data
profile_data = re.compile(r'window\._sharedData = (.+);<\/')

# load config
with open("config.json") as file:
    config = json.loads(file.read())

REDIS_ENDPOINT = config["REDIS_ENDPOINT"]
REDIS_PORT = config["REDIS_PORT"]
REDIS_PASSWORD = config["REDIS_PASSWORD"]

IG_USER = config["INSTAGRAM_USER"]
IG_PASS = config["INSTAGRAM_PASS"]

JSON_FOLDER = config["JSON_FOLDER"]



def eprint(*args, **kwargs):
    """
    Prints to STDERR
    """

    if "end" not in kwargs:
        kwargs["end"] = ""

    print(*args, **kwargs)

    sys.exit()


def get_user_info(user):
    resp = requests.get("https://instagram.com/{}/".format(user))

    if resp.status_code >= 400:
        return 404

    resp = resp.text
    data = profile_data.search(resp)

    if data:
        data = json.loads(data.group(1))

        return data["entry_data"]["ProfilePage"][0]["graphql"]["user"]
    else:
        return 404


username = sys.argv[1]

# verify that account exists before continuing
info = get_user_info(username)
if info == 404:
    eprint("404")

if info["is_private"]:
    eprint("PRV")

num_posts = info["edge_owner_to_timeline_media"]["count"]

try:
    conn = redis.Redis(REDIS_ENDPOINT, REDIS_PORT, password=REDIS_PASSWORD)

    key = username

    if conn.exists(key):
        eprint("ABG".format(username))

    print("SCN")

    conn.set(key, "0/{}".format(num_posts), ex=400)

    cmd = ["instagram-scraper", username, "--media-types", "none", "--media-metadata",
         "--destination", JSON_FOLDER,
         "-u", IG_USER, "-p", IG_PASS]

    if platform.system() == "Windows":
        cmd = ["python", "background/instagram-scraper-script.py", username, "--media-types", "none", "--media-metadata",
         "--destination", JSON_FOLDER,
         "-u", IG_USER, "-p", IG_PASS]

    # begin media search process
    process = subprocess.Popen(
        ,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    progress = process.stderr.read(64)

    while progress:
        try:
            media = re.search(r" (\d+) media ", progress.decode("utf-8"))

            if media:
                media = int(media.group(1))

                conn.set(key, "{}/{}".format(media, num_posts))
        except Exception as e:
            conn.set(key, str(e))

        progress = process.stderr.read(64)

    conn.set(key, "{0}/{0}".format(num_posts))

    print()
except redis.RedisError as e:
    eprint(e)
