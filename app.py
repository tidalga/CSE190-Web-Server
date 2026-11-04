import flask
from flask import Flask, render_template, request, make_response, redirect
from datetime import datetime
from pathlib import Path
import requests as rq
import uuid
import psycopg
import sys
import json

p3 = Path(__file__).resolve().parent / "part3"
sys.path.append(str(p3))

import classifier as cs # type: ignore (fixed with path appending)

app = Flask(__name__)
CONNECT_STR = ""
classifier = None

# ---- Route decorator calls ---- #
@app.route("/")
def index():
    # create response object with HTML page
    resp = make_response(render_template("new_boogle.html"))
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
    
    #addRequest(request)
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

@app.route("/ad")
def displayAd():
    # Fetch user history from database
    userHistory = getUserHistory(request.cookies.get("boogle_id"))
    # Format user searches into array
    userHistoryArr = extractSearches(userHistory["searches"])
    assert(classifier is not None)
    labels = classifier.generateLabels(userHistoryArr)
    # Remove 'unknown' labels, format into list
    labelsArr = classifier.prepLabelsForRTB(labels)
    # Format OpenRTB request
    requestSpecs = getRTBRequestSpecs()
    rtbRequest = formatRTBRequest(labelsArr, request, requestSpecs)
    # Handle request
    ad = getAd(rtbRequest, requestSpecs)
    # Display ad
    if (ad is not None):
        return ad
    return ('', 200)

@app.route("/ad/feedback", methods=["POST"])
def handleFeedback():
    return ('', 200)

# ---- Helper functions ---- #
def currTime() -> str:
    #return datetime.now().strftime("%Y-%m-%dT%H:%M:%S:%fZ")
    time = str(datetime.now())
    return time

def extractSearches(userHistory: list[dict]) -> list[str]:
    searchesArr = []
    for i in range(len(userHistory)):
        searchesArr.append(userHistory[i]["query"])

    return searchesArr

def getRTBRequestSpecs() -> dict:
    return {
        "id": str(uuid.uuid4()),
        "impid": "1",
        "bidFloor": 0.5,
        "width": 300,
        "height": 250,
        "badv": []
    }

def formatRTBRequest(labels: list[str], request: flask.Request, requestSpecs: dict) -> str:
    rtbRequest = {
        "id": requestSpecs["id"],
        "imp": [{
            "id": requestSpecs["impid"],
            "tagid": "boogle-top",
            "banner": {"format": [{"w": 300, "h": 250}]},
            "bidfloor": requestSpecs["bidFloor"]
        }],
        "device": {
            "ua": request.user_agent.string,
            "ip": request.access_route[0]
        },
        "user": {
            "id": request.cookies.get("boogle_id"),
            "data": [{
                "id": "boogle",
                "name": "boogle_inferred",
                "segment": labels,
                "ext": {"segtax": 500}
            }]
        },
        "tmax": 250,
        "badv": requestSpecs["badv"]
    }
    return json.dumps(rtbRequest)

def makeRTBRequest(rtbRequest: str) -> list:
    dsps = ["steady", "niche", "shady", "glitch"]
    responses = []

    for dsp in dsps:
        try:
            response = rq.post("https://webtracking.sysnet.ucsd.edu/pa1/rtb/" + dsp + "/bid", rtbRequest, timeout=0.25)
            if (response is None or response.status_code == 204):
                continue # Don't add to array
            responses.append(response)
        except rq.exceptions.Timeout:
            # Ignore if request time passes
            continue
        

    return responses

def isValidAd(bid, requestSpecs: dict):
    valid = True
    # Perform validation checks
    if (bid.get("w") != requestSpecs.get("width") or
        bid.get("h") != requestSpecs.get("height") or
        bid.get("impid") != requestSpecs.get("impid") or
        bid.get("price") < requestSpecs.get("bidFloor")):
        return False

    return valid

def chooseAd(responses: list[rq.Response], requestSpecs: dict) -> dict:
    bestBid = None
    secondBest = None
    
    for resp in responses:
        try:
            respDict = json.loads(resp.text)
            #print(respDict)
        except:
            # Ad format is invalid, skip
            continue
        # Check if currency is
        if (respDict.get("cur") != "USD"):
            continue
        
        seatBids = respDict.get("seatbid")
        for seatBid in seatBids:
            bidList = seatBid.get("bid")
            for bid in bidList:
                if (not isValidAd(bid=bid, requestSpecs=requestSpecs)):
                    continue
                if (bestBid is None):
                    bestBid = bid
                elif (bid.get("price") > bestBid.get("price")):
                    # Replace best with new bid, set second to old best
                    secondBest = bestBid
                    bestBid = bid
                elif (secondBest is None or bid.get("price") > secondBest.get("price")):
                    # Replace secondBest with new bid
                    secondBest = bid
    
    return {
        "bestBid": bestBid,
        "secondBest": secondBest
    } 

def chargeAd(adPair: dict, requestSpecs: dict):
    best = adPair["bestBid"]
    secondBest = adPair["secondBest"]
    bestPrice = 0
    secondBestPrice = 0

    if (best is None):
        return
    if (secondBest is not None):
        secondBestPrice = secondBest.get("price")

    bestPrice = best.get("price")
    price = min(bestPrice, max(secondBestPrice, requestSpecs["bidFloor"]) + 0.01)
    burl = best.get("burl")
    # Remove price part from burl
    burlList = burl.split("?")
    burl = burlList[0] + "?price=" + price
    response = rq.get(url=burl, timeout=5)

def getAd(rtbRequest: str, requestSpecs: dict):
    responses = makeRTBRequest(rtbRequest)
    bidPair = chooseAd(responses, requestSpecs)
    if (bidPair["bestBid"] is not None):
        ad = bidPair["bestBid"].get("adm")
        chargeAd(bidPair, requestSpecs)
        return ad
    else:
        return None

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
    with open("part2/connection_info.txt", "r") as file:
        CONNECT_STR = file.readline()
        file.close()

    classifier = cs.Classifier()

    app.run(host="0.0.0.0", port=8000, debug=True)