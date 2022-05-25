import itertools
import datetime
from dateutil import parser
from google.protobuf.timestamp_pb2 import Timestamp
import numpy as np
import pandas as pd
import pytz

import settings
from orm import odm

# CONVERT PROTOBUF PROFILE TO DATABASE PROFILE
def convert_p_profile_to_db_profile(protobuf_profile):
    profiles_type = []
    for _dict in protobuf_profile:
        profiles_type.append(next(iter(_dict.values())))
    return profiles_type

# CONVERT PROTOBUF CAMPAIGN WEIGHT TO DATABASE CAMPAIGN WEIGHT
def convert_p_weight_to_db_weight(protobuf_weight):
    weights = {}
    for proto_weight in protobuf_weight:
        
        date = proto_weight['date']
        date_to_insert = datetime.datetime.fromtimestamp(date)
        weight_num = proto_weight['weightNum']
        weights[date_to_insert] = weight_num

    return weights

def db_profiles_to_model_ready_profiles(db_profiles):
    """
    Convert database profiles format to model-ready profiles format.

    Paramters:
    ---------
        db_profiles: list of all database campaign profiles
    
    Returns:
        model_ready_profiles_list: list of all model-ready profiles, model_ready_profiles_list[0] is all model-ready profiles of campaign 0
    """
    profile_types = settings.profile_types
    profile_all_values = settings.profile_all_values
    num_profile_types = settings.num_profile_types

    model_ready_profiles_list = []
    for profile_each_campaign in db_profiles:
        result = []
        #________NEW_________
        if  not profile_each_campaign: #if current cammpaign profile is empty(current profile accept all campaigns)
            temp_result =[]
            for profile_type in profile_types:
                if not temp_result:#temp_result is empty:
                    temp_result +=[[value] for value in profile_all_values[profile_type]]
                else:
                    temp_result_prime = temp_result.copy()
                    for temp_result_value in temp_result:
                        for value in profile_all_values[profile_type]:
                            temp_result_prime.append(temp_result_value+ [value])
                    temp_result = temp_result_prime.copy()
            result = temp_result.copy()
        #_______END NEW______
        else:
            for i in profile_each_campaign:
                temp_result =[]          
                for profile_type in profile_types: #profile type are 'gender','age','income',...
                    #Get the dictionary which has type = current profile type:
                    current_ptype_dict = next((item for item in i if item["type"] == profile_type), None)
                    temp_result_prime = temp_result.copy() 
                    if current_ptype_dict is None: # if that dicionary doesn't exist
                        if not temp_result: # check if current temp result list is empty
                            for value in profile_all_values[profile_type]:
                                temp_result_prime.append([value])
                        else:
                            for to_add_value in profile_all_values[profile_type]:
                                for current_value in temp_result:
                                    current_value_prime = current_value.copy()
                                    current_value_prime.append(to_add_value)
                                    temp_result_prime.append(current_value_prime)
                    else:
                        if not temp_result:# check if current temp result list is empty
                            for value in current_ptype_dict['value']:
                                temp_result_prime.append([value])
                        else:
                            for to_add_value in current_ptype_dict['value']:
                                for current_value in temp_result:
                                    current_value_prime = current_value.copy()
                                    current_value_prime.append(to_add_value)
                                    temp_result_prime.append(current_value_prime)
                    temp_result = temp_result_prime.copy()
                result = result + temp_result

        result_removed_short = result.copy()
        for item in result: # remove unremoved shorter profiles
            if len(item) < num_profile_types:
                result_removed_short.remove(item)
        
        result_removed_short.sort()
        model_ready_profiles_list.append(result_removed_short)
    return model_ready_profiles_list

def list_remove_duplicates(_list):
    _list.sort()
    removed_duplicates_list = list(_list for _list,_ in itertools.groupby(_list))
    return removed_duplicates_list

def protobuf_timestamps_to_dates(protobuf_timestamps):
    """
    Convert protobuf timestamps (string in rfc 3339 format) to interger for easy modelling
    
    Parameters:
    ----------
        protobuf_timestamps:list of protobuf timestamp (rfc 3339 format), e.g. '2020-09-20T00:00:20.000000000Z' (str).
        
    Returns:
    --------
        Time in python datetime.date.
    """
    date_list = []
    
    for protobuf_timestamp in protobuf_timestamps:
        _timestamp = Timestamp()
        _timestamp.FromJsonString(value = protobuf_timestamp)
        _date = _timestamp.ToDatetime().date()
        date_list.append(_date)
        
    return date_list

