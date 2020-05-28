import pandas as pd
import numpy as np
import datetime
import sys
from io import StringIO
from bs4 import BeautifulSoup
import requests
import getpass

class FlightLog:
    """
    """


    def __init__(self, user):
        self.user = user
        self.logbook = self.get_log()


    def get_log(self):
        user = self.user
        
        POSTLOGINURL = (
            "http://www.aerogest-reservation.com/connection/logon?aeroclub=aeroclub_camargue"
        )
        REQUESTURL = "https://www.aerogest-reservation.com/Account/MyPilotLogBook"
        payload = {
            "aeroclub": "aeroclub_camargue",
            "login": user["username"],
            "pass": user["password"],
            "conserverconnexion": "true",
        }

        with requests.Session() as session:
            try:
                _ = session.post(POSTLOGINURL, data=payload)
                r = session.get(REQUESTURL)
            except:
                return None
        # If logged in, should be able to find specific div
        lookfor = {"class": "divMonCarnetDeVols"}
        soup = BeautifulSoup(r.content, features="lxml")
        is_logged = soup.find("div", lookfor) is not None
        if not is_logged:
            return None

        logbook = pd.read_html(
            r.content,
            attrs={"class": "classTableVols"},
            header=1,
            encoding="utf-8",
            parse_dates=True
        )[0]
        logbook = logbook.iloc[:-1, :]

        logbook["Temps (hh:mm)"] = logbook["Temps (hh:mm)"].apply(
           lambda x: f"0 days {int(x[0]):02}:{x[-2:]}:00.000000"
        )
        logbook["Temps (hh:mm)"] = pd.to_timedelta(logbook["Temps (hh:mm)"])
        logbook.rename(columns={"Temps (hh:mm)":"Heures"}, inplace=True)
        logbook["Type"].replace(regex={r"^DR400$": "DR400-140B"}, inplace=True)
        logbook["Type"].replace(regex={r"^DR\s400*": "DR400"}, inplace=True)

        return logbook#.style.set_table_styles(htmlstyle).render()

    @staticmethod
    def heures(s):
        a = int(np.sum(s) / np.timedelta64(1, "h"))
        b = int(
            60 * (np.sum(s) / np.timedelta64(1, "h") - np.sum(s) // np.timedelta64(1, "h"))
        )
        return f"{a}h{b:02}"


    def log_agg(self, columns=[]):
        """columns array of columns
        """
        aggcols = ["Type", "Immat", "Mode", "Vol", "Type de vol"]
        columns = [col for col in columns if col in aggcols]
        if len(columns) == 0:
            columns = aggcols

        tables = []
        for col in columns:
            tables.append(
                pd.pivot_table(
                    self.logbook.rename(columns={"Date": "Vols"}),
                    index=[col],
                    values=["Vols", "Heures"],
                    aggfunc={
                        "Vols": "count",
                        "Heures": self.heures,
                    },
                    margins=True, margins_name="Total"
                )
            )
        return tables

if __name__ == "__main__":
    username = input("Type user name: ")
    password = getpass.getpass("Type password: ")
    user = {"username": username, "password": password}
    log = FlightLog(user)
    print(log.logbook)