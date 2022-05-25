#Import for server
from concurrent import futures
import datetime
import grpc
from google.protobuf.json_format import MessageToDict
from google.protobuf.wrappers_pb2 import StringValue
from google.protobuf.empty_pb2 import Empty
import logging
import mongoengine as me
import multiprocessing as mp
import time

import config as cfg
import exceptions_handler
from generated import acm_solver_pb2, acm_solver_pb2_grpc, acm_base_pb2
from orm import odm
from solver import model_solver
from solver.solver_helpers import SolveStatus
import settings
import utils
import workers

solve_queue = mp.Queue()
insert_db_queue = mp.Queue()

def mass_insert_to_db(data_stream, data_type, problem_id):
    """
    Mass insert data from data_stream to db
    Parameters:
    -----------
        data_stream: request_iterator
        data_type :'campaign' or 'place'
    """
    if data_type == 'campaign':
        doc_object = odm.ASCampaign
    elif data_type == 'place':
        doc_object = odm.ASPlace

    to_insert_list = []
    count = 0
    for data in data_stream:
        count += 1
        if data_type == 'place':
            data_dict = MessageToDict(data,including_default_value_fields= True)
            for view_info in data_dict['views']:
                view_info['date'] = utils.remove_time_str_datetime(view_info['date'])
            data_dict['createDate'] = datetime.datetime.utcnow()
        
        elif data_type == 'campaign':
            data_dict = MessageToDict(data,including_default_value_fields= True)
            data_dict['startDate'] = utils.remove_time_str_datetime(data_dict['startDate'])
            data_dict['expiredDate'] = utils.remove_time_str_datetime(data_dict['expiredDate'])
            for weight_info in data_dict['weights']:
                weight_info['date'] = utils.remove_time_str_datetime(weight_info['date'])
            message_profile = data_dict['profiles']
            data_dict['profiles'] = utils.convert_p_profile_to_db_profile(message_profile)
            data_dict['campaignType'] = data_dict['type']
            data_dict['type'] = acm_base_pb2.CampaignType.Value(data_dict['type'])  # Convert campaign type from string to respected int
            del data_dict['type']

            data_dict['placeIds'] = [int(place_id) for place_id in data_dict['placeIds']]  # google.protobuf.json_format.MessageToDict chuyển 1 list<int64> thành 
                                                                                           # thành 1 list<string> nên phải chuyển về dạng int
            data_dict['createDate'] = datetime.datetime.utcnow()

        data_dict['problemId'] = problem_id

        data_to_insert = doc_object(**data_dict)
        to_insert_list.append(data_to_insert)

    doc_object.objects.insert(to_insert_list)

class AcmSolverServicer(acm_solver_pb2_grpc.AcmSolverServicer):
    def __init__(self):
        pass

    def SetPlaces(self, request_iterator, context):  # Done
        for stream in request_iterator:
            problem_id = stream.problem_id
            # utils.delete_from_db("asPlace",problem_id)  # Delete data from db if existed
            mass_insert_to_db(stream.places,'place',problem_id)

        try:
            logging.info(f"Places set for problem id {problem_id}")
        except:
            logging.info("No place stream was sent!")
        response = Empty()
        return response

    def SetCampaigns(self,request_iterator,context):  # Done
        for stream in request_iterator:
            problem_id = stream.problem_id
            # utils.delete_from_db("asCampaign",problem_id)  # Delete data from db if existed
            mass_insert_to_db(stream.campaigns,'campaign',problem_id)
        
        try:
            logging.info(f"Campaigns set for problem id {problem_id}")
        except:
            logging.info("No campaign stream was sent!")
        response = Empty()
        return response

    def InitProblem(self,request,context):
        # id_generated = uuid.uuid4()
        problem_type = (acm_solver_pb2.ProblemType.Name(request.type))
        problem_name = request.name
        create_date = datetime.datetime.utcnow()
        lower_ratio = request.lower_ratio
        prob_info = odm.ASProblemInfo(name = problem_name, problemType = problem_type, createDate = create_date, lowerRatio = lower_ratio)
        prob_info.save()
        id_to_return = str(prob_info.id)
        # id_to_return = str(problem_type) +"_" + str(id_generated)
        response = StringValue(value = id_to_return)
        return response
    
    @exceptions_handler.handle_grpc_error_decorator
    def Solve(self,request,context):
        try:
            
            problem_id = request.problem_id
            evenness_priority = request.evenness_priority
            logging.info(f'Deleting solved and unplanned in problem {problem_id}')
            utils.delete_from_db("asSolveResult",problem_id)  # Delete data from db if existed
            utils.delete_from_db("asUnplanned",problem_id)
            split_method = "by_places"
            alpha_formula = '3'
            model_solver.solve_prob(problem_id, 
                                    cfg,
                                    solve_queue,
                                    split_method,
                                    alpha_formula =  alpha_formula, 
                                    adjust_start_date = True, 
                                    evenness_priority =  evenness_priority,
                                    method = cfg.solve_method)
            to_return = Empty()
        except Exception as e:
            raise e
        return  to_return
    
    def GetResults(self, request, context):
        problem_id = request.value
        results = list(odm.ASResult.objects(problemId = problem_id).as_pymongo()).copy()
        stream = []
        count = 0
        all_response = acm_solver_pb2.GetResultsResponse()
        for result in results:
            count += 1
            response = acm_solver_pb2.ASResult()
            response.problem_id = result['problemId']
            response.campaign_id = result['campaignId']
            response.place_id = result['placeId']
            response.date.FromDatetime(result['date'])
            response.view = result['view']
            all_response.results.append(response)
            if count % cfg.max_records_per_stream == 0 :
                stream.append(all_response)
                all_response = acm_solver_pb2.GetResultsResponse()
        
        stream.append(all_response)
        for result in stream:
            yield result

    def GetUnplanned(self, request, context):
        problem_id = request.value
        results = list(odm.ASUnplanned.objects(problemId = problem_id).as_pymongo()).copy()
        all_response = acm_solver_pb2.GetUnplannedResponse()
        for result in results:
            response = acm_solver_pb2.UnplannedView()
            response.problem_id = result['problemId']
            response.campaign_id = result['campaignId']
            response.unplanned = result['unplanned']
            all_response.unplanned_views.append(response)

        return all_response
            

def serve():
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO, datefmt='%d-%b-%y %H:%M:%S')

    me.connect(db =settings.db_name, host = cfg.connection_str, tz_aware = True)    
    solve_pool = mp.Pool(cfg.solve_max_process, 
                         workers.solve_subproblem_worker,
                         (solve_queue, insert_db_queue))
    insert_db_process = mp.Process(target =  workers.insert_db_worker, args= (insert_db_queue,))
    insert_db_process.start()
    mp.Manager().register('SolveStatus',SolveStatus)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=cfg.max_grpc_worker))
    acm_solver_pb2_grpc.add_AcmSolverServicer_to_server(
        AcmSolverServicer(), server)
    server.add_insecure_port(f'[::]:{cfg.port}')
    server.start()
    logging.info(f'Server started. Listening on port {cfg.port}.')
    logging.info(cfg.connection_str)
    logging.info(f'Number of solve processes: {cfg.solve_max_process}')
    logging.info(f"solve method: {cfg.solve_method}")

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
        solve_pool.terminate()
        insert_db_process.terminate()


if __name__ == '__main__':
    serve()