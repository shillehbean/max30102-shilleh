from flask import Flask, Response, render_template_string
from picamera2 import Picamera2
import cv2
from heartrate_monitor import HeartRateMonitor  # Assuming you saved the class as heartrate_monitor.py

app = Flask(__name__)

# Initialize Camera
camera = Picamera2()
camera.configure(camera.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
camera.start()

# Initialize HeartRateMonitor
hr_monitor = HeartRateMonitor(print_result=False)
hr_monitor.start_sensor()

# Video feed generator
def generate_frames():
    while True:
        frame = camera.capture_array()
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Route to display video and biometric data
@app.route('/')
def index():
    return render_template_string('''
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Heart Rate and SpO2 Monitor</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f0f0f0;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                }
                h1 {
                    color: #333;
                    margin-bottom: 20px;
                }
                .container {
                    background-color: #fff;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    text-align: center;
                }
                #biometric_data {
                    margin-top: 20px;
                }
                .data {
                    font-size: 1.2em;
                    margin-bottom: 10px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Heart Rate and SpO2 Monitor</h1>
                <div>
                    <img src="{{ url_for('video_feed') }}" width="640" height="480">
                </div>
                <div id="biometric_data">
                    <p class="data">Heart Rate: <span id="heart_rate">Waiting for data...</span></p>
                    <p class="data">SpO2 Level: <span id="spo2">Waiting for data...</span></p>
                </div>
            </div>
            <script>
                function updateBiometricData() {
                    fetch('/biometric_data')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('heart_rate').textContent = data.heart_rate ? data.heart_rate + ' BPM' : 'No data';
                            document.getElementById('spo2').textContent = data.spo2 ? data.spo2 + ' %' : 'No data';
                        })
                        .catch(error => console.error('Error fetching biometric data:', error));
                }
                setInterval(updateBiometricData, 1000); // Update every second
            </script>
        </body>
        </html>
    ''')

@app.route('/biometric_data')
def biometric_data_route():
    # Convert numpy.bool_ to native Python bool
    heart_rate = hr_monitor.get_bpm()
    spo2 = hr_monitor.get_spo2()

    # Note: There is a slight delay in response due to sensor data buffering, processing,
    # and network communication to ensure accuracy and stability in the displayed readings.
    return {
        "heart_rate": heart_rate,
        "spo2": spo2
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
