# Heart Rate and SpO2 Monitor using Raspberry Pi

This project is a simple Flask web application that streams live video from a Raspberry Pi camera and displays real-time heart rate and SpO2 (oxygen saturation) data using a MAX30102 sensor. This setup is ideal for those looking to create a basic health monitoring system or experiment with IoT devices and web technologies.

## Features

- **Live Video Streaming**: Streams video from the Raspberry Pi camera to a web page, accessible from any device on the same network.
- **Real-Time Biometric Data**: Displays heart rate and SpO2 data collected from the MAX30102 sensor in real-time.
- **User-Friendly Interface**: Simple web interface with clear data visualization and live updates every second.

## How It Works

1. **Video Feed**: The application captures video frames using the `Picamera2` library and streams them to a web page using Flask's response stream.
2. **Biometric Data Collection**: The `HeartRateMonitor` class continuously reads data from the MAX30102 sensor to calculate heart rate and SpO2 levels.
3. **Data Display**: Heart rate and SpO2 levels are displayed alongside the video stream on the web page, with automatic updates to reflect real-time changes.

### Prerequisites

- Raspberry Pi with a connected camera module.
- MAX30102 sensor connected to the Raspberry Pi.
- Python 3.x installed on the Raspberry Pi.
- Required Python libraries: Flask, Picamera2, OpenCV, numpy, and any necessary drivers for the MAX30102 sensor.

### Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/max30102-shilleh.git
   cd max30102-shilleh
   ```
