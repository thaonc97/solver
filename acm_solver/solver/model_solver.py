# local
import config as cfg
import exceptions_handler
from orm import odm
from solver import cplex_models, solver_helpers, model_ready_data_converter, reverse_convert, splitter
from solver.solver_helpers import  ProcessClassA, get_num_subproblems
from solver.preprocess import PreprocessConverter
import utils

#others
import logging
import multiprocessing as mp
import os
import pandas as pd
import time


def solve_prob(problem_id, 
               config, 
               solve_queue : mp.Queue(),
               split_method = "by_places", 
               alpha_formula = '3', 
               adjust_start_date = True,
               evenness_priority = 1,
               method = 'TWO_STEPS'):
    """Module chính giải quyết bài toán phân bố tài nguyên của Service Acm Solver

    Parameters
    ----------
    problem_id : str
        problem id
    config : python file
        file chứa các config, thưởng nằm ở ../
    split_method : str, optional
        Cách chia các bài toán con, by default "by_places"
    alpha_formula : str, optional
        Công thức tinh alpha trong mô hình tối ưu được giải bằng CPLEX, by default '2'
    adjust_start_date : bool, optional
        Nếu True, ngày bắt đầu của các campaign sẽ là hôm nay nếu ngày bắt đầu trong db 
        của campaign đấy nhỏ hơn ngày hôm nay, by default True
    """

    full_tik = time.time()
    logging.info(f"Start solving for problem with id: {problem_id}")    
    raw_data, lower_ratio = solver_helpers.query_raw_data(problem_id)

    raw_data = utils.CorrectRawData.correct(raw_data, adjust_start_date)
    exceptions_handler.validate_input(raw_data, problem_id)
    
    # Check problem type 
    problem_type = 'NETWORK_PROBLEM'
    try:
        problem_type  = odm.ASProblemInfo.objects(id = problem_id).as_pymongo()[0]['problemType']
    except:
        logging.info("Không có problem info, có thể đang sử dụng dữ liệu test.")
        pass
    logging.debug(f"Problem type:{problem_type}")

    if problem_type == "STANDALONE_PROBLEM":
        raw_data = solver_helpers.process_standalone_problem(raw_data)
        # Kiểm tra sau khi xử lí bài toán standalone có còn campaign nào không
        exceptions_handler.check_no_campaign(raw_data.campaigns, problem_id) 

    # Nếu không có dữ liệu campaign type B,C thêm 1 campaign giả type B với total ~ 0
    if utils.no_type_b_or_c(raw_data.campaigns) == True:  
        raw_data.campaigns.append(utils.create_temp_campaign(problem_id, raw_data))
    
    approx_num_subproblems = get_num_subproblems(raw_data, config)
    logging.info(f"Splitting into approx {str(approx_num_subproblems)} problem(s)!")
    all_subproblems_data = splitter.split(approx_num_subproblems, raw_data, split_method)
    num_subproblems = len(all_subproblems_data)
    logging.info(f"Splitted {problem_id} into {num_subproblems} problem(s)!")

    subproblems_left = mp.Manager().SolveStatus(num_subproblems) # registered in `app.py`
    for subproblem_data in all_subproblems_data:
        solve_queue.put((problem_id, subproblem_data, lower_ratio, evenness_priority, method, subproblems_left))
        
    timeout= config.subprocess_timeout
    count = 0
    while (not subproblems_left.get_exception() and not subproblems_left.get_subproblems_left()==0 and not count >= timeout): 
        count = count + 1       
        time.sleep(1)
        
    if subproblems_left.get_subproblems_left()==0:
        full_tok = time.time()
        logging.info(f'All Done! Problem {problem_id} solved, total time = {full_tok - full_tik}.')
        return
    elif(count>=timeout):
        raise Exception(f"Timemout when solve problem {problem_id}")
    else:
        e = subproblems_left.get_exception()
        raise e


def solve_sub_prob(subproblem_data,
                   alpha_formula = '3',
                   lower_ratio = 0,
                   evenness_priority = 1,
                   method = 'TWO_STEPS'):
    """Giải bài toán con

    Parameters
    ----------
    subproblem_data : solver_helpers.SubProblem
        Dữ liệu raw bài toán con
    alpha_formula : str, optional
        Công thức tính alpha, by default '3'
    lower_ratio : int, optional
        Cận dưới chặn campaign, by default 0

    Returns
    -------
    None
        
    """
    logging.basicConfig(level = logging.INFO)
    logging.info(f'Start solving in pid {os.getpid()}')
    problem_id = subproblem_data.campaigns[0]['problemId']  # Get problem_id
    # If there is no campaign type B or C, add a fake campaign B with total approx 0
    if utils.no_type_b_or_c(subproblem_data.campaigns) == True:
        subproblem_data.campaigns.append(utils.create_temp_campaign(problem_id,subproblem_data))

    tik = time.time()
    # Preprocess and get model-ready data
    preprocessed_data, mapper = PreprocessConverter.convert_from_raw_data(subproblem_data)
    model_ready_data = model_ready_data_converter.convert_from_processed_data(preprocessed_data)
    solve_details = cplex_models.solve_b_c(model_ready_data,  
                              alpha_formula,
                              l = lower_ratio, 
                              export_model = False,
                              evenness_priority = evenness_priority,
                              method = method)  # Solve B,C

    # Solve A
    docplex_sol = solve_details['solution']
    x_dict = solve_details['x_dict']
    x_a_dict = solve_details['x_a_dict']

    df_x_a = docplex_sol.get_value_df(x_a_dict, 'x_a', ['date','solve_place_id'])  # Data Frame of x_a
    if x_dict:
        df_sol_b_c = docplex_sol.get_value_df(x_dict, key_column_names=['campaign_id', 'date', 'solve_place_id'])
    df_sol_a = ProcessClassA.process_class_a(df_sol_b_c, df_x_a, preprocessed_data)
    logging.info(f"Solved in pid {os.getpid()}.")

    # Reverse mapping
    original_data_b_c = reverse_convert.convert_back_to_db_represent(problem_id, df_sol_b_c, mapper)
    if df_sol_a.empty == False:  # Check if there are any class A will run
        original_data_a =  reverse_convert.convert_back_to_db_represent(problem_id, df_sol_a, mapper, skip_zero = False)
        original_data = pd.concat([original_data_a,original_data_b_c])
    else:
        original_data = original_data_b_c

    original_data = original_data[original_data['campaignId'] != "-10"]  # Remove fake campaign
    logging.info("Reverse mapped!")
    unplanned_data = solver_helpers.solve_z_to_df_unplanned(solve_details, problem_id, mapper.campaigns_mapper, model_ready_data['priority'])
    obj_function = docplex_sol.objective_value
    obj_function_data = {
        'problemId': problem_id,
        'objectiveFunctionValue': obj_function
    }
    tok = time.time()
    logging.debug(f"Elapsed time in pid {os.getpid()} = {tok - tik} \n")
    return original_data, unplanned_data, obj_function_data