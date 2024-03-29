# *_* coding: utf-8 *_*

"""Flask views."""

import os
import logging
import urllib
from datetime import datetime, timezone
from PythonMETAR.metar import NOAAServError
import jsonpickle
import pandas as pd
import PythonMETAR

from flask import (
    abort,
    Blueprint,
    current_app,
    render_template,
    flash,
    session,
    redirect,
    request,
    url_for,
    send_from_directory,
)

from .emport_carburant import EmportCarburant

from .emport_carburant_form import EmportCarburantForm
from .ads import ADs
from .oils import Avgas
from .logbook import FlightLog
from .planes import WeightBalance
from .plane_perf import PlanePerf
from .forms import PrepflightForm
from .connexion_form import ConnexionForm
from .links import Links

main = Blueprint("main", __name__)


def get_aerogest_data(current_data):
    """Retrieve flight log data from aerogest.

    It detects a change of aerogest user to refresh the data
    or returns the current data if no change.

    Stores a new dictionary in session variable aerogest_data:
    - pilot: dictionary of username/password
    - flightlog: serialized instance of FlightLog class

    Adds session variable is_logged from FlightLog is_logged attribute.
    """
    if not current_data:
        # Initializing a dict of aerogest data
        # (pilot and flightlog)
        current_data = {}
        session["aerogest_data"] = {}

    if current_data == {} or current_data["pilot"]["username"] != session["username"]:
        new_data = {}
        logging.info("Calling aerogest")
        new_data["pilot"] = {
            "username": session["username"],
            "password": session["password"],
        }
        flightlog = FlightLog(new_data["pilot"], log_format="json")
        # Serialize the instance of FlightLog
        new_data["flightlog"] = jsonpickle.encode(flightlog)

        session["aerogest_data"] = new_data
        session["is_logged"] = flightlog.is_logged


@main.route("/login", methods=["GET", "POST"])
def login():
    """Login to Aerogest Online web site."""
    abort(400)
    if session.get("is_logged"):
        flash("Already logged in.")
        return redirect(url_for("main.profile"))
        # return redirect(request.referrer)

    if request.method == "POST":
        username = request.form.get("name")
        password = request.form.get("password")

        session["username"] = username
        session["password"] = password

        get_aerogest_data(session.get("aerogest_data"))

        if not session.get("is_logged"):
            flash("Wrong username or password")
            return redirect(url_for("main.login"))

        return redirect(url_for("main.profile"))

    return render_template(("login.html"))


@main.route("/logout")
def logout():
    """Logout from Aerogest Online."""
    abort(400)
    if "username" in session.keys():
        session.clear()
    return redirect(url_for("main.welcome"))


