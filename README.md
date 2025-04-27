# CISS_BOSCH_PORT_PYTHON3

Allows the utilization of the CISS BOSCH sensor in environments using and Python 3.



## Setup 
### Docker

- docker build -t bosch-sensor .
- docker run --device=/dev/ttyACM0 bosch-sensor:latest 


## Sensor Limitation
- Do not use the Noise sensor.
