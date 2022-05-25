import numpy as np
import pandas as pd 

def convert_from_processed_data(processed_data):
    """
    Get model ready data from processed data.

    Parameters
    ----------
    processed_data: solver_helpers.PreprocessData

    Returns
    -------
    result: dict
        dictionary of model parameters:
        U: number of running-days.
        T: number of campaigns.
        K: number of places.
        D: running days of campaigns. D[9] = [3,20] means the starting day of campaign 9 is 3 and expired day is 20.
        d: required 'views' of every campaign.
        r: predicted views. r[u,k] = 100 means predicted views at place k on day u is 100.
        CTR: CTR[t,k] is CTR of campaign t at place k.
        w: weight dict of each campaign.
        L: L[t] is a list of  model-place id  of campaign t.
        B: B[k] is a list of campaign ran at place k.
        t_0: last index of network campaigns. i.e. {1,2,...,t_0} are the indices of Network campaigns.
        share_rate: share_rate.

    """

    
    processed_campaigns_drop_class_a = processed_data.campaigns[processed_data.campaigns['priority'] != 'CLASS_A']  # Drop campaigns in class A
    processed_campaigns_dict = pd.DataFrame(processed_campaigns_drop_class_a).to_dict(orient = 'list')
    processed_campaigns_non_drop_a_dict = processed_data.campaigns.to_dict(orient = 'list')
    processed_places_dict = pd.DataFrame(processed_data.places).to_dict(orient = 'list')
    t_0 = processed_data.t_0
    
    share_rate = processed_places_dict['share_rate']
    D = processed_campaigns_non_drop_a_dict['dates']
    U = np.max(np.array(D)[:,1]) - np.min(np.array(D)[:,0]) +1 
    L = [np.array(place_id) for place_id in processed_campaigns_dict['solve_place_ids']] 
    T = len(processed_campaigns_dict['solve_id'])
    K = len(processed_places_dict['solve_id'])
    d = processed_campaigns_dict['total']
    priority = processed_campaigns_dict['priority']
    r_ku = processed_places_dict['views'] 
    r =np.array(r_ku).T #Transpose r_ku to get r_uk
    
    CTR_percent_k = processed_places_dict['ctrs']
    CTR_t = processed_campaigns_dict['type']
    CTR = np .zeros((T,K)) #CTR_t_k
    for t in range(T):
        CTR[t] = [CTR_percent_k[k][CTR_t[t]] for k in range(K)]

    try:
        share_type = processed_places_dict['share_type'] # sharetype
    except:
        print("Có vẻ dữ liệu cũ chưa có share type, đặt toàn bộ là soft")
        share_type = [0 for _ in range(K)]
    
    #Generate B_k
    B =[]
    for i in range(K):
        current_place_campaign_list=[]
        for j in range(len(L)) :
            if i in L[j]:
                current_place_campaign_list.append(j)
        B.append(current_place_campaign_list)

    #Calculate w
    w = np.zeros((T,U))
    for t in range(T):
        for u in range(D[t][0],D[t][1]+1):
            if str(u) in processed_campaigns_dict['weights'][t]:
                w[t,u] = processed_campaigns_dict['weights'][t][str(u)]
            else:
                w[t,u] = 10

    result = {
        "U":U,  
        "T":T,  
        "K":K,  
        "D": D,  
        "d":d,  
        "r": r,  
        "CTR": CTR,  
        "w": w,  
        "L": L,  
        "B": B,
        "t_0":t_0,
        "share_rate": share_rate,
        "priority": priority,
        "share_type": share_type
    }

    return result