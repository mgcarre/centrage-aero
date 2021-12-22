#!/usr/bin/env python
# *_* coding: utf-8 *_*

"""Light aviation flight preparation tools.

The module includes a class for weight and balance preparation
and a class for performance predictions.
"""

from pathlib import Path
from base64 import b64encode
import logging
import copy
from io import BytesIO

import datetime
import pkgutil
import pandas as pd
import numpy as np
import yaml
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from prepavol.oils import Avgas
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline

__all__ = ["WeightBalance", "PlanePerf"]


class Error(Exception):
    """Base class for other exceptions."""


class FlightValidationError(Error):
    """Raised when a value is not set within acceptable boundaries. Flight is forbidden."""


class WeightBalance:
    """
    Aircraft weight and balance planification.

    Maintains a fleet of planes along with their characteristics in order to plan
    flights (weight and balance) and predict takeoff and landing performances.

    The characteristics of the aircrafts are:
    - call_sign: call sign (id)
    - bew: basic empty weight
    - arms: distance of all sectors of the aircraft from the datum
    - maxmainfuel: main fuel tank capacity
    - maxauxfuel: auxiliary fuel tank capacity
    - unusable_mainfuel: unusable fuel
    - fuelrate: fuel flow rate at cruise speed
    - mtow: MTOW
    - bagmax: max baggage compartment weight
    - bagmax2: max zone 2 baggage compartment weight (Sonaca)
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
        baggage2 (int, optional): the weight in the zone 2 baggage sector.
        mainfuel (int, optional): amount of fuel in the main tank in litres.
        mainfuel_mass (float, optional): amount of fuel in the main tank in kg.
        mainfuel_gauge (float, optional): amount of fuel in the main tank in fourths of the tank.
        leftwingfuel (int, optional): amount of fuel in the left wing tank in litres.
        leftwingfuel_mass (float, optional): amount of fuel in the left wing tank in kg.
        leftwingfuel_gauge (float, optional): amount of fuel in the left tank in fourths of the tank.
        rightwingfuel (int, optional): amount of fuel in the right wing tank in litres.
        rightwingfuel_mass (float, optional): amount of fuel in the right wing tank in kg.
        rightwingfuel_gauge (float, optional): amount of fuel in the right tank in fourths of the tank.
        auxfuel (int, optional): amount of fuel in the auxiliary tank in litres.
        auxfuel_mass (float, optional): amount of fuel in the auxiliary tank in kg.
        auxfuel_gauge (float, optional): amount of fuel in the auxiliary tank in fourths
                                         of the tank.

        For mainfuel and auxfuel, the volume, mass and gauge indicator are properties and are converted
        in one another.

    Attributes:
        callsign (str): aircraft's call sign.
        planetype (str): the aircraft model.
        bew (float): the basic empty weight.
        mtow (float): the MTOW (max takeoff weight).
        bagmax (int): the max weight in the baggage sector.
        bagmax2 (int): the max weight in the zone 2 baggage sector.
        sumbagmax (int): the max weight for baggage + baggage2.
        sumbag (int): baggage + baggage2 if applicable.
        maxmainfuel (int): the main tank's capacity in litres.
        unusable_mainfuel (int): the unusable main tank fuel in litres.
        maxwingfuel (int): the wing tanks capacity in litres.
        unusable_wingfuel (int): the unusable wing tank fuel in litres.
        maxauxfuel (int): the auxiliary tank's capacity in litres.
        fuelrate (int): the fuel flow rate in litres per hour.
        arms (list): the distance of the from the sectors of the plane to the datum.
        envelope (list of lists): the aircraft's center of gravity envelope.
        is_ready_to_fly (boolean): airworthiness with regards to the all-up weight and balance.
    """

    def __init__(
        self,
        callsign,
        pax0=0,
        pax1=0,
        pax2=0,
        pax3=0,
        baggage=0,
        baggage2=0,
        mainfuel=0,
        #mainfuel_mass=None,
        #mainfuel_gauge=None,
        leftwingfuel=0,
        #leftwingfuel_mass=None,
        #leftwingfuel_gauge=None,
        rightwingfuel=0,
        #rightwingfuel_mass=None,
        #rightwingfuel_gauge=None,
        auxfuel=0,
        #auxfuel_mass=None,
        #auxfuel_gauge=None,
        **_kwargs,
    ):
        """Init."""
        self.is_ready_to_fly = True
        self.reasons = []

        planes = WeightBalance.load_fleet_data()
        if callsign not in planes.keys():
            raise Exception(
                f"No such call sign. Valid call signs are {', '.join(planes.keys())}"
            )
        self.callsign = str(callsign)
        plane = planes[self.callsign]
        self.avgas = Avgas(plane["fuel_name"])
        self.planetype = plane["planetype"]
        self.bew = plane["bew"]
        self.bagmax = plane["bagmax"]
        self.bagmax2 = plane["bagmax2"]
        self.sumbagmax = plane["sumbagmax"]
        self.mtow = plane["mtow"]
        self.maxmainfuel = plane["maxmainfuel"]
        self.unusable_mainfuel = plane["unusable_mainfuel"]
        self.maxwingfuel = plane["maxwingfuel"]
        self.unusable_wingfuel = plane["unusable_wingfuel"]
        self.maxauxfuel = plane["maxauxfuel"]
        self.arms = plane["arms"]
        self.envelope = plane["envelope"]
        self.fuelrate = plane["fuelrate"]
        self.pax0 = int(pax0)
        self.pax1 = int(pax1)
        self.pax2 = int(pax2)
        self.pax3 = int(pax3)
        self.baggage = int(baggage)
        self.baggage2 = int(baggage2)

        self.mainfuel = int(mainfuel)
        # if mainfuel:
        #     self._mainfuel = int(mainfuel)
        #     self._mainfuel_mass = self._volume_to_mass(self.mainfuel)
        #     self._mainfuel_gauge = self._volume_to_gauge(
        #         self.mainfuel, self.maxmainfuel
        #     )
        # elif mainfuel_mass:
        #     self._mainfuel_mass = int(mainfuel_mass)
        #     self._mainfuel = self._mass_to_volume(self.mainfuel_mass)
        #     self._mainfuel_gauge = self._mass_to_gauge(
        #         self.mainfuel_mass, self.maxmainfuel
        #     )
        # elif mainfuel_gauge:
        #     self._mainfuel_gauge = float(mainfuel_gauge)
        #     self._mainfuel = self._gauge_to_volume(
        #         self.mainfuel_gauge, self.maxmainfuel
        #     )
        #     self._mainfuel_mass = self._gauge_to_mass(
        #         self.mainfuel_gauge, self.maxmainfuel
        #     )
        # else:
        #     self._mainfuel = 0
        #     self._mainfuel_mass = 0
        #     self._mainfuel_gauge = 0

        self.leftwingfuel = int(leftwingfuel)
        # if leftwingfuel:
        #     self._leftwingfuel = int(leftwingfuel)
        #     self._leftwingfuel_mass = self._volume_to_mass(self.leftwingfuel)
        #     self._leftwingfuel_gauge = self._volume_to_gauge(
        #         self.leftwingfuel, self.maxwingfuel
        #     )
        # elif leftwingfuel_mass:
        #     self._leftwingfuel_mass = int(leftwingfuel_mass)
        #     self._leftwingfuel = self._mass_to_volume(self.leftwingfuel_mass)
        #     self._leftwingfuel_gauge = self._mass_to_gauge(
        #         self.leftwingfuel_mass, self.maxwingfuel
        #     )
        # elif leftwingfuel_gauge:
        #     self._leftwingfuel_gauge = float(leftwingfuel_gauge)
        #     self._leftwingfuel = self._gauge_to_volume(
        #         self.leftwingfuel_gauge, self.maxwingfuel
        #     )
        #     self._leftwingfuel_mass = self._gauge_to_mass(
        #         self.leftwingfuel_gauge, self.maxwingfuel
        #     )
        # else:
        #     self._leftwingfuel = 0
        #     self._leftwingfuel_mass = 0
        #     self._leftwingfuel_gauge = 0

        self.rightwingfuel = int(rightwingfuel)
        # if rightwingfuel:
        #     self._rightwingfuel = int(rightwingfuel)
        #     self._rightwingfuel_mass = self._volume_to_mass(self.rightwingfuel)
        #     self._rightwingfuel_gauge = self._volume_to_gauge(
        #         self.rightwingfuel, self.maxwingfuel
        #     )
        # elif rightwingfuel_mass:
        #     self._rightwingfuel_mass = int(rightwingfuel_mass)
        #     self._rightwingfuel = self._mass_to_volume(self.rightwingfuel_mass)
        #     self._rightwingfuel_gauge = self._mass_to_gauge(
        #         self.rightwingfuel_mass, self.maxwingfuel
        #     )
        # elif rightwingfuel_gauge:
        #     self._rightwingfuel_gauge = float(rightwingfuel_gauge)
        #     self._rightwingfuel = self._gauge_to_volume(
        #         self.rightwingfuel_gauge, self.maxwingfuel
        #     )
        #     self._rightwingfuel_mass = self._gauge_to_mass(
        #         self.rightwingfuel_gauge, self.maxwingfuel
        #     )
        # else:
        #     self._rightwingfuel = 0
        #     self._rightwingfuel_mass = 0
        #     self._rightwingfuel_gauge = 0

        self.auxfuel = int(auxfuel)
        # if auxfuel:
        #     self._auxfuel = int(auxfuel)
        #     self._auxfuel_mass = self._volume_to_mass(self.auxfuel)
        #     self._auxfuel_gauge = self._volume_to_gauge(self.auxfuel, self.maxauxfuel)
        # elif auxfuel_mass:
        #     self._auxfuel_mass = int(auxfuel_mass)
        #     self._auxfuel = self._mass_to_volume(self.auxfuel_mass)
        #     self._auxfuel_gauge = self._mass_to_gauge(
        #         self.auxfuel_mass, self.maxauxfuel
        #     )
        # elif auxfuel_gauge:
        #     self._auxfuel_gauge = float(auxfuel_gauge)
        #     self._auxfuel = self._gauge_to_volume(self.auxfuel_gauge, self.maxauxfuel)
        #     self._auxfuel_mass = self._gauge_to_mass(
        #         self.auxfuel_gauge, self.maxauxfuel
        #     )
        # else:
        #     self._auxfuel = 0
        #     self._auxfuel_mass = 0
        #     self._auxfuel_gauge = 0

        # Initialize computed properties
        self._auw = 0
        self._moment = 0
        self._cg = 0
        # Need to have attributes instantiated right away
        _ = self.auw, self.moment, self.cg, self.sumbag

    def __repr__(self):
        """Repr."""
        keylist = [
            "callsign",
            "pax0",
            "pax1",
            "pax2",
            "pax3",
            "baggage",
            "baggage2",
            "mainfuel",
            "leftwingfuel",
            "rightwingfuel",
            "auxfuel",
        ]
        # Couldn't use a list comprehension there. Go figure
        valuelist = [
            f"{self.callsign}",
            f"{self.pax0}",
            f"{self.pax1}",
            f"{self.pax2}",
            f"{self.pax3}",
            f"{self.baggage}",
            f"{self.baggage2}",
            f"{self.mainfuel}",
            f"{self.leftwingfuel}",
            f"{self.rightwingfuel}",
            f"{self.auxfuel}",
        ]
        parameters = ", ".join([f"{a}={b}" for a, b in zip(keylist, valuelist)])
        return f"{self.__class__.__name__}({parameters})"

    @staticmethod
    def load_fleet_data():
        """Load planes.yaml data into a variable.

        Returns:
            json: planes data from yaml
        """
        fleet_data = "data/fleet.yaml"
        stream = pkgutil.get_data(__name__, fleet_data)
        return yaml.safe_load(stream)

    def _volume_to_mass(self,volume):
        """Convert a volume of fuel to mass (litres to kg)."""
        assert volume >= 0
        return volume * self.avgas.density

    def _mass_to_volume(self,mass):
        """Convert a mass of fuel to volume (kg to litres)."""
        assert mass > 0
        return mass / self.avgas.density

    @staticmethod
    def _volume_to_gauge(volume, tank):
        """Volume to gauge.

        Convert a volume of fuel to gauge indication (4 fourths)
        knowing the volume of the tank.

        Arguments:
            volume (int): litres.
            tank (int): the tank's capacity.
        """
        assert volume >= 0
        if tank == 0:
            return 0
        return volume / tank * 4

    @staticmethod
    def _mass_to_gauge(mass, tank):
        """Mass to gauge reading.

        Convert a mass of fuel to gauge indication (4 fourths)
        knowing the volume of the tank.

        Arguments:
            mass (int): kg.
            tank (int): the tank's capacity.
        """
        assert mass >= 0
        volume = WeightBalance._mass_to_volume(mass)
        return WeightBalance._volume_to_gauge(volume, tank)

    @staticmethod
    def _gauge_to_volume(gauge, tank):
        """Gauge reading to volume.

        Convert a gauge indication to a volume of fuel
        knowing the volume of the tank

        Arguments:
            gauge (float): gauge indication in fourths by step of .5.
            tank (int): the tank's capacity.
        """
        assert gauge in np.arange(0, 4.5, 0.5)
        return gauge * tank / 4

    def _gauge_to_mass(self, gauge, tank):
        """Gauge reading to mass.

        Convert a gauge indication to a mass of 100LL gas
        knowing the volume of the tank.

        Arguments:
            gauge (float): gauge indication in fourths by step of .5.
            tank (int): the tank's capacity.
        """
        assert 0 <= gauge <= 4
        return gauge * tank / 4 * self.avgas.density

    @property
    def auw(self):
        """All-up weight. Sum of all the parts.

        Returns:
            (float): all-up weight in kg.
        """
        reason = "All-up weight above MTOW"
        self._auw = (
            self.bew  # BEW
            + self.pax0
            + self.pax1  # Front row
            + self.pax2
            + self.pax3  # Back row
            + self.baggage  # Baggage row
            + self.baggage2 # zone 2 baggage in Sonaca
            + self.mainfuel_mass  # Main fuel tank
            + self.leftwingfuel_mass  # Left wing fuel tank
            + self.rightwingfuel_mass  # Right wing fuel tank
            + self.auxfuel_mass  # Auxiliary fuel tank
        )
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
        """Overall moment. Sum of the moments of all the sectors.

        Returns:
            (float): overall moment in kg.m.
        """
        self._moment = (
            self.bew * self.arms["bew"]
            + (self.pax0 + self.pax1) * self.arms["front"]
            + (self.pax2 + self.pax3) * self.arms["rear"]
            + self.baggage * self.arms["baggage"]
            + self.baggage2 * self.arms["baggage2"]
            + self.mainfuel_mass * self.arms["mainfuel"]
            + self.leftwingfuel_mass * self.arms["wingfuel"]
            + self.rightwingfuel_mass * self.arms["wingfuel"]
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
        reason = "Balance out of cg envelope"
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
        """Mass of pax in kg."""
        return self._pax0

    @pax0.setter
    def pax0(self, value):
        self._pax0 = value

    @property
    def pax1(self):
        """Mass of pax in kg."""
        return self._pax1

    @pax1.setter
    def pax1(self, value):
        self._pax1 = value

    @property
    def pax2(self):
        """Mass of pax in kg."""
        return self._pax2

    @pax2.setter
    def pax2(self, value):
        self._pax2 = value

    @property
    def pax3(self):
        """Mass of pax in kg."""
        return self._pax3

    @pax3.setter
    def pax3(self, value):
        self._pax3 = value

    @property
    def frontweight(self):
        """Compute mass of front row."""
        return self.pax0 + self.pax1

    @property
    def frontmoment(self):
        """Moment of front row."""
        return self.frontweight * self.arms["front"]

    @property
    def rearweight(self):
        """Compute mass of rear row."""
        return self.pax2 + self.pax3

    @property
    def rearmoment(self):
        """Moment of rear row."""
        return self.rearweight * self.arms["rear"]

    @property
    def baggage(self):
        """Mass of baggage in kg."""
        return self._baggage

    @baggage.setter
    def baggage(self, value):
        """Baggage weight input.

        It is checked against the aircraft's max baggage weight
        and the max weight in zone 1 and 2.

        Args:
            value (int): baggage weight in kg.
        """
        reason = "Baggage weight over max weight"
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
        """Moment of baggage."""
        return self.baggage * self.arms["baggage"]

    @property
    def baggage2(self):
        """Mass of zone2 baggage in kg."""
        return self._baggage2

    @baggage2.setter
    def baggage2(self, value):
        """Zone 2 baggage weight input.

        It is checked against the aircraft's max zone 2 baggage weight.

        Args:
            value (int): zone 2 baggage weight in kg.
        """
        reason = "Zone 2 baggage weight over max weight"
        if value > self.bagmax2:
            self.is_ready_to_fly = False
            if reason not in self.reasons:
                logging.error(reason)
                self.reasons.append(reason)
        else:
            self.reasons = [k for k in self.reasons if k != reason]
        self._baggage2 = value

    @property
    def bagmoment2(self):
        """Moment of zone 2 baggage."""
        return self.baggage2 * self.arms["baggage2"]

    @property
    def sumbag(self):
        """Zone 1 + zone 2 baggages.
        
        Checked against sumbagmax parameter.
        """
        reason = f"Baggage + baggage2 over {self.sumbagmax}kg for type {self.planetype}"
        if self.sumbagmax and self.baggage + self.baggage2 > self.sumbagmax:
            self.is_ready_to_fly = False
            if reason not in self.reasons:
                logging.error(reason)
                self.reasons.append(reason)
        else:
            self.reasons = [k for k in self.reasons if k != reason]
        return self.baggage + self.baggage2

    @property
    def mainfuel(self):
        """Fuel quantity in litres."""
        return self._mainfuel

    @mainfuel.setter
    def mainfuel(self, value):
        self._mainfuel = value
        if self.maxmainfuel == 0 and value > 0:
            msg = f"{self.callsign} has no main fuel tank. Setting volume to 0."
            logging.warning(msg)
            self._mainfuel = 0
        elif value > self.maxmainfuel:
            msg = f"Main tank max volume is {self.maxauxfuel}"
            logging.error(msg)
            self._mainfuel = self.maxmainfuel
        self._mainfuel_mass = self._volume_to_mass(self._mainfuel)
        self._mainfuel_gauge = self._volume_to_gauge(self._mainfuel, self.maxmainfuel)

    @property
    def mainfuel_mass(self):
        """Fuel quantity in kg."""
        return self._mainfuel_mass

    @mainfuel_mass.setter
    def mainfuel_mass(self, value):
        assert 0 <= value <= self._volume_to_mass(self.maxmainfuel)
        self._mainfuel_mass = value
        self._mainfuel = self._mass_to_volume(self._mainfuel_mass)
        self._mainfuel_gauge = self._volume_to_gauge(self._mainfuel, self.maxmainfuel)

    @property
    def mainfuel_gauge(self):
        """Fuel gauge indicator in fourths with step of .5."""
        return self._mainfuel_gauge

    @mainfuel_gauge.setter
    def mainfuel_gauge(self, value):
        assert 0 <= value <= 4  # 4 fourths of a tank
        self._mainfuel_gauge = value
        self._mainfuel = self._gauge_to_volume(self._mainfuel_gauge, self.maxmainfuel)
        self._mainfuel_mass = self._gauge_to_mass(
            self._mainfuel_gauge, self.maxmainfuel
        )

    @property
    def mainfuelmoment(self):
        """Moment of main fuel tank."""
        return self.mainfuel_mass * self.arms["mainfuel"]

    @property
    def leftwingfuel(self):
        """Left wing fuel quantity in litres."""
        return self._leftwingfuel

    @leftwingfuel.setter
    def leftwingfuel(self, value):
        self._leftwingfuel = value
        if self.maxwingfuel == 0 and value > 0:
            msg = f"{self.callsign} has no wing fuel tank. Setting volume to 0."
            logging.warning(msg)
            self._leftwingfuel = 0
        elif value > self.maxwingfuel:
            msg = f"Wing tank max volume is {self.maxwingfuel}"
            logging.error(msg)
            self._leftwingfuel = self.maxwingfuel
        self._leftwingfuel_mass = self._volume_to_mass(self._leftwingfuel)
        self._leftwingfuel_gauge = self._volume_to_gauge(
            self._leftwingfuel, self.maxwingfuel
        )

    @property
    def leftwingfuel_mass(self):
        """Left wing fuel quantity in kg."""
        return self._leftwingfuel_mass

    @leftwingfuel_mass.setter
    def leftwingfuel_mass(self, value):
        assert 0 <= value <= self._volume_to_mass(self.maxwingfuel)
        self._leftwingfuel_mass = value
        self._leftwingfuel = self._mass_to_volume(self._leftwingfuel_mass)
        self._leftwingfuel_gauge = self._volume_to_gauge(
            self._leftwingfuel, self.maxwingfuel
        )

    @property
    def leftwingfuel_gauge(self):
        """Left wing fuel gauge indicator in fourths with step of .5."""
        return self._leftwingfuel_gauge

    @leftwingfuel_gauge.setter
    def leftwingfuel_gauge(self, value):
        assert 0 <= value <= 4  # 4 fourths of a tank
        self._leftwingfuel_gauge = value
        self._leftwingfuel = self._gauge_to_volume(
            self._leftwingfuel_gauge, self.maxwingfuel
        )
        self._leftwingfuel_mass = self._gauge_to_mass(
            self._leftwingfuel_gauge, self.maxwingfuel
        )

    @property
    def rightwingfuel(self):
        """Right wing fuel quantity in litres."""
        return self._rightwingfuel

    @rightwingfuel.setter
    def rightwingfuel(self, value):
        self._rightwingfuel = value
        if self.maxwingfuel == 0 and value > 0:
            msg = f"{self.callsign} has no wing fuel tank. Setting volume to 0."
            logging.warning(msg)
            self._rightwingfuel = 0
        elif value > self.maxwingfuel:
            msg = f"Wing tank max volume is {self.maxwingfuel}"
            logging.error(msg)
            self._rightwingfuel = self.maxwingfuel
        self._rightwingfuel_mass = self._volume_to_mass(self._rightwingfuel)
        self._rightwingfuel_gauge = self._volume_to_gauge(
            self._rightwingfuel, self.maxwingfuel
        )

    @property
    def rightwingfuel_mass(self):
        """Right wing fuel quantity in kg."""
        return self._rightwingfuel_mass

    @rightwingfuel_mass.setter
    def rightwingfuel_mass(self, value):
        assert 0 <= value <= self._volume_to_mass(self.maxwingfuel)
        self._rightwingfuel_mass = value
        self._rightwingfuel = self._mass_to_volume(self._rightwingfuel_mass)
        self._rightwingfuel_gauge = self._volume_to_gauge(
            self._rightwingfuel, self.maxwingfuel
        )

    @property
    def rightwingfuel_gauge(self):
        """Right wing fuel gauge indicator in fourths with step of .5."""
        return self._rightwingfuel_gauge

    @rightwingfuel_gauge.setter
    def rightwingfuel_gauge(self, value):
        assert 0 <= value <= 4  # 4 fourths of a tank
        self._rightwingfuel_gauge = value
        self._rightwingfuel = self._gauge_to_volume(
            self._rightwingfuel_gauge, self.maxwingfuel
        )
        self._rightwingfuel_mass = self._gauge_to_mass(
            self._rightwingfuel_gauge, self.maxwingfuel
        )

    @property
    def wingfuel_mass(self):
        """Total mass of wing fuel tanks."""
        return self.leftwingfuel_mass + self.rightwingfuel_mass

    @property
    def wingfuelmoment(self):
        """Moment of wing fuel tanks."""
        return (self.leftwingfuel_mass + self.rightwingfuel_mass) * self.arms[
            "wingfuel"
        ]

    @property
    def auxfuel(self):
        """Auxiliary fuel in litres."""
        return self._auxfuel

    @auxfuel.setter
    def auxfuel(self, value):
        assert value >= 0
        self._auxfuel = value
        if self.maxauxfuel == 0 and value > 0:
            msg = f"{self.callsign} has no auxiliary fuel tank. Setting volume to 0."
            logging.warning(msg)
            self._auxfuel = 0
        elif value > self.maxauxfuel:
            msg = f"Auxiliary tank max volume is {self.maxauxfuel}"
            logging.error(msg)
            self._auxfuel = self.maxauxfuel
        self._auxfuel_mass = self._volume_to_mass(self._auxfuel)

    @property
    def auxfuel_mass(self):
        """Auxiliary fuel in kg."""
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
        """Auxiliary fuel gauge indicator in fourths with step of .5."""
        return self._auxfuel_gauge

    @auxfuel_gauge.setter
    def auxfuel_gauge(self, value):
        assert 0 <= value <= 4  # 4 fourths of a tank
        self._auxfuel_gauge = value
        self._auxfuel = self._gauge_to_volume(self._auxfuel_gauge, self.maxauxfuel)
        self._auxfuel_mass = self._gauge_to_mass(self._auxfuel_gauge, self.maxauxfuel)

    @property
    def auxfuelmoment(self):
        """Moment of auxiliary fuel tank."""
        return self.auxfuel_mass * self.arms["auxfuel"]

    @property
    def endurance(self):
        """Endurance of the flight.

        Roughly the usable fuel divided by the fuel flow rate at cruise speed.

        Returns:
            float: endurance in hours.
        """
        usable_fuel = (
            self.mainfuel + self.leftwingfuel + self.rightwingfuel + self.auxfuel
        ) - (self.unusable_mainfuel + 2 * self.unusable_wingfuel)
        # Fix uggly negative endurance when no fuel
        if usable_fuel < 0:
            usable_fuel = 0
        endurance = usable_fuel / self.fuelrate
        # Round down to multiples of 5 mn
        # (convert to mn then round down base 5 then back to hours)
        return 5 * int(60 * endurance / 5) / 60

    @property
    def flight_time(self):
        """Flight time given the 30 minutes ICAO regulation for day VFR"""
        return max(0, self.endurance - 0.5)

    @property
    def flight_time_night(self):
        """Flight time given the 45 minutes ICAO regulation for night VFR"""
        return max(0, self.endurance - 0.75)

    def plot_balance(self, encode=False):
        """Plot the envelope with the evolution of the cg.

        Arguments:
            encode (boolean): returns BytesIO if True.

        Returns:
            image or image bytes.
        """
        # Envelope
        polygon = Polygon(tuple(k) for k in self.envelope)

        # Get cg and auw with no fuel
        no_fuel_plane = copy.copy(self)
        no_fuel_plane.mainfuel = 0
        no_fuel_plane.leftwingfuel = 0
        no_fuel_plane.rightwingfuel = 0
        no_fuel_plane.auxfuel = 0

        # Get rid of matplotlib thread warning
        backend = plt.get_backend()
        matplotlib.use("Agg")
        fig = plt.figure()
        axis = plt.gca()
        axis.plot(*polygon.exterior.xy, c="b")
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        axis.set_title(f"Centrage de {self.callsign} - {date}")
        # Start and no fuel points
        axis.plot([self.cg, no_fuel_plane.cg], [self.auw, no_fuel_plane.auw], "r")
        axis.plot([self.cg], [self.auw], "ro", markerfacecolor="w", markersize=12)
        axis.plot(
            [no_fuel_plane.cg],
            [no_fuel_plane.auw],
            "r^",
            markerfacecolor="w",
            markersize=12,
        )
        axis.set_xlabel("m", fontsize=12)
        axis.set_ylabel("Kg", fontsize=12)
        plt.tight_layout()

        if encode:
            canvas = FigureCanvas(fig)
            png = BytesIO()
            canvas.print_png(png)
            figdata = b64encode(png.getvalue()).decode("ascii")
            plt.close(fig)
            return figdata

        # Restore original matplotlib backend
        matplotlib.use(backend)
        _ = plt.show()


class PlanePerf:
    """Predict DR400 planes takeoff and landing distances (50ft).

    Distances are predicted given an all-up weight, the ground altitude,
    temperature and QNH.

    Arguments:
        planetype (str):
            "DR400-120", "DR400-140B", "S201" ...
        auw (float):
            all-up weight in kg.
        altitude (int):
            altitude in feet.
        temperature (int):
            temperature in Celsius degrees.
        qnh (int):
            QNH in mbar.
    """

    def __init__(self, planetype, auw, altitude, temperature, qnh, **_kwargs):
        """Init."""
        self.planetype = str(planetype)
        self.auw = float(auw)
        self.altitude = int(altitude)
        self.temperature = int(temperature)
        self.qnh = int(qnh)

    def __repr__(self):
        """Repr."""
        return f"""{self.__class__.__name__}(
                planetype='{self.planetype}',
                auw={self.auw}, altitude={self.altitude},
                temperature={self.temperature}, qnh={self.qnh})"""

    @staticmethod
    def pressure_altitude(elevation, qnh):
        """Compute the pressure altitude from a ground elevation and the QNH.

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
        """Pressure altitude in feet."""
        return PlanePerf.pressure_altitude(self.altitude, self.qnh)

    @staticmethod
    def density_altitude(elevation, temperature, qnh):
        """Compute the densisty altitude.

        Density altitude is computed given an elevation, an outside air temperature
        and the QNH.

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
        Zp = PlanePerf.pressure_altitude(elevation, qnh)
        return 1.2376 * Zp + 118.8 * temperature - 1782

    @property
    def Zd(self):
        """Density altitude in feet."""
        return PlanePerf.density_altitude(self.altitude, self.temperature, self.qnh)

    def takeoff_data(self):
        """
        Raw takeoff performance data.

        Data source is the POH (pilot operating handbook.
        Data is loaded from a csv file stored in ./data.
        """
        input_file = Path(__file__).parent / "data" / (self.planetype + "_takeoff.csv")
        try:
            tkoff = pd.read_csv(input_file, sep="\t", header=0)
        except Exception as exception:
            logging.error("file %s does not exist or is not readable.", input_file)
            logging.error(exception)
            raise

        tkoff = tkoff.melt(id_vars=["alt", "temp"], var_name="mass", value_name="m")
        tkoff["temp"] = tkoff["temp"] + 273
        tkoff["mass"] = tkoff["mass"].astype("int")
        return tkoff

    def landing_data(self):
        """
        Raw landing performance data.

        Data source is the POH (pilot operating handbook.
        Data is loaded from a csv file stored in ./data.
        """
        input_file = Path(__file__).parent / "data" / (self.planetype + "_landing.csv")
        try:
            ldng = pd.read_csv(input_file, sep="\t", header=0)
        except Exception as exception:
            logging.error("file %s does not exist or is not readable.", input_file)
            logging.error(exception)
            raise

        ldng = pd.read_csv(input_file, sep="\t", header=0)
        ldng = ldng.melt(id_vars=["alt", "temp"], var_name="mass", value_name="m")
        ldng["temp"] = ldng["temp"] + 273
        ldng["mass"] = ldng["mass"].astype("int")
        return ldng

    def make_model(self, operation):
        """Return a trained model of takeoff or landing performance.

        Arguments:
            operation (str): "takeoff" or "landing"

        Returns:
            sklearn linear regression model.
        """
        assert operation in ["takeoff", "landing"]

        if operation == "takeoff":
            data_df = self.takeoff_data()
        elif operation == "landing":
            data_df = self.landing_data()

        model = make_pipeline(PolynomialFeatures(2), LinearRegression())
        _ = model.fit(data_df.iloc[:, :3].values, data_df.iloc[:, 3].values)

        return model

    def predict(self, operation):
        """Predict takeoff or landing distance.

        - Build a linear regression model out of the raw data.
        - Predict takeoff or landing distance (50ft) given:
            - type of plane
            - altitude in ft
            - temperature in °C
            - auw in kg
            - QNH in mbar

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
        # Zd = self.density_altitude(self.altitude, self.temperature, self.qnh)

        distance = model.predict([[Zp, Ktemp, self.auw]])
        # Applying coefficient for head wind
        if operation == "takeoff":
            asphalt = np.around(distance * np.array([[1, 0.85, 0.65, 0.55]]))
        else:
            asphalt = np.around(distance * np.array([[1, 0.78, 0.63, 0.52]]))
        df_distance = pd.DataFrame(asphalt, columns=["0kts", "10kts", "20kts", "30kts"])
        # Applying coefficient for grass runway
        df_distance = df_distance.append(
            df_distance.iloc[0].apply(lambda x: round(x * 1.15))
        ).astype("int")
        df_distance.index = ["dur", "herbe"]
        df_distance.columns.name = "Ve"
        # title = {"takeoff": "de décollage", "landing": "d'atterrissage"}
        # print(
        # f"\nDistance {title[operation]} (15m)\nZp {Zp}ft\nZd {Zd} ft
        # \n{self.temperature}°C\n{self.auw}kg\n"
        # )

        return df_distance

    def plot_performance(self, operation, encode=False):
        """Plot takeoff or landing peformance.

        Plot a contour graph of the takeoff or landing performance
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
        n_zones = 10

        # Make a mesh grid of altitudes and temperatures
        predict_a, predict_t = np.meshgrid(
            np.linspace(0, 10000, n_zones), np.linspace(243, 323, n_zones)
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

        # Get rid of matplotlib thread warning
        backend = plt.get_backend()
        matplotlib.use("Agg")
        fig = plt.figure(figsize=(12, 10))
        axis = plt.gca()
        contours = axis.contourf(
            predict_a,
            predict_t - 273,
            predict_y.reshape(predict_a.shape),
            # cmap=surf.cmap.name,
            cmap=cm.jet,
            alpha=0.6,
        )
        title = {"takeoff": "décollage", "landing": "atterrissage"}
        axis.set_title(f"{title[operation]} (15m) à {self.auw:.2f}Kg", size=26)
        axis.contour(contours, colors="k")
        cbar = fig.colorbar(contours, ax=axis)
        axis.set_xlabel("Zp (ft)", size=24)
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        axis.set_ylabel("°C", size=24)
        cbar.ax.set_ylabel("mètres", rotation=270, size=24, labelpad=20)
        cbar.ax.tick_params(labelsize=20)
        # plt.scatter(self.altitude, self.temperature,s=500,c="white")
        fig.patch.set_alpha(1)
        fig.tight_layout()

        if encode:
            canvas = FigureCanvas(fig)
            png = BytesIO()
            canvas.print_png(png)
            figdata = b64encode(png.getvalue()).decode("ascii")
            plt.close(fig)
            return figdata

        # Restore original matplotlib backend
        matplotlib.use(backend)
        _ = plt.show()