def get_runing_days(start_date_list,expired_date_list):
    """
    Get total number of campaign running days.
    
    Parameters:
    ----------
        start_date_list: list of start dates (list<datetime>).
        exppired_date_list  list of expired dates (list<datetime>).
        
    Returns:
    --------
        total of running day (int).
    """
    min_d = min(start_date_list)
    max_d = max(expired_date_list)
    num_days = (max_d-min_d).days +1
    return num_days 

def map_datetime_to_int(total_days,start_date):
    """
    map datetime to int.
    
    Parameters:
    ----------
        total_days: total of running day (int).
        start_date:  the youngest date among start dates of problems (datetime).
        
    Returns:
    --------
        a dictionary maps datetimes to intergers (dict<datetime,int>).
    """
    datetime_to_int_map = {}
    
    for _days in range(total_days):
        datetime_to_int_map[start_date + datetime.timedelta(days =_days)] = _days

    return datetime_to_int_map

def map_int_to_p_timestamps(start_timestamps,expired_timestamps):
    """
    map int to protobuf timestamp.
    
    Parameters:
    ----------
        start_timestamps: a list of protobuf timestamp (rfc 3339 format), e.g. '2020-09-20T00:00:20.000000010Z' (str).
        expired_timestamps: a list of protobuf timestamp (rfc 3339 format), e.g. '2020-09-20T00:00:20.000000010Z' (str).
        
    Returns:
    --------
        a dictionary maps model-ready-interger to protobuf timestamp json string (dict<int,string>).
    """
    start_dates_list = protobuf_timestamps_to_dates(start_timestamps)
    expired_dates_list = protobuf_timestamps_to_dates(expired_timestamps)
    youngest_date = min(start_dates_list)
    # oldest_date = max(expired_dates_list)
    total_days = get_runing_days(start_dates_list,expired_dates_list)
    
    int_to_protobuf_timestamps_dict= {}
    
    for int_date in range(total_days):
        cur_date = youngest_date + datetime.timedelta(days =int_date)
        cur_date_time = datetime.datetime(cur_date.year,cur_date.month,cur_date.day)
        cur_timestamp = Timestamp()
        cur_timestamp.FromDatetime(cur_date_time)
        int_to_protobuf_timestamps_dict[int_date] = cur_timestamp.ToJsonString()
        
    return int_to_protobuf_timestamps_dict

def sum_estimate_views_places_each_campaign(raw_campaigns, raw_places):
    """
    Get total estimate views of all places in all days of each campaign.
    
    Parameters:
    -----------
    raw_campaigns: list

    raw_places: list
    Returns:
    --------
    result: dictionary
        A dict in the form of {campaign a: total estimate views of all places in all days of campaign a,...}
    """
    
    result = {}
    for campaign in raw_campaigns:
        place_views_list = np.sum([np.sum(pd.DataFrame(place['views'])['value']) for place in raw_places if place['placeId'] in campaign['placeIds']])
        result[campaign['campaignId']] = place_views_list

    return result

def get_all_possible_list_profile(profile_all_values_dict = settings.profile_all_values.values()):
    """
    Return all posible profiles in list representation.
    
    Parameters:
    -----------
    profile_all_value_dict: dict
        Something like this: profile_all_values = {'gender':[0,1],'age':[0,1,2,3,4,5,6]}, the order of the keys in the dictionary must follow 
        the order of profile_types.
    
    Returns:
    --------
    all_possible_profile : list
        List of all profiles in list representation.


    >>>_all_possible_list_profile({'gender':[0,1],'age':[0,1,2,3,4,5,6]})
    [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [0, 6], [1, 0], [1, 1], [1, 2], [1, 3], [1, 4], [1, 5], [1, 6]]
    """
    profile_all_values = [values for values in profile_all_values_dict]
    all_possible_profile = []
    for profile in itertools.product(*[value for value in profile_all_values]):
        all_possible_profile.append(list(profile))
    
    return all_possible_profile

def map_profile_list_int(all_list_profiles):
    """
    Return all posible profiles in int representation.
    
    Parameters:
    -----------
    all_list_profiles: list
        List of all possible profiles in list representation.
        E.g. [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [0, 6], [1, 0], [1, 1], [1, 2], [1, 3], [1, 4], [1, 5], [1, 6]]
    
    Returns:
    --------
    map_dict : list
        Dictionary to map representation of list-profile to respected representation of int profile


    >>>_map_profile_list_int([[0, 0], [0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [0, 6], [1, 0], [1, 1], [1, 2], [1, 3], [1, 4], [1, 5], [1, 6]])
    {(0, 0): 0, (0, 1): 1, (0, 2): 2, (0, 3): 3, (0, 4): 4, (0, 5): 5, (0, 6): 6, (1, 0): 7, (1, 1): 8, (1, 2): 9, (1, 3): 10, (1, 4): 11, (1, 5): 12, (1, 6): 13}
    """

    k = 0
    map_dict ={}
    for i in all_list_profiles:
        map_dict[tuple(i)] = k
        k +=1
    return map_dict

