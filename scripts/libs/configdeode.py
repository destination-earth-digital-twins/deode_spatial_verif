import os
import re
import tomllib
import yaml
from datetime import datetime, timedelta
from dateutil import parser
import pandas as pd
import pyproj

from LoadWriteData import LoadConfigFileFromYaml

vars_dict_deode = {
    "pcp": {
        "var": [
            "tirf", {"parameterCategory": 1, "parameterNumber": 75}, "sprate"
        ],
        "accum": True,
        "verif_0h": False,
        "postprocess": "tp_deode",
        "find_min": False
    },
    "rain": {
        "var": "tirf",
        "accum": True,
        "verif_0h": False,
        "postprocess": "None",
        "find_min": False
    },
    "lat": {
        "var": "lat",
        "description": "latitude coordinates in degrees"
    },
    "lon": {
        "var": "lon",
        "description": "longitude coordinates in degrees"
    }
}


class ConfigDeode(object):
    def __init__(
        self, config_toml, yaml_exp_template, yaml_case_template,
        vars_dict=vars_dict_deode
    ):
        self.config_toml = config_toml
        self.data = {}
        self.case_name = ""
        self.exp_name = "@CNMEXP@_@CSC@_@CYCLE@_@DOMAIN@"
        self.fp_path = ""
        self.fp_filename = ""
        self._exp_dict = LoadConfigFileFromYaml(yaml_exp_template)
        self._case_dict = LoadConfigFileFromYaml(yaml_case_template)
        self._vars_dict = vars_dict
        self._load_toml()

    def write_config_exp(self):
        replaced_exp_name = self._get_replaced_attr(self.exp_name)
        replaced_filename = self._get_replaced_attr(self.fp_filename)
        replaced_filepath = self._get_replaced_attr(self.fp_path)

        inits_str, fcsts_str = self._get_times_args()
        init_dict = {}
        for k, v in zip(inits_str, fcsts_str):
            init_dict.update({
                k: {
                    "path": 0,
                    "fcast_horiz": v
                }
            })

        config_filename = f"config/exp/config_{replaced_exp_name}.yaml"
        if os.path.isfile(config_filename):
            self._exp_dict = LoadConfigFileFromYaml(config_filename)
            self._exp_dict["inits"].update(init_dict)
        else:
            self._exp_dict["model"]["name"] = self.data["CSC"]
            self._exp_dict["format"]["filepaths"] = [replaced_filepath,]
            self._exp_dict["format"]["filename"] = replaced_filename
            self._exp_dict["format"]["fileformat"] = "Grib"
            self._exp_dict["inits"] = init_dict
            self._exp_dict["vars"] = self._vars_dict

        with open(config_filename, "w") as config_file:
            yaml.dump(self._exp_dict, config_file, default_flow_style=False)
        return replaced_exp_name

    def write_config_case(self):
        replaced_case_name = self._get_replaced_attr(self.case_name)

        inits_str, fcsts_str = self._get_times_args()
        lon_min, lon_max, lat_min, lat_max = self._compute_extension()

        config_filename = f"config/Case/config_{replaced_case_name}.yaml"
        if os.path.isfile(config_filename):
            self._case_dict = LoadConfigFileFromYaml(config_filename)
            date_end_config = datetime.strptime(
                self._case_dict["dates"]["end"], "%Y%m%d%H"
            )
            date_end_fcst = datetime.strptime(fcsts_str[-1], "%Y%m%d%H")
            if date_end_fcst > date_end_config:
                self._case_dict["dates"]["end"] = fcsts_str[-1]
        else:
            self._case_dict["dates"]["ini"] = inits_str[0]
            self._case_dict["dates"]["end"] = fcsts_str[-1]
            self._case_dict["location"]["NOzoom"] = [
                lon_min, lon_max, lat_min, lat_max
            ]
            self._case_dict["verif_domain"] = {
                inits_str[0]: [
                    lon_min + 1, lon_max - 1, lat_min + 1, lat_max - 1
                ]
            }

        with open(config_filename, "w") as config_file:
            yaml.dump(self._case_dict, config_file, default_flow_style=False)
        return replaced_case_name

    def _load_toml(self):
        with open(self.config_toml, "rb") as config_file:
            username = self.config_toml.split("/")[2]
            data = tomllib.load(config_file)
            self.data = {
                "SCRATCH": os.path.join(
                    ConfigDeode.replace_select_chr(
                        os.getenv("SCRATCH"),
                        dict_replace={
                            os.getenv("USER"): username
                        }
                    ),
                    "deode"
                ),
                "CNMEXP": data["general"]["cnmexp"],
                "DOMAIN": data["domain"]["name"],
                "DURATION_ARCHIVE": ConfigDeode.replace_select_chr(
                    data["file_templates"]["duration"]["archive"],
                    dict_replace={
                        "@LLLH@": "%LLLL",
                        "@LM@": "00",
                        "@LS@": "00"
                    }
                ),
                "CSC": data["general"]["csc"],
                "CASE_PREFIX": "",
                "CYCLE": data["general"]["cycle"],
                "TIME_INI": data["general"]["times"]["start"],
                "TIME_END": data["general"]["times"]["end"],
                "TIME_FREQ": data["general"]["times"]["cycle_length"],
                "TIME_FCST": data["general"]["times"]["forecast_range"],
                "NIMAX": data["domain"]["nimax"],
                "NJMAX": data["domain"]["njmax"],
                "XDX": data["domain"]["xdx"],
                "XDY": data["domain"]["xdy"],
                "XLATCEN": data["domain"]["xlatcen"],
                "XLONCEN": data["domain"]["xloncen"],
                "XLAT0": data["domain"]["xlat0"],
                "XLON0": data["domain"]["xlon0"],
                "PREV_CASE": data["system"]["prev_case"]
            }
            self.case_raw = data["general"]["case"]
            self.data["CASE"] = self._get_replaced_attr(self.case_raw)
            self.case_name = ConfigDeode.replace_select_chr(
                self.data["PREV_CASE"],
                dict_replace={
                    "@CYCLE@": "",
                    "@CSC@": ""
                }
            )
            self.fp_path = os.path.join(
                data["platform"]["archive_root"],
                "%Y/%m/%d/%H"
            )
            self.fp_filename = data["file_templates"]["fullpos"]["grib"]

    def _get_replaced_attr(self, attribute):
        patterns = re.findall(r"@(\w+)@", attribute)
        result = attribute
        for pattern in patterns:
            if pattern in self.data:
                result = result.replace(f"@{pattern}@", self.data[pattern])
        return result

    def _get_times_args(self):
        date_ini = parser.parse(self.data["TIME_INI"])
        date_end = parser.parse(self.data["TIME_END"])
        freq = self.data["TIME_FREQ"][2:].lower()
        fcst = int(self.data["TIME_FCST"][2:].replace("H", ""))
        dates = pd.date_range(date_ini, date_end, freq=freq).to_pydatetime()
        inits = [date.strftime("%Y%m%d%H") for date in dates]

        fcsts = []
        for date in dates:
            date_fcst = date + timedelta(hours=fcst)
            fcsts.append(date_fcst.strftime("%Y%m%d%H"))
        return inits, fcsts

    def _compute_extension(self):
        proj4 = "+proj=lcc " \
            + f"+lat_0={self.data['XLAT0']} +lon_0={self.data['XLON0']} " \
            + f"+lat_1={self.data['XLAT0']} +lat_2={self.data['XLAT0']}"
        projection = pyproj.Proj(proj4)
        half_height = int(self.data["NJMAX"] / 2) * self.data["XDY"]
        half_width = int(self.data["NIMAX"] / 2) * self.data["XDX"]
        x_0, y_0 = projection(self.data["XLONCEN"], self.data["XLATCEN"])
        lon_0, lat_max = projection(x_0, y_0 + half_height, inverse=True)
        lon_min, lat_ul = projection(
            x_0 - half_width, y_0 + half_height, inverse=True
        )
        lon_max, lat_ur = projection(
            x_0 + half_width, y_0 + half_height, inverse=True
        )
        lon_ll, lat_min = projection(
            x_0 - half_width, y_0 - half_height, inverse=True
        )
        return lon_min, lon_max, lat_min, lat_max

    @staticmethod
    def replace_select_chr(string_raw, dict_replace):
        for k, v in dict_replace.items():
            string_raw = string_raw.replace(k, v)
        return string_raw
