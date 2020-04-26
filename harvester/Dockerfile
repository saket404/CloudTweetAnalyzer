FROM python:3
WORKDIR /usr/src/app
COPY . /usr/src/app
RUN pip install --trusted-host pypi.python.org -r requirements.txt
ENV NAME harvester
CMD ["python","harvester.py"]
