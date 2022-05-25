import config as cfg
from solver import solver_helpers
from solver.model_solver import solve_sub_prob
import settings

import logging
import multiprocessing as mp
import mongoengine as me

def solve_subproblem_worker(solve_queue : mp.Queue(),   insert_db_queue: mp.Queue()):
    while True:
        problem_id, subproblem_data, lower_ratio, eveness_priority, method, subproblems_left = solve_queue.get()
        try:
            solved, unplanned,_ = solve_sub_prob(subproblem_data,lower_ratio = lower_ratio, evenness_priority = eveness_priority, method = method)
            insert_db_queue.put((problem_id, solved, unplanned, subproblems_left))
        except Exception as e:
            ex = Exception(str(e))
            subproblems_left.set_exception(ex)
            raise e


def insert_db_worker(insert_db_queue: mp.Queue(), connection_str = cfg.connection_str):
    me.connect(db = settings.db_name, host = connection_str, tz_aware = True)
    while True:
        problem_id, solved, unplanned, subproblems_left = insert_db_queue.get()
        try:
            solver_helpers.insert_solved_to_db(solved)
            solver_helpers.insert_unplanned_to_db(unplanned)
            logging.info(f"Inserted {problem_id} to database.")
            subproblems_left.decrease_by_1()
            logging.info(f"{problem_id} has {subproblems_left.get_subproblems_left()} subproblem lefts")
        except Exception as e:
            ex = Exception(str(e))
            subproblems_left.set_exception(ex)
            raise e