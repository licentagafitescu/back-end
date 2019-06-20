FROM ubuntu:latest

RUN apt-get update --fix-missing

# Install virtualenv, nginx, supervisor
RUN apt-get install -y build-essential git
RUN apt-get install -y python3 python-dev python-setuptools
RUN apt-get install -y python3-pip python-virtualenv
RUN apt-get install -y nginx 


# create virtual env and install dependencies
# Due to a bug with h5 we install Cython first
RUN virtualenv -p python3 /opt/venv
ADD ./requirements.txt /opt/venv/requirements.txt
RUN /opt/venv/bin/pip install Cython && /opt/venv/bin/pip install -r /opt/venv/requirements.txt

# expose port
EXPOSE 80


# Add our config files
ADD ./nginx.conf /etc/nginx/nginx.conf

# Copy our service code
ADD ./service /opt/app

# restart nginx to load the config
RUN service nginx stop

# start supervisor to run our wsgi server
CMD  /opt/venv/bin/gunicorn main:app -w 2 -b 0.0.0.0:5000 --log-level=debug --chdir=/opt/app 
