from max30102 import MAX30102
import threading
import time
import numpy as np
import hrcalc


class HeartRateMonitor(object):
    """
    A class that encapsulates the max30102 device into a thread
    """

    LOOP_TIME = 0.01

    def __init__(self, print_raw=False, print_result=False):
        self.bpm = 0
        self.spo2 = 0
        self.print_raw = print_raw
        self.print_result = print_result
        self._thread = None
        self._stopped = threading.Event()

    def run_sensor(self):
        sensor = MAX30102()
        ir_data = []
        red_data = []
        bpms = []
        spo2s = []

        while not self._stopped.is_set():
            num_bytes = sensor.get_data_present()
            if num_bytes > 0:
                while num_bytes > 0:
                    red, ir = sensor.read_fifo()
                    ir_data.append(ir)
                    red_data.append(red)
                    num_bytes -= 1
                    if self.print_raw:
                        print("{0}, {1}".format(ir, red))

                if len(ir_data) >= 100:
                    ir_data = ir_data[-100:]
                    red_data = red_data[-100:]
                    bpm, valid_bpm, spo2, valid_spo2 = hrcalc.calc_hr_and_spo2(ir_data, red_data)

                    if valid_bpm:
                        bpms.append(bpm)
                        while len(bpms) > 4:
                            bpms.pop(0)
                        self.bpm = np.mean(bpms)

                    if valid_spo2:
                        spo2s.append(spo2)
                        while len(spo2s) > 4:
                            spo2s.pop(0)
                        self.spo2 = np.mean(spo2s)

                    if (np.mean(ir_data) < 50000 and np.mean(red_data) < 50000):
                        self.bpm = 0
                        self.spo2 = 0
                        if self.print_result:
                            print("Finger not detected")
                    if self.print_result:
                        print(f"BPM: {self.bpm}, SpO2: {self.spo2}")

            time.sleep(self.LOOP_TIME)

        sensor.shutdown()

    def start_sensor(self):
        self._thread = threading.Thread(target=self.run_sensor)
        self._thread.start()

    def stop_sensor(self, timeout=2.0):
        self._stopped.set()
        self.bpm = 0
        self.spo2 = 0
        self._thread.join(timeout)

    def get_bpm(self):
        return self.bpm

    def get_spo2(self):
        return self.spo2
