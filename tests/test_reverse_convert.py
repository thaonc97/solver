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

# Module to test
import reverse_convert

def test_convert_back_to_db_represent():
    # Arrange
    input_df_sol = pd.DataFrame({'campaign_id': {0: 0, 1: 0, 2: 1, 3: 1},
                                        'date': {0: 0, 1: 0, 2: 0, 3: 0},
                                        'solve_place_id': {0: 0, 1: 1, 2: 0, 3: 1},
                                        'value': {0: 0.0, 1: 10.0, 2: 40.0, 3: 10.0}})

    mocked_mapper = Mock()
    mocked_mapper.campaigns_mapper = {0: '100', 1: '101'}
    mocked_mapper.places_mapper = {0: 100, 1: 101}

    date_to_int = {pd.Timestamp('2020-09-10') :0,
                pd.Timestamp('2020-09-11') :1}
    int_to_date = {0: pd.Timestamp('2020-09-10') ,
                1:pd.Timestamp('2020-09-11')}
    mocked_mapper.date_int_mapper = {'date_to_int':date_to_int,'int_to_date':int_to_date}
    # mocked_solve_details = Mock()
    # mocked_solve_details['solution'].return_value = Mock()
    # mocked_solve_details['x_dict'] =Mock()
    # mocked_solve_details[]
    problem_id ="102"
    
    
    expected = pd.DataFrame({'problemId': {0: '102', 1: '102', 2: '102'},
                            'campaignId': {0: '100', 1: '101', 2: '101'},
                            'placeId': {0: 101, 1: 100, 2: 101},
                            'date': {0: pd.Timestamp('2020-09-10 00:00:00'),
                            1: pd.Timestamp('2020-09-10 00:00:00'),
                            2: pd.Timestamp('2020-09-10 00:00:00')},
                            'view': {0: 10.0, 1: 40.0, 2: 10.0}})
    
    # Act
    actual = reverse_convert.convert_back_to_db_represent(problem_id,input_df_sol, mocked_mapper) 
    
    pd.testing.assert_frame_equal(actual,expected,check_names = False, check_dtype = False)

