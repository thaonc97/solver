# Locals
import config as cfg
from orm import odm
import settings
import utils

# Site packages
import copy
import datetime
import logging
import math
import mongoengine as me
import numpy as np
import os
import pandas as pd 


class SolveStatus():
    
    def __init__(self,subproblems_left):
        self.subproblems_left = subproblems_left
        self.exception = None
    
    def set_subproblems_left(self, subproblems_left):
        self.subproblems_left = subproblems_left

    def get_subproblems_left(self):
        return self.subproblems_left

    def decrease_by_1(self):
        self.subproblems_left -=1

    def set_exception(self, exception):
        self.exception = exception

    def get_exception(self):
        return self.exception


class NumSubProblemLeft():
    def __init__(self,value):
        self.value = value
        self.exception = None
        #TODO để trả v ề lỗi 


class RawData:
    def __init__(self):
        self.campaigns = None
        self.places = None
        self.lower_ratio = None
        # self.share_rate = None


class SubProblemRawData:
    def __init__(self):
        self.campaigns = None
        self.places = None
        self.lower_ratio = None
        # self.share_rate = None


class PreprocessedData:
    def __init__(self):
        self.campaigns = None
        self.places = None
        # self.share_rate = None
        self.t_0 = None
        self.lower_ratio = None


class PartitionedData:
    def __init__(self):
        self.campaigns = None
        self.places = None
        # self.share_rate = None
        self.t_0 = None
        self.lower_ratio = None


class Mapper:
    def __init__(self):
        self.date_int_mapper = None
        self.places_mapper = None
        self.campaigns_mapper = None


class PlaceProfile:
    """
    A class for the purpose of representing place profile-ratio in database, list, and int form.
    """

    def __init__(self,db_represent = None):
        if db_represent is not None:
            self.db_rep = db_represent
            self.list_rep  = self._to_list_rep()
            self.int_rep = self._to_int_rep()
        else:
            self.db_rep = None
            self.list_rep  = None
            self.int_rep = None
    
    def _to_list_rep(self):
        """
        Transfer database representation to list representation. Can only be called when `self.db_rep` is defined.

        Returns
        -------
        profiles_ratio_list_rep : list
            List of list representation of place profile ratio
        """

        profiles_ratio_list_rep = []
        df_db_rep = pd.DataFrame(self.db_rep)
        for profile_type in settings.profile_types:
            current_profile_type_ratio = df_db_rep.loc[df_db_rep['type'] == profile_type,'ratio'].values[0]
            profiles_ratio_list_rep.append(current_profile_type_ratio)
        return profiles_ratio_list_rep
    
    def _to_int_rep(self):
        """
        Transfer list representation to int representation. Can only be called when `self.list_rep` is defined.

        Returns
        -------
        place_profiles_int_rep : list
            List of int representation of place profile ratio
        """

        place_profiles_int_rep = []
        for category_ratio in self.list_rep:
            if not place_profiles_int_rep:
                place_profiles_int_rep = category_ratio
            else:
                temp_place_profiles_int_rep = [x*y for x in place_profiles_int_rep for y in category_ratio ]
                place_profiles_int_rep = temp_place_profiles_int_rep

        return place_profiles_int_rep


class CampaignProfile:
    """
    A class for the purpose of representing place profile-ratio in database, list, and int form.
    """

    def __init__(self,db_represent =None):
        if db_represent is None:
            self.db_rep = None
            self.list_rep = None
            self.int_rep = None
        else:
            self.db_rep = db_represent
            self.list_rep = self._to_list_rep()
            self.int_rep = self._to_int_rep()
            
    def _to_list_rep(self):
        """
        Convert database profiles format to list-representation profiles format. Can only be called when `self.db_rep` is defined.

        Paramters
        ---------

        Returns
        -------
            result_removed_short : list 
                List of list representation of campaign profiles
        """
        profile_types = settings.profile_types
        profile_all_values = settings.profile_all_values
        num_profile_types = settings.num_profile_types

        result = []
        if  not self.db_rep: #if current cammpaign profile is empty(current profile accept all campaigns)
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
        else:
            for i in self.db_rep:
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
                            for value in current_ptype_dict['values']:
                                temp_result_prime.append([value])
                        else:
                            for to_add_value in current_ptype_dict['values']:
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
        return result_removed_short
    
    def _to_int_rep(self):
        """
        Transfer list representation to int representation. Can only be called when `self.list_rep` is defined.

        Returns
        -------
        frozenset(int_rep_list) : frozenset
            A frozenset of int representation of campaign profiles
        """
        map_profile_list_int_rep = settings.map_profile_list_int_rep
        int_rep_list = []
        for list_profile in self.list_rep:
            int_rep_list.append(map_profile_list_int_rep[tuple(list_profile)])
            
        return frozenset(int_rep_list)


