import datetime

import humanize
from.planes import WeightBalance
from .emport_carburant_form import TypeVol


class EmportCarburant():
    def __init__(
        self,
        callsign,
        branches,
        type_vol,
        nb_branches,
        degagement,
        marge,
        mainfuel,
        leftwingfuel,
        rightwingfuel,
        auxfuel,
        **kwargs
        ) -> None:
        self.callsign = callsign
        self.branches = branches[0:nb_branches]
        self.type_vol = TypeVol[type_vol]
        self.nb_branches = nb_branches
        self.degagement = degagement
        self.marge = marge
        self.mainfuel = mainfuel
        self.leftwingfuel = leftwingfuel
        self.rightwingfuel = rightwingfuel
        self.auxfuel = auxfuel
        self.plane = WeightBalance(callsign)

    @property
    def rng_nb_branches(self):
        return range(self.nb_branches)

    @property
    def unusable_fuel(self) -> int:
        return self.plane.unusable_fuel

    @property
    def unusable_fuel_time(self) -> int:
        return 0

    @property
    def roulage_time(self) -> int:
        return self.nb_branches * 5

    @property
    def roulage_fuel(self) -> float:
        return (self.plane.fuelrate / 60) * self.roulage_time

    @property
    def arrival_time(self) -> int:
        return self.nb_branches * 10

    @property
    def arrival_fuel(self) -> float:
        return (self.plane.fuelrate / 60) * self.arrival_time

    @property
    def degagement_time(self) -> int:
        return (60 / (100 - self.degagement["vent"])) * self.degagement["distance"]

    @property
    def degagement_fuel(self) -> float:
        return (self.plane.fuelrate / 60) * self.degagement_time

    @property
    def marge_time(self) -> int:
        return int(self.marge)

    @property
    def marge_fuel(self) -> float:
        return (self.plane.fuelrate / 60) * self.marge_time

    @property
    def reserve_time(self) -> int:
        if self.type_vol.name == "NUIT":
            return 45
        elif self.type_vol.name == "NAV" or self.type_vol.name == "VLJHA":
            return 30
        else:
            return 10

    @property
    def max_flight_time(self) -> int:
        return self.sum_carburant_emporte_time - self.reserve_time
    
    @property
    def reserve_fuel(self) -> float:
        return (self.plane.fuelrate / 60) * self.reserve_time

    @staticmethod
    def calculate_tps_vol_corrige(vent, distance):
        if vent >= 0:
            sh = (60 / (100 - vent)) * distance
        else:
            sh = (60 / (100 + vent)) * distance
        return sh 

    @property
    def branches_time(self):
        br = []
        for b in self.branches:
            vent = b["vent"]
            dist = b["distance"]
            tsv = EmportCarburant.calculate_tps_vol_corrige(vent, dist)
            br.append(tsv)
        return br

    @property
    def branches_fuel(self):
        br = []
        for b in self.branches:
            vent = b["vent"]
            dist = b["distance"]
            tps = EmportCarburant.calculate_tps_vol_corrige(vent, dist)
            fu = (self.plane.fuelrate / 60) * tps
            br.append(fu)
        return br

    @property
    def sum_time(self):
        return sum(self.branches_time) + self.marge_time + self.arrival_time + self.roulage_time + self.reserve_time + self.degagement_time + self.unusable_fuel_time

    @property
    def sum_fuel(self):
        return sum(self.branches_fuel) + self.marge_fuel + self.arrival_fuel + self.roulage_fuel + self.reserve_fuel + self.degagement_fuel + self.unusable_fuel

    @property
    def carburant_wings(self):
        return self.leftwingfuel + self.rightwingfuel

    @property
    def carburant_emporte_wings(self):
        return self.plane.maxwingfuel * (self.carburant_wings / 100)

    @property
    def carburant_emporte_wings_time(self):
        return (self.carburant_emporte_wings / self.plane.fuelrate * 60) - (self.plane.unusable_wingfuel / self.plane.fuelrate * 60)
    
    @property
    def carburant_emporte_main(self):
        return self.plane.maxmainfuel * (self.mainfuel / 100)
    
    @property
    def carburant_emporte_main_time(self):
        return (self.carburant_emporte_main / self.plane.fuelrate * 60) - (self.plane.unusable_mainfuel / self.plane.fuelrate * 60)
    
    @property
    def carburant_emporte_aux(self):
        return self.plane.maxauxfuel * (self.auxfuel / 100)

    @property
    def carburant_emporte_aux_time(self):
        return self.carburant_emporte_aux / self.plane.fuelrate * 60

    @property
    def sum_carburant_emporte(self):
        return self.carburant_emporte_main + self.carburant_emporte_aux + self.carburant_emporte_wings
    
    @property
    def sum_carburant_emporte_time(self):
        return self.carburant_emporte_main_time + self.carburant_emporte_wings_time + self.carburant_emporte_aux_time

    @property
    def compare_fuel(self) -> bool:
        return self.sum_carburant_emporte >= self.sum_fuel

    def authorized(self):
        return self.compare_fuel

    @property
    def get_compared_fuel(self):
        return self.sum_fuel - self.sum_carburant_emporte

    @property
    def get_report(self):
        ph = []
        _ = humanize.activate("fr")
        if self.compare_fuel:
            ph.append(f"Avec un emport minimum de {humanize.apnumber(self.sum_fuel)} litres, l'objectif de {self.type_vol.value.lower()} avec le {self.callsign} ({self.plane.planetype}) est <strong>autorisé</strong>. La durée de ce vol inclant {self.nb_branches} branche(s), {self.nb_branches} départ(s) et {self.nb_branches} arrivée(s) est estimée à {str(datetime.timedelta(minutes=self.sum_time))}. Avec {humanize.apnumber(self.sum_carburant_emporte)} litres embarqués, vous aurez une autonomie de {humanize.naturaldelta(datetime.timedelta(minutes=self.sum_carburant_emporte_time))} ({str(datetime.timedelta(minutes=self.sum_carburant_emporte_time))} minutes). Votre vol ne devra pas excéder {str(datetime.timedelta(minutes=self.max_flight_time))} car votre réserve finale est de {self.reserve_time}mn. Ces valeurs sont à reporter à la section 2 de votre devis de masse et centrage. Les performances de décollages / atterrissages sont à vérfier dans le manuel de vol. <strong>BON VOL</strong>".split(". "))
            ph.append("is-success")
        else:
            ph.append(f"Ce vol n'est pas autorisé car il manque {humanize.apnumber(self.get_compared_fuel)} litres de carburant.".split("."))
            ph.append("is-danger")
        return ph
