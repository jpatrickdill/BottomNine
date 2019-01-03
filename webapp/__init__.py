from flask import Flask, send_from_directory

app = Flask(__name__, template_folder="./../templates/")

app.config.from_json("../config.json")

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
