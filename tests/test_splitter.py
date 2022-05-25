import sys
sys.path.append('../acm_solver/')
sys.path.append('../acm_solver/orm/')
sys.path.append('../acm_solver/solver/')
import config as cfg
import datetime
import pandas as pd
import numpy as np
from solver_helpers import RawData, SplitterHelpers

#test library
import pytest
import unittest

#module to test
import splitter
@pytest.mark.xfail(reason = "Outdated")
def test_split_by_places_return_correct_places_each_subproblem():
    # Arrange
    input_db_campaign = [{'problemId': '102',
    'campaignId': '100',
    'isNetwork': True,
    'startDate': datetime.datetime(2020, 9, 10, 0, 0),
    'expiredDate': datetime.datetime(2020, 9, 10, 0, 0),
    'type': 'DEFAULT',
    'total': 35,
    'placeIds': [101],
    'priority': 1,
    'weights': [{'date': '2020-09-10T00:00:00.000Z', 'value': 10}],
    'profiles': [[{'type': 'gender', 'value': [1]}],
    [{'type': 'GENDER', 'value': [0]}, {'type': 'AGE', 'value': [1, 2]}]]},
    {'problemId': '102',
    'campaignId': '101',
    'isNetwork': False,
    'startDate': datetime.datetime(2020, 9, 10, 0, 0),
    'expiredDate': datetime.datetime(2020, 9, 10, 0, 0),
    'type': 'DEFAULT',
    'total': 60,
    'placeIds': [100,101],
    'priority': 1,
    'weights': [{'date': '2020-09-10T00:00:00.000Z', 'value': 10}],
    'profiles': []}]

    input_db_places = [{'problemId': '102',
    'placeId': 100,
    'ctrs': {'default': 1, 'cpc': 0, 'tvc': 0, 'social': 0, 'app': 0},
    'views': [{'date': '2020-09-10T00:00:00.000Z', 'value': 40}],
    'profilesRatio': [{'type': 'GENDER', 'ratio': [1, 0]},
    {'type': 'AGE', 'ratio': [1, 0, 0, 0, 0, 0, 0]}],
    'share_rate': 0.5},
    {'problemId': '102',
    'placeId': 101,
    'ctrs': {'default': 1, 'cpc': 0, 'tvc': 0, 'social': 0, 'app': 0},
    'views': [{'date': '2020-09-10T00:00:00.000Z', 'value': 20}],
    'profilesRatio': [{'type': 'GENDER', 'ratio': [1, 0]},
    {'type': 'AGE', 'ratio': [1, 0, 0, 0, 0, 0, 0]}],
    'share_rate': 0.5}]
    input_subproblems_num = 1
    raw_data =RawData()
    raw_data.places= input_db_places
    raw_data.campaigns= input_db_campaign
    # Act
    actual = splitter.Splitter.split_by_places(input_subproblems_num, raw_data)

    #Assert 
    assert actual[0][0]['originalPlaceId'] == 0
    assert actual[0][1]['originalPlaceId'] == 1

@pytest.mark.xfail(reason = "Outdated")
def test_update_campaigns_new_place_id():
    # Arrange
    input_db_campaigns = [{'problemId': '102',
                        'originalCampaignId': '0',
                        'isNetwork': True,
                        'startDate': datetime.datetime(2020, 9, 10, 0, 0),
                        'expiredDate': datetime.datetime(2020, 9, 10, 0, 0),
                        'cType': 0,
                        'total': 35,
                        'placeIds': [1],
                        'priority': 1,
                        'weights': [{'date': '2020-09-10T00:00:00.000Z', 'weightNum': 10}],
                        'profiles': [[{'type': 'gender', 'value': [0]},
                            {'type': 'age', 'value': [0]}]],
                        'model_id': 0},
                        {'problemId': '102',
                        'originalCampaignId': '1',
                        'isNetwork': False,
                        'startDate': datetime.datetime(2020, 9, 10, 0, 0),
                        'expiredDate': datetime.datetime(2020, 9, 10, 0, 0),
                        'cType': 0,
                        'total': 60,
                        'placeIds': [0, 1],
                        'priority': 1,
                        'weights': [{'date': '2020-09-10T00:00:00.000Z', 'weightNum': 10}],
                        'profiles': [[{'type': 'gender', 'value': [0]},
                            {'type': 'age', 'value': [0]}]],
                        'model_id': 1}]

    input_current_subproblem_places  = [{'problemId': '102',
                'originalPlaceId': 0,
                'ctrs': {'default': 1, 'cpc': 0, 'tvc': 0, 'social': 0, 'app': 0},
                'estimateViews': [40],
                'profilesRatio': [{'type': 'gender', 'details': [1, 0]},
                {'type': 'age', 'details': [1, 0, 0, 0, 0, 0, 0]}],
                'model_id': 0},
                {'problemId': '102',
                'originalPlaceId': 1,
                'ctrs': {'default': 1, 'cpc': 0, 'tvc': 0, 'social': 0, 'app': 0},
                'estimateViews': [20],
                'profilesRatio': [{'type': 'gender', 'details': [1, 0]},
                {'type': 'age', 'details': [1, 0, 0, 0, 0, 0, 0]}],
                'model_id': 1}]

    input_sum_estimate_views_places_each_campaign = {0: 20, 1: 60}

    # expected = [{'problemId': '102',
    #             'originalCampaignId': 0,
    #             'isNetwork': True,
    #             'startDate': datetime.datetime(2020, 9, 10, 0, 0),
    #             'expiredDate': datetime.datetime(2020, 9, 10, 0, 0),
    #             'cType': 0,
    #             'total': 35.0,
    #             'placeIds': [1],
    #             'priority': 1,
    #             'weights': [{'date': '2020-09-10T00:00:00.000Z', 'weightNum': 10}],
    #             'profiles': [[{'type': 'gender', 'value': [0]},
    #                 {'type': 'age', 'value': [0]}]],
    #             'model_id': 0},
    #             {'problemId': '102',
    #             'originalCampaignId': 1,
    #             'isNetwork': False,
    #             'startDate': datetime.datetime(2020, 9, 10, 0, 0),
    #             'expiredDate': datetime.datetime(2020, 9, 10, 0, 0),
    #             'cType': 0,
    #             'total': 60.0,
    #             'placeIds': [0, 1],
    #             'priority': 1,
    #             'weights': [{'date': '2020-09-10T00:00:00.000Z', 'weightNum': 10}],
    #             'profiles': [[{'type': 'gender', 'value': [0]},
    #                 {'type': 'age', 'value': [0]}]],
    #             'model_id': 1}]

    # Act 
    actual = SplitterHelpers.update_campaigns_new_place_id(input_db_campaigns, input_current_subproblem_places, input_sum_estimate_views_places_each_campaign)

    # Assert 
    assert actual[0]['placeIds'] == [1]
    assert actual[0]['total'] == 35
    assert actual[1]['placeIds'] == [0, 1]
    assert actual[1]['total'] == 60