def remove_network_campaigns(raw_campaigns):
    """
    Remove network campaigns from raw campaigns. Used in case the problem is STANDALONE.
    """
    raw_campaigns_copy = raw_campaigns.copy()
    for campaign in raw_campaigns:
        if campaign['isNetwork'] == True:
            raw_campaigns_copy.remove(campaign)
    
    return raw_campaigns_copy

def set_share_rate_zero(raw_places):
    """
    Set share rate of all places to zero.
    """
    for place in raw_places:
        place['shareRate'] = 0
    
    return raw_places

def delete_from_db(collection_name,problem_id):
    """
    Xóa dữ liệu từ collection "collection_name" có problemId = "problem_id".
    """
    if collection_name == 'asProblemInfo':
        odm.ASProblemInfo.objects(id= problem_id).delete()
    elif collection_name == 'asSolveResult':
        odm.ASResult.objects(problemId = problem_id).delete()
    elif collection_name == 'asCampaign':
        odm.ASCampaign.objects(problemId = problem_id).delete()
    elif collection_name == 'asPlace':
        odm.ASPlace.objects(problemId = problem_id).delete()
    elif collection_name == 'asUnplanned':
        odm.ASUnplanned.objects(problemId = problem_id).delete()

def utc_to_local(utc_dt):  # Chuyển utc về local time
    """
    Chuyển utc time về local time.

    Parameters
    ----------
    utc_dt: datetime.datetime
        Thời gian này phải là timezone aware.

    Returns
    -------
    utc_dt_local : datetime.datetime
        Thời gian đã được chuyển về loca time
    """
    if type(utc_dt) == str:
        pd_timestamp = pd.Timestamp(utc_dt)
        utc_dt = pd.Timestamp.to_pydatetime(pd_timestamp)

    utc_dt_local = utc_dt.replace(tzinfo = datetime.timezone.utc).astimezone(tz = None)
    return utc_dt_local

def get_local_tz_aware_now():
    """
    Trả về ngày hôm nay đã được bỏ phần time của local time với timezone aware.
    """
    now_tz_aware = utc_to_local(datetime.datetime.utcnow().replace(tzinfo=pytz.utc))
    now_removed_time_tz_aware = datetime.datetime(now_tz_aware.year,now_tz_aware.month,now_tz_aware.day,tzinfo = now_tz_aware.tzinfo)  # Bỏ phần thời gian đi, giữ lại date
    return now_removed_time_tz_aware
    

