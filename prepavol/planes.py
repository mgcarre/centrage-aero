#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np

import datetime
import sys
from base64 import b64encode
import logging
import copy
from io import StringIO, BytesIO
import matplotlib.pyplot as plt
from matplotlib import cm, lines
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from sklearn.linear_model import Ridge, LinearRegression, Lasso
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline


class Error(Exception):
    """Base class for other exceptions.
    """

    pass


class FlightValidationError(Error):
    """Raised when a value is not set within acceptable boundaries.
    Flight is forbidden.
    """

    pass


class WeightBalance:
    """Maintains a fleet of planes along with their characteristics
    in order to plan flights (weight and balance) and predict takeoff
    and landing performances.
    
    The characteristics of the aircrafts are:
    - call_sign: call sign (id)
    - bew: basic empty weight
    - arms: distance of all sectors of the aircraft from the datum
    - maxfuel: fuel tank capacity
    - maxauxfuel: auxiliary fuel tank capacity
    - unusfuel: unusable fuel
    - fuelrate: fuel flow rate at cruise speed
    - mtow: MTOW
    - bagmax: max baggage compartment weight
    - envelope: aircraft center of gravity envelope
    
    At any point in the loading the following properties are available:
    - auw: all-up weight
    - moment: the overall moment of the weight items
    - cg: the center of gravity, with reference to the datum
    - endurance: flight length capability given the amount of fuel
    - is_ready_to_fly: indicates violations of the load and balance
    - reasons: specific violation indications

    Args:
        callsign (str): the aircraft's call sign.
        pax[0-3] (int, optional): the weight of the occupants from front left to rear right.
        baggage (int, optional): the weight in the baggage sector.
        fuel (int, optional): amount of fuel in the main tank in litres.
        fuel_mass (float, optional): amount of fuel in the main tank in kg.
        fuel_gauge (float, optional): amount of fuel in the main tank in fourths of the tank.
        auxfuel (int, optional): amount of fuel in the auxiliary tank in litres.
        auxfuel_mass (float, optional): amount of fuel in the auxiliary tank in kg.
        auxfuel_gauge (float, optional): amount of fuel in the auxiliary tank in fourths of the tank.

        For fuel and auxfuel, the volume, mass and gauge indicator are properties and are converted in one another.

    Attributes:
        callsign (str): aircraft's call sign.
        planetype (str): the aircraft model.
        bew (float): the basic empty weight.
        mtow (float): the MTOW (max takeoff weight).
        bagmax (int): the max weight in the baggage sector.
        maxfuel (int): the main tank's capacity in litres.
        unusfuel (int): the unusable fuel in litres.
        maxauxfuel (int): the auxiliary tank's capacity in litres.
        fuelrate (int): the fuel flow rate in litres per hour.
        arms (list): the distance of the from the sectors of the plane to the datum.
        envelope (list of lists): the aircraft's center of gravity envelope.
        is_ready_to_fly (boolean): airworthiness with regards to the all-up weight and balance.
    """

    _planes = {
        "FHAAC": {
            "planetype": "DR400-120",
            "bew": 586,
            "bagmax": 40,
            "mtow": 900,
            "maxfuel": 110,
            "unusfuel": 1,
            "maxauxfuel": 0,
            "fuelrate": 25,
            "arms": {
                "bew": 0.331,
                "front": 0.41,
                "rear": 1.19,
                "baggage": 1.9,
                "fuel": 1.12,
                "auxfuel": 0,
            },
            "envelope": [
                [0.205, 550],
                [0.205, 750],
                [0.428, 900],
                [0.564, 900],
                [0.564, 550],
            ],
        },
        "FGGXD": {
            "planetype": "DR400-120",
            "bew": 595.9,
            "bagmax": 40,
            "mtow": 900,
            "maxfuel": 110,
            "unusfuel": 10,
            "maxauxfuel": 0,
            "fuelrate": 25,
            "arms": {
                "bew": 0.351,
                "front": 0.41,
                "rear": 1.19,
                "baggage": 1.9,
                "fuel": 1.12,
                "auxfuel": 0,
            },
            "envelope": [
                [0.205, 550],
                [0.205, 750],
                [0.428, 900],
                [0.564, 900],
                [0.564, 550],
            ],
        },
        "FBUPS": {
            "planetype": "DR400-140B",
            "bew": 593.5,
            "bagmax": 40,
            "mtow": 1000,
            "maxfuel": 110,
            "unusfuel": 0,
            "maxauxfuel": 50,
            "fuelrate": 35,
            "arms": {
                "bew": 0.290,
                "front": 0.41,
                "rear": 1.19,
                "baggage": 1.9,
                "fuel": 1.12,
                "auxfuel": 1.61,
            },
            "envelope": [
                [0.205, 550],
                [0.205, 750],
                [0.428, 1000],
                [0.564, 1000],
                [0.564, 550],
            ],
        },
    }

    def __init__(
        self,
        callsign,
        pax0=0,
        pax1=0,
        pax2=0,
        pax3=0,
        baggage=0,
        fuel=None,
        fuel_mass=None,
        fuel_gauge=None,
        auxfuel=None,
        auxfuel_mass=None,
        auxfuel_gauge=None,
        **kwargs,
    ):
        planes = self.__class__._planes
        if callsign not in planes.keys():
            raise Exception(
                f"No such call sign. Valid call signs are {', '.join(planes.keys())}"
            )
        self.callsign = str(callsign)
        plane = planes[self.callsign]
        self.planetype = plane["planetype"]
        self.bew = plane["bew"]
        self.bagmax = plane["bagmax"]
        self.mtow = plane["mtow"]
        self.maxfuel = plane["maxfuel"]
        self.unusfuel = plane["unusfuel"]
        self.maxauxfuel = plane["maxauxfuel"]
        self.arms = plane["arms"]
        self.envelope = plane["envelope"]
        self.fuelrate = plane["fuelrate"]
        self._pax0 = int(pax0)
        self._pax1 = int(pax1)
        self._pax2 = int(pax2)
        self._pax3 = int(pax3)
        self._baggage = int(baggage)

        if fuel:
            self._fuel = int(fuel)
            self._fuel_mass = self._volume_to_mass(self.fuel)
            self._fuel_gauge = self._volume_to_gauge(self.fuel, self.maxfuel)
        elif fuel_mass:
            self._fuel_mass = int(fuel_mass)
            self._fuel = self._mass_to_volume(self.fuel_mass)
            self._fuel_gauge = self._mass_to_gauge(self.fuel_mass, self.maxfuel)
        elif fuel_gauge:
            self._fuel_gauge = float(fuel_gauge)
            self._fuel = self._gauge_to_volume(self.fuel_gauge, self.maxfuel)
            self._fuel_mass = self._gauge_to_mass(self.fuel_gauge, self.maxfuel)
        else:
            self._fuel = 0
            self._fuel_mass = 0
            self._fuel_gauge = 0

        if auxfuel:
            self._auxfuel = int(auxfuel)
            self._auxfuel_mass = self._volume_to_mass(self.auxfuel)
            self._auxfuel_gauge = self._volume_to_gauge(self.auxfuel, self.maxauxfuel)
        elif auxfuel_mass:
            self._auxfuel_mass = int(auxfuel_mass)
            self._auxfuel = self._mass_to_volume(self.auxfuel_mass)
            self._auxfuel_gauge = self._mass_to_gauge(
                self.auxfuel_mass, self.maxauxfuel
            )
        elif auxfuel_gauge:
            self._auxfuel_gauge = float(auxfuel_gauge)
            self._auxfuel = self._gauge_to_volume(self.auxfuel_gauge, self.maxauxfuel)
            self._auxfuel_mass = self._gauge_to_mass(
                self.auxfuel_gauge, self.maxauxfuel
            )
        else:
            self._auxfuel = 0
            self._auxfuel_mass = 0
            self._auxfuel_gauge = 0
        self.is_ready_to_fly = True
        self.reasons = []
        # Need to initialize computed properties
        _ = self.auw, self.cg, self.moment

    def __repr__(self):
        keylist = [
            "callsign",
            "pax0",
            "pax1",
            "pax2",
            "pax3",
            "baggage",
            "fuel",
            "auxfuel",
        ]
        # Couldn't use a list comprehension there. Go figure
        valuelist = [f"'{self.callsign}'"]
        for k in keylist[1:]:
            valuelist.append(eval(f"self.{k}"))
        parameters = ", ".join([f"{a}={b}" for a, b in zip(keylist, valuelist)])
        return f"{self.__class__.__name__}({parameters})"

    def _volume_to_mass(self, v):
        """Converts a volume of 100LL gas to mass (litres to kg).
        """
        assert v >= 0
        return v * 0.72

    def _mass_to_volume(self, m):
        """Converts a mass of 100LL gas to volume (kg to litres).
        """
        assert m > 0
        return m / 0.72

    def _volume_to_gauge(self, v, tank):
        """Converts a volume of fuel to gauge indication (4 fourths)
        knowing the volume of the tank.

        Arguments:
            v (int): litres.
            tank (int): the tank's capacity.
        """
        assert v >= 0
        return v / tank * 4

    def _mass_to_gauge(self, m, tank):
        """Converts a mass of fuel to gauge indication (4 fourths)
        knowing the volume of the tank.

        Arguments:
            m (int): kg.
            tank (int): the tank's capacity.
        """
        assert m >= 0
        volume = self._mass_to_volume(m)
        return self._volume_to_gauge(volume, tank)

    def _gauge_to_volume(self, g, tank):
        """Converts a gauge indication to a volume of fuel
        knowing the volume of the tank

        Arguments:
            g (float): gauge indication in fourths by step of .5.
            tank (int): the tank's capacity.
        """
        assert 0 <= g <= 4
        return g * tank / 4

    def _gauge_to_mass(self, g, tank):
        """Converts a gauge indication to a mass of 100LL gas
        knowing the volume of the tank.

        Arguments:
            g (float): gauge indication in fourths by step of .5.
            tank (int): the tank's capacity.
        """
        assert 0 <= g <= 4
        return g * tank / 4 * 0.72

    @property
    def auw(self):
        """All-up weight. Sum of all the parts.

        Returns:
            (float): all-up weight in kg.
        """
        reason = f"All-up weight above MTOW"
        self._auw = (
            self.bew  # BEW
            + self.pax0
            + self.pax1  # Front row
            + self.pax2
            + self.pax3  # Back row
            + self.baggage  # Baggage row
            + self.fuel_mass  # Main fuel tank
            + self.auxfuel_mass
        )  # Auxiliary fuel tank
        if self._auw > self.mtow:
            self.is_ready_to_fly = False
            logging.error(reason)
            if reason not in self.reasons:
                self.reasons.append(reason)
        else:
            self.reasons = [k for k in self.reasons if k != reason]
        return self._auw

    @property
    def moment(self):
        """Overall moment.
        Sum of the moments of all the sectors.

        Returns:
            (float): overall moment in kg.m.
        """
        self._moment = (
            self.bew * self.arms["bew"]
            + (self.pax0 + self.pax1) * self.arms["front"]
            + (self.pax2 + self.pax3) * self.arms["rear"]
            + self.baggage * self.arms["baggage"]
            + self.fuel_mass * self.arms["fuel"]
            + self.auxfuel_mass * self.arms["auxfuel"]
        )
        return self._moment

    @property
    def cg(self):
        """Center of gravity as a distance from the datum.
        Computed from the all-up weight and the overall moment.
        
        Returns:
            (float): center of gravity in meters from the datum.
        """
        reason = f"""Balance out of cg envelope"""
        self._cg = self.moment / self.auw
        polygon = Polygon(tuple(k) for k in self.envelope)
        point = Point(self._cg, self.auw)
        if not polygon.contains(point):
            self.is_ready_to_fly = False
            logging.error(reason)
            if reason not in self.reasons:
                self.reasons.append(reason)
        else:
            self.reasons = [k for k in self.reasons if k != reason]
        return self._cg

    @property
    def pax0(self):
        return self._pax0

    @pax0.setter
    def pax0(self, value):
        self._pax0 = value

    @property
    def pax1(self):
        return self._pax1

    @pax1.setter
    def pax1(self, value):
        self._pax1 = value

    @property
    def pax2(self):
        return self._pax2

    @pax2.setter
    def pax2(self, value):
        self._pax2 = value

    @property
    def pax3(self):
        return self._pax3

    @pax3.setter
    def pax3(self, value):
        self._pax3 = value

    @property
    def frontweight(self):
        return self.pax0 + self.pax1

    @property
    def frontmoment(self):
        return self.frontweight * self.arms["front"]

    @property
    def rearweight(self):
        return self.pax2 + self.pax3

    @property
    def rearmoment(self):
        return self.rearweight * self.arms["rear"]

    @property
    def baggage(self):
        return self._baggage

    @baggage.setter
    def baggage(self, value):
        """Baggage weight input.
        It is checked against the aircraft's max baggage weight.

        Args:
            value (int): baggage weight in kg.
        """
        reason = f"Baggage weight over max weight"
        if value > self.bagmax:
            self.is_ready_to_fly = False
            if reason not in self.reasons:
                logging.error(reason)
                self.reasons.append(reason)
        else:
            self.reasons = [k for k in self.reasons if k != reason]
        self._baggage = value

    @property
    def bagmoment(self):
        return self.baggage * self.arms["baggage"]

    @property
    def fuel(self):
        """Fuel quantity in litres.
        """
        return self._fuel

    @fuel.setter
    def fuel(self, value):
        self._fuel = value
        self._fuel_mass = self._volume_to_mass(self._fuel)
        self._fuel_gauge = self._volume_to_gauge(self._fuel, self.maxfuel)

    @property
    def fuel_mass(self):
        """Fuel quantity in kg.
        """
        return self._fuel_mass

    @fuel_mass.setter
    def fuel_mass(self, value):
        assert 0 <= value <= self._volume_to_mass(self.maxfuel)
        self._fuel_mass = value
        self._fuel = self._mass_to_volume(self._fuel_mass)
        self._fuel_gauge = self._volume_to_gauge(self._fuel, self.maxfuel)

    @property
    def fuel_gauge(self):
        """Fuel gauge indicator in fourths with step of .5.
        """
        return self._fuel_gauge

    @fuel_gauge.setter
    def fuel_gauge(self, value):
        assert 0 <= value <= 4  # 4 fourths of a tank
        self._fuel_gauge = value
        self._fuel = self._gauge_to_volume(self._fuel_gauge, self.maxfuel)
        self._fuel_mass = self._gauge_to_mass(self._fuel_gauge, self.maxfuel)

    @property
    def fuelmoment(self):
        return self.fuel_mass * self.arms["fuel"]

    @property
    def auxfuel(self):
        """Auxiliary fuel in litres.
        """
        return self._auxfuel

    @auxfuel.setter
    def auxfuel(self, value):
        assert value >= 0
        self._auxfuel = value
        if self._auxfuel == 0 and value > 0:
            msg = f"{self.callsign} has no auxiliary fuel tank. Setting volume to 0."
            logging.warning(msg)
            self._auxfuel = 0
        elif value > self.maxauxfuel:
            msg = f"Auxiliary tank max volumes is {self.maxauxfuel}"
            logging.error(msg)
            self._auxfuel = self.maxauxfuel
        self._auxfuel_mass = self._volume_to_mass(self._auxfuel)

    @property
    def auxfuel_mass(self):
        """Auxiliary fuel in kg.
        """
        return self._auxfuel_mass

    @auxfuel_mass.setter
    def auxfuel_mass(self, value):
        assert value >= 0
        self._auxfuel_mass = value
        max_auxfuel_mass = self._volume_to_mass(self.maxauxfuel)
        if max_auxfuel_mass == 0 and value > 0:
            msg = f"{self.callsign} has no auxiliary fuel tank. Setting mass to 0."
            logging.warning(msg)
            self._auxfuel_mass = 0
        elif value > max_auxfuel_mass:
            msg = f"Auxiliary tank max weight is {max_auxfuel_mass}"
            logging.error(msg)
            self._auxfuel_mass = max_auxfuel_mass
        self._auxfuel = self._mass_to_volume(self._auxfuel_mass)

    @property
    def auxfuel_gauge(self):
        """Auxiliary fuel gauge indicator in fourths with step of .5.
        """
        return self._auxfuel_gauge

    @auxfuel_gauge.setter
    def auxfuel_gauge(self, value):
        assert 0 <= value <= 4  # 4 fourths of a tank
        self._auxfuel_gauge = value
        self._auxfuel = self._gauge_to_volume(self._auxfuel_gauge, self.maxauxfuel)
        self._auxfuel_mass = self._gauge_to_mass(self._auxfuel_gauge, self.maxauxfuel)

    @property
    def auxfuelmoment(self):
        return self.auxfuel_mass * self.arms["auxfuel"]

    @property
    def endurance(self):
        """Endurance of the flight is roughly the usable fuel divided
        by the fuel flow rate at cruise speed.

        Returns:
            float: endurance in hours.
        """
        usable_fuel = self.fuel + self.auxfuel - self.unusfuel
        return usable_fuel / self.fuelrate

    def plot_balance(self, encode=False):
        """Plots the envelope with the evolution of the cg.

        Arguments:
            encode (boolean): returns BytesIO if True.

        Returns:
            image or image bytes.
        """
        # Envelope
        polygon = Polygon(tuple(k) for k in self.envelope)

        # Get cg and auw with no fuel
        no_fuel_plane = copy.copy(self)
        no_fuel_plane.fuel = 0
        no_fuel_plane.auxfuel = 0

        fig = plt.figure()
        ax = plt.gca()
        ax.plot(*polygon.exterior.xy, c="b")
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        ax.set_title(f"centrage de {self.callsign} - {date}")
        # Start and no fuel points
        ax.plot([self.cg, no_fuel_plane.cg], [self.auw, no_fuel_plane.auw], "r")
        ax.plot([self.cg], [self.auw], "ro", markerfacecolor="w", markersize=12)
        ax.plot(
            [no_fuel_plane.cg],
            [no_fuel_plane.auw],
            "r^",
            markerfacecolor="w",
            markersize=12,
        )
        ax.set_xlabel("m", fontsize=12)
        ax.set_ylabel("kg", fontsize=12)
        plt.tight_layout()

        if encode:
            canvas = FigureCanvas(fig)
            png = BytesIO()
            canvas.print_png(png)
            figdata = b64encode(png.getvalue()).decode("ascii")
            plt.close(fig)
            return figdata
        else:
            _ = plt.show()


