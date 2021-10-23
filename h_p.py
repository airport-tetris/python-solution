import datetime
import json
import math
import pandas as pd
import numpy as np

from functions import *

path_air_classes = 'Aircraft_Classes_Private.csv'
path_air_stands = 'Aircraft_Stands_Private.csv'
path_handing_rates = 'Handling_Rates_Private.csv'
path_handing_time = 'Handling_Time_Private.csv'
path_timetable = 'Timetable_private.csv'

data_air_classes = pd.read_csv(path_air_classes)
data_air_stands = pd.read_csv(path_air_stands)
data_handing_rates = pd.read_csv(path_handing_rates, index_col='Name')
data_handing_time = pd.read_csv(path_handing_time)
data_timetable = pd.read_csv(path_timetable, index_col=0)

data_air_stands['Terminal'] = data_air_stands['Terminal'].fillna(10)
data_timetable['empty_spaces'] = pd.Series(data_timetable.flight_AC_PAX_capacity_total - data_timetable.flight_PAX)
data_timetable['air_classes'] = pd.Series(({a<121:'Regional', 120<a<221: 'Narrow_Body'}.get(True, 'Wide_Body') for a in data_timetable.flight_AC_PAX_capacity_total.values))
data_timetable['count_date'] = data_timetable.groupby('flight_datetime')['flight_datetime'].transform('count')
data_timetable.flight_datetime = pd.to_datetime(data_timetable.flight_datetime)
dict_terminal_Aircraft_Stand = {i:data_air_stands.Aircraft_Stand[data_air_stands.Terminal == i].values for i in range(1, 6)}
data_air_stands['sosedi'] = find_sosedi(data_air_stands, dict_terminal_Aircraft_Stand)

table_cost_values = table_cost(data_timetable, data_air_stands, data_handing_rates, data_handing_time)
global_min_value = find_global_min(table_cost_values)
print(f'global min -> {global_min_value}')
data_mc = {i[0]:{'type_mc': i[8], 'JetBridge_on_Arrival': i[1], 'JetBridge_on_Departure': i[2], 'time_used':[], 'index':0, 'C_vc':0, 'sosedi':i[-1]} for i in data_air_stands.values}
wide = []
mc_air = []
data_sort = data_timetable.copy()
data_ready = pd.DataFrame(result(data_sort, table_cost_values, data_air_stands, data_mc, data_handing_time))
data_ready[data_timetable.columns].to_csv(f'result.csv')
print(f'cost -> {data_ready.C_vc.sum()}')
