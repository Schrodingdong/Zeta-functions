FROM python:3.13-rc-alpine
WORKDIR /zeta
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY zeta_types.py .
COPY zeta_main.py .
RUN mkdir log
EXPOSE 6969
CMD [ "fastapi", "run", "--host", "0.0.0.0", "--port", "6969", "--entrypoint", "zeta_main:app" ]