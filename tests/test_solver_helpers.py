import sys
sys.path.append('../acm_solver/')
sys.path.append('../acm_solver/orm/')
sys.path.append('../acm_solver/solver/')
sys.path.append('../acm_solver/generated')
import pandas as pd
import numpy as np
import pytest
from unittest.mock import Mock

# Module to test
import solver_helpers

test_CampaignProfile_to_list_rep_input_1 = [[{'type': 'GENDER', 'values': [1]}, {'type': 'AGE', 'values': [1, 2, 3]}],
 [{'type': 'GENDER', 'values': [0]}, {'type': 'AGE', 'values': [1, 2]}]]
test_CampaignProfile_to_list_rep_output_1 = [[0,1],[0,2],[1,1],[1,2],[1,3]]
test_CampaignProfile_to_list_rep_input_2 = [[{'type': 'AGE', 'values': [1, 2, 3]}]]
test_CampaignProfile_to_list_rep_output_2 = [[0,1],[0,2],[0,3],[1,1],[1,2],[1,3],[2,1],[2,2],[2,3]]
test_CampaignProfile_to_list_rep_input_3 = [[{'type': 'GENDER', 'values': [1]}],
 [{'type': 'GENDER', 'values': [0]}, {'type': 'AGE', 'values': [1, 2]}]]
test_CampaignProfile_to_list_rep_output_3 = [[0,1],[0,2],[1,0],[1,1],[1,2],[1,3],[1,4],[1,5],[1,6],[1,7]]
test_CampaignProfile_to_list_rep_input_0 = []
test_CampaignProfile_to_list_rep_output_0 = [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [0, 6], [0, 7], [1, 0], [1, 1], [1, 2], 
    [1, 3], [1, 4], [1, 5], [1, 6], [1, 7], [2, 0], [2, 1], [2, 2], [2, 3], [2, 4], [2, 5], [2, 6], [2, 7]]

test_CampaignProfile_to_list_rep_data = [(test_CampaignProfile_to_list_rep_input_0,test_CampaignProfile_to_list_rep_output_0),
(test_CampaignProfile_to_list_rep_input_1,test_CampaignProfile_to_list_rep_output_1),
(test_CampaignProfile_to_list_rep_input_2,test_CampaignProfile_to_list_rep_output_2),
(test_CampaignProfile_to_list_rep_input_3,test_CampaignProfile_to_list_rep_output_3),
]

test_CampaignProfile_to_int_rep_input_0 = [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [0, 6], [0, 7], [1, 0], [1, 1], [1, 2], 
    [1, 3], [1, 4], [1, 5], [1, 6], [1, 7], [2, 0], [2, 1], [2, 2], [2, 3], [2, 4], [2, 5], [2, 6], [2, 7]]
test_CampaignProfile_to_int_rep_input_1 = [[0,1],[0,2],[1,1],[1,2],[1,3]]
test_CampaignProfile_to_int_rep_input_2 = [[0,1],[0,2],[0,3],[1,1],[1,2],[1,3]]
test_CampaignProfile_to_int_rep_input_3 = [[0,1],[0,2],[1,0],[1,1],[1,2],[1,3],[1,4],[1,5],[1,6]]
test_CampaignProfile_to_int_rep_output_0 = frozenset({0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23})
test_CampaignProfile_to_int_rep_output_1 = frozenset({1, 2, 9, 10, 11})
test_CampaignProfile_to_int_rep_output_2 = frozenset({1, 2, 3, 9, 10, 11})
test_CampaignProfile_to_int_rep_output_3 = frozenset({1, 2, 8, 9, 10, 11, 12, 13, 14})

test_CampaignProfile_to_int_rep_data = [(test_CampaignProfile_to_int_rep_input_0,test_CampaignProfile_to_int_rep_output_0),
(test_CampaignProfile_to_int_rep_input_1,test_CampaignProfile_to_int_rep_output_1),
(test_CampaignProfile_to_int_rep_input_2,test_CampaignProfile_to_int_rep_output_2),
(test_CampaignProfile_to_int_rep_input_3,test_CampaignProfile_to_int_rep_output_3),
]


