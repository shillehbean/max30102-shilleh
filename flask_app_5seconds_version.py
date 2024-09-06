from flask import Flask, Response, render_template_string, jsonify
from picamera2 import Picamera2
import cv2
import time
from heartrate_monitor import HeartRateMonitor

app = Flask(__name__)

# Initialize Camera
camera = Picamera2()
camera.configure(camera.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
camera.start()

# Initialize HeartRateMonitor
hr_monitor = HeartRateMonitor(print_result=False)
hr_monitor.start_sensor()

# Reference normal ranges for heart rate and SpO2
NORMAL_HEART_RATE_RANGE = (60, 100)  # Normal resting heart rate in BPM
NORMAL_SPO2_RANGE = (95, 100)  # Normal SpO2 percentage

# Collect data for averaging
measurement_start_time = None
heart_rate_sum = 0
spo2_sum = 0
measurement_count = 0
is_measuring = False
finished = False
average_heart_rate = 0
average_spo2 = 0
countdown = 5  # Initial countdown time

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
                .normal {
                    color: green;
                }
                .watch {
                    color: orange;
                }
                .high {
                    color: red;
                }
                .acceptable-ranges {
                    margin-left: 30px;
                    font-size: 1em;
                    color: #555;
                }
                button {
                    margin-top: 20px;
                    padding: 10px 20px;
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                }
                button:hover {
                    background-color: #0056b3;
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
                    <p class="data" id="status"><b>Please place your finger on the sensor...</b></p>
                    <p class="data">Heart Rate: <span id="heart_rate" class="normal">Waiting for data...</span></p>
                    <p class="data">SpO2 Level: <span id="spo2" class="normal">Waiting for data...</span></p>
                    <div id="acceptable_ranges" class="acceptable-ranges" style="display:none;">
                        <p>Acceptable Ranges:</p>
                        <p>Heart Rate: 60 - 100 BPM</p>
                        <p>SpO2: 95% - 100%</p>
                    </div>
                    <button id="reset_button" style="display:none;" onclick="resetMeasurements()">Reset</button>
                </div>
            </div>
            <script>
                let measuring = false;

                function updateBiometricData() {
                    fetch('/biometric_data')
                        .then(response => response.json())
                        .then(data => {
                            if (data.is_measuring) {
                                document.getElementById('status').textContent = "Measuring... Hold your finger still for 5 seconds.";
                            } else if (data.finished) {
                                document.getElementById('status').textContent = "Done"
                                const heartRateElement = document.getElementById('heart_rate');
                                const spo2Element = document.getElementById('spo2');
                                
                                // Update heart rate and SpO2 values with colors
                                heartRateElement.textContent = data.average_heart_rate + ' BPM';
                                spo2Element.textContent = data.average_spo2 + ' %';

                                // Color coding for heart rate
                                if (data.average_heart_rate < 60 || data.average_heart_rate > 100) {
                                    heartRateElement.className = 'high';  // Red
                                } else if (data.average_heart_rate >= 90) {
                                    heartRateElement.className = 'watch';  // Orange
                                } else {
                                    heartRateElement.className = 'normal';  // Green
                                }

                                // Color coding for SpO2
                                if (data.average_spo2 < 95) {
                                    spo2Element.className = 'high';  // Red
                                } else if (data.average_spo2 >= 98) {
                                    spo2Element.className = 'watch';  // Orange
                                } else {
                                    spo2Element.className = 'normal';  // Green
                                }

                                // Show acceptable ranges and reset button
                                document.getElementById('acceptable_ranges').style.display = 'block';
                                document.getElementById('reset_button').style.display = 'inline-block';
                            }
                        })
                        .catch(error => console.error('Error fetching biometric data:', error));
                }

                function resetMeasurements() {
                    // Reset the displayed text
                    document.getElementById('heart_rate').textContent = 'Waiting for data...';
                    document.getElementById('spo2').textContent = 'Waiting for data...';
                    document.getElementById('status').textContent = 'Please place your finger on the sensor...';
                    
                    // Reset the color classes to normal
                    document.getElementById('heart_rate').className = 'normal';
                    document.getElementById('spo2').className = 'normal';
                    
                    // Hide the reset button
                    document.getElementById('reset_button').style.display = 'none';
                    
                    // Hide acceptable ranges
                    document.getElementById('acceptable_ranges').style.display = 'none';  
                    
                    // Fetch reset from server
                    fetch('/reset_measurement');
                }

                setInterval(updateBiometricData, 100); // Update every second
            </script>
        </body>
        </html>
    ''')

@app.route('/biometric_data')
def biometric_data_route():
    global measurement_start_time, heart_rate_sum, spo2_sum, measurement_count, average_heart_rate, average_spo2, is_measuring, countdown, finished
    
    heart_rate = hr_monitor.get_bpm()
    spo2 = hr_monitor.get_spo2()

    # Ensure heart_rate and spo2 are valid (non-zero and non-null)
    print(finished)
    if not finished:
        if (heart_rate and heart_rate > 0 and spo2 and spo2 > 0) or is_measuring:  # Finger detected or is_measuring
            if not is_measuring:
                # Start the measurement process
                measurement_start_time = time.time()
                heart_rate_sum = 0
                spo2_sum = 0
                measurement_count = 0
                is_measuring = True

            # Sum the sensor data, only valid readings
            if (heart_rate > 0 and spo2 > 0):
                heart_rate_sum += heart_rate
                spo2_sum += spo2
                measurement_count += 1
                print(f"Detected Heart Rate {heart_rate}")
                print(f"Detected Spo2 {spo2}")
            else:
                print("Invalid Reading")
            
            # Calculate the remaining time
            elapsed_time = time.time() - measurement_start_time

            # Check if 5 seconds have passed
            if elapsed_time >= 5:
                # Calculate the averages
                average_heart_rate = heart_rate_sum / measurement_count
                average_spo2 = spo2_sum / measurement_count
                
                # Compare with normal ranges
                comparison_result = "Heart rate and SpO2 are normal."
                if average_heart_rate < NORMAL_HEART_RATE_RANGE[0]:
                    comparison_result = "Heart rate is low."
                elif average_heart_rate > NORMAL_HEART_RATE_RANGE[1]:
                    comparison_result = "Heart rate is high."
                if average_spo2 < NORMAL_SPO2_RANGE[0]:
                    comparison_result += " SpO2 is low."
                
                is_measuring = False  # Measurement finished
                finished = True # We do this so that the average does not continue
                return jsonify({
                    "finished": True,
                    "average_heart_rate": round(average_heart_rate),
                    "average_spo2": round(average_spo2),
                    "comparison_result": comparison_result
                })
            else:
                return jsonify({"is_measuring": True})
        else:
            return jsonify({"is_measuring": False})
    else:
        return jsonify({"is_measuring": False})

@app.route('/reset_measurement')
def reset_measurement():
    global is_measuring, measurement_start_time, heart_rate_sum, spo2_sum, measurement_count, finished
    is_measuring = False
    finished = False
    measurement_start_time = None
    heart_rate_sum = 0
    spo2_sum = 0
    measurement_count = 0
    return "Reset successful", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
