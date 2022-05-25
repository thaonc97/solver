db_name = "acmSolver"
place_stat_collection = "asPlace"
share_rate_collection = "asShareRate"
campaign_collection = "asCampaign"
output_collection = "asSolveResult"
problem_info_collection = "asProblemInfo"
unplanned_collection = "asUnplanned"
#User profiles
profile_types = ['GENDER','AGE']
profile_all_values = {'GENDER':[0,1,2],'AGE':[0,1,2,3,4,5,6,7]}
num_profile_types = 2  # GENDER and AGE
all_list_profiles = [[0, 0],
 [0, 1],
 [0, 2],
 [0, 3],
 [0, 4],
 [0, 5],
 [0, 6],
 [0, 7],
 [1, 0],
 [1, 1],
 [1, 2],
 [1, 3],
 [1, 4],
 [1, 5],
 [1, 6],
 [1, 7],
 [2, 0],
 [2, 1],
 [2, 2],
 [2, 3],
 [2, 4],
 [2, 5],
 [2, 6],
 [2, 7]]  # Get this by running `utils.get_all_possible_list_profile(cfg.profile_all_values.values())`
map_profile_list_int_rep = {(0, 0): 0,
 (0, 1): 1,
 (0, 2): 2,
 (0, 3): 3,
 (0, 4): 4,
 (0, 5): 5,
 (0, 6): 6,
 (0, 7): 7,
 (1, 0): 8,
 (1, 1): 9,
 (1, 2): 10,
 (1, 3): 11,
 (1, 4): 12,
 (1, 5): 13,
 (1, 6): 14,
 (1, 7): 15,
 (2, 0): 16,
 (2, 1): 17,
 (2, 2): 18,
 (2, 3): 19,
 (2, 4): 20,
 (2, 5): 21,
 (2, 6): 22,
 (2, 7): 23}  # Get this by running `utils.map_profile_list_int(all_list_profiles)`
universe_int_rep =  frozenset({0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23})  # Get this by running `frozenset([value for value in map_profile_list_int_rep.values()])`