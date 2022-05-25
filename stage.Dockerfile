# FROM acmsolver_env:1.02-slim
FROM  registry.awing.vn/acm-stage/acmsolver-env:2
COPY . /acmsolver/

#Install python requirement libraries
RUN pip install -r /acmsolver/requirements.txt --no-cache-dir --compile

WORKDIR /acmsolver/acm_solver/server/
CMD ["python", "acm_solver_server.py"]