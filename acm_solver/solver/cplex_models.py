# local
from solver import solver_helpers
from solver.solver_helpers import Alpha

#others
from docplex.mp.model import Model
import logging
import numpy as np

def solve_b_c(data,
              alpha_formula = '3', 
              output_status = False, 
              time_limit = 3600, 
              gap = 0.1, l = 0, 
              export_model = False, 
              optimality_target = 0,
              evenness_priority = 1,
              method = "TWO_STEPS"
              ):
    
    methods = {
        "TWO_STEPS" : solve_b_c_2_steps,
        "SOFT_CONSTRAINT": solve_b_c_soft
    }
    
    choosen_method = methods[method]
    
    solve_result= choosen_method(data = data,  
                        alpha_formula = alpha_formula,
                        output_status = output_status,
                        time_limit= time_limit,
                        gap = gap, l = l, 
                        export_model = export_model,
                        optimality_target = optimality_target,
                        evenness_priority = evenness_priority)
                        
    return solve_result


def solve_b_c_2_steps(data,
              alpha_formula = '3', 
              output_status = False, 
              time_limit = 3600, 
              gap = 0.1, l = 0.5, 
              export_model = False, 
              optimality_target = 0,
              evenness_priority = 1
              ):
    """
    Sử dụng CPLEX để giải bài toán tối ưu 2 bước, không có biến nguyên, có cận dưới,
    mô hình sau này của a Phong.
    """
    step_1_solve_details = _solve_step_1(data,  
                                        alpha_formula,
                                        output_status = output_status,
                                        time_limit= time_limit,
                                        gap = gap, l = l, 
                                        export_model = export_model,
                                        optimality_target = optimality_target,
                                        evenness_priority = evenness_priority)  # Solve B,C

    step_2_solve_details = _solve_step_2(data,
                                        step_1_solve_details,
                                        alpha_formula,
                                        output_status = output_status,
                                        time_limit= time_limit,
                                        gap = gap, l = l, 
                                        export_model = export_model,
                                        optimality_target = optimality_target,
                                        evenness_priority = evenness_priority)  # Solve B,C
    
    return step_2_solve_details

