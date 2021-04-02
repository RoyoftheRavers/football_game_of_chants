import os
import re
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


# validation functions
def validate_username(username):
    # validate username only allowing letters and numbers
    # mininimum chars 5/max 15
    return re.match("^[a-zA-Z0-9]{5, 15}$", username)


def validate_password(password):
    # validate password by only allowing min chars 5/max 15
    return re.match("^.{5, 15}$", password)


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_chants")
def get_chants():
    chants = list(mongo.db.chants.find())
    return render_template("chants.html", chants=chants)


@app.route("/register", methods=["GET", "POST"])
def register():
    # check if method is POST
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect((url_for("profile", username=session["user"])))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # check if method is POST
    if request.method == "POST":
        # check if username and password data is validated
        if request.form.get("username") == "" or validate_username(
          request.form.get("username").lower()):
            flash("Invalid username and/or password.")
            return redirect(url_for("login"))
        if request.form.get("password") == "" or validate_password(
          request.form.get("password")):
            flash("Invalid username and/or password.")
            return redirect(url_for("login"))

        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
              existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(
                    request.form.get("username")))
                return redirect(url_for(
                    "profile", username=session["user"]
                ))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been successfully logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_chant", methods=["GET", "POST"])
def add_chant():
    if request.method == "POST":
        chant = {
            "chant_title": request.form.get("chant_title"),
            "club_name": request.form.get("club_name"),
            "country": request.form.get("country"),
            "chant_lyrics": request.form.get("chant_lyrics")
        }
        mongo.db.chants.insert_one(chant)
        flash("Your chant was submitted, thank you!")
        return redirect(url_for("get_chants"))

    return render_template("add_chant.html")


@app.route("/edit_chant/<chant_id>", methods=["GET", "POST"])
def edit_chant(chant_id):
    if request.method == "POST":
        submit = {
            "chant_title": request.form.get("chant_title"),
            "club_name": request.form.get("club_name"),
            "country": request.form.get("country"),
            "chant_lyrics": request.form.get("chant_lyrics")
        }
        mongo.db.chants.update({"_id": ObjectId(chant_id)}, submit)
        flash("Chant Sucessfully Updated")

    chant = mongo.db.chants.find_one({"_id": ObjectId(chant_id)})
    return render_template("edit_chant.html", chant=chant)


@app.route("/delete_chant/<chant_id>")
def delete_chant(chant_id):
    mongo.db.chants.remove({"_id": ObjectId(chant_id)})
    flash("Chant Successfully Deleted")
    return redirect(url_for("get_chants"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
