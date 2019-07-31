FROM python:3.6

WORKDIR /usr/src/app

RUN apt-get update
RUN apt-get install -y gettext

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python setup.py install

CMD ["exp1572"]