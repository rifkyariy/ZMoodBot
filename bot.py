# basic things
import time
import datetime
from datetime import datetime as dt
import os
import json

# screenshooting
import pyautogui

# image processing
from PIL import Image
import cv2

# request
import requests

# firebase
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# firebase config
# change this .json to your firestore service account
cred = credentials.Certificate("zmood_firebase.json") 
firebase_admin.initialize_app(cred)
db = firestore.client()

# date Time
todayDate = datetime.date.today()
hour = str(datetime.datetime.now())[11:13]
minute = str(datetime.datetime.now())[14:16]

# screen size
screenWidth, screenHeight = pyautogui.size()

# meeting 
firebaseMeetingId = ""

# open zoom function
def openZoom(meetingID, password):
  time.sleep(5)
  # Using Mac OS as Bot
  # Open Zoom Via Mac Spotlight
  pyautogui.hotkey('command', 'space') 
  pyautogui.typewrite('Zoom')
  pyautogui.hotkey('enter')
  
  # Join Meeting 
  time.sleep(2)
  pyautogui.hotkey('command', 'j') 
  pyautogui.typewrite(meetingID)
  pyautogui.hotkey('enter') 
  time.sleep(3)
  pyautogui.typewrite(password)
  pyautogui.hotkey('enter') 
  
  # Change Screen Layout
  # time.sleep(4)
  # pyautogui.hotkey('command','shift','w') 
  
  return {
    "status": "success",
    "data": "zoom opened"
  } 
  
def takeScreenshoot() :
  # directory Location
  DIR_NAME = "./data/raw"
  
  os.chdir(DIR_NAME) # change directory to save screenshot
  filename = str(todayDate)+'.png' 
  
  time.sleep(5)
  pyautogui.screenshot(filename)
  
  img = cv2.pyrDown(cv2.imread(filename, cv2.IMREAD_UNCHANGED))
  cv2.imwrite(filename, img)
  # cropedImage = img[100:screenHeight-200, 0:screenWidth]  # crop to remove dock and top navbar
  # cv2.imwrite(filename, cropedImage)

  return str(todayDate)+'.png'
  
intervalIndex = 0
def addIntervalIndex():
  global intervalIndex
  intervalIndex = intervalIndex + 1
  