class TestCampaignProfile:

    @pytest.mark.parametrize('input_db_rep,expect_output',test_CampaignProfile_to_list_rep_data)
    def test_CampaignProfile_to_list_rep(self,input_db_rep,expect_output):
        campaign_profile = solver_helpers.CampaignProfile(input_db_rep)
        actual_list_rep = campaign_profile.list_rep
        assert actual_list_rep == expect_output

    @pytest.mark.parametrize('input_list_rep,expect_output',test_CampaignProfile_to_int_rep_data)
    def test_CampaignProfile_to_int_rep(self,input_list_rep,expect_output):
        campaign_profile = solver_helpers.CampaignProfile()
        campaign_profile.list_rep = input_list_rep
        actual_int_rep = campaign_profile._to_int_rep()
        assert actual_int_rep == expect_output

class TestPlaceProfile:

    def test_PlaceProfile_to_list_rep(self):
        input_db_rep = [{'type': 'GENDER', 'ratio': [0.5, 0.5]}, {'type': 'AGE', 'ratio': [0.15, 0.1, 0.1, 0.2, 0.1, 0.1, 0.25]}]
        expect_output = [[0.5, 0.5], [0.15, 0.1, 0.1, 0.2, 0.1, 0.1, 0.25]]

        place_profile = solver_helpers.PlaceProfile(input_db_rep)
        actual_list_rep = place_profile.list_rep
        assert sorted(actual_list_rep) == sorted(expect_output)

    def test_PlaceProfile_to_int_rep(self):
        place_profile = solver_helpers.PlaceProfile()
        place_profile.list_rep = [[0.5, 0.5], [0.15, 0.1, 0.1, 0.2, 0.1, 0.1, 0.25]]
        expect_output = [0.075,0.05,0.05,0.1,0.05,0.05,0.125,0.075,0.05,0.05,0.1,0.05,0.05,0.125]

        actual_int_rep = place_profile._to_int_rep()
        assert actual_int_rep  == expect_output

@pytest.mark.xfail(reason = "unimplimented")
class TestProcessClassA:
    def test_process_class_a_return_correct_value(self,input_test_process_class_a_return_correct_value, output_test_process_class_a_return_correct_value):
        
        assert 1 == 2


class TestCalculatedAlphaDoesntHaveNanWhenAllViewsEqualZero:
    """
    khi views = 0 hết cho 1 địa điểm nào đấy, mẫu số trong các công thức tính alpha có thể = 0, nên kết quả chia có thể ra nan. Bài test này xem đã xử lí hết chưa
    """
    data ={'U': 1,
                'T': 1,
                'K': 2,
                'D': [np.array([0, 0])],
                'd': [5],
                'r': np.array([[ 0., 0]]),
                'CTR': np.array([[0.734323, 0.734323]]),
                'w': np.array([[10.]]),
                'L': [np.array([0])],
                'B': [[0], []],
                't_0': 1,
                'share_rate': [1.0, 1.0],
                'priority': ['CLASS_B']}
        
    def test_calculated_alpha_doesnt_have_nan_formula_0(self):
        # Arrange
        expected = np.array([[[0., 0.]]])
        # Act
        actual = solver_helpers.Alpha.calculate(self.data,'0')
        # Assert
        np.testing.assert_array_almost_equal(actual,expected)

    def test_calculated_alpha_doesnt_have_nan_formula_1(self):
        # Arrange
        expected = np.array([[[0., 0.]]])
        # Act
        actual = solver_helpers.Alpha.calculate(self.data,'1')
        # Assert
        np.testing.assert_array_almost_equal(actual,expected)

    def test_calculated_alpha_doesnt_have_nan_formula_2(self):
        # Arrange
        expected = np.array([[[0., 0.]]])
        # Act
        actual = solver_helpers.Alpha.calculate(self.data,'2')
        # Assert
        np.testing.assert_array_almost_equal(actual,expected)


