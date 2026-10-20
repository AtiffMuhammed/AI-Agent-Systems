# Project evidence report

Question: How often does the firmware sample soil moisture?

Created (UTC): 2026-10-20T07:41:33+00:00
Mode: evidence | Status: answered

These are retrieved excerpts, not an AI-generated answer.

[S1]
```text
Line 7: The firmware samples soil moisture every 30 seconds.
```

[S2]
```text
Line 7: The sample does not include a server URL, credentials, working firmware, or measured results.
```

[S3]
```text
Line 5: TODO: Calibrate the soil moisture sensor using dry soil and wet soil samples.
```

## Suggested next steps (not executed)

- Calibrate the soil moisture sensor using dry soil and wet soil samples.
- Test Wi-Fi reconnection after the access point is restarted.
- Unplug the sensor and confirm the relay stays off.
- Check that duplicate MQTT messages do not create duplicate alerts.
- Record actual battery current before estimating runtime.

## Evidence snapshots

### [S1] design.md — lines 1–12
SHA-256: 06b84ca1a33fb936d51432541d6baafa8f8576778ddb53fc40a741b002c6ce3a

```text
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
```

### [S2] decisions.md — lines 1–7
SHA-256: f4a92adf532ecca3f3fe04c51a55187c37603a17545fac342b88e51bccdd5409

```text
# Sample engineering decisions — fictional demonstration data

MQTT was chosen for the sample design because publish/subscribe fits sensor telemetry.
TLS is required for the MQTT connection when sending readings over the Internet.
Use a capacitive sensor instead of the inexpensive exposed resistive probe to reduce corrosion.
The exact moisture threshold must be determined through calibration, not copied from another project.
The sample does not include a server URL, credentials, working firmware, or measured results.
```

### [S3] test-plan.md — lines 1–11
SHA-256: 17f26b3f53b01dd518400f5ec1ebca0b9d7a768c3ba1b38eaaad8431f8c65a70

```text
# Sample test plan — fictional demonstration data

No measurements have been performed. These are planned checks, not completed work.

TODO: Calibrate the soil moisture sensor using dry soil and wet soil samples.
TODO: Test Wi-Fi reconnection after the access point is restarted.
TODO: Unplug the sensor and confirm the relay stays off.
TODO: Check that duplicate MQTT messages do not create duplicate alerts.
TODO: Record actual battery current before estimating runtime.

Battery capacity and measured current are unknown. Battery runtime cannot be calculated from these notes.
```

## Limits

Search is lexical. Valid source references do not prove that an AI claim is factually supported. Review the excerpts. Suggestions are never executed automatically.
