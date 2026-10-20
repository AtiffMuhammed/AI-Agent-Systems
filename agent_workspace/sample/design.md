# Sample irrigation monitor — fictional demonstration data

This is a fictional example for testing the workspace, not a report of a real deployed device.

The controller is an ESP32. A capacitive soil moisture sensor connects to an ADC input.
The planned hardware budget is 1,250 INR, excluding an already available ESP32.
The firmware samples soil moisture every 30 seconds.
Measurements are sent over Wi-Fi to an MQTT broker using TLS.
An n8n workflow subscribes to the readings and records them in a spreadsheet.
The system sends an alert when soil moisture stays below the calibrated threshold for three consecutive readings.
The relay should remain off when the sensor is disconnected or the reading is invalid.
There is no automatic watering implementation in this sample design yet.