class SplitterHelpers:

    @staticmethod
    def get_new_running_days(num_parts, start_day_original_problem, expired_day_original_problem):
        """
        Get new running days of each problem by splitting evenly original running days to number of parts
        
        Returns
        -------
            new_running_days_list: list
                list of all [subproblem_x_start_day(datetime.datetime), subproblem_y_start_day(datetime.datetime)]
        """
        total_running_day = (expired_day_original_problem - start_day_original_problem).days + 1
        new_start_day_list = []
        new_expired_day_list = []
        days_each_part = math.ceil(total_running_day/num_parts)
        next_start_day = start_day_original_problem
        last_day = expired_day_original_problem
        
        for i in range(num_parts):
            cur_start_day = next_start_day
            new_start_day_list.append(cur_start_day)
            cur_expired_day = min(next_start_day + datetime.timedelta(days_each_part), last_day)  # If last day is before expired 
                                                                                                # day acquired by the formula,
                                                                                                # then the current subprob is the last one
                                                                                                # and expired day = the last day instead.
            new_expired_day_list.append(cur_expired_day)
            next_start_day = cur_expired_day + datetime.timedelta(1)

        new_running_days_list = [[start, expired] for start, expired in zip(new_start_day_list, new_expired_day_list)]
        
        return new_running_days_list

    @staticmethod
    def get_campaigns_running_days_info(raw_campaigns,start_date_field_name = 'startDate',expired_date_field_name = 'expiredDate'):
        df_raw_campaigns = pd.DataFrame(raw_campaigns)

        start_day = min(df_raw_campaigns[start_date_field_name])
        exipired_day = max(df_raw_campaigns[expired_date_field_name])
        total_runing_days = (exipired_day - start_day).days + 1
        return start_day, exipired_day, total_runing_days


    @staticmethod
    def update_campaigns_new_place_id(raw_campaigns, current_subproblem_places, sum_estimate_views_places_each_campaign):
        """
        Update place-id of all campaigns in a subproblem. Used in splitter.places_by_days
        
        Parameters
        ----------
            raw_campaigns: list
                list of all raw campaigns, acquire from database queries
            current_subproblem_places:

            sum_estimate_views_places_each_campaign: dict

        Return:
        -------
            raw_campaigns_updated: list
                list of all raw campaigns with place_id updated .E.g. {0: 20, 1: 60}
        """
        current_subproblem_place_ids =[place['placeId'] for place in current_subproblem_places]
        raw_campaigns_updated = []
        for campaign in raw_campaigns:
            campaign_updated = campaign.copy()
            campaign_id = campaign['campaignId']
            # Update place ids
            campaign_updated['placeIds'] = [place_id for place_id in campaign['placeIds'] if place_id in current_subproblem_place_ids]
            # Update run required
            campaign_updated_total_nume = np.sum([np.sum(pd.DataFrame(place['views'])['value']) for place in current_subproblem_places if place['placeId'] in campaign['placeIds']])
            campaign_updated_total_deno = sum_estimate_views_places_each_campaign[campaign_id]
            percent_total =  campaign_updated_total_nume/(campaign_updated_total_deno + 10**-6)
            campaign_updated['total'] = campaign['total']*percent_total
            raw_campaigns_updated.append(campaign_updated)

        return raw_campaigns_updated
    
    @staticmethod
    def get_squarest_split(num_subproblems,num_places,num_running_days):
        """
        Tìm cách chia "vuông nhất" khi chia bài toán theo cả ngày cả địa điểm
        """
        nums_split_by_days = math.ceil((num_running_days*num_subproblems/num_places)**0.5)
        num_split_by_places = math.ceil(num_subproblems/nums_split_by_days)

        num_split = {
            'by_days': nums_split_by_days,
            'by_places': num_split_by_places
        }
        return num_split


