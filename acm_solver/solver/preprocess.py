import config as cfg
from generated import acm_base_pb2
import settings
from solver.solver_helpers import  PreprocessedData, Mapper, PlaceProfile, CampaignProfile, Partition

import datetime
import pandas as pd
import numpy as np


class PreprocessConverter:
    """
    Preprocess data: Convert dữ liệu thô lấy từ db (raw data) thành preprocessed data
    """

    @staticmethod
    def convert_from_raw_data(raw_data, partition = True):
        """
        Convert dữ liệu từ raw data thành preprocess data
        
        Parameters
        ----------
        raw_data : solver_helpers.RawData
        partition : bool, default True
            Nếu True, các địa điểm sẽ được phân hoạch thành các địa điểm con sao cho mỗi địa điểm con chỉ chứa 1 nhóm profile.

        Returns
        -------
        preprocessed_data: solver_helpers.PreprocessedData
        mapper: solver_helpers.Mapper
        """
        raw_campaigns = raw_data.campaigns
        raw_places = raw_data.places
    
        preprocessed_data = PreprocessedData()
        mapper = Mapper()

        problem_start_date = min(pd.DataFrame(raw_campaigns)['startDate'])

        date_int_mapper = PreprocessConverter._map_datetime_to_int(problem_start_date, cfg)
        mapper.date_int_mapper = date_int_mapper
        total_days = PreprocessConverter._get_running_days(pd.DataFrame(raw_campaigns))

        preprocessed_data.places, mapper.places_mapper = PreprocessConverter._preprocess_places(raw_places,date_int_mapper,total_days)
        preprocessed_data.campaigns, t_0, mapper.campaigns_mapper = PreprocessConverter._preprocess_campaigns(raw_campaigns, preprocessed_data.places, date_int_mapper)
        preprocessed_data.t_0 = t_0
        # preprocessed_data.share_rate = raw_data.share_rate
        
        if partition == True:
            partitioned_data, mapper.places_mapper = Partition.partition(settings.universe_int_rep, preprocessed_data)
            preprocessed_data.campaigns = partitioned_data.campaigns
            preprocessed_data.places = partitioned_data.places

        # Update mapper campaign with id = -10, -1
        mapper.campaigns_mapper["-1"] = "-1"
        mapper.campaigns_mapper["-10"] = "-10"

        return preprocessed_data, mapper
        
    @staticmethod
    def _campaigns_to_df(jsons):
        """
        Transfer campaigns json to a dataframe of campaigns, add a new id to campaigns such that all network campaigns's new id are indexed first.
        I.e. {1,2,...first_domain_id -1} are new id of network campaigns, {first_domain_id, first_domain_id +1, ...} are new id of domain campaigns.

        Parameters
        ----------
            jsons : list
                list of odm.as_campaign.objects

        Returns
        -------
            df: pandas.DataFrame
                Dataframe of data, added raw model id.
            first_domain_id: int
                value of first_domain_id in model
        """
        cur_solve_id = 0
        # network campaigns of class B or C will be indexed first
        for doc in jsons:
            if doc['isNetwork'] == True and doc['priority'] != 'CLASS_A': 
                doc['solve_id'] = cur_solve_id
                cur_solve_id += 1

        # domain campaigns of class B or C will be indexed second
        first_domain_id  = cur_solve_id
        for doc in jsons:
            if doc['isNetwork'] == False and doc['priority'] != 'CLASS_A':
                doc['solve_id'] = cur_solve_id
                cur_solve_id += 1

        #campaigns in class A will be indexed last
        first_class_A_id = cur_solve_id
        for doc in jsons:
            if doc['priority'] == 'CLASS_A':
                doc['solve_id'] = cur_solve_id
                cur_solve_id += 1

        df = pd.DataFrame(jsons).sort_values('solve_id')
        df = df.reset_index(drop = True)
        return df, first_domain_id
    
    @staticmethod
    def _get_running_days(df_campaigns, start_date_field_name = 'startDate', expired_date_field_name = 'expiredDate'):
        """
        Get total number of campaign running days.

        Parameters:
        ----------
            df_campaigns: pandas.DataFrame
                A data frame of raw campaigns

        Returns:
        ----------
            num_days : int
                total running days of current problem.
        """
        min_d = min(df_campaigns[start_date_field_name])
        max_d = max(df_campaigns[expired_date_field_name])
        num_days = (max_d-min_d).days +1
        return num_days
    
    @staticmethod
    def _map_datetime_to_int(start_date, config):
        """
        map datetime to int.

        Parameters:
        ----------
            config : config module 
            start_date : datetime.datetime
                the youngest date among start dates of problems

        Returns:
        --------
            date_int_mapper: dict
                A dictionary maps datetime in range(start_date, start_date +config.range_date_int_mapper) to respected intergers. 
        """
        datetime_to_int_map = {}
        int_to_datetime_map = {}
        for _days in range(-config.range_date_int_mapper, config.range_date_int_mapper):
            datetime_to_int_map[start_date + datetime.timedelta(days = _days)] = _days
            int_to_datetime_map[_days] = start_date + datetime.timedelta(days = _days)
        
        date_int_mapper = {'date_to_int': datetime_to_int_map,
                    'int_to_date': int_to_datetime_map}

        return date_int_mapper

    @staticmethod
    def _add_int_dates(df_campaigns,date_to_int_mapper):
        """
        Thêm cột ngày bắt đầu, ngày kết thúc dưới dạng int vào dataframe raw_campaigns (có thể đã được xử lí trước một ít).
        Parameters:
        -----------
            df_campaigns: pandas.DataFrame
                Dataframe của raw capmaigns (có thể đã được xử lí 1 ít)
            date_to_int_mapper: dict<datetime, int>
        
        Returns:
        --------
            pd.DataFrame(list_campaigns): pandas.DataFrame
        """
        list_campaigns = df_campaigns.to_dict(orient ='records')
        for doc in list_campaigns:
            start_date = doc['startDate']
            expired_date = doc['expiredDate']
            doc['startInt'] = date_to_int_mapper[start_date]
            doc['expiredInt'] = date_to_int_mapper[expired_date]
        
        return pd.DataFrame(list_campaigns)
    
    @staticmethod
    def _get_dates_list(df_campaigns):
        """
        Parameters:
        -----------
        df_campaigns: pandas.DataFrame
            A completed data frame of campaigns

        Returns:
        ----------
        list(dates_matrix) : list
            A list of [start_date (int), expired_date (int)] for each campaign 
        """

        starts_int = df_campaigns['startInt'].to_numpy()
        expireds_int = df_campaigns['expiredInt'].to_numpy()
        dates_matrix = np.stack((starts_int,expireds_int)).T
        return list(dates_matrix)
    
    @staticmethod
    def _convert_weight_date_to_int(date_int_mapper,df_campaigns):
        """
        Convert date from field weights of  raw campaign dataframe to int.
        
        Parameters:
        -----------
        date_int_mapper: solver_helpers.Mapper.date_int_mapper
        df_campaigns: pandas.DataFrame
            Dataframe raw_campaigns(có thể đã được xử lí trước 1 ít)
        
        Returns:
        --------
            df_campaigns: pandas.DataFrame
        """
        weights_int_all_campaigns = []
        weights_list = [db_weights for db_weights in df_campaigns['weights']]

        for weights_each_campaign in weights_list:
            date_str_list = [cur_date_weight['date'] for cur_date_weight in weights_each_campaign]
            date_pdtimestamp_list = date_str_list.copy()
            weight_num_list = [cur_date_weight['value'] for cur_date_weight in weights_each_campaign]
            cur_campaign_weights = {str(date_int_mapper['date_to_int'][date_pdtimestamp]) : weight_num for (date_pdtimestamp, weight_num) in zip(date_pdtimestamp_list, weight_num_list)}
            weights_int_all_campaigns.append(cur_campaign_weights)
            
        df_campaigns['weights'] = weights_int_all_campaigns
        return df_campaigns
    
    @staticmethod
    def _add_solve_place_ids(df_raw_campaigns, preprocessed_places):
        """
        Thêm trường solve_place_ids vào raw campaigns.
        Parameters:
        -----------
            df_raw_campaigns: pandas.DataFrame
            preprocessed_places: pandas.DataFrame

        """
        campaigns_dict = df_raw_campaigns.to_dict(orient = 'records')
        place_ids_map = [[original_id, solve_id] for original_id, solve_id in zip(preprocessed_places['original_id'], preprocessed_places['solve_id'])]
        partitioned_campaigns = []
        for campaign in campaigns_dict:
            cur_cmpgn = campaign.copy()
            cur_cmpgn['solve_place_ids'] = []
            for place_id in campaign['place_ids']:
                for place in place_ids_map:
                    if place_id == place[0]:
                        cur_cmpgn['solve_place_ids'].append(place[1])
            
            partitioned_campaigns.append(cur_cmpgn)
        
        df_partitioned_campaigns = pd.DataFrame(partitioned_campaigns)

        return df_partitioned_campaigns

    @staticmethod
    def _preprocess_campaigns(raw_campaigns, preprocessed_places, date_int_mapper):
        """
        Chuyển raw campaign về preprocessed campaign
        Parameters:
        -----------
            raw_campaigns: dict
            preprocessed_places: pandas.DataFrame
            date_int_mapper: solver_helpers.Mapper.date_int_mapper
        
        Returns:
        --------
        df_campaigns: pandas.DataFrame
            dictionary of proprcessed data
        t_0: int
            first id of domain campaign (t_0 in model)
        campaigns_mapper_solve_to_original_dict: dict<original_id,solve_id>
            1 dictionary để map sove_id thành original_id của campaign
        """
    
        df_campaigns,t_0 = PreprocessConverter._campaigns_to_df(raw_campaigns)
        start_date = min(df_campaigns['startDate'])
        total_days = PreprocessConverter._get_running_days(df_campaigns)
        df_campaigns = PreprocessConverter._add_int_dates(df_campaigns,date_int_mapper['date_to_int'])
        df_campaigns = PreprocessConverter._convert_weight_date_to_int(date_int_mapper, df_campaigns)
        df_campaigns['dates'] = PreprocessConverter._get_dates_list(df_campaigns)
        df_campaigns.rename(columns = {'campaignId': 'original_id', 'cType': 'type', 'placeIds': 'place_ids'},inplace= True)
        df_campaigns['profiles'] = [CampaignProfile(profile_db_rep) for profile_db_rep in df_campaigns['profiles']]
        df_campaigns = PreprocessConverter._add_solve_place_ids(df_campaigns, preprocessed_places)
        df_campaigns['type'] = df_campaigns['type'].apply(lambda x: acm_base_pb2.CampaignType.Value(x))  # Convert campaign type from string to equivalent int
        to_drop = ['_id', 'startDate', 'expiredDate','startInt','expiredInt']
        df_campaigns.drop(columns =to_drop, inplace = True, errors='ignore')
        
        campaigns_mapper = pd.DataFrame({'original_id' : df_campaigns['original_id'].to_list(), 'solve_id' : df_campaigns['solve_id'].to_list()})
        campaigns_mapper_solve_to_original_dict = {solve : original for solve, original in  zip(df_campaigns['solve_id'],df_campaigns['original_id'])}
        return df_campaigns, t_0, campaigns_mapper_solve_to_original_dict

    @staticmethod
    def raw_places_to_df(raw_places):
        """
        Chuyển raw places thành dataframe và đánh solve id.
        Parameters:
        ----------
            data: raw_places (list<dict>) acquire from list(odm.as_place.objects.as_pymongo()).copy()

        Returns:
        --------
            a data frame (df) of places with model_id added, sorted by model_id ASC.
        """
        solve_id = 0
        for doc in raw_places:
            doc['solve_id'] = solve_id
            solve_id +=1

        df = pd.DataFrame(raw_places).sort_values('solve_id')
        df = df.reset_index(drop=True)
        return df
    
    @staticmethod
    def get_ctrs_list(df_places):
        """
        Từ data frame raw places, trả về list chỉ chứa giá trị ctrs của từng địa điểm, VD: [[1.0, 0.0, 0.0, 0.0, 0.0], [1.0, 0.5, 0.0, 0.0, 0.0]]
        Parameters:
        -----------
            df_places: pandas.DataFrame
        
        Returns:
        --------
            ctrs_list: list
                list giá trị ctrs của từng địa điểm, VD: [[1.0, 0.0, 0.0, 0.0, 0.0], [1.0, 0.5, 0.0, 0.0, 0.0]]
        """
        ctrs_dict_all_campaigns = []  # list of all ctrs in the old form of all places. E.g. : [{ "default" : 1, "cpc" : 0, "tvc" : 0, "social" : 0, "app" : 0 }, ...]
        for ctrs_each_campaign in df_places['ctrs']:
            cur_campaign_ctrs_dict = {cur_ctr['type']: cur_ctr['value'] for cur_ctr in ctrs_each_campaign}
            ctrs_dict_all_campaigns.append(cur_campaign_ctrs_dict)

        ctr_types_list = acm_base_pb2.CampaignType.keys()  # E.g. ['DEFAULT', 'CPC', 'TVC', 'APP', 'SOCIAL']
        ctrs_list = [[cur_place_ctrs_detail[ctr_type] for ctr_type in ctr_types_list]for cur_place_ctrs_detail in ctrs_dict_all_campaigns]  # list of ctrs of all campaign in value only
                                                                                                                                            # eg.[[1.0, 0.0, 0.0, 0.0, 0.0], [1.0, 0.5, 0.0, 0.0, 0.0]]
        return ctrs_list
    
    @staticmethod
    def get_profiles_details(df_places):
        """
        
        """
        profiles_ratio_list = []
        for doc in df_places['profilesRatio']:
            cur_doc = []
            for profile_type in doc:
                cur_doc.append(profile_type['details'])
            profiles_ratio_list.append(cur_doc)
        return profiles_ratio_list

    @staticmethod
    def _convert_views_date_to_int(date_int_mapper,df_places,total_running_days):
        """
        Convert date from field 'views' of raw place dataframe to int.

        Parameters:
        -----------
            date_int_mapper: Mapper.date_int_mapper
            df_places: pandas.DataFrame
            total_running_days: int
        Returns:
        --------
            df_places: pandas.DataFrame
                Dataframe của place với ngày tháng trường views đã được chuyển thành int 
        """
        views_int_all_campaigns = []
        views_list = [db_views for db_views in df_places['views']]
        views_all_no_days = []
        for views_each_campaign in views_list:
            date_str_list = [cur_date_view['date'] for cur_date_view in views_each_campaign]
            date_pdtimestamp_list = date_str_list.copy()
            view_num_list = [cur_date_view['value'] for cur_date_view in views_each_campaign]
            
            cur_campaign_views = {int(date_int_mapper['date_to_int'][date_pdtimestamp]) : view_num for (date_pdtimestamp, view_num) in zip(date_pdtimestamp_list, view_num_list)}
            cur_campaign_view_no_day = [cur_campaign_views[i] for i in range(total_running_days)]

            views_int_all_campaigns.append(cur_campaign_views)  # views_int_all_campaigns will be in the form [[{0:10},{1: 20},...],[{0:17},{15: 30},...],..]
            views_all_no_days.append(cur_campaign_view_no_day)

        df_places['views'] = views_all_no_days
        return df_places

    @staticmethod
    def _preprocess_places(raw_places, date_int_mapper,total_running_days):
        """
        Tiền xử lí dữ liệu địa điểm.

        Parameters:
        -----------
            raw_places: list<dict>
            List dữ liệu thô được vừa được lấy từ db
            date_int_mapper: dict
            total_running_days: int
        
        Returns: 
        --------
            df_places: pandas.DataFrame
            places_mapper_solve_to_orginal_dict: dict
                dict dùng để mmap solve id thành orignal id, có dạng {solve_id_1: original_id_1, solve_id_2: original_id_2, ...}
            
        """
        df_places = PreprocessConverter.raw_places_to_df(raw_places)
        
        df_places = df_places.rename(columns= {'placeId':'original_id', 'shareType': 'share_type'})
        df_places['ctrs'] = PreprocessConverter.get_ctrs_list(df_places)
        df_places = PreprocessConverter._convert_views_date_to_int(date_int_mapper, df_places, total_running_days)
        df_places["profiles_ratio"] = [PlaceProfile(profile_db_rep) for profile_db_rep in df_places['profilesRatio']]
        df_places.rename(columns={'shareRate':'share_rate'} , inplace= True)
        df_places.drop(columns = ['_id', 'profilesRatio', 'problemId'], inplace = True, errors='ignore')
        df_places['share_type'] = df_places['share_type'].apply(lambda x: acm_base_pb2.ShareType.Value(x))  # Convert string to int
        places_mapper = pd.DataFrame({'original_id' : df_places['original_id'].to_list(), 'solve_id' : df_places['solve_id'].to_list()})
        places_mapper_solve_to_orginal_dict = {solve : original for solve, original in  zip(df_places['solve_id'],df_places['original_id'])}
        return df_places, places_mapper_solve_to_orginal_dict