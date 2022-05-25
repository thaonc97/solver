import sys
sys.path.append('../acm_solver/solver/')
sys.path.append('../acm_solver/')
sys.path.append('../acm_solver/orm/')
sys.path.append('../acm_solver/solver/solver_utils/')
sys.path.append('../acm_solver/generated')
import pytest
import config as cfg
import numpy as np
import model_solver
import datetime

# Module to test
import utils
#data
# convert_p_profile_to_db_profile_input_1 =[{'profile_types': [{'type': 'GENDER', 'values': [1]},
#    {'type': 'AGE', 'values': [1, 2, 3]}]},
#  {'profile_types': [{'type': 'GENDER', 'values': [0]},
#    {'type': 'AGE', 'values': [1, 2]}]}]
# convert_p_profile_to_db_profile_output_1 = [[{'type': 'GENDER', 'values': [1]}, {'type': 'AGE', 'values': [1, 2, 3]}],
#  [{'type': 'GENDER', 'values': [0]}, {'type': 'AGE', 'values': [1, 2]}]]

# db_profiles_to_model_ready_profiles_input_1 = [[{'type': 'GENDER', 'values': [1]}, {'type': 'AGE', 'values': [1, 2, 3]}],
#  [{'type': 'GENDER', 'values': [0]}, {'type': 'AGE', 'values': [1, 2]}]]
# db_profiles_to_model_ready_profiles_output_1 = [[0,1],[0,2],[1,1],[1,2],[1,3]]
# db_profiles_to_model_ready_profiles_input_2 = [[{'type': 'AGE', 'values': [1, 2, 3]}]]
# db_profiles_to_model_ready_profiles_output_2 = [[0,1],[0,2],[0,3],[1,1],[1,2],[1,3]]
# db_profiles_to_model_ready_profiles_input_3 = [[{'type': 'GENDER', 'values': [1]}],
#  [{'type': 'GENDER', 'values': [0]}, {'type': 'AGE', 'values': [1, 2]}]]
# db_profiles_to_model_ready_profiles_output_3 = [[0,1],[0,2],[1,0],[1,1],[1,2],[1,3],[1,4],[1,5],[1,6]]
# db_profiles_to_model_ready_profiles_input_4 = []
# db_profiles_to_model_ready_profiles_output_4 = [[0,0],[0,1],[0,2],[0,3],[0,4],[0,5],[0,6],[1,0],[1,1],[1,2],[1,3],[1,4],[1,5],[1,6]]

# db_profiles_to_model_ready_profiles_input = [db_profiles_to_model_ready_profiles_input_1,
# db_profiles_to_model_ready_profiles_input_2,
# db_profiles_to_model_ready_profiles_input_3,
# db_profiles_to_model_ready_profiles_input_4]
# db_profiles_to_model_ready_profiles_output = [db_profiles_to_model_ready_profiles_output_1,
# db_profiles_to_model_ready_profiles_output_2,
# db_profiles_to_model_ready_profiles_output_3,
# db_profiles_to_model_ready_profiles_output_4]
# db_profiles_to_model_ready_profiles_data = [(db_profiles_to_model_ready_profiles_input,db_profiles_to_model_ready_profiles_output)]

# def test_convert_p_profile_to_db_profile():
#     actual_output = utils.convert_p_profile_to_db_profile(convert_p_profile_to_db_profile_input_1)
#     assert actual_output == convert_p_profile_to_db_profile_output_1

# @pytest.mark.parametrize('input,expect_output',db_profiles_to_model_ready_profiles_data)
# def test_db_profile_to_model_ready_profile(input,expect_output):
#     actual_output = utils.db_profiles_to_model_ready_profiles(input)
#     assert actual_output == expect_output

def test_sum_estimate_views_places_each_campaign():
    #Arrange 
    input_db_places  = [{'problemId': '102',
                'placeId': 0,
                'ctrs': {'default': 1, 'cpc': 0, 'tvc': 0, 'social': 0, 'app': 0},
                'views': [{'date': '2020-09-10T00:00:00.000Z', 'value': 40}],
                'profilesRatio': [{'type': 'GENDER', 'ratio': [1, 0]},
                {'type': 'AGE', 'ratio': [1, 0, 0, 0, 0, 0, 0]}],
                'shareRate': 0.5},
                {'problemId': '102',
                'placeId': 1,
                'ctrs': {'default': 1, 'cpc': 0, 'tvc': 0, 'social': 0, 'app': 0},
                'views': [{'date': '2020-09-10T00:00:00.000Z', 'value': 20}],
                'profilesRatio': [{'type': 'GENDER', 'ratio': [1, 0]},
                {'type': 'AGE', 'ratio': [1, 0, 0, 0, 0, 0, 0]}],
                'shareRate': 0.5}]

    input_db_campaigns = [{'problemId': '102',
                        'campaignId': '0',
                        'isNetwork': True,
                        'startDate': datetime.datetime(2020, 9, 10, 0, 0),
                        'expiredDate': datetime.datetime(2020, 9, 10, 0, 0),
                        'type': 0,
                        'total': 35,
                        'placeIds': [1],
                        'priority': 1,
                        'weights': [{'date': '2020-09-10T00:00:00.000Z', 'value': 10}],
                        'profiles': [[{'type': 'GENDER', 'values': [0]},
                            {'type': 'AGE', 'values': [0]}]],
                        'model_id': 0},
                        {'problemId': '102',
                        'campaignId': '1',
                        'isNetwork': False,
                        'startDate': datetime.datetime(2020, 9, 10, 0, 0),
                        'expiredDate': datetime.datetime(2020, 9, 10, 0, 0),
                        'type': 0,
                        'total': 60,
                        'placeIds': [0, 1],
                        'priority': 1,
                        'weights': [{'date': '2020-09-10T00:00:00.000Z', 'value': 10}],
                        'profiles': [[{'type': 'GENDER', 'values': [0]},
                            {'type': 'AGE', 'values': [0]}]],
                        'model_id': 1}]
    
    expected = {'0': 20, '1': 60}

    
    # Act
    actual = utils.sum_estimate_views_places_each_campaign(input_db_campaigns, input_db_places)

    # Assert
    assert actual == expected

def test_remove_time_str_datetime_work_correctly():

    #Arrange
    tzinfo = datetime.timezone(datetime.timedelta(seconds= 25200), 'SE Asia Standard Time')
    expected1 = datetime.datetime(2030,7,10,0,0,0).replace(tzinfo=tzinfo)
    expected2 = datetime.datetime(2011,6,10,0,0,0).replace(tzinfo=tzinfo)
    expected = [expected1, expected2]
    input_str_datetime1 = '2030-07-09T19:11:11.000Z'
    input_str_datetime2 = '2011-06-10T11:11:11.000Z'
    input_str_datetimes = [input_str_datetime1, input_str_datetime2]

    #Act
    actual = [utils.remove_time_str_datetime(input_str_datetime) for input_str_datetime in input_str_datetimes]

    assert actual == expected