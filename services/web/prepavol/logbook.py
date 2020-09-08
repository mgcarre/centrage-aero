# *_* coding: utf-8 *_*

"""Extraction of aerogest data and aggregations.
"""

__author__ = "Yannick Teresiak"
__copyright__ = "Copyright 2020, Prepavol"
__credits__ = ["Yannick Teresiak"]
__license__ = None
__version__ = "1.1.0"
__maintainer__ = "Yannick Teresiak"
__email__ = "yannick.teresiak@gmail.com"
__status__ = "Production"

from datetime import datetime
import getpass
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests

class FlightLog:
    """Returns a flight log from aerogest web site as a pandas dataframe.
    The class also provides different aggregations of the data.

    Args:
        user (dictionary): Aerogest username and password

    Attributes:
        is_logged (boolean): if data retrieval from web site was OK
        logbook (dataframe): the flight log
    """

    def __init__(self, user):
        self.user = user
        self.is_logged = False
        self.logbook = self.get_log()

    def get_log(self):
        """Retrieves flight log data from aerogest.

        Returns:
            logbook (pandas dataframe): flight log
        """
        user = self.user

        POSTLOGINURL = ("http://www.aerogest-reservation.com/connection/"
                        "logon?aeroclub=aeroclub_camargue")
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
            except requests.RequestException:
                return None
        # If logged in, should be able to find specific div
        lookfor = {"class": "divMonCarnetDeVols"}
        soup = BeautifulSoup(r.content, features="lxml")
        self.is_logged = soup.find("div", lookfor) is not None
        if not self.is_logged:
            return None

        logbook = pd.read_html(
            r.content,
            attrs={"class": "classTableVols"},
            header=1,
            encoding="utf-8",
            parse_dates=True,
        )[0]
        logbook = logbook.iloc[:-1, :]

        logbook["Temps (hh:mm)"] = logbook["Temps (hh:mm)"].apply(
            lambda x: f"0 days {int(x[0]):02}:{x[-2:]}:00.000000"
        )
        logbook["Temps (hh:mm)"] = pd.to_timedelta(logbook["Temps (hh:mm)"])
        logbook.rename(columns={"Temps (hh:mm)": "Heures"}, inplace=True)
        logbook["Type"].replace(regex={r"^DR400$": "DR400-140B"}, inplace=True)
        logbook["Type"].replace(regex={r"^DR\s400*": "DR400"}, inplace=True)

        return logbook  # .style.set_table_styles(htmlstyle).render()

    @staticmethod
    def heures(s):
        """Pretty display of hours
        """
        a = int(np.sum(s) / np.timedelta64(1, "h"))
        b = int(
            60
            * (np.sum(s) / np.timedelta64(1, "h") - np.sum(s) // np.timedelta64(1, "h"))
        )
        return f"{a}h{b:02}"

    def log_agg(self, columns=None):
        """Returns a list of aggregations of the flight log.

        Args:
            columns (list, optional): List of columns to aggregate over.
                The list is validated against the full list of columns.

        Returns:
            [list]: list of pivoted dataframes.
        """
        if not isinstance(self.logbook, pd.DataFrame):
            return [pd.DataFrame()]

        if not columns:
            columns = []

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
                    aggfunc={"Vols": "count", "Heures": self.heures,},
                    margins=True,
                    margins_name="Total",
                )
            )
        return tables

    def last_quarter(self):
        """Provides aggregates of the flight log over the last 3 months.

        Returns:
            [dataframe]: last three months of flight log aggregated.
        """
        if not isinstance(self.logbook, pd.DataFrame):
            return pd.DataFrame()

        quarter_index = pd.to_datetime(self.logbook["Date"], format="%d/%m/%Y") >= (
            datetime.now().date() - pd.offsets.DateOffset(months=3)
        )
        df = self.logbook[quarter_index]
        pivot_df = pd.pivot_table(
            df.rename(columns={"Date": "Vols"}),
            index=["Type"],
            values=["Vols", "Heures"],
            aggfunc={"Vols": "count", "Heures": self.heures,},
            margins=True,
            margins_name="Total",
        )
        return pivot_df


if __name__ == "__main__":
    username = input("Type user name: ")
    password = getpass.getpass("Type password: ")
    aerogest_user = {"username": username, "password": password}
    log = FlightLog(aerogest_user)
    print(log.logbook)
