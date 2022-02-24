from typing import List
import pandas as pd
from pathlib import Path
import logging
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from io import BytesIO
from base64 import b64encode

from matplotlib import cm
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline

__all__ = ["WeightBalance"]

class PlanePerf:
    """Predict how planes takeoff and landing distances (50ft).

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
    def revetements() -> List[str]:
        return ["dur", "herbe", "dur mouillée", "herbe mouillée", "pente 2%", "contaminée", "multiple"]

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

    def predict(self, operation, revetements = ["dur", "herbe"]):
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
        columns = ["0kts", "10kts", "20kts", "30kts"]
        df_distance = pd.DataFrame(asphalt, columns=columns)
        # Series for grass runway
        s_grass = pd.Series(
            df_distance.iloc[0].apply(lambda x: round(x * (1.2,1.15)[operation == "landing"])),
            index=columns
        )
        # Series for wet runway
        s_wet = pd.Series(
            df_distance.iloc[0].apply(lambda x: round(x * (1,1.15)[operation == "landing"])),
            index=columns
        )
        # Series for wet grass runway
        s_wet_grass = pd.Series(
            df_distance.iloc[0].apply(lambda x: round(x * (1.3,1.35)[operation == "landing"])),
            index=columns
        )
        # Series for inclined runway
        s_inclined = pd.Series(
            df_distance.iloc[0].apply(lambda x: round(x * 1.1)),
            index=columns
        )
        # Series for contaminated runway
        s_snow = pd.Series(
            df_distance.iloc[0].apply(lambda x: round(x * 1.2)),
            index=columns
        )
        # Series for contaminated runway
        s_multiple = pd.Series(
            df_distance.iloc[0].apply(lambda x: round(x * (1.33,1.43)[operation == "landing"])),
            index=columns
        )
        df_retour = pd.concat([
            df_distance, 
            s_grass.to_frame().T,
            s_wet.to_frame().T,
            s_wet_grass.to_frame().T,
            s_inclined.to_frame().T,
            s_snow.to_frame().T,
            s_multiple.to_frame().T
            ]).astype("int")
        df_retour.index = PlanePerf.revetements()
        df_retour.columns.name = "Ve"
        # title = {"takeoff": "de décollage", "landing": "d'atterrissage"}
        # print(
        # f"\nDistance {title[operation]} (15m)\nZp {Zp}ft\nZd {Zd} ft
        # \n{self.temperature}°C\n{self.auw}kg\n"
        # )

        return df_retour[df_retour.index.isin(revetements)]

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
