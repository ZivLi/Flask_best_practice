FROM python:3.6
COPY requirements.txt ./
RUN pip install --upgrade pip setuptools
RUN pip install --default-timeout=1000 \
        --no-cache-dir -r requirements.txt
COPY . /opt/project
WORKDIR /opt/project