class PlanePerf:
    """Predicts DR400 planes takeoff and landing distances (50ft)
    given an all-up weight, the ground altitude, temperature and QNH.

    Arguments:
        planetype (str):
            either "DR400-120" or "DR400-140B".
        auw (float):
            all-up weight in kg.
        altitude (int):
            altitude in feet.
        temperature (int):
            temperature in Celsius degrees.
        qnh (int):
            QNH in mbar.
    """

    def __init__(self, planetype, auw, altitude, temperature, qnh, **kwargs):
        
        self.planetype = str(planetype)
        self.auw = float(auw)
        self.altitude = int(altitude)
        self.temperature = int(temperature)
        self.qnh = int(qnh)

    def __repr__(self):
        return f"""{self.__class__.__name__}(
                planetype='{self.planetype}',
                auw={self.auw}, altitude={self.altitude},
                temperature={self.temperature}, qnh={self.qnh})"""

    def pressure_altitude(self, elevation, qnh):
        """Computes the pressure altitude from a ground elevation
        and the QNH.

        Arguments:
            elevation (int):
                ground elevation in feet.
            qnh (int):
                QNH in mbar.
        
        Returns:
            float: pressure altitude.
        """
        return elevation - 27 * (qnh - 1013)

    @property
    def Zp(self):
        return self.pressure_altitude(self.altitude, self.qnh)

    def density_altitude(self, elevation, temperature, qnh):
        """Computes the densisty altitude given an elevation,
        an outside air temperature and the QNH.

        Arguments:
            elevation (int):
                ground elevation in feet.
            temperature (int):
                outside air temperature in °C.
            qnh (int):
                QNH in mbar

        Returns:
            float: density altitude.
        """
        Zp = self.pressure_altitude(elevation, qnh)
        return 1.2376 * Zp + 118.8 * temperature - 1782

    @property
    def Zd(self):
        return self.density_altitude(self.altitude, self.temperature, self.qnh)

    def takeoff_data(self):
        """Returns the raw performance data for the given type of plane.
        Choices are DR400-120 or DR400-140B.
        """
        # Takeoff data from POH
        raw = {}
        raw[
            "DR400-120"
        ] = """alt\ttemp\t700\t900
                    0\t-5\t285\t480
                    0\t15\t315\t535
                    0\t35\t345\t590
                    4000\t-13\t375\t645
                    4000\t7\t415\t720
                    4000\t27\t460\t800
                    8000\t-21\t500\t890
                    8000\t-1\t560\t1000
                    8000\t19\t620\t1125"""
        raw[
            "DR400-140B"
        ] = """alt\ttemp\t800\t1000
                    0\t-5\t245\t435
                    0\t15\t265\t485
                    0\t35\t290\t535
                    4000\t-13\t320\t580
                    4000\t7\t350\t645
                    4000\t27\t385\t720
                    8000\t-21\t415\t780
                    8000\t-1\t465\t870
                    8000\t19\t515\t975"""

        assert self.planetype in raw.keys()

        tkoff = pd.read_csv(StringIO(raw[self.planetype]), sep="\t", header=0)
        tkoff = tkoff.melt(id_vars=["alt", "temp"], var_name="mass", value_name="m")
        tkoff["temp"] = tkoff["temp"] + 273
        tkoff["mass"] = tkoff["mass"].astype("int")
        return tkoff

    def landing_data(self):
        """Returns the raw performance data for the given type of plane.
        Choices are DR400-120 or DR400-140.
        """
        # From POH
        raw = {}
        raw[
            "DR400-120"
        ] = """alt\ttemp\t700\t900
                        0\t-5\t365\t435
                        0\t15\t385\t460
                        0\t35\t400\t485
                        4000\t-13\t395\t475
                        4000\t7\t420\t505
                        4000\t27\t440\t535
                        8000\t-21\t430\t525
                        8000\t-1\t460\t555
                        8000\t19\t485\t590"""

        raw[
            "DR400-140B"
        ] = """alt\ttemp\t800\t1000
                        0\t-5\t380\t445
                        0\t15\t400\t470
                        0\t35\t420\t500
                        4000\t-13\t410\t490
                        4000\t7\t435\t520
                        4000\t27\t460\t550
                        8000\t-21\t450\t540
                        8000\t-1\t480\t575
                        8000\t19\t505\t610"""

        assert self.planetype in raw.keys()

        ldng = pd.read_csv(StringIO(raw[self.planetype]), sep="\t", header=0)
        ldng = ldng.melt(id_vars=["alt", "temp"], var_name="mass", value_name="m")
        ldng["temp"] = ldng["temp"] + 273
        ldng["mass"] = ldng["mass"].astype("int")
        return ldng

    def make_model(self, operation):
        """Returns a trained model of takeoff or landing performance.

        Arguments:
            operation (str): "takeoff" or "landing"

        Returns:
            sklearn linear regression model.
        """
        assert operation in ["takeoff", "landing"]

        data_df = eval(f"self.{operation}_data()")

        model = make_pipeline(PolynomialFeatures(2), LinearRegression())
        _ = model.fit(data_df.iloc[:, :3], data_df.iloc[:, 3])

        return model

    def predict(self, operation):
        """Builds a linear regression model out of the raw data.
        Predicts takeoff or landing distance (50ft) given:
        type of plane
        altitude in ft
        temperature in °C
        auw in kg
        QNH in mbar

        Arguments:
            operation (str): "takeoff" or "landing"]

        Returns:
            dataframe: takeoff or landing for different ground types and head winds.
        """

        assert operation in ["takeoff", "landing"]

        model = self.make_model(operation)

        # A little engineering
        # Convert temperature in K
        Ktemp = self.temperature + 273
        # Convert altitude in Zp
        Zp = self.pressure_altitude(self.altitude, self.qnh)
        Zd = self.density_altitude(self.altitude, self.temperature, self.qnh)

        distance = model.predict([[Zp, Ktemp, self.auw]])
        # Applying coefficient for head wind
        if operation == "takeoff":
            asphalt = np.around(distance * np.array([[1, 0.85, 0.65, 0.55]]))
        else:
            asphalt = np.around(distance * np.array([[1, 0.78, 0.63, 0.52]]))
        df = pd.DataFrame(asphalt, columns=["0kn", "10kn", "20kn", "30kn"])
        # Applying coefficient for grass runway
        df = df.append(df.iloc[0].apply(lambda x: round(x * 1.15))).astype("int")
        df.index = ["dur", "herbe"]
        df.columns.name = "Ve"
        title = {"takeoff": "de décollage", "landing": "d'atterrissage"}
        print(
            f"\nDistance {title[operation]} (15m)\nZp {Zp}ft\nZd {Zd} ft\n{self.temperature}°C\n{self.auw}kg\n"
        )

        return df

    def plot_performance(self, operation, encode=False):
        """Plots a contour graph of the takeoff or landing performance
        given a plane's all-up weight.

        Arguments:
            operation (str): "takeoff" or "landing"
            encode (boolean): if True, returns a bytes stream instead of showing the plot

        Returns:
            image or image bytes.
        """
        assert operation in ["takeoff", "landing"]

        model = self.make_model(operation)

        # Number of zones in the contour graph
        N = 10

        # Make a mesh grid of altitudes and temperatures
        predict_a, predict_t = np.meshgrid(
            np.linspace(0, 13000, N), np.linspace(243, 323, N)
        )
        predict_x = np.concatenate(
            (
                predict_a.reshape(-1, 1),
                predict_t.reshape(-1, 1),
                np.array(100 * [self.auw]).reshape(-1, 1),
            ),
            axis=1,
        )
        predict_x_ = model.steps[0][1].fit_transform(predict_x)
        predict_y = model.steps[1][1].predict(predict_x_)

        fig = plt.figure(figsize=(12, 10))
        ax = plt.gca()
        cs = ax.contourf(
            predict_a,
            predict_t - 273,
            predict_y.reshape(predict_a.shape),
            # cmap=surf.cmap.name,
            cmap=cm.jet,
            alpha=0.6,
        )
        title = {"takeoff": "décollage", "landing": "atterrissage"}
        ax.set_title(f"{title[operation]} (15m) à {self.auw:.2f}kg", size=26)
        ax.contour(cs, colors="k")
        cbar = fig.colorbar(cs, ax=ax)
        ax.set_xlabel("Zp (ft)", size=24)
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        ax.set_ylabel("°C", size=24)
        cbar.ax.set_ylabel("mètres", rotation=270, size=24, labelpad=20)
        cbar.ax.tick_params(labelsize=20)
        fig.patch.set_alpha(1)
        fig.tight_layout()

        if encode:
            canvas = FigureCanvas(fig)
            png = BytesIO()
            canvas.print_png(png)
            figdata = b64encode(png.getvalue()).decode("ascii")
            plt.close(fig)
            return figdata
        else:
            _ = plt.show()
