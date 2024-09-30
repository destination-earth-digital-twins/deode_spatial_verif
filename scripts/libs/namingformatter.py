import datetime

from LoadWriteData import LoadConfigFileFromYaml
from times import lead_time_replace


class NamingFormatter(object):
    def __init__(
        self, obs, case, exp, config_file="config/config_formatting.yaml"
    ):

        self.config_naming = LoadConfigFileFromYaml(config_file)
        self.config_exp = LoadConfigFileFromYaml(
            f"config/exp/config_{exp}.yaml"
        )
        obs_db, var_verif = obs.split('_')
        exp_model = self.config_exp["model"]["name"]
        exp_model_in_filename = exp_model.replace(' ', '').replace('.', '-')
        self.placeholders = {
            "@obs@": obs,
            "@case@": case,
            "@exp@": exp,
            "@obs_db@": obs_db,
            "@var_verif@": var_verif,
            "@exp_model@": exp_model,
            "@exp_model_filename@": exp_model_in_filename
        }

    def format_string(
        self, template, valid_time=None, init_time=None, lead_time=None
    ):
        
        if template in self.config_naming['Filenames']:
            template_str = self.config_naming['Filenames'][template]
        elif template in self.config_naming['Plots']:
            template_str = self.config_naming['Plots'][template]
        else:
            raise ValueError(
                f"Template string '{template}' not found in the configuration"
            )

        if init_time is not None:
            template_str = template_str.replace("@init_time@", init_time)
        for placeholder, value in self.placeholders.items():
            template_str = template_str.replace(placeholder, value)
        
        if isinstance(lead_time, list):
            template_str = template_str.replace("%LL1", str(lead_time[0]).zfill(2))
            template_str = template_str.replace("%LL2", str(lead_time[-1]).zfill(2))
        elif isinstance(lead_time, int):
            template_str = lead_time_replace(template_str, replace_with = lead_time)

        if valid_time is not None:
            return valid_time.strftime(template_str)
        else:
            return template_str
