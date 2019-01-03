import json
import sys
import os

username = sys.argv[1]
path = "background/scraper/{}.json".format(username)

if not os.path.isfile(path):
    print("404")

    sys.exit()

print("200")

with open(path, encoding="utf-8") as file:
    posts = json.loads(file.read())

# remove any posts not made in 2018

MIN_TIME = 1514764800
MAX_TIME = 1546300800

i = 0
while i < len(posts):
    if not (MIN_TIME <= posts[i]["taken_at_timestamp"] < MAX_TIME):
        del posts[i]
    else:
        i += 1

posts = sorted(posts, key=lambda p: p["edge_media_preview_like"]["count"])[:9]

with open(path, "w") as file:
    file.write(json.dumps(posts))


