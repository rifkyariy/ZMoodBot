# import json
# import shlex

from bot import startBot, stopBot
import threading

# zoom
from pyzoom import ZoomClient
import http.client

from flask import Flask, request           # import flask
app = Flask(__name__)             # create an app instance b

@app.route("/")
def hello():
 return "its Bot" 

@app.route("/triggerBot" ,methods=['POST']) 
def triggerBot():
  # global room_id,passcode,intervals,meeting_id,started_session
  room_id = request.form['room_id'] # sing seko zoom
  passcode = request.form['passcode']
  intervals = request.form['intervals']
  meeting_id = request.form['meeting_id'] # to firestore
  
  print(meeting_id)
  t = threading.Thread(target=startBot, args=[room_id, passcode, meeting_id, intervals])
  t.setDaemon(False)
  # starting the thread
  t.start()
  
  # started_session = 1
  return("session started")

@app.route("/endBot" ,methods=['GET']) 
def endBot():
  stopBot()
  
  return("Bot Shut Down")

if __name__ == "_main_":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

