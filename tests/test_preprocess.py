import sys
sys.path.append('../acm_solver/')
sys.path.append('../acm_solver/orm/')
sys.path.append('../acm_solver/solver/')
sys.path.append('../acm_solver/generated')
import config as cfg
import datetime
import pandas as pd
import numpy as np

# test library
import pytest
import unittest
from unittest.mock import patch
from unittest.mock import Mock

# Local modules
from solver_helpers import PreprocessedData,RawData
# Module to test
import preprocess



class TestPreprocessConverter:

    def test_preprocessconverter(self):
        # Arrange
        date = datetime.datetime.strptime("21 June, 2030", "%d %B, %Y")
        print(date)
        input_db_campaign = [{'problemId': '102',
        'campaignId': '100',
        'isNetwork': True,
        'startDate': date,
        'expiredDate': date,
        'type': 'DEFAULT',
        'total': 35,
        'placeIds': [101],
        'priority': 1,
        'weights': [{'date': date, 'value': 10}],
        'profiles': [[{'type': 'GENDER', 'values': [1]}],
        [{'type': 'GENDER', 'values': [0]}, {'type': 'AGE', 'values': [1, 2]}]]},
        {'problemId': '102',
        'campaignId': '101',
        'isNetwork': False,
        'startDate': date,
        'expiredDate': date,
        'type': 'DEFAULT',
        'total': 60,
        'placeIds': [100,101],
        'priority': 1,
        'weights': [{'date': date, 'value': 10}],
        'profiles': []}]

        input_db_places = [{'problemId': '102',
        'placeId': 100,
        "ctrs": [
        {
        "type": "DEFAULT",
        "value": 1
        },
        {
        "type": "BANNER_STATIC",
        "value": 0
        },
        {
        "type": "BANNER_EFFECT",
        "value": 0
        },
        {
        "type": "BANNER_SLIDE",
        "value": 0
        },
        {
            "value": 0,
            "type": "CPA"
        },
        {
            "value":0,
            "type": "SURVEY"
        },
        {
            "value": 0,
            "type": "VIDEO"
        },
        {
            "value": 0,
            "type": "GAME"
        },
        {
            "value": 0,
            "type": "TEXT_MATCHING"
        },
        {
            "value":0,
            "type": "OTHER"
        }
        ],
        'shareType': "SOFT",
        'views': [{'date': date, 'value': 40}],
        'profilesRatio': [{'type': 'GENDER', 'ratio': [1, 0, 0]},
        {'type': 'AGE', 'ratio': [1, 0, 0, 0, 0, 0, 0, 0]}],
        'share_rate': 0.5},
        {'problemId': '102',
        'placeId': 101,
        "ctrs": [
        {
        "type": "DEFAULT",
        "value": 1
        },
        {
        "type": "BANNER_STATIC",
        "value": 0
        },
        {
        "type": "BANNER_EFFECT",
        "value": 0
        },
        {
        "type": "BANNER_SLIDE",
        "value": 0
        },
        {
            "value": 0,
            "type": "CPA"
        },
        {
            "value":0,
            "type": "SURVEY"
        },
        {
            "value": 0,
            "type": "VIDEO"
        },
        {
            "value": 0,
            "type": "GAME"
        },
        {
            "value": 0,
            "type": "TEXT_MATCHING"
        },
        {
            "value":0,
            "type": "OTHER"
        }
        ],
        'shareType': "SOFT",
        'views': [{'date': date, 'value': 20}],
        'profilesRatio': [{'type': 'GENDER', 'ratio': [1, 0, 0]},
        {'type': 'AGE', 'ratio': [1, 0, 0, 0, 0, 0, 0, 0]}],
        'share_rate': 0.5}]

        expected_preprocess_campaigns = pd.DataFrame({'problemId': {0: '102', 1: '102'},
        'original_id': {0: '100', 1: '101'},
        'isNetwork': {0: True, 1: False},
        'type': {0: 0, 1: 0},
        'total': {0: 35, 1: 60},
        'place_ids': {0: [101], 1: [100, 101]},
        'priority': {0: 1, 1: 1},
        'weights': {0: {'0': 10}, 1: {'0': 10}},
        'solve_id': {0: 0, 1: 1},
        'dates': {0: np.array([0, 0]), 1: np.array([0, 0])},
        'solve_place_ids': {0: [2], 1: [0, 1,2,3]}})

        expected_preprocess_places = pd.DataFrame({'original_id': {0: 100, 1: 100, 2: 101, 3: 101},
        'ctrs': {0: [1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        1: [1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        2: [1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        3: [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
        'views': {0: np.array([0]), 1: np.array([40]), 2: np.array([0]), 3: np.array([20])},
        'share_rate': {0: 0.5, 1: 0.5, 2: 0.5, 3: 0.5},
        'unpartitioned_solve_id': {0: 0, 1: 0, 2: 1, 3: 1},
        'share_type':{0:0, 1:0, 2:0, 3:0} ,
        'profiles_ratio_int': {0: [1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0],
        1: [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        2: [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        3: [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
        'profiles': {0: frozenset({1, 2, 8, 9, 10, 11, 12, 13, 14, 15}),
        1: frozenset({0, 3, 4, 5, 6, 7, 16, 17, 18, 19, 20, 21, 22, 23}),
        2: frozenset({1, 2, 8, 9, 10, 11, 12, 13, 14, 15}),
        3: frozenset({0, 3, 4, 5, 6, 7, 16, 17, 18, 19, 20, 21, 22, 23})},
        'solve_id': {0: 0, 1: 1, 2: 2, 3: 3}})

        raw_input_data = RawData()
        raw_input_data.campaigns = input_db_campaign
        raw_input_data.places = input_db_places

        # Act
        
        actual_preprocessed_data, actual_mapper = preprocess.PreprocessConverter.convert_from_raw_data(raw_input_data)
        actual_preprocessed_campaigns = actual_preprocessed_data.campaigns
        actual_preprocessed_places = actual_preprocessed_data.places
        actual_preprocessed_campaigns.drop(columns =['profiles'], inplace = True, errors = 'ignore')
        actual_preprocessed_places.drop(columns = ['profiles_ratio'], inplace =  True, errors = 'ignore')

        # Assert
        pd.testing.assert_frame_equal(actual_preprocessed_campaigns,expected_preprocess_campaigns, check_like= True, check_dtype=False)
        pd.testing.assert_frame_equal(actual_preprocessed_places,expected_preprocess_places, check_like = True, check_dtype=False)