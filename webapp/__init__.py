from flask import Flask, send_from_directory
from flask_caching import Cache


app = Flask(__name__, template_folder="./../templates/")

app.config.from_json("../config.json")

# redis cache
cache = Cache(app, config={
    "CACHE_TYPE": "redis",

    "CACHE_DEFAULT_TIMEOUT": app.config["CACHE_TIMEOUT"],
    "CACHE_KEY_PREFIX": "cache.",
    "CACHE_REDIS_HOST": app.config["REDIS_ENDPOINT"],
    "CACHE_REDIS_PORT": app.config["REDIS_PORT"],
    "CACHE_REDIS_PASSWORD": app.config["REDIS_PASSWORD"],

    "CACHE_REDIS_DB": 0,
})

from webapp.bottomnine import bottom_nine

app.register_blueprint(bottom_nine)


@app.route("/css/<path:path>")
def css(path):
    return send_from_directory("../static", path)


# add google analytics code

ANALYTICS = app.config.get("ANALYTICS")
if ANALYTICS:
    @app.context_processor
    def inject_analytics():
        return dict(analytics=ANALYTICS)

###

if __name__ == "__main__":
    app.run("localhost", 3000, debug=True)
