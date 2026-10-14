from flask import Flask, render_template, request, make_response, redirect
import uuid
import json
import psycopg

app = Flask(__name__)
CONNECT_STR = ""

# ---- Route decorator calls ---- #

@app.route("/")
def index():
    # create response object with HTML page
    resp = make_response(render_template("boogle.html"))
    id = request.cookies.get("boogle_id")
    # set boogle_id cookie if doesn't already exist
    if id == None:
        id = uuid.uuid4()
        resp.set_cookie("boogle_id", str(id), 999999999, None, "/", None, False, False, "Lax")
        # Add user to clients database
        initializeClient(str(id))
    else:
        # Update last seen for client
        updateClient(str(id))
    
    addRequest(request)
    return resp

@app.route("/jsontest")
def returnJSONTest():
    resp = {
        "data": "I am in CSE190/CSE291!"
    }
    addRequest(request)
    return resp

@app.route("/search")
def search():
    query = request.args["q"]
    if (query != ""):
        addSearchQuery(request)
    
    addRequest(request)
    return redirect("/", 303)

@app.route("/api/history")
def displayHistory():
    # Get boogle_id from request cookies
    id = request.cookies.get("boogle_id")
    # Fetch python dictionary of user seraches by boogle_id
    userHistory = getUserHistory(id)
    addRequest(request)
    return userHistory

@app.route("/dump")
def returnDump():
    # Implement to use dump
    resp = {
        "clients": [
            {"client_id": "id"}
        ]
    }
    return resp

# ---- Helper functions ---- #
def addRequest(request) -> None:
    # Connect to database
    with psycopg.connect(CONNECT_STR) as conn:
        # Initialize cursor for interacting with database
        with conn.cursor() as cur:
            # Insert request values into requests table
            id = request.cookies["boogle_id"]
            values = {
                "id": id, "ip": request.access_route[0], "referer": request.referrer, "path": request.path
            }
            cur.execute("""
                INSERT INTO requests (client_id, ts, ip, referer, path)
                VALUES (%(id)s, DEFAULT, %(ip)s, %(referer)s, %(path)s)
            """, values)
            conn.commit()

def initializeClient(id: str):
    with psycopg.connect(CONNECT_STR) as conn:
        # Initialize cursor for interacting with database
        with conn.cursor() as cur:
            # Add new row for client
            cur.execute("""
                INSERT INTO clients (client_id, first_seen, last_seen) VALUES (%s, DEFAULT, DEFAULT)
            """, (id,))
            conn.commit()

def updateClient(id: str):
    # Updating last seen of client
    with psycopg.connect(CONNECT_STR) as conn:
        with conn.cursor() as cur:
            # Update value in table
            cur.execute("""
                UPDATE clients 
                SET last_seen = DEFAULT
                WHERE client_id = %(client_id)s
            """, {"client_id": id})
            conn.commit()


def addSearchQuery(request):
    # Adding user search query to database
    print("Adding search into searches table")
    # with psycopg.connect(CONNECT_STR) as conn:
        
    #         # Initialize cursor for interacting with database
    #         with conn.cursor() as cur:
    #             # Add search into searches table
    #             cur.execute("""
    #                 INSERT INTO clients (client_id, first_seen, last_seen) VALUES (%s, DEFAULT, DEFAULT)
    #             """, (id,))
    #             conn.commit()


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
    # Initializing db connection info
    with open("connection_info.txt", "r") as file:
        CONNECT_STR = file.readline()
        file.close()

    app.run(host="0.0.0.0", port=8000)