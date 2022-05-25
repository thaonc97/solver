"""
Module giúp xử lí các exception.
"""
import numpy as np
import datetime
import grpc
import functools

class SolverException(Exception):
    """
    Các lỗi chung liên quan đến Solver
    """
    pass


class InvalidInputException(Exception):
    pass


class NoCampaign(Exception):
    pass


class NoPlace(Exception):
    pass


class InvalidCampaign(Exception):
    pass


class InvalidPlace(Exception):
    pass


class InvalidPlaceDayClassC(Exception):
    pass


def get_no_campaign_msg(problem_id):
    msg = f"Không có campaign nào với problem :{problem_id}"
    return msg

def get_no_place_msg(problem_id):
    msg = f"Không có place nào với problem {problem_id}"
    return msg

def ctr_nan_msg(problem_id, place_id):
    msg = f"Problem {problem_id} chứa place hoặc domain {place_id} chứa ctr không phải là số."
    return msg

def ctr_out_of_range_msg(problem_id, place_id):
    msg = f"Problem {problem_id} chứa place hoặc domain {place_id} chứa ctr nằm ngoài khoảng [0,1]."
    return msg

def profiles_nan_msg(problem_id,place_id):
    msg = f"Problem {problem_id} chứa place hoặc domain {place_id} chứa profiles không phải là số."
    return msg

def profiles_out_of_range_msg(problem_id, place_id, profile_type):
    msg = f"Problem {problem_id} chứa place hoặc domain {place_id} có tổng tỉ lệ profile loại {profile_type} khác 1."
    return msg

def place_view_negative_msg(problem_id, place_id):
    msg = f"Problem {problem_id} chứa place hoặc domain {place_id} âm."
    return msg

def campaign_negative_total_msg(problem_id, campaign_id):
    msg = f"Problem {problem_id} chứa campaign {campaign_id} có yêu cầu booking âm."
    return msg

def invalid_place_share_type_msg(problem_id, place_id):
    msg = f"Problem {problem_id} chứa place {place_id} có share type không hợp lệ."
    return msg

def validate_input(raw_data, problem_id):
    raw_campaigns = raw_data.campaigns
    raw_places = raw_data.places
    
    check_invalid_share_type(raw_places, problem_id)
    check_no_campaign(raw_campaigns, problem_id)
    check_no_place(raw_places, problem_id)
    check_invalid_campaign(raw_campaigns, problem_id)
    check_invalid_place(raw_places, problem_id)
    check_valid_number_class_c(raw_campaigns, True)
    check_valid_number_class_c(raw_campaigns, False)

def check_no_campaign(raw_campaigns, problem_id):
    if len(raw_campaigns) ==0:
        error_msg = get_no_campaign_msg(problem_id)
        raise NoCampaign(error_msg)

def check_no_place(raw_places, problem_id):
    if len(raw_places) == 0 :
        error_msg = get_no_place_msg(problem_id)
        raise NoPlace(error_msg)
    
def check_invalid_campaign(raw_campaigns, problem_id):
    for campaign in raw_campaigns:
        _check_total_booking(campaign, problem_id)

def check_invalid_place(raw_places, problem_id):
    for place in raw_places:
        _check_ctrs(place, problem_id)
        _check_place_views(place, problem_id)
        _check_profiles_ratio(place, problem_id)

def _check_ctrs(raw_place, problem_id):
    eps = 10**-3
    for ctr_type in raw_place['ctrs']:
        if ctr_type['value'] < (0 - eps) or ctr_type['value'] > (1 + eps):
            place_id = raw_place['placeId']
            error_msg = ctr_out_of_range_msg(problem_id, place_id)
            raise InvalidPlace(error_msg)
        
        elif type(ctr_type['value']) is str:
            place_id = raw_place['placeId']
            error_msg = ctr_nan_msg(problem_id, place_id)
            raise InvalidPlace(error_msg)

def _check_total_booking(raw_campaign, problem_id):
    if raw_campaign['total'] < 0:
        campaign_id = raw_campaign['campaignId']
        error_msg = campaign_negative_total_msg(problem_id, campaign_id)
        raise InvalidCampaign(error_msg)

def _check_place_views(raw_place, problem_id):
    for place_view in raw_place['views']:
        if place_view['value'] < 0:
            place_id = raw_place['placeId']

            error_msg = place_view_negative_msg(problem_id, place_id)
            raise InvalidPlace(error_msg)

