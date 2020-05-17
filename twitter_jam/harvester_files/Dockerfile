FROM python:3
ENV http_proxy http://wwwproxy.unimelb.edu.au:8000/
ENV https_proxy http://wwwproxy.unimelb.edu.au:8000/
WORKDIR /usr/src/app
COPY . /usr/src/app
RUN pip install --trusted-host pypi.python.org -r requirements.txt
CMD ["python","harvester.py"]
