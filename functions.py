import math
import datetime
import pandas as pd

def table_cost(table_data_timetable, table_data_air_stands, data_handing_rates, data_handing_time):
    table_cost = {i:{} for i in table_data_timetable.index}
    time_dict = {}
    for i in table_cost:
        for j in table_data_air_stands.values:
            l = {j[0]:{}}
            time_dict = {**time_dict, **l}
        table_cost[i] = time_dict
    cost_air = {}
    for i in table_cost:
        for k in table_data_air_stands.values:
            air = table_data_timetable[table_data_timetable.index == i].values[0]
            C_vc, type_mc, handling_time, C_jet_away = cost_all(air, k, data_handing_rates, table_data_air_stands, data_handing_time)
            li = {k[0]:{
                'Cost': int(C_vc),
                'Type_mc': type_mc,
                'Handling_time': int(handling_time),
                'Taxiing_Time': int(k[-2]),
                'C_jet_away': int(C_jet_away)
            }}
            cost_air = {**cost_air, **li}
        table_cost[i] = cost_air
    return table_cost


def cost_all(air, k, data_handing_rates, data_air_stands, data_handing_time):
    C_mc = data_handing_rates.loc['Aircraft_Taxiing_Cost_per_Minute'].Value * data_air_stands.Taxiing_Time[data_air_stands.Aircraft_Stand == k[0]].values[0]
    type_mc = 'jetbridge' if k[8] != 10 else 'away'
    if type_mc == 'jetbridge':
        handling_time = data_handing_time.JetBridge_Handling_Time[data_handing_time.Aircraft_Class == air[-2]].values[0]
        C_jet_away = data_handing_rates.loc['JetBridge_Aircraft_Stand_Cost_per_Minute'].Value * handling_time
    else: 
        handling_time = data_handing_time.Away_Handling_Time[data_handing_time.Aircraft_Class == air[-2]].values[0]
        C_away = data_handing_rates.loc['Away_Aircraft_Stand_Cost_per_Minute'].Value * handling_time
        count_bus_path = math.ceil(air[9] / 80)
        C_bus = data_handing_rates.loc['Bus_Cost_per_Minute'].Value * count_bus_path * data_air_stands[data_air_stands.Aircraft_Stand == k[0]][str(air[5])].values[0]
        C_jet_away = C_away + C_bus
    C_vc = C_jet_away + C_mc
    return C_vc, type_mc, handling_time, C_jet_away


def find_global_min(table_cost_all):
    global_min = 0
    for i in table_cost_all:
        global_min += min_cost(table_cost_all[i])[1]
    return global_min


def check_wide_time(start_time_value, finish_time_value, mc, air, data_mc):
    if not data_mc[mc]['time_used']:
        data_mc[mc]['time_used'].append({'type_vc': air['air_classes'], 'start':start_time_value, 'finish':finish_time_value})
        data_mc[mc]['time_used'].sort(key=lambda d: d['start']) 
        return True
    
    for i, j in enumerate(data_mc[mc]['time_used']):
        first_flag = start_time_value > j['finish']
        second_flag = finish_time_value < j['start']
        if i + 1 == len(data_mc[mc]['time_used']):
            if (first_flag is True) & (second_flag is False):
                data_mc[mc]['time_used'].append({'type_vc': air['air_classes'], 'start':start_time_value, 'finish':finish_time_value})
                data_mc[mc]['time_used'].sort(key=lambda d: d['start'])
                return True
            elif (first_flag is False) & (second_flag is True):
                data_mc[mc]['time_used'].append({'type_vc': air['air_classes'], 'start':start_time_value, 'finish':finish_time_value})
                data_mc[mc]['time_used'].sort(key=lambda d: d['start'])
                return True
            elif (first_flag is False) & (second_flag is False):
                return False
        elif (first_flag is False) & (second_flag is False):
            return False
        elif (first_flag is False) & (second_flag is True):
            data_mc[mc]['time_used'].append({'type_vc': air['air_classes'], 'start':start_time_value, 'finish':finish_time_value})
            data_mc[mc]['time_used'].sort(key=lambda d: d['start'])
            return True
        elif (first_flag is True) & (second_flag is False):
            continue


def check_sosed_time(start_time_value, finish_time_value, mc, air, data_mc):
    if air['air_classes'] != 'Wide_Body':
        return True
    sosedi = data_mc[mc]['sosedi']
    for i in sosedi:
        time_used = data_mc[i]['time_used'] 
        for j in time_used:
            if j['type_vc'] == 'Wide_Body':
                first_flag = start_time_value > j['finish']
                second_flag = finish_time_value < j['start']
                if (first_flag is True) & (second_flag is False):
                    continue
                elif (first_flag is False) & (second_flag is False):
                    return False
                elif (first_flag is False) & (second_flag is True):
                    continue
    return True


