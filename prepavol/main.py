import os
import logging
import urllib
from datetime import datetime, timezone
from flask import (
    Blueprint,
    render_template,
    flash,
    session,
    redirect,
    request,
    url_for,
    send_from_directory,
)
from .logbook import FlightLog
from .planes import WeightBalance, PlanePerf
from .forms import PrepflightForm


main = Blueprint("main", __name__)

# Global variables
pilot = None
flightlog = None
logbook = None


def get_aero():
    """Retrieves flight log data from aerogest
    """
    global pilot, flightlog, logbook

    if pilot:
        if pilot["username"] != session["username"]:
            pilot = None

    if not pilot or not flightlog:
        logging.info("CALLING AEROGEST AGAIN")
        pilot = {"username": session["username"], "password": session["password"]}
        flightlog = FlightLog(pilot)
        logbook = flightlog.logbook


@main.route("/login", methods=["GET", "POST"])
def login():
    print(request.referrer)
    if "username" in session.keys():
        flash("Already logged in.")
        return redirect(url_for("main.profile"))
        # return redirect(request.referrer)

    if request.method == "POST":
        username = request.form.get("name")
        password = request.form.get("password")

        session["username"] = username
        session["password"] = password

        return redirect(url_for("main.profile"))

    return render_template(("login.html"))


@main.route("/logout")
def logout():
    if "username" in session.keys():
        session.clear()
    pilot = None
    flightlog = None
    logbook = None
    return redirect(url_for("main.prepflight"))


@main.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(main.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@main.route("/profile")
def profile():
    if "username" not in session.keys():
        return redirect(url_for("main.login"))

    get_aero()
    return render_template(
        "profile.html", name=session["username"], dataframe=logbook.to_html(index=None)
    )


@main.route("/stats")
def stats():
    if "username" not in session.keys():
        return redirect(url_for("main.login"))

    get_aero()
    flightstats = flightlog.log_agg()
    last_quarter = flightlog.last_quarter().to_html(index=True)
    flightstats_html = [k.to_html(index=True) for k in flightstats]
    return render_template(
        "stats.html",
        name=session["username"],
        dataframes=flightstats_html,
        last_quarter=last_quarter,
    )


@main.route("/", methods=["GET", "POST"])
def prepflight():
    # form defaults
    form = PrepflightForm()

    if request.method == "POST":
        if form.validate_on_submit():
            # WeightBalance accepts extra parameters - full dict is Ok
            plane = WeightBalance(**form.data)

            if not plane.is_ready_to_fly:
                flash("Chargement invalide", "error")
                return render_template("prepflight.html", form=form, plane=plane)

            tkoff = PlanePerf(
                plane.planetype,
                plane.auw,
                form.data["tkalt"],
                form.data["tktemp"],
                form.data["tkqnh"],
            )
            ldng = PlanePerf(
                plane.planetype,
                plane.auw,
                form.data["ldalt"],
                form.data["ldtemp"],
                form.data["ldqnh"],
            )

            # Get plot images
            balance_img = plane.plot_balance(encode=True)
            tkoff_data = tkoff.predict("takeoff").to_html()
            tkoff_img = tkoff.plot_performance("takeoff", encode=True)
            ldng_data = ldng.predict("landing").to_html()
            ldng_img = ldng.plot_performance("landing", encode=True)

            timestamp = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M %Z")

            return render_template(
                "report.html",
                form=form,
                plane=plane,
                timestamp=timestamp,
                balance=urllib.parse.quote(balance_img),
                takeoff_data=tkoff_data,
                takeoff=urllib.parse.quote(tkoff_img),
                landing_data=ldng_data,
                landing=urllib.parse.quote(ldng_img),
            )

        else:
            logging.error(form.errors)

    return render_template("prepflight.html", form=form)