class ProcessClassA:
    
    @staticmethod
    def _get_leftover_details(df_sol_b_c, df_x_a, preprocessed_data):
        """
        Trả về 1 dataframe chi tiết về lượng thừa của campaign, place

        Parameters
        ----------
        df_sol_b_c: pandas.DataFrame
            output sau khi chạy solve_single_model
        df_x_a: pandas.DataFrame
        preprocessed_data: preprocessed data
        
        Returns
        -------
        df_leftovers_details: pandas.DataFrame
            dataframe chi tiết về lượng thừa domain, network, tổng lượng chạy campaign
            class A tại từng địa điểm từng ngày có campaign class A
        """
        share_rate = preprocessed_data.places['share_rate'].to_numpy()
        r = np.stack([views_each_place for views_each_place in preprocessed_data.places['views']])
        r = r.T
        t_0 = preprocessed_data.t_0

        df_sol_b_c_network = df_sol_b_c[df_sol_b_c['campaign_id'] <t_0]
        df_sol_b_c_network_grouped = df_sol_b_c_network.groupby(['date','solve_place_id']).agg({"value":"sum"}).reset_index()
        df_sol_b_c_network_grouped = df_sol_b_c_network_grouped.rename(columns = {"value":"value_network"},errors = 'ignore')

        df_sol_b_c_domain = df_sol_b_c[df_sol_b_c['campaign_id'] >=t_0]
        df_sol_b_c_domain_grouped = df_sol_b_c_domain.groupby(['date','solve_place_id']).agg({"value":"sum"}).reset_index()
        df_sol_b_c_domain_grouped = df_sol_b_c_domain_grouped.rename(columns = {"value":"value_domain"},errors = 'ignore')

        estimate_views_network =  r*share_rate
        estimate_views_domain = r*(1 - np.array(share_rate))
        
        df_sol_b_c_grouped = pd.merge(df_sol_b_c_network_grouped,df_sol_b_c_domain_grouped, how = 'outer', on = ['date','solve_place_id'],sort = True)
        df_sol_b_c_grouped= df_sol_b_c_grouped.fillna(0)
        df_sol_b_c_grouped['network_leftovers'] = estimate_views_network.reshape(-1) - df_sol_b_c_grouped['value_network']
        df_sol_b_c_grouped['domain_leftovers'] = estimate_views_domain.reshape(-1) - df_sol_b_c_grouped['value_domain']
        
        df_leftovers_details = pd.merge(df_sol_b_c_grouped, df_x_a, on=['date','solve_place_id'])

        return df_leftovers_details
    
    @staticmethod
    def _add_campaigns_details_to_df(df_leftovers_details,preprocessed_data):
        """
        Thêm trường series_campaign_network_a_solve_ids, series_campaign_domain_a_solve_ids vào df leftovers để biết ngày và địa điêm đấy có
        campaign loại a network và campaign loại a domain nào chạy
        """
        preprocessed_campaigns_a = preprocessed_data.campaigns.loc[preprocessed_data.campaigns['priority'] == 'CLASS_A']
        preprocessed_campaigns_a_dict = preprocessed_campaigns_a.to_dict(orient = 'records')

        series_campaign_network_a_solve_ids = []
        series_campaign_domain_a_solve_ids = []

        for date,solve_place_id in zip(df_leftovers_details['date'],df_leftovers_details['solve_place_id']):
            campaign_network_a_solve_ids = []
            campaign_domain_a_solve_ids = []
            # df_leftovers_details
            for campaign in preprocessed_campaigns_a_dict:
                if solve_place_id in campaign['solve_place_ids'] and date in range (campaign['dates'][0],campaign['dates'][1] +1):
                    if campaign['isNetwork'] == True and not (str(date) in campaign['weights'] and campaign['weights'][str(date)] == 0):
                        campaign_network_a_solve_ids.append(campaign['solve_id'])
                    if campaign['isNetwork'] == False and not (str(date) in campaign['weights'] and campaign['weights'][str(date)] == 0):
                        campaign_domain_a_solve_ids.append(campaign['solve_id'])

            series_campaign_network_a_solve_ids.append(campaign_network_a_solve_ids)
            series_campaign_domain_a_solve_ids.append(campaign_domain_a_solve_ids)

        df_leftovers_details['campaign_network_a_solve_ids'] = series_campaign_network_a_solve_ids
        df_leftovers_details['campaign_domain_a_solve_ids'] = series_campaign_domain_a_solve_ids

        return df_leftovers_details

    @staticmethod
    def _compute_class_a(df_leftovers_details):
        """
        Tính toán lượng view chi tiết mỗi ngày địa điểm.
        """
        df_leftovers_details_non_zero = df_leftovers_details[df_leftovers_details['x_a'] > 10**-6]  #'dates-places has x_a != 0'
        df_leftovers_details_only_zero = df_leftovers_details[df_leftovers_details['x_a'] <= 10**-6]  # 'dates-places has x_a  = 0'
        
        leftovers_details_non_zero_dict = df_leftovers_details_non_zero.to_dict(orient = 'records')
        leftovers_details_only_zero_dict = df_leftovers_details_only_zero.to_dict(orient = 'records')
        sol_campaigns_a = []
        
        for date_place in leftovers_details_non_zero_dict :  # When  x_a >0
            num_class_a_networks = len(date_place['campaign_network_a_solve_ids'])
            num_class_a_domains = len(date_place['campaign_domain_a_solve_ids'])
            if num_class_a_networks != 0 and num_class_a_domains == 0:  # campaigns class A network only
                for campaign_id in date_place['campaign_network_a_solve_ids']:
                    sol_campaigns_a = ProcessClassA._append_class_a(sol_campaigns_a, campaign_id, date_place['solve_place_id'], date_place['date'], date_place['x_a']/num_class_a_networks)

            elif num_class_a_domains != 0 and num_class_a_networks == 0:  # campaigns class A domain only
                for campaign_id in date_place['campaign_domain_a_solve_ids']:
                    sol_campaigns_a = ProcessClassA._append_class_a(sol_campaigns_a, campaign_id, date_place['solve_place_id'], date_place['date'], date_place['x_a']/num_class_a_domains)

            elif num_class_a_domains != 0 and num_class_a_networks != 0:  # both class A network and domain
                if date_place['domain_leftovers'] >=10**-6 and date_place['network_leftovers'] >= 10**-6:  # Both domain and network still have resources
                    for campaign_id in date_place['campaign_domain_a_solve_ids']:
                        sol_campaigns_a = ProcessClassA._append_class_a(sol_campaigns_a, 
                                                                        campaign_id, 
                                                                        date_place['solve_place_id'], 
                                                                        date_place['date'], 
                                                                        date_place['domain_leftovers']/num_class_a_domains)

                    for campaign_id in date_place['campaign_network_a_solve_ids']:
                        sol_campaigns_a = ProcessClassA._append_class_a(sol_campaigns_a, 
                                                                        campaign_id, 
                                                                        date_place['solve_place_id'], 
                                                                        date_place['date'], 
                                                                        date_place['network_leftovers']/num_class_a_networks)

                if date_place['domain_leftovers'] >=10**-6 and date_place['network_leftovers'] <= 10**-6:  # Only domain has resources
                    for campaign_id in date_place['campaign_domain_a_solve_ids']:
                        sol_campaigns_a = ProcessClassA._append_class_a(sol_campaigns_a, campaign_id, date_place['solve_place_id'], date_place['date'], date_place['x_a']/num_class_a_domains)
                        
                if date_place['domain_leftovers'] <= 10**-6 and date_place['network_leftovers'] > 10**-6: # Only network has resources
                    for campaign_id in date_place['campaign_network_a_solve_ids']:
                        sol_campaigns_a = ProcessClassA._append_class_a(sol_campaigns_a, campaign_id, date_place['solve_place_id'], date_place['date'], date_place['x_a']/num_class_a_networks)
                        
            elif num_class_a_domains == 0 and num_class_a_networks == 0:
                sol_campaigns_a = ProcessClassA._append_class_a(sol_campaigns_a, "-1", date_place['solve_place_id'], date_place['date'], date_place['x_a'])
        
        for date_place in leftovers_details_only_zero_dict:  # when xA = 0 
            if len(date_place['campaign_domain_a_solve_ids']) >0:  # have campaign domain type A
                for campaign_id in date_place['campaign_domain_a_solve_ids']:
                    sol_campaigns_a = ProcessClassA._append_class_a(sol_campaigns_a, campaign_id, date_place['solve_place_id'], date_place['date'], 0)
            
            if len(date_place['campaign_network_a_solve_ids']) >0:  # have campaign network type A
                for campaign_id in date_place['campaign_network_a_solve_ids']:
                    sol_campaigns_a = ProcessClassA._append_class_a(sol_campaigns_a, campaign_id, date_place['solve_place_id'], date_place['date'], 0)

        
        return pd.DataFrame(sol_campaigns_a)

    @staticmethod
    def _append_class_a(sol_campaigns_a, campaign_id, solve_place_id, date, value):
        """
        Append class a campaigns to a dict. Used in ProcessClassA._compute_class_a
        """
        sol_campaigns_a.append({
            'campaign_id' : campaign_id,
            'solve_place_id':solve_place_id,
            'date': date,
            'value': value
        })
        
        return sol_campaigns_a

    @staticmethod
    def process_class_a(df_sol_b_c, df_x_a, preprocessed_data):
        """
        Main function to run. Process class a .

        Parameters
        ----------
            df_sol_b_c: pd.DataFrame
            Dataframe solution of all campaigns in class b and c
            df_x_a: pd.DataFrame
            Dataframe of x_a (leftovers after campaigns b,c ran) in each place-day. 

        Returns
        -------
            class_a_soltion: pd.DataFrame
            Dataframe of solution of all campaigns class A.
        """
        df_leftovers_details = ProcessClassA._get_leftover_details(df_sol_b_c, df_x_a, preprocessed_data)
        df_leftovers_details = ProcessClassA._add_campaigns_details_to_df(df_leftovers_details, preprocessed_data)
        class_a_solution = ProcessClassA._compute_class_a(df_leftovers_details)
        return class_a_solution