def _solve_step_1(  data,
                    alpha_formula='3',
                    output_status=False,
                    time_limit=3600,
                    gap=0.10, l=0.0,
                    export_model=False,
                    optimality_target=0,
                    evenness_priority= 1,
                    delta=0.9):

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
    campaigns_list = np.arange(T)
    t_u_k_set = [(t, u, k) for t in range(T)
                 for u in range(U) for k in range(K)]
    u_k_set = [(u, k) for u in range(U) for k in range(K)]
    t_0 = data['t_0']
    ratio = data['share_rate']
    priority = data['priority']
    share_type = data['share_type']

    # Compute cl
    cl = np.zeros([T, U, K])
    for t in range(T):
        if priority[t] == "CLASS_C":
            for u in range(D[t][0], D[t][1]+1):
                for k in L[t]:
                    cl[t, u, k] = 1

    # Compute have_c
    have_c = np.zeros([U, K])
    have_c_network = np.zeros([U, K])
    have_c_domain = np.zeros([U, K])
    for u in range(U):
        for k in range(K):
            have_c_network[u, k] = np.sum(
                [cl[t, u, k] for t in range(len(cl[:, u, k])) if t < t_0])
            have_c_domain[u, k] = np.sum(
                [cl[t, u, k] for t in range(len(cl[:, u, k])) if t >= t_0])

    # Cập nhật lại trọng số
    w = solver_helpers.update_w(data, have_c_network, have_c_domain)
    data['w'] = w.copy()
    # Compute alpha
    alpha = Alpha.calculate(data, alpha_formula)

    model = Model("Acm Solver 2 steps- Step 1")
    x = model.continuous_var_dict(t_u_k_set, lb=0, name='x')
    z = model.continuous_var_dict(campaigns_list, lb=-99999999, ub=0, name='z')

    model.add_constraints(
        model.sum((CTR[t,k]*x[t,u,k] 
                   for k in L[t] for u in range(D[t][0],D[t][1]+1) if w[t,u] !=0)) -z[t] == d[t] for t in range(T) if priority[t] == 'CLASS_B') 

    model.add_constraints(x[t_prime, u, k] == 0
                          for t in range(t_0) if priority[t] == 'CLASS_C'
                          for u in range(D[t][0], D[t][1]+1) if w[t, u] != 0
                          for k in L[t] for t_prime in range(t_0) if t_prime != t)

    model.add_constraints(x[t_prime, u, k] == 0
                          for t in range(t_0, T) if priority[t] == 'CLASS_C'
                          for u in range(D[t][0], D[t][1] + 1) if w[t, u] != 0
                          for k in L[t] for t_prime in range(t_0, T) if t_prime != t)

    model.add_constraints(
        model.sum(x[t, u, k] for t in range(t_0) if t in B[k]
                  and u in range(D[t][0], D[t][1]+1) and w[t, u] != 0)
        <= ratio[k]*r[u, k] for k in range(K) for u in range(U))  # Chặn cứng

    model.add_constraints(
        model.sum(x[t, u, k] for t in range(t_0, T) if t in B[k]
                  and u in range(D[t][0], D[t][1]+1) and w[t, u] != 0)
        <= (1-ratio[k])*r[u, k] for k in range(K) for u in range(U))  # Chặn cứng

    # Chặn dưới
    model.add_constraints(x[t,u,k] >= l*alpha[t,u,k]*min(1, r[u,k]*ratio[k]/deno) 
        for t in range(t_0) if priority[t] == 'CLASS_B'  
            for u in range(D[t][0],D[t][1]+1) 
                for (deno,k) in ( (np.sum(alpha[:,u, k]),k) for k in L[t] if w[t,u] !=0 and CTR[t,k] !=0) if deno !=0)
    model.add_constraints(x[t,u,k] >= l*alpha[t,u,k]*min(1, r[u,k]*(1-ratio[k])/deno) 
        for t in range(t_0, T) if priority[t] == 'CLASS_B' 
            for u in range(D[t][0],D[t][1]+1) 
                for (deno,k) in ( (np.sum(alpha[:,u, k]),k) for k in L[t] if w[t,u] !=0 and CTR[t,k] !=0) if deno !=0)

    opt_func_even = model.sum(
            model.sum(
                model.sum(
                    1/(alpha[t,u,k]+epsilon)**1*((1-cl[t,u,k])*x[t,u,k]*CTR[t,k]-alpha[t,u,k])**2 + cl[t,u,k]*(x[t,u,k] -r[u,k])**2 
                    for k in L[t]) for u in range(D[t][0],D[t][1]+1)  if w[t,u] !=0)  for t in range (T))
    
    opt_func_max_resource = -model.sum(z[t] for t in range(T))

    model.minimize(evenness_priority * opt_func_even + (1 - evenness_priority) * opt_func_max_resource)

    model.parameters.mip.tolerances.mipgap = gap
    model.time_limit = time_limit
    model.parameters.optimalitytarget = optimality_target
    if export_model == True:
        logging.info(model.export_as_lp())
    sol = model.solve(log_output = output_status)
    
    solve_details = {
        'model': model,
        'solution': sol,
        'x_dict' : x,
        'z_dict': z,
        'alpha': alpha,
    }

    return solve_details