class TestAlphaResultsAreTrue:
    def test_formula_3_correct(self): 
        model_ready_data_1 ={
            'U': 3,
            'T': 4,
            'K': 3,
            'D': [np.array([0, 1]),
            np.array([0, 2]),
            np.array([0, 2]),
            np.array([2, 2])],
            'd': [39.99999991666667,
            39.99999991666667,
            39.99999988888889,
            39.99999966666667],
            'r': np.array([[40., 80., 40.],
                    [40., 80., 40.],
                    [40., 80., 40.]]),
            'CTR': np.array([[1., 1., 1.],
                    [1., 1., 1.],
                    [1., 1., 1.],
                    [1., 1., 1.]]),
            'w': np.array([[10., 10.,  0.],
                    [10., 10.,  0.],
                    [10., 10., 10.],
                    [ 0.,  0., 10.]]),
            'L': [np.array([0, 1, 2]), np.array([0, 1, 2]), np.array([0, 1]), np.array([2])],
            'B': [[0, 1, 2], [0, 1, 2], [0, 1, 3]],
            't_0': 4,
            'share_rate': [0.4, 0.4, 0.4],
            'priority': ['CLASS_B', 'CLASS_B', 'CLASS_C', 'CLASS_C'],
            'share_type': [0, 0, 0]}
        
        expected_alpha_1 = np.array(
        [[[ 0.        ,  0.        , 19.99999996],
        [ 0.        ,  0.        , 19.99999996],
        [ 0.        ,  0.        ,  0.        ]],

       [[ 0.        ,  0.        , 19.99999996],
        [ 0.        ,  0.        , 19.99999996],
        [ 0.        ,  0.        ,  0.        ]],

       [[ 0.        ,  0.        ,  0.        ],
        [ 0.        ,  0.        ,  0.        ],
        [ 0.        ,  0.        ,  0.        ]],

       [[ 0.        ,  0.        ,  0.        ],
        [ 0.        ,  0.        ,  0.        ],
        [ 0.        ,  0.        ,  0.        ]]])

        model_ready_data_2 = {
            'U': 3,
            'T': 4,
            'K': 3,
            'D': [np.array([0, 1]),
            np.array([0, 2]),
            np.array([1, 1]),
            np.array([2, 2])],
            'd': [39.99999991666667,
            39.99999991666667,
            39.999999833333334,
            39.99999988888889],
            'r': np.array([[40., 80., 40.],
                    [40., 80., 40.],
                    [40., 80., 40.]]),
            'CTR': np.array([[1., 1., 1.],
                    [1., 1., 1.],
                    [1., 1., 1.],
                    [1., 1., 1.]]),
            'w': np.array([[10., 10.,  0.],
                    [10., 10., 10.],
                    [ 0., 10.,  0.],
                    [ 0.,  0., 10.]]),
            'L': [np.array([0, 1, 2]), np.array([0, 1, 2]), np.array([1]), np.array([1, 2])],
            'B': [[0, 1], [0, 1, 2, 3], [0, 1, 3]],
            't_0': 4,
            'share_rate': [0.4, 0.4, 0.4],
            'priority': ['CLASS_B', 'CLASS_B', 'CLASS_C', 'CLASS_C'],
            'share_type': [0, 0, 0]}

        expected_alpha_2 =  np.array(
        [[[ 4.99999999,  9.99999998,  4.99999999],
        [ 9.99999998,  0.        ,  9.99999998],
        [ 0.        ,  0.        ,  0.        ]],

       [[ 3.33333333,  6.66666665,  3.33333333],
        [ 6.66666665,  0.        ,  6.66666665],
        [13.33333331,  0.        ,  0.        ]],

       [[ 0.        ,  0.        ,  0.        ],
        [ 0.        ,  0.        ,  0.        ],
        [ 0.        ,  0.        ,  0.        ]],

       [[ 0.        ,  0.        ,  0.        ],
        [ 0.        ,  0.        ,  0.        ],
        [ 0.        ,  0.        ,  0.        ]]])

        all_model_ready_data = [model_ready_data_1, model_ready_data_2]
        all_expected_alpha = [expected_alpha_1, expected_alpha_2]

        # Act 
        
        all_actual_alpha = [solver_helpers.Alpha.calculate(data,'3') for data in all_model_ready_data]
        for actual_alpha,expected_alpha in  zip(all_actual_alpha, all_expected_alpha):
            np.testing.assert_almost_equal(actual_alpha,expected_alpha)