class Alpha:
    """
    Các công thức tính alpha.
    """
    @staticmethod
    def formula_0(model_ready_data):
        """
        Công thức phức tạp thầy Sơn
        """
        data = model_ready_data
        epsilon = 10**-6
        K = data['K']
        U = data['U']
        T = data['T']
        r = data['r']
        D = data['D']
        CTR = data['CTR']
        d = data['d']
        w = data['w']
        L = data['L']
        B = data['B']
        places_list = np.arange(K)
        campaigns_list = np.arange(T)
        t_u_k_set= [(t,u,k) for t in range(T) for u in range(U) for k in range(K)]
        u_k_set = [(u,k) for u in range(U) for k in range(K)]
        t_0 = data['t_0']
        ratio = data['share_rate']
        priority = data['priority']
        
            # Calculate s_k
        s = []
        s_network = []
        s_domain = []
        for k in range(K):
            s_k_network = 0
            s_k_domain = 0
            for i in B[k]:
                if priority[i] == 'CLASS_B':
                    if i < t_0 :
                        s_k_network += d[i]/(len(L[i])*(D[i][1]+1-D[i][0]))
                    if i >= t_0:
                        s_k_domain += d[i]/(len(L[i])*(D[i][1]+1-D[i][0]))

            s_network.append(s_k_network)
            s_domain.append(s_k_domain)

        # Calculate alpha_tuk
        alpha_network =np.zeros((T,U,K))
        alpha_domain = np.zeros((T,U,K))
        for t in range(T):
            if t < t_0 and priority[t] == 'CLASS_B':
                deno = np.sum([w[t,u_bar]*r[u_bar,k_bar]/s_network[k_bar]
                            for u_bar in range(D[t][0], D[t][1]+1) for k_bar in L[t]])

                if deno !=0:
                    for u in range(D[t][0], D[t][1]+1):
                        for k in L[t]:
                            nume = w[t,u]*r[u,k]/s_network[k]
                            alpha_network[t,u,k] = nume/deno*d[t]
                else:
                    for u in range(D[t][0], D[t][1]+1):
                        for k in L[t]:
                            alpha_network[t,u,k] = 0  # If denominator = 0 then all associated alphas = 0

            if t>=t_0 and priority[t] == 'CLASS_B':
                deno = np.sum([w[t,u_bar]*r[u_bar,k_bar]/s_domain[k_bar] 
                            for u_bar in range(D[t][0], D[t][1]+1) for k_bar in L[t]])
                if deno !=0:
                    for u in range(D[t][0], D[t][1]+1):
                        for k in L[t]:
                            nume = w[t,u]*r[u,k]/s_domain[k]
                            alpha_domain[t,u,k] = nume/deno*d[t]
                else:
                    for u in range(D[t][0], D[t][1]+1):
                        for k in L[t]:
                            alpha_domain[t,u,k] = 0  # If denominator = 0 then all associated alphas = 0

        alpha = alpha_network + alpha_domain
        
        return alpha
    
    @staticmethod
    def formula_1(model_ready_data):
        """
        Tính theo công thức của thầy Sơn + đều theo ngày a Phong
        """
        data = model_ready_data
        epsilon = 10**-9
        K = data['K']
        U = data['U']
        T = data['T']
        r = data['r']
        D = data['D']
        CTR = data['CTR']
        d = data['d']
        w = data['w']
        L = data['L']
        B = data['B']
        places_list = np.arange(K)
        campaigns_list = np.arange(T)
        t_u_k_set= [(t,u,k) for t in range(T) for u in range(U) for k in range(K)]
        u_k_set = [(u,k) for u in range(U) for k in range(K)]
        t_0 = data['t_0']
        ratio = data['share_rate']
        priority = data['priority']
        
        # Calculate d_tu
        d_tu = [d[t]*w[t]/(np.sum(w[t])) for t in range(T)]
        
        # Calculate s_k
        s = []
        s_network = []
        s_domain = []
        for k in range(K):
            s_k_network = 0
            s_k_domain = 0
            for i in B[k]:
                if priority[i] == 'CLASS_B':
                    if i < t_0 :
                        s_k_network += d[i]/(len(L[i])*(D[i][1]+1-D[i][0]))
                    if i >= t_0:
                        s_k_domain += d[i]/(len(L[i])*(D[i][1]+1-D[i][0]))

            s_network.append(s_k_network)
            s_domain.append(s_k_domain)
        
        # Calculate alpha_tuk
        alpha_network =np.zeros((T,U,K))
        alpha_domain = np.zeros((T,U,K))
        for u in range(U):
            for t in range(T):
                if D[t][0] <= u <= D[t][1]:
                    if t < t_0 and priority[t] == 'CLASS_B':
                        deno = np.sum([r[u,k_bar]/s_network[k_bar] for k_bar in L[t]])

                        if deno !=0:
                            for k in L[t]:
                                nume = r[u,k]/s_network[k]
                                alpha_network[t,u,k] = nume/deno*d_tu[t][u]
                        else:
                            for k in L[t]:
                                alpha_network[t,u,k] = 0  # If denominator = 0 then all associated alphas = 0

                    if t>=t_0 and priority[t] == 'CLASS_B':
                        deno = np.sum([r[u,k_bar]/s_domain[k_bar] for k_bar in L[t]])
                        
                        if deno !=0:
                            for k in L[t]:
                                nume = r[u,k]/s_domain[k]
                                alpha_domain[t,u,k] = nume/deno*d_tu[t][u]
                        else:
                            for k in L[t]:
                                alpha_domain[t,u,k] = 0  # If denominator = 0 then all associated alphas = 0

        alpha = alpha_network + alpha_domain
        
        return alpha
    
    @staticmethod
    def formula_2(model_ready_data):
        """
        Tính theo công thức đều theo ngày ez của a Phong
        """

        data = model_ready_data
        epsilon = 10**-9
        K = data['K']
        U = data['U']
        T = data['T']
        r = data['r']
        D = data['D']
        CTR = data['CTR']
        d = data['d']
        w = data['w']
        L = data['L']
        B = data['B']

        # Calculate d_tu: lượng yêu cầu chạy theo ngày của từng campaign
        d_tu = [d[t]*w[t]/(np.sum(w[t])) for t in range(T)] 

        alpha =np.zeros((T,U,K))
        for t in range(T):
            for u in range(D[t][0],D[t][1]+1):
                for k in L[t]:
                    deno = np.sum([r[u,k_bar] for k_bar in L[t]])
                    if deno ==0:
                        alpha[t,u,k] == 0
                    else: 
                        alpha[t,u,k] = d_tu[t][u]*r[u,k]/deno
                    
        return alpha
    
    @staticmethod
    def formula_3(model_ready_data):
        """
        Tính theo công thức đều theo ngày ez của a Phong, nhưng:
        Việc tinh alpha của các campaign cấp B phải xét xem 
        ngày địa điểm đó có bị chiếm bởi campagin cấp C hay không.

        """

        data = model_ready_data
        epsilon = 10**-9
        K = data['K']
        U = data['U']
        T = data['T']
        r = data['r']
        D = data['D']
        CTR = data['CTR']
        d = data['d']
        w = data['w']
        L = data['L']
        B = data['B']
        t_0 = data['t_0']
        priority = data['priority']
        # Compute cl
        cl = np.zeros([T,U,K])
        for t in range(T):
            if priority[t] == "CLASS_C":
                for u in range(D[t][0], D[t][1]+1):
                    for k in L[t]:
                        cl[t,u,k] = 1
        
        # Compute have_c
        have_c_network = np.zeros([U,K])
        have_c_domain = np.zeros([U,K])
        for u in range(U):
            for k in range(K):
                have_c_network[u,k] = np.sum([cl[t,u,k] for t in range(len(cl[:,u,k])) if t <t_0])
                have_c_domain[u,k] = np.sum([cl[t,u,k] for t in range(len(cl[:,u,k])) if t >= t_0])

        # Calculate d_tu: lượng yêu cầu chạy theo ngày của từng campaign
        d_tu = [calculate_d_t_u(d[t],w[t]) for t in range(T)]
        d_tu = np.nan_to_num(d_tu)  # Chuyển những thằng nan về 0, có thể không cần

        alpha =np.zeros((T,U,K))

        for t in range(t_0):
            for u in range(D[t][0],D[t][1]+1):
                for k in L[t] :
                    if have_c_network[u,k] == 0:
                        deno = np.sum([r[u,k_bar] for k_bar in L[t] if have_c_network[u,k_bar] == 0])
                        if deno ==0:
                            alpha[t,u,k] == 0
                        else: 
                            alpha[t,u,k] = d_tu[t][u]*r[u,k]/deno
                            
        for t in range(t_0, T):
            for u in range(D[t][0],D[t][1]+1):
                for k in L[t] :
                    if have_c_domain[u,k] == 0:
                        deno = np.sum([r[u,k_bar] for k_bar in L[t] if have_c_domain[u,k_bar] == 0])
                        if deno ==0:
                            alpha[t,u,k] == 0
                        else: 
                            alpha[t,u,k] = d_tu[t][u]*r[u,k]/deno

        return alpha

    @staticmethod
    def calculate(data,formula = '3'):
        if formula == '0' :
            return Alpha.formula_0(data)
        elif formula == '1':
            return Alpha.formula_1(data)
        elif formula == '2':
            return Alpha.formula_2(data)
        elif formula == '3':
            return Alpha.formula_3(data)
        else:
            print("Invalid formula number!")


