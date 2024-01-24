import re
import numpy as np
from datetime import datetime

def hours_between_dates(date_ini, date_end):
    hours = int((date_end - date_ini).total_seconds() / 3600.0)
    return hours

def set_lead_times(date_ini, date_end, date_sim_init, date_sim_forecast):
    if date_sim_init < date_ini:
        lead_time_ini = hours_between_dates(date_sim_init, date_ini)
    else:
        lead_time_ini = 0
    if date_end < date_sim_forecast:
        lead_time_end = hours_between_dates(date_sim_init, date_end)
    else:
        lead_time_end = hours_between_dates(date_sim_init, date_sim_forecast)
    lead_times = np.arange(lead_time_ini, lead_time_end + 1)
    return lead_times.copy()

def replace_function(text, replace_with):
    if isinstance(replace_with, int):
        return str(replace_with).zfill(len(text) - 1)
    else:
        return "*"

def lead_time_replace(text, replace_with = '*'):
    pattern = r'(%LL+)'
    new_text = re.sub(pattern, lambda match: replace_function(match.group(0), replace_with), text)
    return new_text
