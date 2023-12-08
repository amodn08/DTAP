# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, redirect, request, url_for
from flask_login import current_user, login_user, logout_user
from flask_dance.contrib.github import github

from apps import db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.authentication.models import Users

from apps.authentication.util import verify_pass
import sounddevice as sd
import soundfile as sf
import numpy as np

import librosa
import numpy as np
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
import os
import joblib

sample_rate = 44100 
duration = 1
num_of_samples = 1
current_usr = ""

sentences = ["Machine learning 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20",
             "Birds can be found in every Habitat, from the tundra to the arid desert, and come in a dizzying array of shapes, sizes, and colours",
             "For many people, birds are simply beings that exist outside their windows or that they might see on a nature hike",
             "Bird watching can be a relaxing hobby or a lifelong passion, and it offers a unique opportunity to connect with nature",
             "Each time you go bird watching, you have the chance to encounter new species and learn more about the incredible world we live in",
             "When you think about recycling, you might simply think about throwing your soda cans and plastic bottles into a blue bin",
             "However, recycling is much more complicated than that – and it’s important to understand how the process works to do it effectively",
             "Most recycling plants require that different types of plastics be separated before they can be recycled",
             "This is because different types of plastics are made of different chemicals, and mixing them can contaminate the batch",
             "Well, for one thing, it takes a lot less energy to recycle a plastic bottle than it does to create a new one from scratch",
             "Additionally, recycling helps to reduce the amount of plastic waste that ends up in our landfills and oceans"]


def extract_features(file_path):
    audio, sample_rate = librosa.load(file_path, res_type='kaiser_fast')
    mfccs = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=35)
    mfccs_scaled = np.mean(mfccs.T, axis=0)
    return mfccs_scaled

def train_model():
    global current_usr
    data_dir = 'C:/Users/Asus/.vscode/DTAP/voice samples'

    features = []
    labels = []

    for user_folder in os.listdir(data_dir):
        user_folder_path = os.path.join(data_dir, user_folder)
        if os.path.isdir(user_folder_path):
            for file_name in os.listdir(user_folder_path):
                file_path = os.path.join(user_folder_path, file_name)
                if file_path.endswith('.flac' or '.wav'):
                    extracted_features = extract_features(file_path)
                    features.append(extracted_features)
                    labels.append(user_folder)
                    print(f"Done extracting features from {file_name}")

    data_dir = 'C:/Users/Asus/.vscode/DTAP/samples'
    for file_name in os.listdir(data_dir):
        file_path = os.path.join(data_dir, file_name)
        if file_path.endswith('.flac' or '.wav'):
            extracted_features = extract_features(file_path)
            features.append(extracted_features)
            labels.append(current_usr)
            print(f"Done extracting features from {file_name}")


    # print("Done")
    X = np.array(features)
    y = np.array(labels)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = SVC(kernel='linear', probability=True)
    model.fit(X_train, y_train)

    joblib.dump(model, 'SVC_model_34ssamples.joblib')

    y_train_pred = model.predict(X_train)
    train_accuracy = np.mean(y_train_pred == y_train)

    y_test_pred = model.predict(X_test)
    test_accuracy = np.mean(y_test_pred == y_test)

    print("\nTraining Accuracy:", train_accuracy)
    print("\nTesting Accuracy:", test_accuracy)

    print("\nClassification Report:")
    print(classification_report(y_test, y_test_pred))


@blueprint.route("/")
def route_default():
    return redirect(url_for("authentication_blueprint.login"))


# Login & Registration


@blueprint.route("/github")
def login_github():
    """Github login"""
    if not github.authorized:
        return redirect(url_for("github.login"))

    res = github.get("/user")
    return redirect(url_for("home_blueprint.index"))


@blueprint.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm(request.form)
    if "login" in request.form:
        # read form data
        user_id = request.form["username"]  # we can have here username OR email
        password = request.form["password"]

        # Locate user
        user = Users.find_by_username(user_id)

        # if user not found
        if not user:
            user = Users.find_by_email(user_id)

            if not user:
                return render_template(
                    "accounts/login.html", msg="Unknown User or Email", form=login_form
                )

        # Check the password
        if verify_pass(password, user.password):
            login_user(user)
            return redirect(url_for("authentication_blueprint.route_default"))

        # Something (user or pass) is not ok
        return render_template(
            "accounts/login.html", msg="Wrong user or password", form=login_form
        )

    if not current_user.is_authenticated:
        return render_template("accounts/login.html", form=login_form)

    return redirect(url_for("home_blueprint.index"))


@blueprint.route("/register", methods=["GET", "POST"])
def register():
    global current_usr
    create_account_form = CreateAccountForm(request.form)
    if "register" in request.form:
        username = request.form["username"]
        email = request.form["email"]
        current_usr = username


        # Check usename exists
        user = Users.query.filter_by(username=username).first()
        if user:
            return render_template(
                "accounts/register.html",
                msg="Username already registered",
                success=False,
                form=create_account_form,
            )

        # Check email exists
        user = Users.query.filter_by(email=email).first()
        if user:
            return render_template(
                "accounts/register.html",
                msg="Email already registered",
                success=False,
                form=create_account_form,
            )

        # else we can create the user
        user = Users(**request.form)
        db.session.add(user)
        db.session.commit()

        # Delete user from session
        logout_user()

        return render_template(
            "accounts/register.html",
            msg="User created successfully.",
            success=True,
            form=create_account_form,
        )

    else:
        return render_template("accounts/register.html", form=create_account_form)


@blueprint.route("/record_voice", methods=["GET", "POST"])
def record():
    return render_template("accounts/record_voice.html", text = sentences[0])

@blueprint.route("/record_samples", methods=["GET","POST"])
def record_samples():
    global num_of_samples
    audio = sd.rec(int(sample_rate*duration), samplerate=sample_rate, channels=1) 
    sd.wait()
    file_path = f"samples/{num_of_samples}.flac"
    sf.write(file_path, audio, sample_rate)
    num_of_samples += 1
    print(num_of_samples)
    if(num_of_samples<=10):
        return render_template('accounts/record_voice.html', text = sentences[0])
    elif(num_of_samples<21):
        return render_template('accounts/record_voice.html', text = sentences[num_of_samples-10])
    else:
        return redirect(url_for("authentication_blueprint.login"))


@blueprint.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("authentication_blueprint.login"))


# Errors
@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template("home/page-403.html"), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template("home/page-403.html"), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template("home/page-404.html"), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template("home/page-500.html"), 500