class Partition():
    @staticmethod
    def _partition_profile(universe_int_rep, profiles_list):
        """
        Partition profiles in int repprestation.
        Parameters
        ----------
        universe_int_rep: frozenset 
            frozenset of all possible profile in int representation.
        profiles_list: list or pandas.Series 
            list of every campaigns' solver_helpers.CampaignProfile.
        Returns
        -------
        partitioned_sets: list
            list of all partitioned profiles in int rep
        """
        partitioned_sets = [profiles_list[0].int_rep, universe_int_rep - profiles_list[0].int_rep]
        temp_result = partitioned_sets.copy()
        for entry in profiles_list:
            entry = entry.int_rep
            to_add = []
            entry_left = entry.copy()
            for subset_result in temp_result:
                g = entry_left.intersection(subset_result)
                entry_left = entry - g
                if g:
                    to_add.extend([g])
                if subset_result-g:
                    to_add.extend([subset_result-g])

            #to_add.extend(entry_left)
            temp_result = to_add.copy()

        partitioned_sets = temp_result
        return partitioned_sets

    @staticmethod
    def _partition_places(profile_partitioned_sets, preprocessed_places):
        """
        Partition places.

        Parameters
        ----------
            profile_partitioned_sets: list
                list of all partitioned profile
            preprocessed_places: pandas.DataFrame
                a dataframe of preprocessed places

        Returns
        -------
            partitioned_places: list<dict>
                list of all partitioned places
        """

        places_data_df = pd.DataFrame(preprocessed_places)
        places_data_df['profiles_ratio_int'] = [profile.int_rep for profile in places_data_df['profiles_ratio']]
        partitioned_places = []
        k = 0
        places_data_dict  =places_data_df.to_dict(orient= 'records')
        for place in places_data_dict:
            for subset in profile_partitioned_sets:
                cur_place = place.copy()
                # cur_place['views'] = np.round(np.array(cur_place['views'])*np.sum([place['profiles_ratio_int'][int_rep] for int_rep in(list(subset))]))
                cur_place['views'] = np.array(cur_place['views'])*np.sum([place['profiles_ratio_int'][int_rep] for int_rep in(list(subset))])
                cur_place['profiles'] = subset
                cur_place['solve_id_updated'] = k
                k += 1
                partitioned_places.append(cur_place)
                
        df_partitioned_places = pd.DataFrame(partitioned_places)
        df_partitioned_places.rename(columns={'solve_id': 'unpartitioned_solve_id'}, inplace = True)
        df_partitioned_places.rename(columns={'solve_id_updated': 'solve_id'}, inplace = True)
        
        places_mapper_updated = pd.DataFrame(
            {'original_id' : df_partitioned_places['original_id'].to_list(), 'solve_id' : df_partitioned_places['solve_id'].to_list()}
            )
        places_mapper_solve_to_orginal_updated_dict = {
            solve : original for solve, original in  zip(df_partitioned_places['solve_id'],df_partitioned_places['original_id'])
            }
            
        return df_partitioned_places, places_mapper_solve_to_orginal_updated_dict

    @staticmethod
    def _add_partitioned_places(preprocessed_campaigns, partitioned_places):
        """
        Add new solve-place-ids to campaigns dataframe.

        Parameters
        ----------
            preprocessed_campaigns: pandas.DataFrame
                DataFrame of all preprocessed campaigns
            partitioned_place: pandas.DataFrame
                list of all partitioned places

        Returns
        -------
            df_partitioned_campaigns: pandas.DataFrame
                dataframe of all campaigns details with updated model place-id
        """
        df_places = partitioned_places
        campaign_dict = preprocessed_campaigns.to_dict(orient = 'records')

        place_ids_map = [[original_id, profiles, solve_id] for original_id, profiles, solve_id in zip(df_places['original_id'], df_places['profiles'], df_places['solve_id'])]
        partitioned_campaigns =[]
        for campaign in campaign_dict:
            cur_cmpgn = campaign.copy()
            cur_cmpgn['solve_place_ids'] = []
            for place_id in campaign['place_ids']:
                for place in place_ids_map:
                    if place_id == place[0] and list(place[1])[0] in campaign['profiles'].int_rep:
                        cur_cmpgn['solve_place_ids'].append(place[2])

            partitioned_campaigns.append(cur_cmpgn)

        df_partitioned_campaigns = pd.DataFrame(partitioned_campaigns)

        return df_partitioned_campaigns

    @staticmethod
    def partition(universe_int_rep, preprocessed_data):
        """
        Phân hoạch dữ liệu: các địa điểm được phân thành các địa điểm con sao cho mỗi địa điểm chỉ có 1 nhóm user profiles
        Parameters
        -----------
            universe_int_rep: frozenset
                Tập hợp của các profile dưới dạng int
            preprocesseed_data: solver_helpers.PreprocessedData
                Dữ liệu đã được tiền xử lí
        
        Returns
        --------
            partitioned_data: preprocessed.PartitionedData
                Dữ liệu đã đuộc phân hoạch
            places_mapper_updated: dict
                dict để map dữ liệu place {solve_id_updated_1: original_id_1}
        """
        partitioned_data = PartitionedData()
        partitioned_profile_sets = Partition._partition_profile(universe_int_rep, preprocessed_data.campaigns['profiles'])
        partitioned_data.places, places_mapper_updated = Partition._partition_places(partitioned_profile_sets, preprocessed_data.places)
        partitioned_data.campaigns = Partition._add_partitioned_places(preprocessed_data.campaigns, partitioned_data.places)
        
        return partitioned_data, places_mapper_updated


