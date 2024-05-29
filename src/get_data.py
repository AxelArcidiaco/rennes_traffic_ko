# Importation des bibliothèques requises
import pandas as pd
import requests
import logging


class GetData(object):

    def __init__(self, url) -> None:
        self.url = url
        try:
            response = requests.get(self.url)
            response.raise_for_status()  # Vérifie si la requête a réussi
            self.data = response.json()
        except requests.exceptions.RequestException as e:
            logging.error("Failed to retrieve data", exc_info=True)
            raise

    def processing_one_point(self, data_dict: dict):
        try:
            temp = pd.DataFrame(
                {
                    key: [data_dict[key]]
                    for key in [
                        "datetime",
                        "trafficstatus",
                        "geo_point_2d",
                        "averagevehiclespeed",
                        "traveltime",
                    ]
                }
            )
            temp = temp.rename(columns={"trafficstatus": "traffic"})
            temp["lat"] = temp.geo_point_2d.map(lambda x: x["lat"])
            temp["lon"] = temp.geo_point_2d.map(lambda x: x["lon"])
            del temp["geo_point_2d"]

            return temp
        except KeyError as e:
            logging.error("Key error while processing data point", exc_info=True)
            raise

    def __call__(self):
        try:
            res_df = pd.DataFrame()

            for data_dict in self.data:
                temp_df = self.processing_one_point(data_dict)
                res_df = pd.concat([res_df, temp_df], ignore_index=True)

            res_df = res_df[
                res_df.traffic != "unknown"
            ]  # Correctly close the filtering

            return res_df
        except Exception as e:
            logging.error("Error during data processing", exc_info=True)
            raise
