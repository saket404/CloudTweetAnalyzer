FROM python:3
EXPOSE 8050
WORKDIR /usr/src/app
COPY . /usr/src/app
RUN pip install --trusted-host pypi.python.org -r requirements.txt
CMD ["python","frontend.py"]