def min_cost(table_cost_pop_v):
    min_cost_value = math.inf
    mc = math.inf
    for i in table_cost_pop_v:
        cost = table_cost_pop_v[i]['Cost']
        if cost < min_cost_value:
            min_cost_value = cost
            mc = i
    return mc, min_cost_value

def choice_mc(air, ind, data_handing_time, table_cost_values, data_air_stands, data_mc):
    flag_wide = False
    flag_continue_wide = False
    handiing_time_jet = data_handing_time.JetBridge_Handling_Time[data_handing_time.Aircraft_Class == air['air_classes']].values[0]
    handiing_time_away = data_handing_time.Away_Handling_Time[data_handing_time.Aircraft_Class == air['air_classes']].values[0]
  
    if air['air_classes'] == 'Wide_Body':
        flag_wide = True
  
    table_cost_pop = table_cost_values[ind].copy()
    print(ind, ' ', len(table_cost_pop))
    opt_mc, opt_min_cost_value = min_cost(table_cost_pop)
    air['opt_mc'] = opt_mc
    air['opt_min_cost_value'] = opt_min_cost_value

    while pd.isnull(air['Aircraft_Stand']):
        count = count + 1
        flag_check_sosed = False           
        flag_check_time = False
        flag_wrong_id = False
        flag_wrong_term  = False
            
        mc, min_cost_value = min_cost(table_cost_pop)
        mc_taxiing = data_air_stands.Taxiing_Time[data_air_stands.Aircraft_Stand == mc].values[0]
        
        isDepart = air['flight_AD'] == 'D'
        isAway = data_mc[mc]['type_mc'] == 10
        handling_time = handiing_time_away if isAway else handiing_time_jet
        
        if isDepart:
            flight_datetime_start = air['flight_datetime'] - datetime.timedelta(minutes=int(handling_time)) - datetime.timedelta(minutes=int(mc_taxiing))
        else:
            flight_datetime_start = air['flight_datetime'] + datetime.timedelta(minutes=int(mc_taxiing))
        flight_datetime_finish =  flight_datetime_start + datetime.timedelta(minutes=int(handling_time))
        
        keyID = 'JetBridge_on_Departure' if isDepart else 'JetBridge_on_Arrival'
        if (isAway or (air['flight_terminal_#'] == data_mc[mc]['type_mc'])):
            if (isAway or (air['flight_ID'] == data_mc[mc][keyID])):
                if check_wide_time(flight_datetime_start, flight_datetime_finish, mc, air, data_mc):
                    if check_sosed_time(flight_datetime_start, flight_datetime_finish, mc, air, data_mc):
                        air['Aircraft_Stand'] = mc
                        air['type_mc'] = 'away' if isAway else 'jetbridge' 
                        air['flight_datetime_start'] = flight_datetime_start
                        air['flight_datetime_finish'] = flight_datetime_finish
                        air['C_vc'] = min_cost_value
                        data_mc[mc]['C_vc'] = min_cost_value
                        data_mc[mc]['index'] = ind
                        print('air',ind ,' skipped ',count)
                        return air
                    else:
                        flag_check_sosed = True
                else:
                    flag_check_time = True
            else:
                flag_wrong_id = True
        else: 
            flag_wrong_term  = True
#         if ind == 590:
#             print(flag_wrong_term,flag_wrong_id, flag_check_time, flag_check_sosed)
#             print(data_mc[mc], min_cost_value)
#             print(len(table_cost_pop))
            
        table_cost_pop.pop(mc)
def result(data, table_cost_values, data_air_stands, data_mc, data_handing_time):
    data_mc = {i[0]:{'type_mc': i[8], 'JetBridge_on_Arrival': i[1], 'JetBridge_on_Departure': i[2], 'time_used':[], 'index':0, 'C_vc':0, 'sosedi':i[-1]} for i in data_air_stands.values}
    wide = []
    mc_air = []
    for ind in data.index.values:
        air = list(data[data.index == ind].to_dict('index').values())[0]
        air = choice_mc(air, ind, data_handing_time, table_cost_values, data_air_stands, data_mc)
        air['index'] = ind
        mc_air.append(air)
    return mc_air


def find_sosedi(data_air_stands, dict_terminal_Aircraft_Stand):
    sosedi = []
    sosedi_term = []
    for i in range(data_air_stands.shape[0]):
        terminal = data_air_stands.values[i][-2]
        if terminal == 10:
            sosedi.append([])
        else:
            mc_value = data_air_stands.values[i][0]
            mc_value_sosed_one = mc_value + 1
            mc_value_sosed_two = mc_value - 1
            if mc_value_sosed_one in dict_terminal_Aircraft_Stand[terminal]:
                sosedi_term.append(mc_value_sosed_one)
            if mc_value_sosed_two in dict_terminal_Aircraft_Stand[terminal]:
                sosedi_term.append(mc_value_sosed_two) 
            sosedi.append(sosedi_term)
            sosedi_term = []
    return sosedi