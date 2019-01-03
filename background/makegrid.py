import json
import os
import sys
import shutil
import logging
from io import BytesIO

import redis

from PIL import Image, ImageDraw, ImageFont
from gevent import monkey

# patches stdlib (including socket and ssl modules) to cooperate with other greenlets
monkey.patch_all()

import gevent

import cloudinary
import cloudinary.uploader
import requests

# config
with open("config.json") as file:
    config = json.loads(file.read())

JSON_FOLDER = config["JSON_FOLDER"]
IMAGE_TEMP = config["IMAGE_TEMP"]

FONT = config["FONT"]
TEXT = config["TEXT"]

cloudinary.config(**config["CLOUDINARY"])

REDIS_ENDPOINT = config["REDIS_ENDPOINT"]
REDIS_PORT = config["REDIS_PORT"]
REDIS_PASSWORD = config["REDIS_PASSWORD"]

try:
    conn = redis.Redis(REDIS_ENDPOINT, REDIS_PORT, password=REDIS_PASSWORD)
except redis.RedisError:
    print("500")
    sys.exit()

log = logging.getLogger("bottomnine")
log.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler("bottomnine.log")
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level

# begin

username = sys.argv[1]
posts_path = "{}/{}.json".format(JSON_FOLDER, username)

if not os.path.isfile(posts_path):
    print("404")

    sys.exit()

print("200")  # allow flask to respond to request. remainder of command runs in background

try:

    with open(posts_path, encoding="utf-8") as file:
        posts = json.loads(file.read())

    # remove any posts not made in 2018

    MIN_TIME = 1514764800
    MAX_TIME = 1546300800

    # sort posts

    i = 0
    while i < len(posts):
        if not (MIN_TIME <= posts[i]["taken_at_timestamp"] < MAX_TIME):
            del posts[i]
        else:
            i += 1

    posts = sorted(posts, key=lambda p: p["edge_media_preview_like"]["count"])[:9]

    with open(posts_path, "w") as file:
        file.write(json.dumps(posts))


    # download images

    def download_file(url, path):
        r = requests.get(url)
        with open(path, "wb") as file:
            file.write(r.content)

        return True


    img_temp = "{}/{}".format(IMAGE_TEMP, username)

    if not os.path.exists(img_temp):
        os.makedirs(img_temp)

    tasks = []
    i = 0

    for post in posts:
        tasks.append(gevent.spawn(download_file, post["display_url"], "{}/{}.jpg".format(img_temp, i)))

        i += 1

    gevent.joinall(tasks, timeout=10)

    # determine grid size

    grid_size = 3

    if len(posts) < 9:
        grid_size = 2
        if len(posts) < 4:
            grid_size = 1

    cell_size = int(1200 / grid_size)

    # make grid !

    log.info("making grid", grid_size, username)

    img = Image.new("RGB", (1200, 1400), "white")

    i = 0
    for y in range(grid_size):
        for x in range(grid_size):
            to_paste = Image.open("{}/{}.jpg".format(img_temp, i))

            # make image square
            sx, sy = to_paste.size

            if sx != sy:
                if sx < sy:
                    # portrait
                    offset = (sy - sx) / 2
                    crop = (0, offset, sx, sy - offset)

                    to_paste = to_paste.crop(crop)
                else:
                    # landscape
                    offset = (sx - sy) / 2
                    crop = (offset, 0, sx - offset, sy)

                    to_paste = to_paste.crop(crop)

            # check whether downsizing or not
            mode = Image.ANTIALIAS if cell_size ** 2 > sx * sy else Image.BICUBIC

            to_paste = to_paste.resize((cell_size, cell_size), mode)

            img.paste(to_paste, (x * cell_size, y * cell_size))

            i += 1

            if i >= len(posts):
                break
        if i >= len(posts):
            break

    # add caption

    big = ImageFont.truetype(FONT, 64)
    small = ImageFont.truetype(FONT, 36)
    draw = ImageDraw.Draw(img)

    draw.rectangle((0, 1200, 1200, 1400), fill=(229, 45, 64))
    draw.rectangle((0, 1325, 1200, 1400), fill=(20, 20, 20))

    # big text
    tx, ty = draw.textsize(TEXT, big, spacing=6)
    draw.text((600 - tx / 2, 1255 - ty / 2), TEXT, fill=(255, 255, 255), font=big, spacing=6)

    # small text
    tx, ty = draw.textsize("paric.xyz", small, spacing=12)
    draw.text((600 - tx / 2, 1362 - ty / 2), "paric.xyz", fill=(255, 255, 255), font=small, spacing=12)

    buffer = BytesIO()

    img.save(buffer, "png")

    buffer.seek(0)

    resp = cloudinary.uploader.upload(buffer)

    conn.set("images.{}".format(username), resp["url"])

    log.info("upload successful")

    # delete tmp files and redis progress value

    shutil.rmtree(img_temp)
    os.remove("{}/{}.json".format(JSON_FOLDER, username))

    conn.delete(username)

except Exception as e:

    log.error(e.__class__.__name__ + ": " + str(e))
