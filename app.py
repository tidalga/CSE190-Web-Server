from flask import Flask, render_template, request, make_response, redirect
import uuid
from datetime import datetime
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
        addClient(str(id), request)
    else:
        # Update last seen for client
        updateClient(request)
    
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
    query = request.args.get("q")
    if (query is not None and query.strip() != ""):
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
    dump = getDump()
    return dump

# ---- Helper functions ---- #
def currTime() -> str:
    #return datetime.now().strftime("%Y-%m-%dT%H:%M:%S:%fZ")
    time = str(datetime.now())
    return time

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
            time = currTime()
            values = {
                "id": id, "ip": request.access_route[0], "time": time, "referer": request.referrer, "path": request.path
            }
            cur.execute("""
                INSERT INTO requests (client_id, ts, ip, referer, path)
                VALUES (%(id)s, %(time)s, %(ip)s, %(referer)s, %(path)s)
            """, values)
            conn.commit()

def addClient(id: str, request):
    with psycopg.connect(CONNECT_STR) as conn:
        # Initialize cursor for interacting with database
        with conn.cursor() as cur:
            # Add new row for client
            time = currTime()
            latest_ip = str(request.access_route[0])
            ips = [latest_ip]
            cur.execute("""
                INSERT INTO clients (client_id, first_seen, last_seen, latest_ip, ips) VALUES (%(id)s, %(time)s, %(time)s, %(latest_ip)s, %(ips)s)
            """, {"id": id, "time": time, "latest_ip": latest_ip, "ips": ips})
            conn.commit()

def updateClient(request):
    # Updating last seen of client
    with psycopg.connect(CONNECT_STR) as conn:
        with conn.cursor() as cur:
            # Fetch information from request
            id = request.cookies.get("boogle_id")
            latest_ip = str(request.access_route[0]) # array of client IPs
            # Fetch array of previously used IPs
            cur.execute("""
                SELECT * FROM clients WHERE client_id = %s
            """, (id,))
            row = cur.fetchone()
            ips = None
            if row:
                # Fetch array of previous IPs
                ips = row[4]
                addToList = True
                # Check if IP already exists
                for ip in ips:
                    if (ip == latest_ip):
                        addToList = False
                        break
                if addToList:
                    ips.append(latest_ip)
            # Update values in table
            time = currTime()
            cur.execute("""
                UPDATE clients 
                SET last_seen = %(time)s,
                latest_ip = %(latest_ip)s,
                ips = %(ips)s
                WHERE client_id = %(client_id)s
            """, {"time": time, "latest_ip": latest_ip, "client_id": id, "ips": ips})
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
                INSERT INTO searches (client_id, request_id, query, ts) VALUES (%s, %s, %s, %s)
            """, (id, request_id, request.args["q"], currTime()))
            conn.commit()


# Fetching data of a specific user
def getUserHistory(id: str | None) -> dict:
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
                    SELECT * FROM searches WHERE client_id = %s ORDER BY request_id DESC
                """, (id,))

                # Add each search to searches array of data dictionary
                rows = cur.fetchall()
                for row in rows:
                    data["searches"].append({
                        "query": row[3],
                        "ts": str(row[4]) # Object is a datetime object, use now() and convert to str
                    })

                conn.commit()

    return data

def getDump() -> dict:
    dump = {
        "clients": []
    }
    # Add info of each client
    with psycopg.connect(CONNECT_STR) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM clients")
            row = cur.fetchone()

            while (row):
                # Get history data of user
                userHistory = getUserHistory(row[0])
                # Fetch info of each user frin row
                client = {
                    "client_id": row[0],
                    "first_seen": str(row[1]),
                    "last_seen": str(row[2]),
                    "latest_ip": row[3],
                    "ips": row[4],
                    "searches": userHistory.get("searches")
                }
                dump["clients"].append(client)
                row = cur.fetchone()

            cur.close()
            conn.commit()
                

    return dump


if __name__ == "__main__":
    # Initializing db connection info
    with open("connection_info.txt", "r") as file:
        CONNECT_STR = file.readline()
        file.close()

    app.run(host="0.0.0.0", port=8000, debug=True)