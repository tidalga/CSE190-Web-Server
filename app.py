from flask import Flask, render_template, request, make_response, redirect
import uuid
import json 

app = Flask(__name__)

# ---- Route decorator calls ---- #

@app.route('/')
def index():
    # create response object with HTML page
    resp = make_response(render_template('boogle.html'))
    # set boogle_id cookie if doesn't already exist
    if request.cookies.get('boogle_id') == None:
        id = uuid.uuid4()
        resp.set_cookie('boogle_id', str(id), 999999999, None, '/', None, False, False, 'Lax')
    
    return resp

@app.route('/jsontest')
def returnJSONTest():
    resp = {
        "data": "I am in CSE190/CSE291!"
    }
    return resp

@app.route('/search')
def search():
    query = request.args['q']
    if (query != ""):
        print("search: " + query)
        addSearchQuery(request.cookies["boogle_id"], query)
    
    return redirect("/")

@app.route("/api/history")
def displayHistory():
    # Get user_id
    id = getUserIDFromCookies(request.cookies)
    # Fetch python dictionary of user seraches by boogle_id
    userHistory = getUserHistory(id)
    return userHistory


# ---- Helper functions ---- #
def getUserIDFromCookies(cookies: dict[str, str]) -> str | None:
    id = None
    if ("boogle_id" in cookies):
        id = cookies["boogle_id"]
        print("getUserIDFromCookies: id = " + id)
    
    return id

# Adding user search query to database
def addSearchQuery(id: str, query: str) -> None:
    # TODO create database
    # TODO implement adding to database
    print("Added " + query + " for " + id)

# Fetching data of a specific user
def getUserHistory(id: str | None) -> dict:
    # Add user searches into dictionary
    if id is None:
        print("getUserHistory: Hardcoding default history")
        # Hard code empty search history
        data = {
            "client_id": "",
            "seraches": []
        }
        return data
    else:
        # Fetch data from database
        print("getUserHistory: Fetching data from database")
        # TODO change to fetch from database
        with open("history_example.json", "r") as file:
            data = json.load(file)

        return data
    

if __name__ == "__main__":
    print("does this work")
    app.run(host="0.0.0.0", port=8000)