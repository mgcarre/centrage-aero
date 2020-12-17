# *_* coding: utf-8 *_*

"""Extraction of aerogest-online data and aggregations."""

from datetime import datetime
import getpass
import json
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests

__all__ = ["FlightLog"]


class FlightLog:
    """
    Return a flight log from aerogest-online web site as a pandas dataframe.

    The class also provides different aggregations of the data.

    Args:
        user (dictionary): Aerogest-online username and password
        log_format (string): 'json' returns logbook as a json string. None returns a dataframe.

    Attributes:
        is_logged (boolean): if data retrieval from web site was OK
        logbook (dataframe): the flight log. Return as json string if log_format is used.
    """

    def __init__(self, user, log_format=None):
        """Init."""
        self.user = user
        self.format = log_format
        self.is_logged = False
        self.logbook = self.get_log()

    def get_log(self):
        """
        Retrieve flight log data from aerogest-online.

        Returns:
            logbook (pandas dataframe): flight log
        """
        login_url = "https://online.aerogest.fr/Connection/logon"
        logbook_url = "https://online.aerogest.fr/FlightManagement/Flight/indexPilot"
        api_url = "https://online.aerogest.fr/api/FlightManagement/FlightAPI/getPilot"
        payload = {
            "login": self.user["username"],
            "password": self.user["password"],
            "rememberMe": "true",
        }

        with requests.Session() as session:
            try:
                # Read the login form token and add it to the payload
                response = session.get(login_url)
                soup = BeautifulSoup(response.content, features="html5lib")
                payload["__RequestVerificationToken"] = soup.find(
                    "input", attrs={"name": "__RequestVerificationToken"}
                )["value"]
                response = session.post(login_url, data=payload)

                # Get the pilot id and add it to the payload
                # Use epoch as first date to collect all data until now
                flight_data = {
                    "date1": "1970-01-01",
                    "date2": datetime.now().strftime("%Y-%m-%d"),
                }
                response = session.get(logbook_url)
                soup = BeautifulSoup(response.content, features="html5lib")
                tag = soup.find("input", attrs={"id": "idPilot"})
                if tag:
                    flight_data["idPilot"] = tag["value"]
                    # Then collect the data from the logbook API
                    response = session.post(api_url, data=flight_data)
                    soup = BeautifulSoup(response.content, features="html5lib")
                    # Get the text
                    rawdata = soup.find("body").text
                    # The whole thing is validated if the string "aircraft" appears is the soup
                    self.is_logged = "aircraft" in rawdata
                    # Finally convert the string into a dictionary
                    log_data = json.loads(rawdata)
            except requests.RequestException:
                return None

        # ('id', 'date', 'pilot', 'instr', 'aircraft', 'dep', 'arr', 'time',
        #  'classe', 'type', 'mode', 'nature', 'validated', 'aeroclub',
        #  'counterDep', 'counterArr', 'fuelDep', 'fuelArr',
        #  'fuelTypeDep', 'fuelTypeArr', 'fuelModeDep', 'fuelModeArr')
        log_columns = [
            "id",
            "date",
            "pilot",
            "instr",
            "aircraft",
            "dep",
            "arr",
            "time",
            "classe",
            "type",
            "mode",
            "nature",
        ]
        if not self.is_logged:
            logbook = pd.DataFrame(columns=log_columns)
            # Need to rename the columns of the empty data frame
            # so as not to fail the aggregations
            logbook.rename(
                columns={
                    "pilot": "pilote",
                    "instr": "FI",
                    "aircraft": "immat",
                    "dep": "dep(UTC)",
                    "arr": "arr(UTC)",
                    "time": "heures",
                },
                inplace=True,
            )
            if self.format == "json":
                logbook = logbook.to_json()
            return logbook

        logbook = pd.DataFrame(log_data)[log_columns]
        # Convert duration into timedelta then strings
        logbook["time"] = pd.to_timedelta(logbook["time"])
        logbook["time"] = logbook["time"].apply(lambda x: str(x).split(" ")[2])
        # Finally rename the columns
        logbook.rename(
            columns={
                "pilot": "pilote",
                "instr": "FI",
                "aircraft": "immat",
                "dep": "dep(UTC)",
                "arr": "arr(UTC)",
                "time": "heures",
            },
            inplace=True,
        )
        # This info is no longer available - unfortunately
        # logbook["Type"].replace(regex={r"^DR400$": "DR400-140B"}, inplace=True)
        # logbook["Type"].replace(regex={r"^DR\s400*": "DR400"}, inplace=True)

        if self.format == "json":
            return logbook.to_json()

        return logbook

    @staticmethod
    def heures(series):
        """Pretty display of summed hours."""
        if series.empty:
            return "00h00"

        # series = series.apply(lambda x: f"0 days {int(x[0]):02}:{x[-2:]}:00.000000")
        flighthours = pd.to_timedelta(series)
        hours = int(np.sum(flighthours) / np.timedelta64(1, "h"))
        minutes = int(
            60
            * (
                np.sum(flighthours) / np.timedelta64(1, "h")
                - np.sum(flighthours) // np.timedelta64(1, "h")
            )
        )
        return f"{hours:02}h{minutes:02}"

    def log_agg(self, columns=None):
        """
        Return a list of aggregations of the flight log.

        Args:
            columns (list, optional): List of columns to aggregate over.
                The list is validated against the full list of columns.

        Returns:
            [list]: list of pivoted dataframes.
        """
        # Required to kind of deserialize the logbook - used in Flask
        if self.format == "json":
            logbook = pd.read_json(self.logbook, convert_dates=False)
        else:
            logbook = self.logbook

        if not isinstance(logbook, pd.DataFrame):
            return [pd.DataFrame()]

        if not columns:
            columns = []

        aggcols = ["type", "immat", "mode", "nature"]
        columns = [col for col in columns if col in aggcols]
        if len(columns) == 0:
            columns = aggcols

        tables = []
        for col in columns:
            tables.append(
                pd.pivot_table(
                    logbook.rename(columns={"date": "vols"}),
                    index=[col],
                    values=["vols", "heures"],
                    aggfunc={
                        "vols": "count",
                        "heures": self.heures,
                    },
                    margins=True,
                    margins_name="Total",
                )
            )
        return tables

    def last_quarter(self):
        """
        Provide aggregates of the flight log over the last 3 months.

        Returns:
            [dataframe]: last three months of flight log aggregated.
        """
        # Required to kind of deserialize the logbook - used in Flask
        if self.format == "json":
            logbook = pd.read_json(self.logbook, convert_dates=False)
        else:
            logbook = self.logbook

        if not isinstance(logbook, pd.DataFrame):
            return pd.DataFrame()

        quarter_index = pd.to_datetime(logbook["date"], format="%d/%m/%Y") >= (
            datetime.now().date() - pd.offsets.DateOffset(months=3)
        )
        df_quarter = logbook[quarter_index]
        pivot_df = pd.pivot_table(
            df_quarter.rename(columns={"date": "vols"}),
            index=["type"],
            values=["vols", "heures"],
            aggfunc={
                "vols": "count",
                "heures": self.heures,
            },
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
