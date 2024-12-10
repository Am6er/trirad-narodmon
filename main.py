import time
import datetime
import requests as requests
import serial

port = "COM15"
baudrate = 9600
bytesize = serial.EIGHTBITS
parity = serial.PARITY_NONE
stopbits = serial.STOPBITS_ONE
sleeptime = 60.0*5.0 # in seconds
sensitivty = 0.05453301870661058 # counts per 1 uR/h

class Data:
    counts_list = []
    def add_metrics(self, counts: float):
        if len(self.counts_list) == 0:
            self.counts_list.append(counts)
            return
        if counts < self.counts_list[-1]:
            # 65535 value reached
            last_counts = self.counts_list[-1]
            self.counts_list.clear()
            self.counts_list.append(0.0)
            self.counts_list.append(65535.0 - last_counts + counts)
            return
        self.counts_list.append(counts)

    def get_last_intensity(self) -> float:
        last_counts = self.get_last_counts()
        return last_counts / sensitivty / sleeptime

    def get_last_counts(self) -> float:
        if len(self.counts_list) > 1:
            return self.counts_list[-1] - self.counts_list[-2]
        else:
            return -1


DATA = Data()

while True:
    time.sleep(sleeptime)
    try:
        ser = serial.Serial(port, baudrate, bytesize, parity, stopbits)
    except serial.SerialException as e:
        print("Error open port:", e)
    else:
        try:
            ser.write(b"#nuc workset\r")
            received_data = ser.readline().strip()
            current_counts = str(received_data).split(",")[0].split(" ")[2]
            DATA.add_metrics(float(current_counts))
            if DATA.get_last_intensity() > 0:
                post_data = {
                    'ID': 'Trirad-radiascope1-437-00003',
                    'NAME': 'Trirad-radiascope1',
                    'R_DoseRate': DATA.get_last_intensity(),
                }

                post_headers = {
                    'Content-Length': str(len(post_data)),
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Host': 'narodmon.ru'
                }
                try:
                    response = requests.post(url='https://narodmon.ru/post.php', data=post_data, headers=post_headers)
                    print(
                        f"{datetime.datetime.now()} Post data to narodmon AVG Intesity: {DATA.get_last_intensity()} \u03BCR/h, Counts: {DATA.get_last_counts()}, Result: {response}")
                except Exception as e:
                    print(f"{datetime.datetime.now()} Error while sending data to narodmon. {e.__str__()}")
        except serial.SerialException as e:
            print("Error send receive data:", e)
        finally:
            ser.close()