def update_total(old_total, prev_total_unplanned):
    """
    Được dùng trong trường hợp chia nhỏ các bài toán con,
    cập nhật lại lượng chạy yêu cầu của từng chiến dịch.
    
    Parameters
    ----------
    sub_problem

    prev_solve_result
    
    Returns
    -------
    updated_sub_problem
    """
    new_total = np.array(old_total) +np.array(prev_total_unplanned)

    return new_total

def get_total_unplanned(solve_details):
    """
    Tính lượng tài nguyên của từng campaign mà chưa được plan
    """
    docplex_sol = solve_details['solution']
    negative_unplanned_df = docplex_sol.get_value_df(solve_details['z_dict']) # negative vì -z mới là lượng chưa chạy
    unplanned_series = -negative_unplanned_df.sort_values('key')['value']
    unplanned = unplanned_series.to_list()

    return unplanned

def get_num_subproblems(raw_data, config, settings = settings):
    """Tính kích thức bài toán

    Parameters
    ----------
    raw_data : solver_helpers.RawData
    config : file config
    Returns
    -------
    problem_size : int
        Kích thước bài toán
    """
    # TODO
    profile_list = [CampaignProfile(campaign['profiles']) for campaign in raw_data.campaigns]
    num_profiles_group = len(Partition._partition_profile(settings.universe_int_rep,profile_list))  # Number of profiles group
    # logging.info(f"problem {raw_data.campaigns[0]['problemId']} has {num_profiles_group} profile groups.")
    problem_start_date = min(pd.DataFrame(raw_data.campaigns)['startDate'])
    problem_end_date =max(pd.DataFrame(raw_data.campaigns)['expiredDate'])
    problem_total_days = (problem_end_date - problem_start_date).days + 1
    problem_size = len(raw_data.campaigns) * len(raw_data.places) * problem_total_days * num_profiles_group

    logging.info(f"problem size: approx {problem_size}")
    num_subproblems = math.ceil(problem_size/config.problem_max_size)  # Number of subproblems
    return num_subproblems

