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
    addRequest(request)
    resp = {
        "data": "I am in CSE190/CSE291!"
    }
    return resp

@app.route("/search")
def search():
    addRequest(request)
    query = request.args["q"]
    if (query != ""):
        addSearchQuery(request)
    
    return redirect("/", 303)

@app.route("/api/history")
def displayHistory():
    addRequest(request)
    # Get boogle_id from request cookies
    id = request.cookies.get("boogle_id")
    # Fetch python dictionary of user seraches by boogle_id
    userHistory = getUserHistory(id)
    return userHistory

@app.route("/dump")
def returnDump():
    addRequest(request)
    # Implement to use dump
    resp = {
        "clients": [
            {"client_id": "id"}
        ]
    }
    return resp

# ---- Helper functions ---- #
def addRequest(request) -> None:
    # Don't add request if id not initialized yet
    if request.cookies.get("boogle_id") == None:
        return
    # Connect to database
    with psycopg.connect(CONNECT_STR) as conn:
        # Initialize cursor for interacting with database
        with conn.cursor() as cur:
            # Insert request values into requests table
            id = request.cookies.get("boogle_id")
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
    # Get boogle_id from cookies
    id = request.cookies.get("boogle_id")
    if id is None:
        return
    # Adding user search query to database
    with psycopg.connect(CONNECT_STR) as conn:
        with conn.cursor() as cur:
            # Select most recent request to get request_id
            cur.execute("""
                SELECT * FROM requests WHERE client_id = %s ORDER BY request_id DESC
            """, (id,))
            row = cur.fetchone()
            request_id = ""
            # Checking there is at least one search
            if row:
                request_id = row[0] # 1st column in schema
            # Insert query to searches
            cur.execute("""
                INSERT INTO searches (client_id, request_id, query, ts) VALUES (%s, %s, %s, DEFAULT)
            """, (id, request_id, request.args["q"]))
            conn.commit()


# Fetching data of a specific user
def getUserHistory(id: str | None) -> dict:
    # TODO change to fetch from database
    data = {
        "client_id": "",
        "searches": []
    }
    if id is not None:
        data["client_id"] = id
        with psycopg.connect(CONNECT_STR) as conn:
            with conn.cursor() as cur:
                # Select searches by client_id
                cur.execute("""
                    SELECT * FROM searches WHERE client_id = %s
                """, (id,))

                # Add each search to searches array of data dictionary
                rows = cur.fetchall()
                for row in rows:
                    data["searches"].append({
                        "query": row[3],
                        "ts": row[4]
                    })

                conn.commit()

    return data
    

if __name__ == "__main__":
    # Initializing db connection info
    with open("connection_info.txt", "r") as file:
        CONNECT_STR = file.readline()
        file.close()

    app.run(host="0.0.0.0", port=8000, debug=False)