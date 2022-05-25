import sys
from typing_extensions import final
from numpy.lib.function_base import insert
sys.path.append('../acm_solver/solver/')
sys.path.append('../acm_solver/')
sys.path.append('../acm_solver/orm/')
sys.path.append('../acm_solver/solver/solver_utils/')
sys.path.append('../acm_solver/generated/')
import pytest
import config as cfg
import multiprocessing as mp
import numpy as np
import odm
import bson
import json
import datetime
import mongoengine as me
import pandas as pd
import time
from queue import Queue

import solver_helpers
import settings
import exceptions_handler
# from fixtures import clean_db_fixture
import helpers 
#Module to test
import model_solver
from bson.json_util import loads
import workers
import logging
logging.basicConfig(level= logging.DEBUG)

@pytest.fixture()
def setup_teardown_db_fixture():
    me.disconnect_all()
    # me.connect('mocked_mongo_db', host='mongomock://localhost')
    me.connect('mocked_mongo_db')
    odm.ASCampaign.drop_collection()
    odm.ASPlace.drop_collection()
    odm.ASResult.drop_collection()
    odm.ASUnplanned.drop_collection()
    solver_helpers.me= me
    yield 
    # me.disconnect_all()


def test_solve_prob_preset_data_soft_constraints_return_correct_result(setup_teardown_db_fixture):

    # Arrange
    # Populate mocked db
    mocked_queue = helpers.MockedQueue()
    mp.Manager = helpers.MockedManager
    #Insert data from jsons to mocked db
    with open('./data/asCampaign.json') as f:  
        file_data = json.load(f)
        campaigns_data = loads(json.dumps(file_data))
    for campaign in campaigns_data:
        campaign['campaignType'] = campaign['type']
        campaign.pop('type')
    odm.ASCampaign.objects().delete()
    odm.ASCampaign.objects.insert([odm.ASCampaign(**data) for data in campaigns_data])

    prob_ids = set([data['problemId'] for data in file_data])

    with open('./data/asPlace.json') as f:
        file_data = json.load(f)
        places_data = loads(json.dumps(file_data))
    odm.ASPlace.objects.insert([odm.ASPlace(**data) for data in places_data])
    
    with open('./data/asSolveResult.json') as f:
        file_data = json.load(f)
        solve_data = loads(json.dumps(file_data))
    for data in solve_data:
        data.pop('_id')
        data['date'] = data['date'].replace(tzinfo = None)

    # Act

    [model_solver.solve_prob(prob_id, cfg, solve_queue = mocked_queue, alpha_formula = '3', method ="SOFT_CONSTRAINT",) for prob_id in prob_ids]

    for prob_id in prob_ids:
        actual = list(odm.ASResult.objects(problemId = prob_id).as_pymongo()).copy()
        df_actual = pd.DataFrame(actual)
        df_actual.drop(columns = ['_id','createDate'], inplace = True, errors = 'ignore')
        df_expected_all = pd.DataFrame(solve_data)
        df_expected_all.drop(columns = ['_id','createDate'], inplace = True, errors = 'ignore')
        df_expected = df_expected_all[df_expected_all['problemId']==prob_id].reset_index(drop = True)

        # Assert
        try:
            pd.testing.assert_frame_equal(df_expected, df_actual, check_dtype= False, check_like= True)
        except AssertionError as e:
            print("df_expected: \n ", df_expected)
            print("df_actual: \n", df_actual)
            e.args += ("problem_id: ",prob_id)
            raise
    # me.disconnect()


