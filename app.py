from flask import Flask, render_template, request, make_response, redirect
import uuid
import json 
from datetime import datetime

app = Flask(__name__)

# ---- Route decorator calls ---- #

@app.route("/")
def index():
    # create response object with HTML page
    resp = make_response(render_template("boogle.html"))
    # set boogle_id cookie if doesn't already exist
    if request.cookies.get("boogle_id") == None:
        id = uuid.uuid4()
        resp.set_cookie("boogle_id", str(id), 999999999, None, "/", None, False, False, "Lax")
    
    return resp

@app.route("/jsontest")
def returnJSONTest():
    resp = {
        "data": "I am in CSE190/CSE291!"
    }
    return resp

@app.route("/search")
def search():
    query = request.args["q"]
    if (query != ""):
        time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S:%fZ")
        query = {
            "query": query,
            "ts": time
        }
        addSearchQuery(request.cookies["boogle_id"], query)
    
    return redirect("/")

@app.route("/api/history")
def displayHistory():
    # Get boogle_id from request cookies
    id = request.cookies.get("boogle_id")
    # Fetch python dictionary of user seraches by boogle_id
    userHistory = getUserHistory(id)
    return userHistory


# ---- Helper functions ---- #
# Adding user search query to database
def addSearchQuery(id: str, query: dict) -> None:
    # TODO create database
    # TODO implement adding to database
    print("Added " + query["query"] + " for " + id + " at " + query["ts"])

# Fetching data of a specific user
def getUserHistory(id: str | None) -> dict:
    # Add user searches into dictionary
    if id is None:
        # Hard code empty search history
        data = {
            "client_id": "",
            "seraches": []
        }
        return data
    else:
        # Fetch data from database
        # TODO change to fetch from database
        with open("history_example.json", "r") as file:
            data = json.load(file)

        return data
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)