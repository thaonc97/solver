import pandas as pd


def convert_back_to_db_represent(problem_id, df_sol, mapper, skip_zero = True):
    """
    Convert solve result về một DataFrame có dạng giống với collections ASSolveResult
    
    Parameters
    ----------
    problem_id :string
    df_sol: pandas.DataFrame 
        dataframe của solution, các cột  lần lượt là 'campaign_id', 'date', 'model_place_id', value
    mapper: solver_helpers.Mapper
    skip_zero: bool, default True
        Nếu True: bỏ qua các dòng có value = 0 (tức campaign không chạy ở địa điểm và ngày đấy)
    """

    if skip_zero == True:
        df_sol = df_sol[df_sol['value'] != 0]

    dict_sol = df_sol.to_dict(orient= 'records')
    list_original_id = []
    
    for sol in dict_sol:
        temp_original = {}
        temp_campaign_id = sol['campaign_id']
        temp_date = sol['date']
        temp_place_id = sol['solve_place_id']

        temp_original['problemId'] = problem_id
        temp_original['campaignId'] = mapper.campaigns_mapper[temp_campaign_id]
        temp_original['placeId'] = mapper.places_mapper[temp_place_id]
        temp_original['date'] = mapper.date_int_mapper['int_to_date'][temp_date]
        temp_original['view'] = sol['value']

        list_original_id.append(temp_original)
    
    if list_original_id:  # If the list is not empty
        df_original = pd.DataFrame(list_original_id)
        df_original_grouped = df_original.groupby(['problemId','campaignId','placeId','date'])['view'].sum().reset_index()
    else:
        df_original_grouped = pd.DataFrame(columns= ['problemId','campaignId','placeId','date','view'])
    
    return df_original_grouped