def _check_profiles_ratio(raw_place, problem_id):
    epsilon = 10**-3
    for profile_info in raw_place['profilesRatio']:
        total_ratio = np.sum(profile_info['ratio'])
        if np.abs(total_ratio - 1) > epsilon:
            place_id = raw_place['placeId']
            profile_type  = profile_info['type']
            error_msg = profiles_out_of_range_msg(problem_id, place_id, profile_type)
            raise InvalidPlace(error_msg)

def check_invalid_share_type(raw_places, problem_id):
    """Kiểm tra share type của các place của problem hiện tại
    có hợp lệ không, hợp lệ là loại SOFT hoặc NETWORK_HARD

    Parameters
    ----------
    raw_places : solver_helpers.RawData.places

    problem_id : str
        
    """
    for place in raw_places:
        if place['shareType'] != 'SOFT' and place['shareType'] != 'NETWORK_HARD':
            invalid_place_id = place['placeId']
            error_msg = invalid_place_share_type_msg(problem_id, invalid_place_id)
            raise(InvalidPlace(error_msg))

def check_valid_number_class_c(raw_campaigns, is_network):
    """
    Kiểm tra xem có nhiều hơn 1 campaign class C thuộc nhóm network hoặc domain trong 1 ngày địa điểm hay không. Return False nếu không hợp lệ.

    Parameters: 
    -----------
    raw_campaigns: solver_helpers.RawData.campaign

    is_network : bool
        True nếu check các campaign Network
        False nếu check các campaign Domain

    Returns:
    --------
    validness: bool
        False nếu không hợp lệ.

    invalid_place_day: None or tupple of (place_id, day)
        Thông tin về địa điểm, ngày không hợp lệ

    """
    invalid_place_day = None
    validness = True
    raw_type_c_campaigns = [campaign for campaign in raw_campaigns if campaign['priority'] == 'CLASS_C' and campaign['isNetwork'] == is_network]
    num_campaigns_c_each_place_day = {}
    
    for campaign in raw_type_c_campaigns:
        campaign_day_range = campaign['expiredDate'] - campaign['startDate'] +datetime.timedelta(1)
        for day in range(campaign_day_range.days):
            cur_day = campaign['startDate'] + datetime.timedelta(day)
            for place in campaign['placeIds']:
                if (place, cur_day) not in num_campaigns_c_each_place_day:
                    num_campaigns_c_each_place_day[place,cur_day] = 1
                else:
                    num_campaigns_c_each_place_day[place,cur_day] += 1
                    
    for place_day in num_campaigns_c_each_place_day:
        if num_campaigns_c_each_place_day[place_day] > 1:
            validness = False
            invalid_place_day = place_day
            raise InvalidPlaceDayClassC("INVALID, MORE THAN 1 CAMPAIGN TYPE C AT (place_id, day):", invalid_place_day)
            
    return validness, invalid_place_day

def handle_grpc_error_decorator(func):
    @functools.wraps(func)
    def wrapper_handle_error(*args, **kwargs):
        # Do something before
        context = args[2] # args[2] là context
        try:
            value = func(*args, **kwargs)
        except SolverException as e:
            context.set_code(grpc.StatusCode.UNKNOWN)
            context.set_details(grpc_error_message(e))
            raise e
        except InvalidCampaign as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(grpc_error_message(e))
            raise e
        except InvalidInputException as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(grpc_error_message(e))
            raise e
        except InvalidPlace as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(grpc_error_message(e))
            raise e
        except InvalidPlaceDayClassC as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(grpc_error_message(e))
            raise e
        except NoCampaign as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(grpc_error_message(e))
            raise e
        except NoPlace as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(grpc_error_message(e))
            raise e
        except Exception as e:
            context.set_code(grpc.StatusCode.UNKNOWN) 
            context.set_details(grpc_error_message(e))
            raise e

        # Do something after
        return value
    return wrapper_handle_error

def grpc_error_message(exception):
    exception_name = type(exception).__name__
    exception_msg = str(exception)
    grpc_error_msg ={
        'exception':exception_name,
        'detail':exception_msg
    }
    
    return str(grpc_error_msg)

"""
InvalidCampaign: campaign có Booking < 0
InvalidPlace: place có ctr nằm ngoài [0,1], view <0, có tổng profile ratio của thằng nào đấy > 1, sharetype không hợp lệ
InvalidPlaceDayClassC: tại 1 ngày địa điểm có >1 campaign type C chạy ở hoặc Network hoặc Domain
NoCampaign: yêu cầu giải problem không có campaign nào trong db (hoặc tất cả campaign đã bị loại bỏ)
NoPlace: yêu cầu giải problem không có place nào trong db (hoặc tất cả place đã bị loại bỏ)
"""