def _solve_step_2(  data,
                    step_1_solve_result,
                    alpha_formula='3',
                    output_status=False,
                    time_limit=3600,
                    gap=0.10, l= 0,
                    export_model=False,
                    optimality_target=0,
                    evenness_priority= 1,
                    delta= 0.9,
                    have_TC = False):

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
    t_u_k_set = [(t, u, k) for t in range(T)
                 for u in range(U) for k in range(K)]
    u_k_set = [(u, k) for u in range(U) for k in range(K)]
    t_0 = data['t_0']
    ratio = data['share_rate']
    priority = data['priority']
    share_type = data['share_type']

    # Compute cl
    cl = np.zeros([T, U, K])
    for t in range(T):
        if priority[t] == "CLASS_C":
            for u in range(D[t][0], D[t][1]+1):
                for k in L[t]:
                    cl[t, u, k] = 1

    # Compute have_c
    have_c = np.zeros([U, K])
    have_c_network = np.zeros([U, K])
    have_c_domain = np.zeros([U, K])
    for u in range(U):
        for k in range(K):
            have_c_network[u, k] = np.sum(
                [cl[t, u, k] for t in range(len(cl[:, u, k])) if t < t_0])
            have_c_domain[u, k] = np.sum(
                [cl[t, u, k] for t in range(len(cl[:, u, k])) if t >= t_0])

    # Cập nhật lại trọng số
    w = solver_helpers.update_w(data, have_c_network, have_c_domain)
    data['w'] = w.copy()
    # Compute alpha
    alpha = Alpha.calculate(data, alpha_formula)
    step_1_docplex_sol = step_1_solve_result['solution']
    step_1_x_dict = step_1_solve_result['x_dict']
    step_1_z_dict = step_1_solve_result['z_dict']
    x_star = step_1_docplex_sol.get_value_dict(step_1_x_dict)
    z_star = step_1_docplex_sol.get_value_dict(step_1_z_dict)

    model = Model("AcmSolver 2 steps-Step 2")
    x = model.continuous_var_dict(t_u_k_set, lb=0, name='x')
    x_a = model.continuous_var_dict(u_k_set, lb=0, name='x_a')
    z = model.continuous_var_dict(campaigns_list, lb=-99999999, ub=0, name='z')

    model.add_constraints(
        model.sum((CTR[t, k]*x[t, u, k]
                   for k in L[t] for u in range(D[t][0], D[t][1]+1) if w[t, u] != 0)) -z[t] == d[t] for t in range(T) if priority[t] == 'CLASS_B') 

    model.add_constraints(
        model.sum(x[t, u, k] for t in B[k] if u in range(D[t][0], D[t][1]+1) if w[t, u] != 0) + x_a[u, k] == r[u, k] for u in range(U) for k in range(K)) 

    model.add_constraints(x[t_prime, u, k] == 0
                          for t in range(t_0) if priority[t] == 'CLASS_C'
                          for u in range(D[t][0], D[t][1]+1) if w[t, u] != 0
                          for k in L[t] for t_prime in range(t_0) if t_prime != t)

    model.add_constraints(x[t_prime, u, k] == 0
                          for t in range(t_0, T) if priority[t] == 'CLASS_C'
                          for u in range(D[t][0], D[t][1] + 1) if w[t, u] != 0
                          for k in L[t] for t_prime in range(t_0, T) if t_prime != t)

    model.add_constraints(x_a[u, k] == 0
                          for t in range(T) if priority[t] == 'CLASS_C'
                          for u in range(U)
                          for k in range(K) if u in range(D[t][0], D[t][1]+1) and w[t, u] != 0 and k in L[t])

    model.add_constraints(
        model.sum((x[t, u, k]
                   for k in L[t] for u in range(D[t][0], D[t][1]+1) if w[t, u] != 0)) >= 
                   np.sum([x_star[t,u,k] for k in L[t] for u in range(D[t][0], D[t][1]+1) if w[t, u] != 0 ]) for t in range(T))   

    model.add_constraints(
        model.sum(x[t,u,k] for t in range(t_0) if t in B[k] and u in range(D[t][0],D[t][1]+1) and w[t,u] !=0) 
        <= ratio[k]*r[u,k] for k in range(K) if share_type[k] == 1 for u in range(U)) # Không cho network tràn sang domain
        
    # Chặn dưới
    model.add_constraints(x[t,u,k] >= l*alpha[t,u,k]*min(1, r[u,k]*ratio[k]/deno) 
        for t in range(t_0) if priority[t] == 'CLASS_B'  
            for u in range(D[t][0],D[t][1]+1) 
                for (deno,k) in ( (np.sum(alpha[:,u, k]),k) for k in L[t] if w[t,u] !=0 and CTR[t,k] !=0) if deno !=0)
    model.add_constraints(x[t,u,k] >= l*alpha[t,u,k]*min(1, r[u,k]*(1-ratio[k])/deno) 
        for t in range(t_0, T) if priority[t] == 'CLASS_B' 
            for u in range(D[t][0],D[t][1]+1) 
                for (deno,k) in ((np.sum(alpha[:,u, k]),k) for k in L[t] if w[t,u] !=0 and CTR[t,k] !=0) if deno !=0)
    
    opt_func_even = model.sum(
            model.sum(
                model.sum(
                    1/(alpha[t,u,k]+epsilon)**1*((1-cl[t,u,k])*x[t,u,k]*CTR[t,k]-alpha[t,u,k])**2 + cl[t,u,k]*(x[t,u,k] -r[u,k])**2 
                    for k in L[t]) for u in range(D[t][0],D[t][1]+1)  if w[t,u] !=0)  for t in range (T))
    
    opt_func_max_resource = -model.sum(z[t] for t in range(T))

    model.minimize(evenness_priority * opt_func_even + (1 - evenness_priority) * opt_func_max_resource)

    model.parameters.mip.tolerances.mipgap = gap
    model.time_limit = time_limit
    model.parameters.optimalitytarget = optimality_target
    if export_model == True:
        logging.info(model.export_as_lp())
    sol = model.solve(log_output = output_status)
    
    solve_details = {
        'model': model,
        'solution': sol,
        'x_dict' : x,
        'x_a_dict' :x_a,
        'z_dict': z,
        'alpha': alpha,
    }

    return solve_details