def test_solve_prob_preset_data_two_steps_return_correct_result(setup_teardown_db_fixture):

    # Arrange
    # Populate mocked db
    mocked_queue = helpers.MockedQueue()
    mp.Manager = helpers.MockedManager
    #Insert data from jsons to mocked db
    with open('./data/asCampaign.json') as f:  
        file_data = json.load(f)
        campaigns_data = loads(json.dumps(file_data))
    for campaign in campaigns_data:
        campaign['campaignType'] = campaign['type']
        campaign.pop('type')
    odm.ASCampaign.objects().delete()
    odm.ASCampaign.objects.insert([odm.ASCampaign(**data) for data in campaigns_data])

    prob_ids = set([data['problemId'] for data in file_data])
    # prob_ids.remove('4')
    # prob_ids.remove('5')
    with open('./data/asPlace2Steps.json') as f:
        file_data = json.load(f)
        places_data = loads(json.dumps(file_data))
    odm.ASPlace.objects.insert([odm.ASPlace(**data) for data in places_data])
    
    with open('./data/asSolveResult2Steps.json') as f:
        file_data = json.load(f)
        solve_data = loads(json.dumps(file_data))
    for data in solve_data:
        data.pop('_id')
        data['date'] = data['date'].replace(tzinfo = None)

    # Act

    [model_solver.solve_prob(prob_id, cfg, solve_queue = mocked_queue, alpha_formula = '3', method ="TWO_STEPS",) for prob_id in prob_ids]

    for prob_id in prob_ids:
        actual = list(odm.ASResult.objects(problemId = prob_id).as_pymongo()).copy()
        df_actual = pd.DataFrame(actual)
        df_actual.drop(columns = ['_id','createDate'], inplace = True, errors = 'ignore')
        df_expected_all = pd.DataFrame(solve_data)
        df_expected_all.drop(columns = ['_id','createDate'], inplace = True, errors = 'ignore')
        df_expected = df_expected_all[df_expected_all['problemId']==prob_id].reset_index(drop = True)

        # Assert
        try:
            pd.testing.assert_frame_equal(df_expected, df_actual, check_dtype= False, check_like= True, check_less_precise = True)
        except AssertionError as e:
            print("df_expected: \n ", df_expected)
            print("df_actual: \n", df_actual)
            e.args += ("problem_id: ",prob_id)
            raise
    # me.disconnect()

def test_unplanned_preset_data_return_correct_result(setup_teardown_db_fixture):

    # Arrange
    # Populate mocked db

    # me.connect('mocked_mongo_db', host='mongomock://localhost',)
    mocked_queue = helpers.MockedQueue()
    mp.Manager = helpers.MockedManager

    #Insert data from jsons to mocked db
    with open('./data/asCampaign.json') as f:  
        file_data = json.load(f)
        campaigns_data = loads(json.dumps(file_data))
    for campaign in campaigns_data:
        campaign['campaignType'] = campaign['type']
        campaign.pop('type')
    odm.ASCampaign.objects.insert([odm.ASCampaign(**data) for data in campaigns_data])

    with open('./data/asPlace.json') as f:
        file_data = json.load(f)
        places_data = loads(json.dumps(file_data))
    odm.ASPlace.objects.insert([odm.ASPlace(**data) for data in places_data])

    with open('./data/asUnplanned.json') as f:
        file_data = json.load(f)
        unplanned_data = loads(json.dumps(file_data))
    for data in unplanned_data:
        data.pop('_id')

    prob_ids = set([data['problemId'] for data in file_data])

    # Act
    [model_solver.solve_prob(prob_id, cfg, solve_queue = mocked_queue, alpha_formula = '3', method ="SOFT_CONSTRAINT",) for prob_id in prob_ids]

    for prob_id in prob_ids:
        actual = list(odm.ASUnplanned.objects(problemId = prob_id).as_pymongo()).copy()
        df_actual = pd.DataFrame(actual)
        df_actual.drop(columns = ['_id','createDate'], inplace = True, errors = 'ignore')
        df_expected_all = pd.DataFrame(unplanned_data)
        df_expected_all.drop(columns = ['_id','createDate'], inplace = True, errors = 'ignore')
        df_expected = df_expected_all[df_expected_all['problemId']==prob_id].reset_index(drop = True)

        # Assert
        try:
            pd.testing.assert_frame_equal(df_expected, df_actual, check_dtype= False, check_like= True)
        except AssertionError as e:
            print("df_expected: \n ", df_expected)
            print("df_actual: \n", df_actual)
            e.args += ("problem_id: ",prob_id)
            raise

    # me.disconnect()


