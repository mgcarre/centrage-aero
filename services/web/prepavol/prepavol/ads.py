import pkgutil
import yaml

class ADs:
    def __init__(
        self,
        nom
    ) -> None:
        terrains = ADs.load_ad_data()
        if nom not in terrains.keys():
            raise Exception(
                f"No such AD name. Valid AD names are {', '.join(terrains.keys())}"
            )
        selected_ad = terrains[nom]
        self.nom: str = selected_ad["nom"]
        self.code: str = selected_ad["code"]
        self.var: float = selected_ad["var"]
        self.point: list = self.get_geo(selected_ad["Geo"])
        self.alt: int = selected_ad["alt"]
        self.GUND_DTHR_ALT_ft: int = selected_ad["GUND_DTHR_ALT_ft"]
        self.trafic: str = selected_ad["trafic"]
        self.statut: str = selected_ad["statut"]

    @staticmethod
    def load_ad_data():
        ad_data = "data/alts.yaml"
        stream = pkgutil.get_data(__name__, ad_data)
        return yaml.safe_load(stream)

    
    def __conversion(self,old):
        direction = {'N':1, 'S':-1, 'E': 1, 'W':-1}
        new = old.replace(u'°',' ').replace('\'',' ').replace('"',' ')
        new = new.split()
        new_dir = new.pop()
        new.extend([0,0,0])
        return round((int(new[0])+int(new[1])/60.0+int(new[2])/3600.0) * direction[new_dir], 5)
    
    def get_geo(self,str):
        lat, lon = str.split(' ')
        return [self.__conversion(lat), self.__conversion(lon)]