def solve_b_c_soft(data,
              alpha_formula = '3', 
              output_status = False, 
              time_limit = 3600, 
              gap = 0.10, l = 0.0, 
              export_model = False, 
              optimality_target = 0,
              evenness_priority = 1,
              get_click = False,
              opt_func = 'trade_off',
              delta = 0.9):
    """
    Sử dụng CPLEX để giải bài toán tối ưu, có các biến nguyên,
    ràng buộc mềm, mô hình ban đầu của thầy Sơn
    """
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
    p = np.ones_like(data['r'])*l
    share_type = data['share_type']
    
    # Compute cl
    cl = np.zeros([T,U,K])
    for t in range(T):
        if priority[t] == "CLASS_C":
            for u in range(D[t][0], D[t][1]+1):
                for k in L[t]:
                    cl[t,u,k] = 1
                    
    # Compute have_c
    have_c = np.zeros([U,K])
    have_c_network = np.zeros([U,K])
    have_c_domain = np.zeros([U,K])
    for u in range(U):
        for k in range(K):
            have_c_network[u,k] = np.sum([cl[t,u,k] for t in range(len(cl[:,u,k])) if t <t_0])
            have_c_domain[u,k] = np.sum([cl[t,u,k] for t in range(len(cl[:,u,k])) if t >= t_0])

    # Cập nhật lại trọng số
    w = solver_helpers.update_w(data, have_c_network, have_c_domain)
    data['w'] = w.copy()
    # Compute alpha
    alpha= Alpha.calculate(data, alpha_formula)
    
    p_network = .9*r/(np.sum(alpha, axis = 0) + 1)
    p_domain = .9*r/(np.sum(alpha, axis = 0) + 1)
    
    p_network = np.minimum(p_network,p)
    p_domain = np.minimum(p_domain,p)

    model = Model("awing_model_ver_10.6")
    x= model.continuous_var_dict(t_u_k_set,lb = 0, name = 'x')
    x_a = model.continuous_var_dict(u_k_set,lb = 0, name = 'x_a')
    y= model.binary_var_dict(campaigns_list, name = 'y')
    z = model.continuous_var_dict(campaigns_list, lb=-99999999, ub = 0, name = 'z')
    
    if get_click ==True: # for research purpose
        click = model.continuous_var_dict(t_u_k_set,lb = 0, name = 'click')
        model.add_constraints(click[t,u,k] == x[t,u,k]*CTR[t,k] for t in range(T) for u in range(U) for k in range(K))
        
    model.add_constraints(
        model.sum((CTR[t,k]*x[t,u,k] 
                   for k in L[t] for u in range(D[t][0],D[t][1]+1) if w[t,u] !=0)) -z[t] == d[t] for t in range(T) if priority[t] == 'CLASS_B') #(1)
    logging.debug('constraints (1) added!')
    
    model.add_constraints(
        model.sum(x[t,u,k] for t in B[k] if u in range(D[t][0],D[t][1]+1) if w[t,u] !=0) + x_a[u,k] == r[u,k] for u in range(U) for k in range(K))  #(2)
    
    model.add_constraints(y[t] == 1 for t in range(T) if priority[t] == 'CLASS_C')
    model.add_constraints(x_a[u,k] == 0 
        for t in range(T) if priority[t] == 'CLASS_C' 
            for u in range(U) 
                for k in range(K) if u in range(D[t][0],D[t][1]+1) and w[t,u] != 0 and k in L[t])
    # Constraint 2 in case  class C
    logging.debug('constraints (2) added!')
    
    cnst_3 = [model.indicator_constraint(y[t], z[t] >= 0, 0) for t in range(T) if priority[t] == 'CLASS_B']
    cnst_3_5 = [model.indicator_constraint(y[t], z[t] <= -10**-3, 1) for t in range(T) if priority[t] == 'CLASS_B']
    model.add_indicator_constraints(cnst_3) # (3)
    model.add_indicator_constraints(cnst_3_5) # (3.5)
    logging.debug('constraints (3) added!')
    
    model.add_constraints(
        model.sum(x[t1,u,k] for t1 in range(t_0) if t1 in B[k] and u in range(D[t1][0],D[t1][1]+1) and w[t1,u] !=0) 
        >=ratio[k]*r[u,k]*y[t] for t in range(t_0) if priority[t] =='CLASS_B' for u in range(D[t][0],D[t][1]+1) for k in L[t] if w[t,u] !=0 and CTR[t,k] !=0  and have_c_network[u,k] == 0 ) #(4)
    logging.debug('constraints (4) added!')
    
    model.add_constraints(
        model.sum(x[t1,u,k] for t1 in range(t_0,T) if t1 in B[k] and u in range(D[t1][0],D[t1][1]+1) and w[t1,u] !=0) 
        >=(1-ratio[k])*r[u,k]*y[t] for t in range(t_0,T) if priority[t] =='CLASS_B' for u in range(D[t][0],D[t][1]+1) for k in L[t] if w[t,u] !=0 and CTR[t,k] !=0 and have_c_domain[u,k] == 0) #(5)
    logging.debug('constraints (5) added!')
    model.add_constraints(x[t_prime,u,k] == 0 
                          for t in range(t_0) if priority[t] == 'CLASS_C'
                          for u in range(D[t][0],D[t][1]+1) if w[t,u] != 0
                          for k in L[t] for t_prime in range(t_0) if t_prime != t)
    
    model.add_constraints(x[t_prime,u,k] == 0 
                          for t in range(t_0,T) if priority[t] == 'CLASS_C'
                          for u in range(D[t][0],D[t][1] + 1) if w[t,u] != 0
                          for k in L[t] for t_prime in range(t_0,T) if t_prime != t)
    
    # _________________ Constraint a Phong new
    
    model.add_constraints(x[t,u,k] >= p_network[u,k]*alpha[t,u,k] for t in range(t_0) if priority[t] =='CLASS_B' for u in range(D[t][0],D[t][1]+1) for k in L[t] if w[t,u] !=0 and CTR[t,k] !=0  and have_c_network[u,k] == 0)
    
    model.add_constraints(x[t,u,k] >= p_domain[u,k]*alpha[t,u,k] for t in range(t_0,T) if priority[t] =='CLASS_B' for u in range(D[t][0],D[t][1]+1) for k in L[t] if w[t,u] !=0 and CTR[t,k] !=0  and have_c_network[u,k] == 0)
    
    #________________End constraint a Phong new

    #_______BEGIN 2 campaign type c case at 1 date place_____
    model.add_constraints(x[t,u,k] >= r[u,k]*ratio[k] for t in range(t_0) if priority[t] == 'CLASS_C' for u in range(D[t][0],D[t][1]+1) for k in L[t] if w[t,u] !=0)
    model.add_constraints(x[t,u,k] >= r[u,k]*(1-ratio[k]) for t in range(t_0,T) if priority[t] == 'CLASS_C'for u in range(D[t][0],D[t][1]+1) for k in L[t] if w[t,u] !=0)
    #______END 2 campaign type c case________
    
    # Strich sharing constraint: ràng buộc share cứng, ko cho network tràn sang domain
    model.add_constraints(
        model.sum(x[t1,u,k] for t1 in range(t_0) if t1 in B[k] and u in range(D[t1][0],D[t1][1]+1) and w[t1,u] !=0) 
        <= ratio[k]*r[u,k] for k in range(K) if share_type[k] == 1 for u in range(U)) # Không cho network tràn sang domain
    
    opt_func_even = model.sum(
            model.sum(
                model.sum(
                    1/(alpha[t,u,k]+epsilon)**1*((1-cl[t,u,k])*x[t,u,k]*CTR[t,k]-alpha[t,u,k])**2 + cl[t,u,k]*(x[t,u,k] -r[u,k])**2 
                    for k in L[t]) for u in range(D[t][0],D[t][1]+1)  if w[t,u] !=0)  for t in range (T))
    
    opt_func_max_resource = -model.sum(z[t] for t in range(T))

    if opt_func =="max_rss":
        logging.debug("Maximum resource possible")
        model.minimize(opt_func_max_resource)
    elif opt_func == 'trade_off':
        logging.debug("Trade off optimization function")
        model.minimize(evenness_priority * opt_func_even + (1 - evenness_priority) * opt_func_max_resource)
    elif opt_func == 'even':
        logging.debug("Trade off optimization function")
        model.minimize(opt_func_even)
    elif opt_func =='max_rss_constraints':
        logging.debug("Max resource constraints")
        max_allocated = data['max_allocated']
        model.add_constraint(
            model.sum((CTR[t,k]*x[t,u,k] 
                        for t in range(T) if priority[t] == 'CLASS_B' for k in L[t] for u in range(D[t][0],D[t][1]+1) if w[t,u] !=0 )) >= delta * max_allocated)
        model.minimize(opt_func_even)
        

    logging.debug('obj.function added!')
    model.parameters.mip.tolerances.mipgap = gap
    model.time_limit = time_limit
    model.parameters.optimalitytarget = optimality_target
    if export_model == True:
        logging.info(model.export_as_lp())
    sol = model.solve(log_output = output_status)
    
    solve_details = {
        'model': model,
        'solution': sol,
        'x_dict' : x,
        'x_a_dict' :x_a,
        'y_dict': y,
        'z_dict': z,
        'alpha': alpha,
    }
    if get_click == True:
        solve_details['click'] = click
    return solve_details