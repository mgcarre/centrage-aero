FROM python:3.7

# Create virtual env
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv ${VIRTUAL_ENV}
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Build application
COPY . /app
WORKDIR /app

# Run the application
ENTRYPOINT ["python"]
CMD ["main.py"]
