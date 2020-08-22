FROM python:3.7-slim

# create directory and change working directory
WORKDIR /usr/bin/gm-service

# add working directory to the PYTHONPATH
ENV PYTHONPATH=.

# first copy only requirements.txt to the previously defined working dir
COPY requirements.txt .

# install all the required packages
RUN pip install -r requirements.txt

# copy the contents of the project to the working directory
COPY . .

# port that will need to be exposed
EXPOSE 5000

# run the app
CMD ["python", "gm/main/app.py"]
