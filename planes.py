#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt
import datetime
import sys
import logging
from io import StringIO
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from sklearn.linear_model import Ridge, LinearRegression, Lasso
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline

#from matplotlib import cm
#from mpl_toolkits.mplot3d import Axes3D
#import matplotlib.lines as mlines

class Error(Exception):
   """Base class for other exceptions"""
   pass

class FlightValidationError(Error):
   """Raised when a value is not set within acceptable boundaries.
   Flight is forbidden."""
   pass

class WeightBalance:
    """Maintains a fleet of planes along with their characteristics
    in order to plan flights (load and balance)
    and predict takeoff and landing performances.
    
    The characteristics of the aircrafts are:
    - call_sign: call sign (id)
    - bew: basic empty weight
    - arms: distance of all parts from datum
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
                "auxfuel": 0
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
                "auxfuel": 0
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
                "auxfuel": 1.61
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
    
    def __init__(self, callsign,
                 pax0=0, pax1=0, pax2=0, pax3=0,
                 baggage=0,
                 fuel=None, fuel_mass=None, fuel_gauge=None,
                 auxfuel=0):
        planes = self._planes
        if callsign not in planes.keys():
            raise Exception(f"No such call sign. Valid call signs are {', '.join(planes.keys())}")
        self.callsign = str(callsign)
        plane = planes[self.callsign]
        self.planetype = plane["planetype"]
        self.bew = plane['bew']
        self.bagmax = plane["bagmax"]
        self.mtow = plane['mtow']
        self.maxfuel = plane['maxfuel']
        self.unusfuel = plane['unusfuel']
        self.maxauxfuel = plane['maxauxfuel']
        self.arms = plane['arms']
        self.envelope = plane['envelope']
        self.fuelrate = plane["fuelrate"]
        self._pax0 = int(pax0)
        self._pax1 = int(pax1)
        self._pax2 = int(pax2)
        self._pax3 = int(pax3)
        self._baggage = int(baggage)
        if fuel:
            self._fuel = int(fuel)
            self._fuel_mass = self._volume_to_mass(fuel)
            self._fuel_gauge = self._volume_to_gauge(fuel)
        elif fuel_mass:
            self._fuel_mass = int(fuel_mass)
            self._fuel = self._mass_to_volume(fuel_mass)
            self._fuel_gauge = self._mass_to_gauge(fuel_mass)
        elif fuel_gauge:
            self._fuel_gauge = float(fuel_gauge)
            self._fuel = self._gauge_to_volume(fuel_gauge)
            self._fuel_mass = self._gauge_to_mass(fuel_gauge)
        else:
            self._fuel = 0
            self._fuel_mass = 0
            self._fuel_gauge = 0
        self._auxfuel = int(auxfuel)
        self._auxfuel_mass = self._auxfuel * .72
        self.is_ready_to_fly = True
        self.reasons = []

    def __repr__(self):
        keylist = ["callsign",
                   "pax0", "pax1", "pax2", "pax3",
                   "baggage",
                   "fuel",
                   "auxfuel"]
        # Couldn't use a list comprehension there. Go figure
        valuelist = [f"'{self.callsign}'"]
        for k in keylist[1:]:
            valuelist.append(eval(f"self.{k}"))
        parameters = ', '.join([f"{a}={b}" for a, b in zip(keylist, valuelist)])
        return (f"{self.__class__.__name__}({parameters})")
        
    def _volume_to_mass(self, v):
        """Converts a volume of 100LL gas to mass
        litres to kg
        """
        assert v >= 0
        return v * .72
    
    def _mass_to_volume(self, m):
        """Converts a mass of 100LL gas to volume
        kg to litres
        """
        assert m > 0
        return m / .72
    
    def _volume_to_gauge(self, v):
        """Converts a volume of fuel to gauge indication (4 fourths)
        """
        assert v >= 0
        return v / self.maxfuel * 4
    
    def _mass_to_gauge(self, m):
        """Converts a mass of fuel to gauge indication (4 fourths)
        """
        assert m >= 0
        volume = self._mass_to_volume(m)
        return self._volume_to_gauge(volume)
    
    def _gauge_to_volume(self, g):
        """Converts a gauge indication to a volume of fuel
        """
        assert 0 <= g <= 4
        return g * self.maxfuel / 4
    
    def _gauge_to_mass(self, g):
        """Converts a gauge indication to a mass of 100LL gas
        """
        assert 0 <= g <= 4
        return g * self.maxfuel / 4 * .72
        
    @property
    def auw(self):
        reason = f"All-up weight above MTOW"
        self._auw = (self.bew                     # BEW
                     + self.pax0 + self.pax1      # Front row
                     + self.pax2 + self.pax3      # Back row
                     + self.baggage               # Baggage row
                     + self.fuel_mass             # Main fuel tank
                     + self.auxfuel_mass)         # Auxiliary fuel tank
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
        self._moment = (self.bew * self.arms["bew"]
                        + (self.pax0 + self.pax1) * self.arms["front"]
                        + (self.pax2 + self.pax3) * self.arms["rear"]
                        + self.baggage * self.arms["baggage"]
                        + self.fuel_mass * self.arms["fuel"]
                        + self.auxfuel_mass * self.arms["auxfuel"]
                       )        
        return self._moment
    
    @property
    def cg(self):
        reason = f"""Plane out of cg envelope"""
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
        """Fuel quantity in litres"""
        return self._fuel
    
    @fuel.setter
    def fuel(self, value):
        self._fuel = value
        self._fuel_mass = self._volume_to_mass(self._fuel)
        self._fuel_gauge = self._volume_to_gauge(self._fuel)

    @property
    def fuel_mass(self):
        return self._fuel_mass
    
    @fuel_mass.setter
    def fuel_mass(self, value):
        assert 0 <= value <= self._volume_to_mass(self.maxfuel)
        self._fuel_mass = value
        self._fuel = self._mass_to_volume(self._fuel_mass)
        self._fuel_gauge = self._volume_to_gauge(self._fuel)

    @property
    def fuel_gauge(self):
        return self._fuel_gauge
        
    @fuel_gauge.setter
    def fuel_gauge(self, value):
        assert 0 <= value <= 4                            # 4 fourths of a tank
        self._fuel_gauge = value
        self._fuel = self._gauge_to_volume(self._fuel_gauge)
        self._fuel_mass = self._gauge_to_mass(self._fuel_gauge)
        
    @property
    def fuelmoment(self):
        return self.fuel_mass * self.arms["fuel"]

    @property
    def auxfuel(self):
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
    def auxfuelmoment(self):
        return self.auxfuel_mass * self.arms["auxfuel"]

    @property
    def endurance(self):
        """Endurance of the flight is roughly
        the usable fuel divided by the fuel flow rate
        at cruise speed
        """
        usable_fuel = (self.fuel + self.auxfuel - self.unusfuel)
        return  usable_fuel / self.fuelrate


class PlanePerf:
    """
    """
    
    def __init__(self, planetype, auw, altitude, temperature, qnh):
        """Predicts DR400 planes takeoff and landing distances (50ft)
        given an all-up weight, airfield altitude, temperature and QNH
        planetype: either DR400-120 or DR400-140B
        auw: all-up weight in kg
        altitude: altitude in feet
        temperature: temperature in Celsius degrees
        qnh: QNH in hPa
        """
        self.planetype = str(planetype)
        self.auw = float(auw)
        self.altitude = int(altitude)
        self.temperature = int(temperature)
        self.qnh = int(qnh)
        
        
    def __repr__(self):
        return (f"""{self.__class__.__name__}(
                planetype='{self.planetype}',
                auw={self.auw}, altitude={self.altitude},
                temperature={self.temperature}, qnh={self.qnh})""")
    
    
    def takeoff_data(self):
        """Gets raw performance data for the given type of plane
        Choices are DR400-120 or DR400-140B
        """
        # Takeoff data from POH
        raw = {}
        raw["DR400-120"] = """alt\ttemp\t700\t900
                    0\t-5\t285\t480
                    0\t15\t315\t535
                    0\t35\t345\t590
                    4000\t-13\t375\t645
                    4000\t7\t415\t720
                    4000\t27\t460\t800
                    8000\t-21\t500\t890
                    8000\t-1\t560\t1000
                    8000\t19\t620\t1125"""
        raw["DR400-140B"] = """alt\ttemp\t800\t1000
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

        
    def takeoff(self):
        """Builds a linear regression model out of the raw data
        Predicts takeoff distance (50ft) given:
        type of plane
        altitude in ft
        temperature in °C
        auw in kg
        QNH in hPa
        """
        tkoff = self.takeoff_data()
        
        takeoff_model = make_pipeline(PolynomialFeatures(2), LinearRegression())
        #X = tkoff.iloc[range(1, len(tkoff), 2), :3].values
        #y = tkoff.iloc[range(1, len(tkoff), 2), 3].values
        _ = takeoff_model.fit(tkoff.iloc[:, :3], tkoff.iloc[:, 3])
        
        # A little engineering
        # Convert temperature in K
        Ktemp = self.temperature + 273
        # Convert altitude in Zp
        Zp = self.altitude - 28 * (self.qnh - 1013.25)
        
        features = takeoff_model.steps[0][1].get_feature_names(tkoff.columns)
        features = [i.replace(" ", " * ").replace("^", "**") for i in features]
        # coefs = takeoff_model.steps[1][1].coef_
        # formula = (
        #     str(takeoff_model.steps[1][1].intercept_)
        #     + " + "
        #     + " + ".join([f"({a}) * {b}" for a, b in zip(coefs, features)])
        # )
        tkoff_distance = takeoff_model.predict([[Zp, Ktemp, self.auw]])
        # Applying coefficient for head wind
        asphalt = np.around(tkoff_distance * np.array([[1, 0.78, 0.63, 0.52]]))
        df = pd.DataFrame(asphalt, columns=["0KN", "10KN", "20KN", "30KN"])
        # Applying coefficient for grass runway
        df = df.append(df.iloc[0].apply(lambda x: round(x * 1.15))).astype("int")
        df.index = ["dur", "herbe"]
        df.columns.name = "Ve"
        print(f"\nDistance de décollage (15m)\nZp {Zp}ft\n{self.temperature}°C\n{self.auw}kg\n")
        print(df)
        return df
    
    
    def ldng_data(self):
        """Gets raw performance data for the given type of plane
        Choices are DR400-120 or DR400-140
        """
        # From POH
        raw = {}
        raw["DR400-120"] = """alt\ttemp\t700\t900
                        0\t-5\t365\t435
                        0\t15\t385\t460
                        0\t35\t400\t485
                        4000\t-13\t395\t475
                        4000\t7\t420\t505
                        4000\t27\t440\t535
                        8000\t-21\t430\t525
                        8000\t-1\t460\t555
                        8000\t19\t485\t590"""

        raw["DR400-140B"] = """alt\ttemp\t800\t1000
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
    
    
    def landing(self):
        """Builds a linear regression model out of the raw data
        Predicts landing distance (50ft) given:
        type of plane
        altitude in ft
        temperature in °C
        auw in kg
        QNH in hPa
        """
        ldng = self.ldng_data()
        
        landing_model = make_pipeline(PolynomialFeatures(2), LinearRegression())

        # X_train = ldng.iloc[range(0, len(ldng), 2), :3].values
        # y_train = ldng.iloc[range(0, len(ldng), 2), 3].values
        # X = ldng.iloc[range(1, len(ldng), 2), :3].values
        # y = ldng.iloc[range(1, len(ldng), 2), 3].values
        _ = landing_model.fit(ldng.iloc[:, :3], ldng.iloc[:, 3])
        # print(f"Landing regression score: {landing_model.score(X, y)}")
        
        # A little engineering
        # Convert t in K
        Ktemp = self.temperature + 273
        # Convert a in Zp
        Zp = self.altitude - 28 * (self.qnh - 1013.25)
        features = landing_model.steps[0][1].get_feature_names(ldng.columns)
        features = [i.replace(" ", " * ").replace("^", "**") for i in features]
        # coefs = landing_model.steps[1][1].coef_
        # To display the regression formula
        # formula = (
        #     str(landing_model.steps[1][1].intercept_)
        #     + " + "
        #     + " + ".join([f"({a})*{b}" for a, b in zip(coefs, features)])
        # )
        #print(formula.replace(" +", "\n+"))
        landing_distance = landing_model.predict([[Zp, Ktemp, self.auw]])
        # Coefficients for head wind
        asphalt = np.around(landing_distance*np.array([[1, .78, .63, .52]]))
        df = pd.DataFrame(asphalt, columns=["0KN", "10KN", "20KN", "30KN"])
        df = df.append(df.iloc[0].apply(lambda x: round(x*1.15))).astype("int")
        df.index = ["dur", "herbe"]
        df.columns.name = "Ve"
        #df.columns = pd.MultiIndex.from_product([[f"atterrissage Zp = {Zp}ft {t}°C {m}kg"], df.columns])
        #print(f"\nLanding distance for Zp = {Zp}ft at {t}°C and mass {m}kg: {landing}m")
        print(f"\nDistance d'atterrissage (15m): \nZp {Zp}ft\n{self.temperature}°C\n{self.auw}kg\n")
        print(df)
        return df        
