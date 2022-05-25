import sys
sys.path.append('../')
import logging
import math
import numpy as np

#local
from solver import solver_helpers
from solver.solver_helpers import SplitterHelpers, SubProblemRawData
import utils


class Splitter:

    @staticmethod
    def split_by_places(num_subproblems, raw_data):
        
        """
        Split places into subplace groups, each problem will solve on each subplace group.
        By letting number of places divided by number of sub-problems (places_num/num_subproblems), we get the number 
        of places in each sub-problem.
        
        Parameters:
        -----------
            num_subproblems: int
                number of problems
            raw_data: solver_helpers.RawData

        Returns:
        --------
            subproblems_places: list<list>
                each element in subproblems_places is a list of all places of a subproblem.
        """
        
        logging.info("Split by places.")
        raw_places = raw_data.places
        places_num = len(raw_places)
        places_each_subproblem = math.ceil(places_num/num_subproblems) # round up
        count = 0
        subproblems_places = []
        cur_subproblem = []
        for place in raw_places:
            count += 1
            cur_subproblem.append(place)
            
            if count % places_each_subproblem == 0:
                subproblems_places.append(cur_subproblem)
                cur_subproblem = []
            
        if cur_subproblem:  # If current subproblem's places list is not empty
            subproblems_places.append(cur_subproblem)

        estimate_views_places_each_campaign = utils.sum_estimate_views_places_each_campaign(raw_data.campaigns, raw_data.places)  # Total estimate views of all places
                                                                                                                                  #  of each campaigns
        all_subproblems = []
        # Update campaigns
        for subproblem_raw_places in subproblems_places:
            subproblem_raw_data = SubProblemRawData()
            subproblem_raw_data.places = subproblem_raw_places
            # Update_campaigns_new_place_id
            subproblem_raw_data.campaigns = SplitterHelpers.update_campaigns_new_place_id(raw_data.campaigns, subproblem_raw_places, estimate_views_places_each_campaign)
            # subproblem_raw_data.share_rate = raw_data.share_rate
            all_subproblems.append(subproblem_raw_data)

        return all_subproblems


    @staticmethod
    def split_by_days(num_subproblems, raw_data):
        
        print("Split by days.")
        start_day, expired_day, total_running_days = SplitterHelpers.get_campaigns_running_days_info(raw_data.campaigns)
        new_running_days_list = SplitterHelpers.get_new_running_days(num_subproblems, start_day, expired_day)
        all_subproblems = [] 
        for running_days in new_running_days_list:
            cur_subproblem_data = solver_helpers.SubProblemRawData()
            cur_subproblem_campaigns = []
            cur_subproblem_places = []
            for campaign in raw_data.campaigns:
                start_day_cur_campaign = campaign['startDate']
                expired_day_cur_campaign = campaign['expiredDate']


                if running_days[1] < start_day_cur_campaign:    # If expired day of current running days group < start day of current
                    continue                                    # campaign, then skip that running days group entirely.          
                if running_days[0] > expired_day_cur_campaign:  # If start day of current running days group > expired day of current
                    continue                                    # campaign, then skip that running days group entirely. 
                cur_subcampaign = campaign.copy()
                cur_subcampaign['startDate'] = max(running_days[0], start_day_cur_campaign)
                cur_subcampaign['expiredDate'] = min(running_days[1], expired_day_cur_campaign)
                cur_subproblem_campaigns.append(cur_subcampaign)

            if len(cur_subproblem_campaigns) == 0:  # If there is no campaign in current running_days, then break
                break

            cur_subproblem_data.campaigns = cur_subproblem_campaigns.copy()
            cur_subproblem_data.places = raw_data.places.copy()
            # cur_subproblem_data.share_rate = raw_data.share_rate
            all_subproblems.append(cur_subproblem_data)
            
        return all_subproblems

    
    @staticmethod
    def split_by_places_days(num_subproblems, raw_data):
        print("Split by both days and places.")

        start_day, expired_day, total_running_days = SplitterHelpers.get_campaigns_running_days_info(raw_data.campaigns)
        num_places = len(raw_data.places)
        num_split = SplitterHelpers.get_squarest_split(num_subproblems,num_places, total_running_days)
        num_subproblems = num_split['by_days'] * num_split['by_places']

        print("Re-split into", num_subproblems, " problems!")
        print("\t Place dimension : ", num_split['by_places'], " parts.") 
        print("\t Day dimension : ", num_split['by_days'], " parts.")

        all_subproblems_splitted_by_days = Splitter.split_by_days(num_split['by_days'], raw_data)
        all_subproblems = []
        for subproblem in all_subproblems_splitted_by_days:
            all_subproblems.extend(Splitter.split_by_places(num_split['by_places'], subproblem))
        #all_subproblems.extend([Splitter.split_by_places( num_split['by_places'],subproblem) for subproblem in all_subproblems_splitted_by_days])

        return all_subproblems

split_methods = {
    'by_places': Splitter.split_by_places,
    'by_days' : Splitter.split_by_days,
    'by_places_days':Splitter.split_by_places_days
}

def split(num_subproblems, raw_data, method, methods_dict = split_methods):
    subproblems_list = methods_dict[str(method)](num_subproblems, raw_data)
    return subproblems_list