def test_solve_prob_preset_data_max_rss_soft_constraints_return_correct_result(setup_teardown_db_fixture):
    # Arrange
    # me.connect('mocked_mongo_db', host='mongomock://localhost')
    mocked_queue = helpers.MockedQueue()
    mp.Manager = helpers.MockedManager
    #Insert data from jsons to mocked db
    with open('./data/trade_off_data/asCampaign.json') as f:  
        file_data = json.load(f)
        campaigns_data = loads(json.dumps(file_data))
    for campaign in campaigns_data:
        campaign['campaignType'] = campaign['type']
        campaign.pop('type')
    odm.ASCampaign.objects.insert([odm.ASCampaign(**data) for data in campaigns_data])

    prob_ids = ['1_max_rss']

    with open('./data/trade_off_data/asPlace.json') as f:
        file_data = json.load(f)
        places_data = loads(json.dumps(file_data))
    odm.ASPlace.objects.insert([odm.ASPlace(**data) for data in places_data])

    with open('./data/trade_off_data/asSolveResult.json') as f:
        file_data = json.load(f)
        solve_data = loads(json.dumps(file_data))
    for data in solve_data:
        data.pop('_id')
        data['date'] = data['date'].replace(tzinfo = None)

    # Act
    check = odm.ASCampaign.objects(problemId = '1_max_rss').as_pymongo()
    print(check)
    [model_solver.solve_prob(prob_id, 
                            cfg, 
                            solve_queue = mocked_queue, 
                            alpha_formula = '3', 
                            evenness_priority = 0, 
                            method = "SOFT_CONSTRAINT") for prob_id in prob_ids]

    for prob_id in prob_ids:
        actual = list(odm.ASResult.objects(problemId = prob_id).as_pymongo()).copy()
        df_actual = pd.DataFrame(actual)
        df_actual.drop(columns = ['_id','createDate'], inplace = True, errors = 'ignore')
        df_expected_all = pd.DataFrame(solve_data)
        df_expected_all.drop(columns = ['_id','createDate'], inplace = True, errors = 'ignore')
        df_expected = df_expected_all[df_expected_all['problemId']==prob_id].reset_index(drop = True)

        # Assert
        try:
            pd.testing.assert_frame_equal(df_expected, df_actual, check_dtype= False, check_like= True)
        except AssertionError as e:
            print("df_expected: \n ", df_expected)
            print("df_actual: \n", df_actual)
            e.args += ("problem_id: ",prob_id)
            raise
    # me.disconnect()

