#
# Team 43, Melbourne
# Aidan McLoughney(1030836)
# Thanaboon Muangwong(1049393)
# Nahid Tajik(1102790)
# Saket Khandelwal (1041999)
# Shmuli Bloom(982837)
#

FROM python:3
ENV http_proxy http://wwwproxy.unimelb.edu.au:8000/
ENV https_proxy http://wwwproxy.unimelb.edu.au:8000/
WORKDIR /usr/src/app
COPY . /usr/src/app
RUN pip install --trusted-host pypi.python.org -r requirements.txt
CMD ["python","harvester.py"]
