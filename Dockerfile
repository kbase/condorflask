FROM python:3
COPY . /condor_flask
WORKDIR /condor_flask
RUN pip install --no-cache-dir -r requirements.txt
CMD [ "/condor_flask/rungunicorn" ]