@main.route("/favicon.ico")
def favicon():
    """Define static path for site favicon."""
    return send_from_directory(
        os.path.join(main.root_path, current_app.config["STATIC_FOLDER"]),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@main.route("/profile")
def profile():
    """Display aerogest log book."""
    abort(400)
    # Gets back to login page if first time or aerogest login failed
    if "username" not in session.keys() or not session.get("is_logged"):
        logging.warning("User %s not logged", session.get("username"))
        return redirect(url_for("main.login"))

    get_aerogest_data(session.get("aerogest_data"))

    # Otherwise display logbook
    flightlog = jsonpickle.decode(session.get("aerogest_data")["flightlog"])
    logbook = pd.read_json(flightlog.logbook, convert_dates=False)
    return render_template(
        "profile.html", name=session["username"], dataframe=logbook.to_html(index=None)
    )

@main.route("/connexion", methods=["GET", "POST"])
def connexion():
    """Route pour connecter le pilote."""
    form = ConnexionForm()

    if session.get("is_logged"):
        flash("Already logged in.")
        return redirect(url_for("main.welcome"))

    if request.method == "POST":
        if form.validate_on_submit():
            # WeightBalance accepts extra parameters - full dict is Ok
            session["pilot_name"] = form.pilot_name.data.upper()
            flash("Vous êtes bien enregistré", "success")
            return redirect(url_for("main.welcome"))
            
    return render_template("connexion.html", form=form)

@main.route("/fleet")
def fleet():
    """Display planes characteristics."""
    club = session.get("club")
    planes = WeightBalance.load_fleet_data()
    return render_template("fleet.html", data=planes, club=club)


@main.route("/stats")
def stats():
    """Aerogest log data aggregated."""
    abort(400)
    if "username" not in session.keys():
        return redirect(url_for("main.login"))

    get_aerogest_data(session.get("aerogest_data"))

    # Deserialize the instance of FlightLog
    flightlog = jsonpickle.decode(session.get("aerogest_data")["flightlog"])

    flightstats = flightlog.log_agg()
    flightstats_html = [k.to_html(index=True) for k in flightstats]

    last_quarter_html = flightlog.last_quarter().to_html()

    return render_template(
        "stats.html",
        name=session.get("club"),
        dataframes=flightstats_html,
        last_quarter=last_quarter_html,
    )

@main.get("/")
def welcome():
    name = session.get("name")
    metar = session.get("metar")
    if metar is not None:
        flash(metar, "info")
    return render_template(
        "welcome.html",
        name=name,
        session=session
        )

@main.route("/pilot/<string:name>")
def set_club(name):
    session["name"] = name
    flash("Votre nom a bien été enregistré", "success")
    return redirect(url_for("main.welcome"))

@main.route("/disconnect")
def disconnect():
    session.clear()
    flash("Vous êtes déconnecté", "info")
    return redirect(url_for("main.welcome"))

@main.route("/devis", methods=["GET", "POST"])
def prepflight():
    """Form for flight preparation."""
    # form defaults + fuel calculation
    form = PrepflightForm(**session)

    if request.method == "POST":
        if form.validate_on_submit():
            # WeightBalance accepts extra parameters - full dict is Ok
            plane = WeightBalance(**form.data)

            if not plane.is_ready_to_fly:
                flash("Chargement invalide", "danger")
                return render_template("prepflight.html", form=form, plane=plane)

            if not plane.active_plane:
                flash("Cet avion est désactivé pour des raisons de sécurité", "warning")

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
            tkoff_data = tkoff.predict("takeoff", form.data.get("rvt")).to_html()
            tkoff_Zp = f"{tkoff.Zp:.0f}"
            tkoff_Zd = f"{tkoff.Zd:.0f}"
            tkoff_img = tkoff.plot_performance("takeoff", encode=True)
            ldng_data = ldng.predict("landing", form.data.get("rvt")).to_html()
            ldng_Zp = f"{ldng.Zp:.0f}"
            ldng_Zd = f"{ldng.Zd:.0f}"
            ldng_img = ldng.plot_performance("landing", encode=True)

            timestamp = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M %Z")

            if form.data["tkaltinput"] == "" or not form.data["tkaltinput"]:
                tkAD = None
            else:
                tkAD = ADs(form.data["tkaltinput"].upper())
            
            if form.data["ldaltinput"] == "" or not form.data["ldaltinput"]:
                ldAD = None
            else:
                ldAD = ADs(form.data["ldaltinput"].upper())

            if not plane.is_valid_weight():
                flash(f"La date de validité de la dernière pesée est échue depuis {plane.humanized_last_weight_difference}", "warning")
            carbu = None
            if session.get("report_carburant") is not None:
                carbu = session.get("carbu")

            return render_template(
                "report.html",
                form=form,
                plane=plane,
                timestamp=timestamp,
                balance=urllib.parse.quote(balance_img),
                takeoff_data=tkoff_data,
                tkoff_Zp=tkoff_Zp,
                tkoff_Zd=tkoff_Zd,
                takeoff=urllib.parse.quote(tkoff_img),
                landing_data=ldng_data,
                ldng_Zp=ldng_Zp,
                ldng_Zd=ldng_Zd,
                landing=urllib.parse.quote(ldng_img),
                tkAD=tkAD,
                ldAD=ldAD,
                carbu=carbu
            )

        logging.error(form.errors)

    return render_template("prepflight.html", form=form)

@main.route("/carburant", methods=["GET","POST"])
def emport_carburant():
    form = EmportCarburantForm(**session)
    timestamp = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M %Z")

    if request.method == "POST":       
        if form.validate_on_submit():
            carbu = EmportCarburant(**form.data)

            if not carbu.authorized():
                flash(f"Prévoyez un complément de carburant car il manque {carbu.hum_compared_fuel()} litres de carburant.", "error")
                return render_template("carburant.html", form=form)

            session["leftwingfuel"] = carbu.carburant_emporte_wings / 2
            session["rightwingfuel"] = carbu.carburant_emporte_wings / 2
            session["auxfuel"] = carbu.carburant_emporte_aux
            session["mainfuel"] = carbu.carburant_emporte_main
            session["callsign"] = carbu.callsign
            session["pilot_name"] = form.pilot_name.data

            if "Enregistrer" in form.submit.raw_data:
                session["carbu"]=carbu
                session["report_carburant"]=True
                flash("Votre rapport d'emport de carburant a bien été enregistré et sera affiché lorsque vous aurez réalisé le devis de masse et centrage","info")
                return redirect(url_for("main.prepflight"))
            else:
                session["report_carburant"]=False
                return render_template(
                    "report_carburant.html", 
                    carbu=carbu,
                    timestamp=timestamp
                    )

        logging.error(form.errors)
        return render_template("carburant.html", form=form)

    metar = session.get("metar")
    logging.info(metar)
    if metar is not None:
        flash(metar, "info")
    return render_template("carburant.html", form=form)

@main.post("/validate")
def validateForm():
    form = PrepflightForm()

    if form.validate_on_submit():
        return "", 204
    
    return form.errors, 422

@main.get("/essence")
def essence():
    if not request.args:
        abort(404)
    oil = Avgas(request.args.get('type'))
    return {'density': oil.density, 'title':oil.title}

@main.get("/ad")
def aerodrome():
    if not request.args:
        abort(404)

    terrain = ADs(request.args.get('code').upper())
    return {
        'code': terrain.code,
        'var': terrain.var,
        'geo': terrain.point,
        'nom': terrain.nom, 
        'alt': terrain.alt, 
        'trafic': terrain.trafic,
        'statut': terrain.statut
        }

@main.get("/metar/<string:station>")
def metar(station):
    if not station or not station.upper().startswith("LF"):
        abort(403)
    try:
        metar = PythonMETAR.Metar(station.upper())
        if metar:
            session["tktemp_metar"] = station
            session["tktemp"] = metar.temperatures["temperature"]
            session["tkqnh"] = metar.qnh
            session["metar"] = metar.metar
            return metar.getAll()
    except NOAAServError:
        abort(404)
    abort(400)

@main.get("/kiosk")
def kiosk():
    year=datetime.now().year
    short="ACDN"
    long="Aéroclub des Navigants"
    useragent=None
    if request.user_agent.browser != "chrome":
        useragent=request.user_agent.browser
        flash("Le navigateur Edge n'est pas supporté par OpenFlyers.")
    links = Links().links
    return render_template("pwa.html", year=year, short=short, long=long, error=useragent, links=links)
