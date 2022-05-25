# FROM acmsolver_env:1.02-slim
FROM  registry.awing.vn/acm-production/acmsolver-env:2.0
COPY . /acmsolver/

#Install python requirement libraries
RUN pip install -r /acmsolver/requirements.txt --no-cache-dir --compile

WORKDIR /acmsolver/acm_solver/
CMD ["python", "app.py"]