class CorrectRawData():
    """
    Sửa lại dữ liệu raw cho đúng, bao gồm :
        Chuyển dữ liệu thời gian về local time,
        Loại bỏ những campaign ko chạy ở đâu,
        Loại bỏ những campaign class B có lượng chạy = 0,
        Nếu ngày bắt đầu của campaign < ngày hôm nay, chuyển ngày bắt đầu về ngày hôm nay,
        Loại bỏ những campaign có start date > end date.
    """

    @staticmethod
    def _to_local_time(raw_data):
        """
        Chuyển đổi những nơi có  thời gian trong raw_data về local time và có timezone aware.

        Parameters:
        -----------
        raw_data: solve_helpers.RawData

        Returns:
        raw_data: solve_helpers.RawData
        """
        raw_campaigns = raw_data.campaigns
        raw_places = raw_data.places
        for campaign in raw_campaigns:
            start_date = campaign['startDate']
            expired_date = campaign['expiredDate']
            campaign['startDate'] = utc_to_local(start_date)
            campaign['expiredDate'] = utc_to_local(expired_date)
            for weight in campaign['weights']:
                weight['date'] = utc_to_local(weight['date'])

        for place in raw_places:
            for view in place['views']:
                view['date'] = utc_to_local(view['date'])

        return raw_data

    @staticmethod
    def _delete_class_b_total_zero(raw_campaigns):
        """
        Loại bỏ trường hợp các campaign class B có lượng yêu cầu = 0 ở raw data.
        
        Parameters:
        -----------
        raw_campaigns: solver_helpers.RawData.campaigns

        Returns:
        --------
        raw_campaigns_deleted_zero: solver_helpers.RawData.campaigns
            dữ liệu đã loại bỏ
        """
        raw_campaigns_deleted_zero = [campaign for campaign in raw_campaigns if not (campaign['total'] <= 0 and campaign['priority'] == 'CLASS_B')]

        return raw_campaigns_deleted_zero

    @staticmethod
    def _remove_campaigns_have_no_place(raw_campaigns):
        modified_raw_campaigns = raw_campaigns.copy()
        for campaign in raw_campaigns:
            if len(campaign['placeIds']) == 0:
                modified_raw_campaigns.remove(campaign)
                print("Campaign ",campaign['campaignId']," has no place, removed.")
        
        return modified_raw_campaigns

    @staticmethod
    def _adjust_past_start_dates(raw_campaigns):
        """
        Đưa start date của campaigns về ngày hôm nay nếu start_date < ngày hôm nay của toàn bộ campaign.

        Parameters:
        -----------
        raw_campaigns: solver_helpers.RawData.campaigns

        Returns:
        --------
        raw_campaigns: solver_helpers.RawData.campaigns
        """
        for campaign in raw_campaigns:
            now_ignore_time = get_local_tz_aware_now()
            if campaign['startDate'] < now_ignore_time:
                campaign['startDate'] = now_ignore_time
        
        return raw_campaigns

    @staticmethod
    def _remove_invalid_date_campaigns(raw_campaigns):
        """
        Loại bỏ các campaign có start_date > end_date.

        Parameters:
        -----------
        raw_campaigns: solver_helpers.RawData.campaigns

        Returns:
        --------
        raw_campaigns_new: solver_helpers.RawData.campaigns
        """
        raw_campaigns_new = [campaign for campaign in raw_campaigns if campaign['startDate'] <= campaign['expiredDate']]
        return raw_campaigns_new

    @staticmethod
    def correct(raw_data, adjust_start_dates = True):
        """
        Sửa lại dữ liệu raw cho đúng, bao gồm :
        Chuyển dữ liệu thời gian về local time,
        Loại bỏ những campaign ko chạy ở đâu,
        Loại bỏ những campaign class B có lượng chạy = 0,
        Nếu ngày bắt đầu của campaign < ngày hôm nay, chuyển ngày bắt đầu về ngày hôm nay,
        Loại bỏ những campaign có start date > end date.
        """
        raw_data = CorrectRawData._to_local_time(raw_data)
        raw_data.campaigns = CorrectRawData._remove_campaigns_have_no_place(raw_data.campaigns)
        raw_data.campaigns = CorrectRawData._delete_class_b_total_zero(raw_data.campaigns)
        if adjust_start_dates == True:
            raw_data.campaigns = CorrectRawData._adjust_past_start_dates(raw_data.campaigns)
        
        raw_data.campaigns = CorrectRawData._remove_invalid_date_campaigns(raw_data.campaigns)
        return raw_data

def no_type_b_or_c(raw_campaigns):
    """
    Return True nếu raw campaigns ko có campaign cấp B hay C.
    """
    flag = True
    for campaign in raw_campaigns:
        if (campaign['priority'] == 'CLASS_B' and len(campaign['placeIds']) != 0)  or (campaign['priority'] == 'CLASS_C' and len(campaign['placeIds']) != 0):
            flag = False
            break

    return flag
        # sys.exit()

def create_temp_campaign(problem_id,raw_data):
    """
    Tạo 1 campaign class B với id = '-10' giả với total xấp xỉ 0.
    """
    temp_campaign = {}
    temp_campaign['problemId'] = problem_id
    temp_campaign['campaignId'] = '-10'
    temp_campaign['isNetwork'] = True
    temp_campaign['startDate'] = raw_data.campaigns[0]['startDate']  # Lấy Start Date của campaign đầu tiên
    temp_campaign['expiredDate'] = raw_data.campaigns[0]['startDate']  # Lấy Start Date của campaign đầu tiên
    temp_campaign['priority'] = 'CLASS_B'
    temp_campaign['type'] = 'DEFAULT'
    temp_campaign['total'] =10**-6
    temp_campaign['placeIds'] = [raw_data.places[0]['placeId']]  # Lấy place id đầu tiên
    temp_campaign['weights'] = []
    temp_campaign['profiles'] = []
    
    return temp_campaign

def str_to_datetime(str_datetime):
    py_datetime = parser.parse(str_datetime)
    return py_datetime

def remove_time(py_datetime):
    removed_time = py_datetime.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
    return removed_time

def remove_time_str_datetime(str_datetime: str):
    """Chuyển datetime từ dạng string (như lúc insert dữ liệu vào db từ grpc) dạng `2030-07-09T00:00:00.000Z`
    sang datetime local và loại bỏ phần thời gian (giờ, phút, giây) đi, vẫn giữ lại thông tin 
    về timezone.

    Parameters
    ----------
    str_datetime : str
        dạng str, sau khi convert từ timestamp grpc bằng MessageToDict

    Returns
    -------
    removed_time
        datetime.datetime
    """
    py_datetime = str_to_datetime(str_datetime)
    py_datetime_localed_with_tz = utc_to_local(py_datetime)
    removed_time = remove_time(py_datetime_localed_with_tz)
    return removed_time