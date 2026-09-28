from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('boogle.html')

@app.route('/jsontest')
def returnJSONTest():
    response = {
        "data": "I am in CSE190/CSE291!"
    }
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="8000")
