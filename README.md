# CISS_BOSCH_PORT_PYTHON3

Allows the utilization of the CISS BOSCH sensor in environments using and Python 3.


## Setup 
### Docker (Does not set up any timeseries DB)

- docker build -t bosch-sensor .
- docker run --device=/dev/ttyACM0 bosch-sensor:latest 

### Docker Compose (Recommended)

- docker-compose up --build -d

#### Port (Precaution)

- Try to use port 5434 as other Postgresql instances might be running

## Sensor

### Sensor Init file

- Only activate the stream variables
- TODO: restart service once new stream is selected

## Sensor Limitation

- Do not use the Noise sensor.