class TestPartition:
    def test_partition_profile(self):
        # Arrange
        universe_int_rep = frozenset([i for i in range(14)])

        profile_campaign_1 = Mock()
        profile_campaign_1.int_rep = frozenset([1,2,3,4])
        profile_campaign_2 = Mock()
        profile_campaign_2.int_rep = frozenset([2,3,4,5,6])
        profiles_list = [profile_campaign_1,profile_campaign_2]
        
        expected = [frozenset({2, 3, 4}),
                    frozenset({1}),
                    frozenset({5, 6}),
                    frozenset({0, 7, 8, 9, 10, 11, 12, 13})]

        # Act
        actual = solver_helpers.Partition._partition_profile(universe_int_rep, profiles_list)

        # Assert 
        assert actual == expected

    def test_partition_places(self):
        # Arrange
        input_profile_partitioned_sets = [frozenset({0}), frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13})]

        input_original_places = {'original_id': [0,1],
                                'ids': [0, 1],
                                'views': [[40], [20]],
                                'ctrs': [[1, 0, 0, 0, 0], [1, 0, 0, 0, 0]]
                                }
        input_profiles_ratio_1 = Mock()
        input_profiles_ratio_1.int_rep = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        input_profiles_ratio_2 = Mock()
        input_profiles_ratio_2.int_rep = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        input_profiles_ratio_list = [input_profiles_ratio_1, input_profiles_ratio_2]
        input_original_places['profiles_ratio'] = input_profiles_ratio_list
        input_original_places = pd.DataFrame(input_original_places)
        # Act
        actual_partitioned_places = solver_helpers.Partition._partition_places(input_profile_partitioned_sets, input_original_places)
        actual_partitioned_places_df = pd.DataFrame(actual_partitioned_places[0])

        # Assert
        pd.testing.assert_series_equal(actual_partitioned_places_df['views'],pd.Series([[40],[0],[20],[0]],name ='views'))
        pd.testing.assert_series_equal(actual_partitioned_places_df['original_id'],pd.Series([0,0,1,1],name ='original_id'))
        pd.testing.assert_series_equal(actual_partitioned_places_df['solve_id'],pd.Series([0,1,2,3],name ='solve_id'))

    def test_add_partitioned_places(self):
        # Arrange 
        input_campaign_dict = {'original_id': ['0','1'],
                            'ids': [0, 1],
                            'dates': [np.array([0, 0]), np.array([0, 0])],
                            'totals': [35, 60],
                            'type': [0, 0],
                            'place_ids': [[1], [0, 1]],
                            'weights': [{'0': 10}, {'0': 10}],
                            }

        input_campaign_dict_profiles_1 = Mock()
        input_campaign_dict_profiles_1.int_rep = frozenset({0})
        input_campaign_dict_profiles_2 = Mock()
        input_campaign_dict_profiles_2.int_rep = frozenset({0})
        input_campaign_dict_profiles = [input_campaign_dict_profiles_1, input_campaign_dict_profiles_2]
        input_campaign_dict['profiles'] = input_campaign_dict_profiles
        input_campaign_df = pd.DataFrame(input_campaign_dict)

        input_partitioned_place_0 = {'original_id': 0, 'profiles': frozenset({0}),'solve_id': 0}
        input_partitioned_place_1 = {'original_id': 0, 'profiles': frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13}),'solve_id': 1}
        input_partitioned_place_2 = {'original_id': 1, 'profiles': frozenset({0}),'solve_id': 2}
        input_partitioned_place_3 = {'original_id': 1, 'profiles': frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13}),'solve_id': 3}
        input_partitioned_places = [input_partitioned_place_0, input_partitioned_place_1, input_partitioned_place_2, input_partitioned_place_3]
        df_input_partitioned_places_map =  pd.DataFrame(input_partitioned_places)

        # Act
        actual = solver_helpers.Partition._add_partitioned_places(input_campaign_df, df_input_partitioned_places_map)

        # Assert
        pd.testing.assert_series_equal(actual['solve_place_ids'],pd.Series([[2],[0,2]]),check_names = False)