def query_raw_data(problem_id):
    """
    Lấy dữ liệu thô từ database

    Parameters
    ----------
    problem_id : string
        Problem id
    """
    raw_data = RawData()
    raw_data.campaigns = list(odm.ASCampaign.objects(problemId = problem_id).as_pymongo()).copy()
    raw_data.places  = list(odm.ASPlace.objects(problemId = problem_id).as_pymongo()).copy()
    try:
        lower_ratio = list(odm.ASProblemInfo.objects(id = problem_id).as_pymongo()).copy()[0]['lowerRatio']
    except:
        lower_ratio = 0

    return raw_data, lower_ratio

def process_standalone_problem(raw_data):
    """Xử lí dữ liệu nếu bài toán kiểu standalone

    Parameters
    ----------
    raw_data : solver_helpers.RawData

    Returns
    -------
    raw_data_standalone : solver_helpers.RawData
    """
    raw_data_standalone = copy.deepcopy(raw_data)
    raw_data_standalone.campaigns = utils.remove_network_campaigns(raw_data_standalone.campaigns)
    logging.info('Network campaigns removed.')
    raw_data_standalone.places = utils.set_share_rate_zero(raw_data_standalone.places)
    logging.info('All places\' share rate have been set to 0.')
    
    return raw_data_standalone

