# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import pyttsx3

import subprocess

import pyautogui
import os
from apps.home import blueprint
from flask import render_template, request
from flask_login import login_required
from jinja2 import TemplateNotFound
import threading
import time
import speech_recognition as sr

voice_id = "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0"

#Function to speak
def Speak(audio):
    engine = pyttsx3.init()
    # engine.setProperty("voice", voice_id)
    engine.setProperty("rate", 140)
    engine.say(audio)
    engine.runAndWait()

r = sr.Recognizer()

def recognize():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print('Listening')
        r.pause_threshold = 0.7
        audio = r.listen(source)
        try:
            print("Recognizing")
            Query = r.recognize_google(audio)
            print("You: '", Query, "'")
        except Exception as ex:
            print(ex)
            print("Pardon")
            return "None"
    import time
    time.sleep(2)
    return Query
    # with sr.Microphone() as source2:
    #     print("Recognising...\n")
    #     r.adjust_for_ambient_noise(source2, duration=0.2)
    #     audio = r.listen(source2)
    #     try:
    #         text = r.recognize_google(audio)
    #         return text
    #     except sr.UnknownValueError:
    #         print("Unable to recognize speech")
    #     except sr.RequestError as e:
    #         print("Error occurred during speech recognition:", str(e))

def detect_slideshow():
    while True:
        if "Slide Show" in pyautogui.getActiveWindowTitle():
            print("Switched to slideshow mode")
            while("Slide Show" in pyautogui.getActiveWindowTitle()):
                command = recognize()
                if "next" in command:
                    pyautogui.press("right")
                elif "previous" in command:
                    pyautogui.press("left")
                else:
                    pass
                time.sleep(1)
            print("Slideshow mode turned off")
        time.sleep(1)

def start_detecting_thread():
    detection_thread = threading.Thread(target=detect_slideshow)
    detection_thread.daemon = True
    detection_thread.start()

start_detecting_thread()


@blueprint.route("/index")
@login_required
def index():
    files = display_file()
    return render_template("home/index.html", segment="index",files=files)


@blueprint.route("/<template>")
@login_required
def route_template(template):
    try:
        if not template.endswith(".html"):
            template += ".html"

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template("home/page-404.html"), 404

    except:
        return render_template("home/page-500.html"), 500


@blueprint.route("/open_presentation", methods=["POST"])
def open_slideshow():
    powerpoint_path = "C:/Program Files/Microsoft Office/root/Office16/POWERPNT.EXE"
    file = request.files["file_path"]
    if file:
        file.save(f"./files/{file.filename}")
        try:
            file_path = "./files/"+file.filename
            # subprocess.Popen([powerpoint_path, "C:/Users/Asus/Desktop/python/app/test.pptx"])
            subprocess.Popen([powerpoint_path, file_path])
            pyautogui.sleep(2)
            pyautogui.press("f5")
            files = display_file()
            return render_template("home/index.html", segment="index", files=files)

        except Exception as e:
            return f"Error: {str(e)}"
    else:
        return "no file selected"

@blueprint.route("/display_filenames")
def display_file():
    files = os.listdir("files")
    return files



# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split("/")[-1]

        if segment == "":
            segment = "index"

        return segment

    except:
        return None