@pytest.mark.skip(reason = "take too much time to run regularly.")
def test_solve_prob_run_within_time_with_high_dimensional_data():

    # Arrange
    np.random.seed(10)

    problem_id = "generated_1"
    campaigns_num = 40
    places_num = 350
    max_days = 50
    t_0_percent = .4
    total_range = [500,5000]
    predicted_views_range = [200,500]
    ratio = 0.5
    start_date_int = np.random.randint(0,1, campaigns_num)
    expired_date_int = start_date_int+(np.random.randint(0, max_days-start_date_int, campaigns_num))
    num_campaign_types = 10
    max_num_days_have_weight = 5
    start_date = datetime.datetime.strptime("21 June, 2030", "%d %B, %Y")

    # Populate campaigns list
    campaigns_list = []
    for i in range(campaigns_num):
        cur_campaign ={}
        cur_campaign['problemId'] = problem_id
        cur_campaign['campaignId'] = i+ 100
        if i  <= round(t_0_percent*campaigns_num):
            cur_campaign['isNetwork'] = True
        else: 
            cur_campaign['isNetwork'] = False
        cur_campaign['startDate'] = start_date + datetime.timedelta(int(start_date_int[i]))
        cur_campaign['expiredDate'] = start_date + datetime.timedelta(int(expired_date_int[i]))
        cur_campaign['priority'] = np.random.choice(['CLASS_A','CLASS_B','CLASS_C'],p = [0.2,0.79,0.01])
        cur_campaign['campaignType'] = np.random.choice(['DEFAULT','BANNER_STATIC','BANNER_EFFECT','BANNER_SLIDE','CPA','SURVEY','VIDEO','GAME','TEXT_MATCHING','OTHER'])
        cur_campaign['total'] = np.random.randint(total_range[0],total_range[1])
        num_places_cur_campaign = np.random.randint(1,places_num)
        cur_campaign['placeIds'] = [int(i) for i in np.random.randint(1, places_num, num_places_cur_campaign)]
        #weights
        num_days_have_weight = np.random.randint(0, max_num_days_have_weight)
        cur_campaign_weight = []
        for j in range(num_days_have_weight):
            cur_weights = {}
            this_day = cur_campaign['startDate'] + datetime.timedelta(np.random.randint(0,expired_date_int[i] - start_date_int[i]+1))
            cur_weights['date'] = this_day
            cur_weights['value'] = int(np.random.choice([0,20]))
            cur_campaign_weight.append(cur_weights)
        cur_campaign['weights'] = cur_campaign_weight

        #profiles
        profile_gender_male = { "type" : "GENDER", "values" : [ 0 ]}
        profile_male_age_value = list(np.random.choice([0,1,2,3,4,5,6,7],size = np.random.randint(1,7),replace = False))
        profile_male_age_value_int = [int(value) for value in profile_male_age_value]
        profile_male_age = {"type": "AGE","values": profile_male_age_value_int}
        cur_profile_male = [profile_gender_male,profile_male_age]

        profile_gender_female = { "type" : "GENDER", "values" : [ 1 ]}
        profile_female_age_value = list(np.random.choice([0,1,2,3,4,5,6,7],size = np.random.randint(1,7),replace = False))
        profile_female_age_value_int = [int(value) for value in profile_female_age_value]
        profile_female_age = {"type": "AGE","values": profile_female_age_value_int}
        cur_profile_female = [profile_gender_female,profile_female_age]

        # profile_gender_unknown = { "type" : "GENDER", "values" : [ 2 ]}
        # profile_unknown_age_value = list(np.random.choice([0,1,2,3,4,5,6,7],size = np.random.randint(1,7),replace = False))
        # profile_unknown_age_value_int = [int(value) for value in profile_unknown_age_value]
        # profile_unknown_age = {"type": "AGE","values": profile_unknown_age_value_int}
        # cur_profile_unknown = [profile_gender_unknown,profile_unknown_age]

        # cur_campaign['profiles'] = [cur_profile_male,cur_profile_female, cur_profile_unknown]

        cur_campaign['profiles'] = [cur_profile_male,cur_profile_female]

        campaigns_list.append(cur_campaign)

    #Populate places list
    places_list = []
    for i in range(places_num):
        cur_place = {}
        cur_place['problemId'] = problem_id
        cur_place['placeId'] = i 
        cur_place['ctrs'] =[

            {
                "value": round(np.random.rand(),2),
                "type": "DEFAULT"
            },
            {
                "value": round(np.random.rand(),2),
                "type": "BANNER_STATIC"
            },
            {
                "value": round(np.random.rand(),2),
                "type": "BANNER_EFFECT"
            },
            {
                "value": round(np.random.rand(),2),
                "type": "BANNER_SLIDE"
            },
            {
                "value": round(np.random.rand(),2),
                "type": "CPA"
            },
            {
                "value": round(np.random.rand(),2),
                "type": "SURVEY"
            },
            {
                "value": round(np.random.rand(),2),
                "type": "VIDEO"
            },
            {
                "value": round(np.random.rand(),2),
                "type": "GAME"
            },
            {
                "value": round(np.random.rand(),2),
                "type": "TEXT_MATCHING"
            },
            {
                "value": round(np.random.rand(),2),
                "type": "OTHER"
            }

        ]
        cur_place['views'] = list(np.random.randint(predicted_views_range[0], predicted_views_range[1], max_days))
        cur_place['shareType'] = 'SOFT'
        cur_place['views'] = [{'date':start_date +datetime.timedelta(i),
          'value':int(value)} for i,value in zip(range(max_days),cur_place['views'])]

        #profiles ratio
        gender_ratio_deno = np.random.randint(1,100,size = 3)
        gender_ratio = list(np.round(gender_ratio_deno/np.sum(gender_ratio_deno),2))
        gender_ratio = [float(ratio) for ratio in gender_ratio]

        age_ratio_deno = np.random.randint(1,100,size = 8)
        age_ratio = list(np.round(age_ratio_deno/np.sum(age_ratio_deno),2))
        age_ratio = [float(ratio) for ratio in age_ratio]

        cur_place['profilesRatio'] =[
            {
                "type":'GENDER',
                "ratio":gender_ratio
            },
            {
                "type":"AGE",
                "ratio": age_ratio
            }
        ]
        cur_place['shareRate'] = 0.5
        places_list.append(cur_place)

    me.connect('mocked_mongo_db', host='mongomock://localhost')
    odm.ASCampaign.objects.insert([odm.ASCampaign(**campaign) for campaign in campaigns_list])
    odm.ASPlace.objects.insert([odm.ASPlace(**place) for place in places_list])
    share_rate = {'problemId':problem_id, 'ratio': ratio}
    odm.ASShareRate.objects.insert([odm.ASShareRate(**share_rate)])

    # Act
    start_time = time.time()
    model_solver.solve_prob(problem_id, cfg, 'by_places')
    end_time = time.time()
    print(end_time- start_time)
    me.disconnect()
    # Assert
    assert end_time -start_time <= 2700