def solve_b_c_result_to_df(solve_details):
    docplex_sol = solve_details['solution']
    x_dict = solve_details['x_dict']
    if x_dict:  # If x_dict is not empty
        df_sol_b_c = docplex_sol.get_value_df(x_dict, key_column_names=['campaign_id', 'date', 'solve_place_id'])
    return df_sol_b_c
    
def insert_solved_to_db(original_data):
    # me.connect(db =settings.db_name, host = cfg.connection_str, tz_aware = True)
    original_data['createDate'] = datetime.datetime.utcnow()  # Thêm trường ngày tạo để tự động hủy khi hết thời gian
    original_data_dict = original_data.to_dict(orient= 'records')
    instances = [odm.ASResult(**data) for data in original_data_dict]
    try:
        odm.ASResult.objects.insert(instances, load_bulk = False)
    except Exception as e:
        logging.info("Some thing wrong with inserting")
        raise(e)


def update_w(model_ready_data, have_c_network, have_c_domain):
    """Cập nhật trọng số cho các campaign:
    Nếu 1 campaign type B bất kì có 1 ngày mà tất cả các địa điểm của nó
    có campaign cấp C chạy, coi như w ngày hôm đó bằng 0.

    Parameters
    ----------
    model_ready_data : list
    have_c_network: np.array()
        Ma trận tồn tại campaign c: have_c[u,k] = 1 nếu ngày u địa điểm k
        có campaign type C network chạy
    have_c_domain : np.array()
        Tương tự have_c_network nhưng cho domain 
    """
    T = model_ready_data['T']
    t_0 = model_ready_data['t_0']
    D = model_ready_data['D']
    L = model_ready_data['L']
    w = model_ready_data['w']
    priority = model_ready_data['priority']

    if 'CLASS_C' not in priority:
        return w  # Không cần tính toán thay đổi nếu ko có class C

    not_have_c_network = 1- have_c_network # Ma trận không có campaign c
    not_have_c_domain = 1 - have_c_domain

    for t in range(T):
        if priority[t] == 'CLASS_B':
            if t < t_0:
                days_filled_by_c= np.sum(not_have_c_network[:,L[t]], axis = 1)

            else:
                days_filled_by_c= np.sum(not_have_c_domain[:,L[t]], axis = 1)
                
            for u in range (D[t][0],D[t][1] + 1):
                if days_filled_by_c[u] == 0: 
                    w[t][u] = 0
                # Giải thích:  Nếu days_filled_by_c[u] = 0 tức tất cả giá trị của
                # not_have_c network (hoặc domain) vào ngày u của các địa điểm
                # mà campaign t chạy đều bằng 0 , điều này đồng nghĩa với tất
                #  cả các địa điểm vào ngày u đều có campaign cấp C chạy.
    return w

def calculate_d_t_u(d,w):
    """TÍnh d_t_u tức lượng view mong muốn chạy của campaign từng ngày

    Parameters
    ----------
    d : int
        Tổng lượng view mong muốn chạy của campaign
    w : np.array()
        mảng chưa trọng số theo từng ngày của campaign, w[i] là trọng số ngày i

    Returns
    -------
    d_t_u:np.array
        mảng lượng view mong muốn từng ngày d_t_u[u] là lượng chạy mong muốn ngày u
    """

    total_w = np.sum(w)
    if total_w == 0:
        d_t_u = np.zeros_like(w)
        return d_t_u

    d_t_u = d*w / total_w
    return d_t_u

def solve_z_to_df_unplanned(solve_details, problem_id, campaigns_mapper, priority_list):
    docplex_sol = solve_details['solution']
    z_dict = solve_details['z_dict']
    df_sol_z = docplex_sol.get_value_df(z_dict, key_column_names='campaignId')
    class_c_solve_id = [i for i, x in enumerate(priority_list) if x == "CLASS_C"]
    df_sol_z = df_sol_z.query('campaignId not in @class_c_solve_id') # Loại bỏ các campaign type c
    df_sol_z['value'] = -df_sol_z.loc[:,['value']] 
    df_unplanned = df_sol_z.rename(columns = {"value":"unplanned"}, errors = 'ignore')
    # del df_sol_z['value']
    df_unplanned['campaignId'] = df_unplanned['campaignId'].apply(lambda x : campaigns_mapper[x]) # Reversemap
    df_unplanned['createDate'] = datetime.datetime.utcnow()
    df_unplanned['problemId'] = problem_id
    df_unplanned = df_unplanned[df_unplanned['campaignId'] != "-10"] # Remove fake campaign
    return df_unplanned

def insert_unplanned_to_db(df_unplanned: pd.DataFrame):
    unplanned_dict = df_unplanned.to_dict('records')
    instances = [odm.ASUnplanned(**data) for data in unplanned_dict]
    if instances:
        try:
            odm.ASUnplanned.objects.insert(instances, load_bulk = False)
            # logging.info("Inserted unplanned to database.")
        except Exception as e:
            logging.info("Some thing wrong with inserting unplanned")
            raise(e)