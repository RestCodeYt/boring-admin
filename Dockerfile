FROM python:3.10
WORKDIR /boring-admin
COPY requirements.txt /boring-admin/
RUN pip install -r requirements.txt
COPY . /boring-admin
CMD python boring-admin.py