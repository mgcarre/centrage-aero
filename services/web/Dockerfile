FROM python:3.7

# Create virtual env
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv ${VIRTUAL_ENV}
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

# Python specifics
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install dependencies
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

# Build application
COPY . /usr/src/app
WORKDIR /usr/src/app

# Run the application
#ENTRYPOINT ["python"]
#CMD ["main.py"]
