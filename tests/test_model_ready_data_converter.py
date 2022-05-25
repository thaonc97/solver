import sys
sys.path.append('../acm_solver/')
sys.path.append('../acm_solver/orm/')
sys.path.append('../acm_solver/solver/')
import config as cfg
import datetime
import pandas as pd
import numpy as np
from solver_helpers import PreprocessedData
#test library
import pytest
import unittest
from unittest.mock import patch
from unittest.mock import Mock
#Module to test
import model_ready_data_converter

class TestModelReadyData():
    def test_model_ready_data(self):
    # Arrange
        input_campaigns = [{'original_id': "0",
                            'solve_id': 0,
                            'dates': np.array([0, 0]),
                            'total': 35,
                            'type': 0,
                            'place_ids': [1],
                            'weights': {'0': 10},
                            'solve_place_ids': [2],
                            'priority': 'CLASS_B'},
                            {'original_id': '1',
                            'solve_id': 1,
                            'dates': np.array([0, 0]),
                            'total': 60,
                            'type': 0,
                            'place_ids': [0, 1],
                            'weights': {'0': 10},
                            'solve_place_ids': [0, 2],
                            'priority': 'CLASS_B'}]

        input_places = [{'original_id': '0',
                        'views': np.array([40]),
                        'ctrs': [1, 0, 0, 0, 0],
                        'solve_id': 0,
                        'share_rate': 0.5},
                        {'original_id': '0',
                        'views': np.array([0]),
                        'ctrs': [1, 0, 0, 0, 0],
                        'solve_id': 1,
                        'share_rate': 0.5},
                        {'original_id': '1',
                        'views': np.array([20]),
                        'ctrs': [1, 0, 0, 0, 0],
                        'solve_id': 2,
                        'share_rate': 0.5},
                        {'original_id': '1',
                        'views': np.array([0]),
                        'ctrs': [1, 0, 0, 0, 0],
                        'solve_id': 3,
                        'share_rate': 0.5}]
    
        input_t_0 = 1
        # input_share_rate = 0.5
        input_data = PreprocessedData()
        input_data.campaigns = pd.DataFrame(input_campaigns)
        input_data.places= pd.DataFrame(input_places)
        input_data.t_0 = input_t_0
        # input_data.share_rate = input_share_rate
        # Act 
        actual  = model_ready_data_converter.convert_from_processed_data(input_data)

        # Assert 
        assert actual['U'] == 1
        assert actual['T'] == 2
        assert actual['K'] == 4
        np.testing.assert_almost_equal(actual['D'], [np.array([0, 0]), np.array([0, 0])])
        assert actual['d'] == [35,60]
        np.testing.assert_almost_equal(actual['r'], np.array([[40,  0, 20,  0]]))
        np.testing.assert_almost_equal(actual['CTR'], np.array([[1., 1., 1., 1.], [1., 1., 1., 1.]]))
        np.testing.assert_almost_equal(actual['w'], np.array([[10],[10]]))
        np.testing.assert_equal(actual['L'], [np.array([2]), np.array([0, 2])])
        np.testing.assert_equal(actual['B'], [[1], [], [0, 1], []])
        assert actual['t_0'] == 1
        assert actual['share_rate'] == [0.5, 0.5, 0.5, 0.5]