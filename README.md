<img src="etc/lego_model.png" align="right" width=300 />

# TrackstormsBot

Face tracking using Raspberry Pi & Lego Mindstorms! The Pi [Build Hat](https://www.raspberrypi.com/products/build-hat/), Pi Camera, and Lego mindstorms motors are combined to create a face tracking robot. It provides a barebones Flask interface for monitoring the bot headlessly.

## Installation

### Hardware

- The robot can be created using Lego pieces from the [Mindstorms Robot Inventor (51515)](https://www.bricklink.com/v2/catalog/catalogitem.page?S=51515-1#T=S&O=%7B%22iconly%22:0%7D) set. Instructions can be found [here](etc/lego_model_v0.1.0.pdf).

- Refer to the tutorial [here](https://www.raspberrypi.com/documentation/accessories/build-hat.html) to setup your Raspberry Pi with the Build Hat.

- Connect the camera to the Raspberry Pi and enable Legacy Camera Support. This can be done by running:

  ```
  sudo raspi-config -> Interface Options -> Legacy Camera
  ```

### Software

Install dependencies and python packages:

```bash
./setup.sh
pip install -r requirements.txt
```

## Usage

Run the provided script to launch the webinterface and start the bot:

```bash
python run.py
```

This will launch a webinterface which can be accessed to monitor the camera feed at `http://<pi_ip>:5000`.