def cropImage(imagePath):
  # input image
  img = cv2.pyrDown(cv2.imread(imagePath, cv2.IMREAD_UNCHANGED))

  # increase contrast and  brightness 
  alpha = 2 # contrast control (1.0-3.0)
  beta = 10 # brightness control (0-100)

  # adjusted image
  adjusted = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)

  # threshold image
  # ret, threshed_img = cv2.threshold(cv2.cvtColor(adjusted, cv2.COLOR_BGR2GRAY), 89, 255, cv2.THRESH_BINARY) # used when small box or max participant -> 25 participant
  ret, threshed_img = cv2.threshold(cv2.cvtColor(adjusted, cv2.COLOR_BGR2GRAY), 127, 255, cv2.THRESH_BINARY) # used when large box or minim participant 
  
  # find contours and get the external one
  contours, hier = cv2.findContours(threshed_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
  
  maxArea = 0 # define max area of rectangle to get best match display box
  for c in contours:
    x, y, w, h = cv2.boundingRect(c) # get contour x, y, width, hight from image
    if w*h >= maxArea: # get max or biggest area so we can define limit below the max
      maxArea = w*h - (1 / 3 * w*h)

  nameIndex = 0 # define name index, used to write imagae name
  for c in contours:
    # get the bounding rect
    x, y, w, h = cv2.boundingRect(c)
    if(w*h >= maxArea ):
      cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
      # draw a green rectangle to visualize the bounding rect
      
      # crop image inside bounding rectangle
      cropedImage = img[y:y+h, x:x+w]
      nameImage = cropedImage[h-50:h, 0:250]
      
      # print(os.path.exists("data/processed/"+str(intervalIndex)))
      if not os.path.exists("data/processed/"+str(intervalIndex)):
        os.makedirs("data/processed/"+str(intervalIndex))
      
      cv2.imwrite("data/processed/"+str(intervalIndex)+"/participantName_"+str(nameIndex)+".png", nameImage)
      cv2.imwrite("data/processed/"+str(intervalIndex)+"/participantFace_"+str(nameIndex)+".png", cropedImage)
      nameIndex=nameIndex+1

  # print count of contour
  print(len(contours))
  print("Done croping Image")
  
  addIntervalIndex()
  
  # draw contour on image
  # cv2.drawContours(img, contours, -1, (255, 255, 0), 1)
  
  cv2.imshow("contours", img)
  
  while True:
      key = cv2.waitKey(1)
      if key == 27: #ESC key to break
          break

  cv2.destroyAllWindows()

def detectFace(imagePath):
  imgName = os.path.basename(imagePath)
  img = cv2.imread(imagePath, cv2.IMREAD_GRAYSCALE)
  face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
  
  faces_detected = face_cascade.detectMultiScale(img, scaleFactor=1.1, minNeighbors=5)
  (x, y, w, h) = faces_detected[0]
  
  # cropedImage = img[y:y+h, x:x+w]
  # cv2.imwrite("data/processed/"+str(imgName), cropedImage)
  
  # cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 1)
  # cv2.imshow("face detected", img)
  
  return {
    "status": "success",
    "data": {
      "message": "face detected",
      "imagePath": imagePath
    }
  }

def detectText(textImagePath):
  import os
  os.environ['GOOGLE_APPLICATION_CREDENTIALS'] ='vision.json'
  
  from google.cloud import vision
  import io
  
  client = vision.ImageAnnotatorClient()

  with io.open(textImagePath, 'rb') as image_file:
      content = image_file.read()

  image = vision.Image(content=content)

  response = client.text_detection(image=image)
  texts = response.text_annotations
      
  status = "fail"
  data = "Text Not Detected"
  
  if texts:
    status = "success"
    data = texts[0].description

  if response.error.message:
      raise Exception(
          '{}\nFor more info on error messages, check: '
          'https://cloud.google.com/apis/design/errors'.format(
              response.error.message))
  
  return {
    "status": status,
    "data": data
  }

def detectExpression(imagePath):
  imgName = os.path.basename(imagePath)
  
  files = {'participant': open(imagePath, 'rb')}
  # res = requests.post("https://a35738977da0.ngrok.io/predict", files=files)
  res = requests.post("https://flaskappzm-t2yoqcmfca-et.a.run.app/predict", files=files)
  
  print(res.text)

  expression = json.loads(res.text)['data']
  
  return {
      "status": "success",
      "data": expression,
    }

# expression count
inactive= 0
angry=0
sad=0
fear=0
disgust=0
neutral=0
surprise=0
happy=0

def addExpression(expression):
  global inactive,angry,sad,fear,disgust,neutral,surprise,happy
  if(expression == "inactive"):
    inactive += 1
  elif(expression == "angry"):
    angry += 1
  elif(expression == "sad"):
    sad += 1
  elif(expression == "fear"):
    fear += 1
  elif(expression == "disgust"):
    disgust += 1
  elif(expression == "neutral"):
    neutral += 1
  elif(expression == "surprise"):
    surprise += 1
  elif(expression == "happy"):
    happy += 1

activeParticipants = []
inactiveParticipants = []
def groupParticipant(participant, status):
  global activeParticipants,inactiveParticipants
  
  if (status == 0):
    inactiveParticipants.append(participant)
  else:
    activeParticipants.append(participant)
    if(participant in inactiveParticipants):
      inactiveParticipants.remove(participant)
      
def addParticipant():
  for activeName in activeParticipants:
    participant = {
      "meeting_id": firebaseMeetingId,
      "name": activeName,
      "status": 1
    }
    
    db.collection('meeting_participants').add(participant)
    
  for inactiveName in inactiveParticipants:
    participant = {
      "meeting_id": firebaseMeetingId,
      "name": inactiveName,
      "status": 0
    }
    db.collection('meeting_participants').add(participant)
  
def screenshootCycle():
  time.sleep(5)
  print("cycle running")
  filename = takeScreenshoot()
  cropImage("/data/raw/"+str(filename))
  # cropImage("./data/raw/duar.png")

  fileCount = int(len(next(os.walk('./data/processed/'+str(intervalIndex - 1)))[2]) / 2)
  
  for image in range(fileCount):
    # check expression if active
    expression = detectExpression('./data/processed/'+str(intervalIndex - 1)+'/participantFace_'+str(image)+'.png')
    participantExpression = "inactive"
    
    if(expression['status'] == "success"):
      participantExpression = expression['data']['expression']
      
    # check text name if active
    participantName = detectText('./data/processed/'+str(intervalIndex - 1)+'/participantName_'+str(image)+'.png')   
    if(participantName['status'] == "success"):
      participantName = participantName['data']
    else:
      # check text name if inactive
      participantNameAlt = detectText('./data/processed/'+str(intervalIndex - 1)+'/participantFace_'+str(image)+'.png')
      if(participantNameAlt['status'] == "success"):
        participantName = participantNameAlt['data']
        participantExpression = "inactive"
      else:
        participantName = "Name Not Found"
    
    print(participantExpression)
    addExpression(participantExpression)
    
    participant = {
      "name": participantName,
      "meeting_id": firebaseMeetingId,
      "status": ( 1 if participantExpression != "inactive" else 0)
    }
    
    print(participant) 
    groupParticipant(participantName, ( 1 if participantExpression != "inactive" else 0) )
  
  timeline = {
    "timestamp":  intervalIndex - 1,
    "classification_0": inactive,
    "classification_1": angry,
    "classification_2": sad,
    "classification_3": fear,
    "classification_4": disgust,
    "classification_5": neutral,
    "classification_6": surprise,
    "classification_7": happy,
    "meeting_id": firebaseMeetingId
  }
  
  db.collection('meeting_recaps').add(timeline)

stopNow = 0
starttime = time.time()

def setMeetingId(meetId):
  global firebaseMeetingId
  firebaseMeetingId = meetId

def startBot(roomId, passCode,meetId, intervals = 3):
  openZoom(roomId, passCode)
  setMeetingId(meetId)
  print("meetid : "+str(meetId))
  
  # if not stopNow: threading.Timer(intervals * 60, screenshootCycle).start()
  while stopNow != 1:
    setStart()
    screenshootCycle()
    
    time.sleep(float(intervals) * 60.0 - ((time.time() - starttime) % float(intervals) * 60.0))

def stopBot():
  addParticipant()
  global stopNow
  stopNow = 1
  
def setStart():
  global stopNow
  stopNow = 0

# cropImage("./data/raw/2021-06-09.png")
cropImage("./data/raw/sample.png")
# cropImage("./duar.png")
# print(detectExpression("./data/processed/0/participantFace_2.png") )

# cropImage
# startBot("meet_id","passcode","nCm7LooVn7P8bcZ6sDfl")
# openZoom('93880473900','3NGKh9')