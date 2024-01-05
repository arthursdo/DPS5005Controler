import time
import datetime
import serial
import sys
import glob
import argparse

from dps_modbus import Import_limits, Serial_modbus, Dps5005

baudrate = 9600
slave_addr = 1

class MyClass:
    
    def __init__(self):
        self.limits = Import_limits("dps5005_limits.ini")
        self.serialconnected = False
        self.time_old = ""
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("command", help="0 to turn off, 1 to turn on")
        self.args = self.parser.parse_args() 
        self.serial_connect()
        self.run()       
            
    def run(self):
        if self.args.command == '0':
            self.off_change()
        elif self.args.command == '1':
            self.on_change()
        else:
            print("Invalid command. Use 0 to turn off, 1 to turn on.")

    def serial_connect(self): 
        self.serialconnected = False
        try:
            global dps
            if not self.limits.port_set: 
                print("Looking for ports...")
                for port in self.scan_serial_ports():
                    print("Trying port: " + port)
                    try:
                        ser = Serial_modbus(port, slave_addr, baudrate, 8)
                        dps = Dps5005(ser, self.limits)
                        if dps.version() != '':
                            self.serialconnected = True
                            self.timer_start()
                            if self.time_old == "":
                                self.time_old = time.time()
                            print([port], baudrate, slave_addr)
                            break
                    except (OSError, serial.SerialException) as detail1:
                        print(datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S"), "Error1 - ", detail1)
            else:
                print("Manual port is set!")
                try:
                    ser = Serial_modbus(self.limits.port_set, slave_addr, baudrate, 8)
                    dps = Dps5005(ser, self.limits)
                    if dps.version() != '':
                        self.serialconnected = True
                        self.timer_start()
                        if self.time_old == "":
                            self.time_old = time.time()
                        print([self.limits.port_set], baudrate, slave_addr)
                except (OSError, serial.SerialException) as detail1:
                    print(datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S"), "Error1 - ", detail1)
        except Exception as detail:
            print(datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S"), "Error - ", detail)
            self.serial_disconnect("Try again !!!")

    def timer_start(self):
        print("Timer started")

    def serial_disconnect(self, status):
        self.serialconnected = False
        print(status)
        
    def scan_serial_ports(self):
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.flush()
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result
    
    def on_change(self):
        self.pass_2_dps('onoff', 'w', str(1))

    def off_change(self):
        self.pass_2_dps('onoff', 'w', str(0))
    
    def pass_2_dps(self, function, cmd = "r", value = 0):
        a = False
        if self.serialconnected != False:
            start = time.time()
            a = eval("dps.%s('%s', %s)" % (function, cmd, value))
            print(function, cmd, value)
            data_rate = ((time.time() - start) * 1000.0)
            print("Data Rate : %8.3fms" % data_rate) # display rate of serial comms
        return(a)
    
if __name__ == "__main__":
    MyClass().run()