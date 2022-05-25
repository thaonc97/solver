# FROM acmsolver_env:1.02-slim
FROM  registry.awing.vn/acm-dev/acmsolver_env:1.0
COPY . /acmsolver/

#Install python requirement libraries
RUN pip install -r /acmsolver/requirements.txt --no-cache-dir --compile

WORKDIR /acmsolver/acm_solver/
CMD ["python", "app.py"]