def test_solve_prob_no_campaign(setup_teardown_db_fixture):
    # Arrange
    # me.connect('mocked_mongo_db', host='mongomock://localhost')
    mocked_queue = helpers.MockedQueue()
    mp.Manager = helpers.MockedManager
    some_unreal_prob_id = "asdfasfdfd"

    # Act
    with pytest.raises(exceptions_handler.NoCampaign):
        model_solver.solve_prob(some_unreal_prob_id,cfg, solve_queue = mocked_queue)
        # me.disconnect()


def test_solve_prob_split_by_places_have_no_error(setup_teardown_db_fixture):

    # Arrange
    cfg.problem_max_size = 100
    cfg.connection_str = 'mongomock://localhost'
    cfg.db_name = 'mocked_mongo_db'
    
    problem_id = "generated_1"
    campaigns_num = 5
    places_num = 10
    max_days = 10
    t_0_percent = .4
    total_range = [500,5000]
    predicted_views_range = [200,500]
    ratio = 0.5
    start_date_int = np.random.randint(0,1, campaigns_num)
    expired_date_int = start_date_int+(np.random.randint(0, max_days-start_date_int, campaigns_num))
    num_campaign_types = 5
    max_num_days_have_weight = 5
    start_date = datetime.datetime.strptime("21 June, 2031", "%d %B, %Y")

    # Populate campaigns list
    campaigns_list = []
    for i in range(campaigns_num):
        cur_campaign ={}
        cur_campaign['problemId'] = problem_id
        cur_campaign['campaignId'] = i+ 100
        if i  <= round(t_0_percent*campaigns_num):
            cur_campaign['isNetwork'] = True
        else: 
            cur_campaign['isNetwork'] = False
        cur_campaign['startDate'] = start_date + datetime.timedelta(int(start_date_int[i]))
        cur_campaign['expiredDate'] = start_date + datetime.timedelta(int(expired_date_int[i]))
        cur_campaign['priority'] = np.random.choice(['CLASS_A','CLASS_B','CLASS_C'],p = [0.2,0.8,0.00])
        cur_campaign['campaignType'] = np.random.choice(['DEFAULT','BANNER_STATIC','BANNER_EFFECT','BANNER_SLIDE','CPA','SURVEY','VIDEO','GAME','TEXT_MATCHING','OTHER'])
        cur_campaign['total'] = np.random.randint(total_range[0],total_range[1])
        num_places_cur_campaign = np.random.randint(1,places_num)
        cur_campaign['placeIds'] = [int(i) for i in np.random.randint(1, places_num, num_places_cur_campaign)]
        #weights
        num_days_have_weight = np.random.randint(0, max_num_days_have_weight)
        cur_campaign_weight = []
        for j in range(num_days_have_weight):
            cur_weights = {}
            this_day = cur_campaign['startDate'] + datetime.timedelta(np.random.randint(0,expired_date_int[i] - start_date_int[i]+1))
            cur_weights['date'] = this_day
            cur_weights['value'] = int(np.random.choice([0,20]))
            cur_campaign_weight.append(cur_weights)
        cur_campaign['weights'] = cur_campaign_weight

        #profiles
        profile_gender_male = { "type" : "GENDER", "values" : [ 0 ]}
        profile_male_age_value = list(np.random.choice([0,1,2,3,4,5,6,7],size = np.random.randint(1,7),replace = False))
        profile_male_age_value_int = [int(value) for value in profile_male_age_value]
        profile_male_age = {"type": "AGE","values": profile_male_age_value_int}
        cur_profile_male = [profile_gender_male,profile_male_age]

        profile_gender_female = { "type" : "GENDER", "values" : [ 1 ]}
        profile_female_age_value = list(np.random.choice([0,1,2,3,4,5,6,7],size = np.random.randint(1,7),replace = False))
        profile_female_age_value_int = [int(value) for value in profile_female_age_value]
        profile_female_age = {"type": "AGE","values": profile_female_age_value_int}
        cur_profile_female = [profile_gender_female,profile_female_age]

        cur_campaign['profiles'] = [cur_profile_male,cur_profile_female]

        campaigns_list.append(cur_campaign)

    #Populate places list
    places_list = []
    for i in range(places_num):
        cur_place = {}
        cur_place['problemId'] = problem_id
        cur_place['placeId'] = i 
        cur_place['ctrs'] =[

            {
                "value": round(np.random.rand(),2),
                "type": "DEFAULT"
            },
            {
                "value": round(np.random.rand(),2),
                "type": "BANNER_STATIC"
            },
            {
                "value": round(np.random.rand(),2),
                "type": "BANNER_EFFECT"
            },
            {
                "value": round(np.random.rand(),2),
                "type": "BANNER_SLIDE"
            },
            {
                "value": round(np.random.rand(),2),
                "type": "CPA"
            },
            {
                "value": round(np.random.rand(),2),
                "type": "SURVEY"
            },
            {
                "value": round(np.random.rand(),2),
                "type": "VIDEO"
            },
            {
                "value": round(np.random.rand(),2),
                "type": "GAME"
            },
            {
                "value": round(np.random.rand(),2),
                "type": "TEXT_MATCHING"
            },
            {
                "value": round(np.random.rand(),2),
                "type": "OTHER"
            }

        ]
        cur_place['shareType'] = 'SOFT'
        cur_place['views'] = list(np.random.randint(predicted_views_range[0], predicted_views_range[1], max_days))
        cur_place['views'] = [{'date':start_date +datetime.timedelta(i),
          'value':int(value)} for i,value in zip(range(max_days),cur_place['views'])]

        #profiles ratio
        gender_ratio_deno = np.random.randint(1,100,size = 3)
        gender_ratio = list(gender_ratio_deno/np.sum(gender_ratio_deno))
        gender_ratio = [float(ratio) for ratio in gender_ratio]

        age_ratio_deno = np.random.randint(1,100,size = 8)
        age_ratio = list(age_ratio_deno/np.sum(age_ratio_deno))
        age_ratio = [float(ratio) for ratio in age_ratio]

        cur_place['profilesRatio'] =[
            {
                "type":'GENDER',
                "ratio":gender_ratio
            },
            {
                "type":"AGE",
                "ratio": age_ratio
            }
        ]
        cur_place['shareRate'] = 0.5
        places_list.append(cur_place)

    # me.disconnect_all()
    # me.connect('mocked_mongo_db', host='mongomock://localhost')
    mocked_queue = helpers.MockedQueue()
    mp.Manager = helpers.MockedManager
    odm.ASCampaign.objects.insert([odm.ASCampaign(**campaign) for campaign in campaigns_list])
    odm.ASPlace.objects.insert([odm.ASPlace(**place) for place in places_list])
    share_rate = {'problemId':problem_id, 'ratio': ratio}
    odm.ASShareRate.objects.insert([odm.ASShareRate(**share_rate)])

    # Act
    start_time = time.time()
    model_solver.solve_prob(problem_id, cfg, solve_queue = mocked_queue, split_method= 'by_places')
    end_time = time.time()
    # me.disconnect()
    # Assert
    assert end_time -start_time <= 100