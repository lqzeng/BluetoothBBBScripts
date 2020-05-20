#! /usr/bin/python
#
#
#
import gpio

from bluetooth import *
from threading import Thread
import Adafruit_BBIO.ADC as ADC
from time import sleep

class BluetoothServer:

    print('start')

    def __init__(self):
        self.sensor_count = 0
        self.building_number = " "

    def inc_count(self):
        self.sensor_count += 1

    def toggleCmd(self, target):
        if target == 'ventilation':
            #print('toggle green')
            self.green_led.toggleGpioValue()
        elif target == 'sensor':
            #print('toggle red')
            self.sensor.toggleGpioValue()
        elif target[0:12] == 'receive_data':
            #print('sending pot data')
            self.pot_on.toggleGpioValue()
            #get the building number
            self.building_number = target[13:]
            #reset the sensor_count when the recieve_data is broken
            if self.pot_on.getGpioValue() == 0:
                self.sensor_count = 0
        else:
            print('unknown remote command')

    def send_ventilation(self, client_sock):
        while True:
            if self.pot_on.getGpioValue() == 1:
                sens_val = ADC.read(self.analog_pin_VENTILATION)
                print('The ventilation value is: ', sens_val)
                sendData = " ".join([str(self.building_number), str(self.sensor_count), str(sens_val)])
                client_sock.send(sendData)
                print("sent data for building" + self.building_number)
                sleep(3)

    def send_sensor(self, client_sock):
        while True:
            if self.sensor.getGpioValue() == 1:
                if ADC.read(self.analog_pin_SENSOR) == 1:
                    self.inc_count()
                    print("Traffic Count: ", self.sensor_count)
                    #client_sock.send(str(sensor_count))
                    sleep(3)
                else:
                    print("Traffic Count: ", self.sensor_count)
                    sleep(3)

    def recv_command(self, client_sock):
        while True:
            #print("inside recv_command")
            data = client_sock.recv(1024).strip()
            print("received [%s]" % data)
            self.toggleCmd(data)

    def execute(self):

        ADC.setup()

        self.green_led = gpio.gpio(48)
        self.green_led.setDirectionValue('out')
        self.green_led.setGpioValue(0)

        self.sensor = gpio.gpio(49)
        self.sensor.setDirectionValue('out')
        self.sensor.setGpioValue(0)

        self.pot_on = gpio.gpio(60)
        self.pot_on.setDirectionValue('out')
        self.pot_on.setGpioValue(0)

        self.analog_pin_VENTILATION = "P9_39"
        self.analog_pin_SENSOR = "P9_40"


        service_uuid = "00001101-0000-1000-8000-00805F9B34FB"

        server_sock = BluetoothSocket(RFCOMM)
        server_sock.bind(("", PORT_ANY))
        server_sock.listen(1)

        port = server_sock.getsockname()[1]

        advertise_service(server_sock, "BBB", service_id = service_uuid, service_classes = [service_uuid, SERIAL_PORT_CLASS], profiles = [SERIAL_PORT_PROFILE])

        print("awaiting RFCOMM connection on channel:%d" % port)

        client_sock, client_info = server_sock.accept()
        print("accepted connection from:", client_info)

        print("\n\n")

        #client_sock.send("HELLO ANDROID, FROM BBB") #this should send message to input stream of android


        #data = client_sock.recv(1024).strip()

        t1 = Thread(target=self.recv_command, args=(client_sock,))
        t1.daemon=True
        t2 = Thread(target=self.send_ventilation, args=(client_sock,))
        t2.daemon=True
        t3 = Thread(target=self.send_sensor, args=(client_sock,))
        t3.daemon=True
        t1.start()
        t2.start()
        t3.start()

        while True:
            try:
                pass
            except (KeyboardInterrupt, SystemExit):
                print("\nexiting system ")
                client_sock.close()
                server_sock.close()
                print("disconnected")
                sys.exit()


#
if __name__ == '__main__':
    server = BluetoothServer()
    server.execute()

#######################
