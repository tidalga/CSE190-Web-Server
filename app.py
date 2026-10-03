from flask import Flask, render_template, request, make_response
import uuid 

app = Flask(__name__)

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="8000")
