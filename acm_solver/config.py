# Database
connection_str = "mongodb://acm:AWing%402020@118.70.206.204:27017/?authSource=admin"  # dev
# connection_str = "mongodb://192.168.10.202:27017"  # demo
# connection_str = "mongodb://172.16.2.106:27017"  # staging

# Miscs.
range_date_int_mapper = 365

# Problem
days_per_problem = 100
solve_max_process = 2

# Solver config
solve_method = "TWO_STEPS" # choose 'TWO_STEPS' or 'SOFT_CONSTRAINT'
problem_max_size = 1*10**6
max_records_per_stream = 1*10**3
subprocess_timeout = 60*60

# grpc config
max_grpc_worker = 10
port = 50051