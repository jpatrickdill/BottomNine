from flask import Flask, send_from_directory, render_template

# from flask_caching import Cache

app = Flask(__name__, template_folder="./../templates/")

app.config.from_json("../config.json")

# redis cache
# cache = Cache(app, config={
#     "CACHE_TYPE": "redis",
#
#     "CACHE_DEFAULT_TIMEOUT": app.config["CACHE_TIMEOUT"],
#     "CACHE_KEY_PREFIX": "cache.",
#     "CACHE_REDIS_HOST": app.config["REDIS_ENDPOINT"],
#     "CACHE_REDIS_PORT": app.config["REDIS_PORT"],
#     "CACHE_REDIS_PASSWORD": app.config["REDIS_PASSWORD"],
#
#     "CACHE_REDIS_DB": 0,
# })

from webapp.bottomnine import bottom_nine

app.register_blueprint(bottom_nine, url_prefix="/bottom-nine")


@app.route("/css/<path:path>")
def css(path):
    return send_from_directory("../static", path)


# add google analytics code

ANALYTICS = app.config.get("ANALYTICS")
if ANALYTICS:
    @app.context_processor
    def inject_analytics():
        return dict(analytics=ANALYTICS)


# front page #

@app.route("/")
def front_page():
    return render_template("front_page.html")


# basic pages

@app.route("/python/")
def python_projects():
    return render_template("python.html")


###

if __name__ == "__main__":
    app.run("localhost", 3000, debug=True)
