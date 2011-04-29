import sys, struct
from pyBusPirate.BinaryMode.I2C import I2C, I2CPins, I2CSpeed
   
class BMP085:
    
    def __init__(self, port, writeaddress, readaddress):
        self.port = port
        self.writeaddress = writeaddress
        self.readaddress = readaddress
    
    def start(self):
        self.i2c = I2C(self.port, 115200)
    
        print "Entering binmode: ",
        if self.i2c.BBmode():
            print "OK."
        else:
            print "failed."
            sys.exit()
        
        print "Entering raw I2C mode: ",
        if self.i2c.enter_I2C():
            print "OK."
        else:
            print "failed."
            sys.exit()
            
        print "Configuring I2C."
        if not self.i2c.cfg_pins(I2CPins.POWER | I2CPins.PULLUPS):
            print "Failed to set I2C peripherals."
            sys.exit()
        if not self.i2c.set_speed(I2CSpeed._50KHZ):
            print "Failed to set I2C Speed."
            sys.exit()
        self.i2c.timeout(0.2)
        
    def get_calibration(self):
        """
        Reads calibration values from BMP085 registers.
        """    
        #self.i2c_write_data([0xee, 0xb2])
        msb = self.get_register(0xb2)
        lsb = self.get_register(0xb3)
        self.AC5 = (msb << 8) + lsb
        print "AC5 Calibration register:", self.AC5
        
        msb = self.get_register(0xb4)
        lsb = self.get_register(0xb5)
        self.AC6 = (msb << 8) + lsb
        print "AC6 Calibration register:", self.AC6

        msb = self.get_register(0xbc)
        lsb = self.get_register(0xbd)
        self.MC = (msb << 8) + lsb
        print "MC Calibration register:", self.MC

        msb = self.get_register(0xbe)
        lsb = self.get_register(0xbf)
        self.MD = (msb << 8) + lsb
        print "MD Calibration register:", self.MD
    
    def read_temp_raw(self):
        """
        Reads raw temperature from BMP085 pressure chip using bus pirate.
        """
        # Start new temperature measurement
        self.control_register(0xf4, 0x2e)
        
        # Read MSB and LSB from registers
        msb = self.get_register(0xf6)
        lsb = self.get_register(0xf7)
        
        # Calculate uncompensated temperature
        self.UT = (msb << 8) + lsb
        print "Uncompensated temperature value: %s" % self.UT

    def calculate_temp(self):
        """
        Calculates the true temperature value.
        """
        x1 = (self.UT - self.AC6) * self.AC5 >> 15
        x2 = (self.MC << 11) / (x1 + self.MD)
        b5 = x1 + x2
        temp = (b5 + 8) >> 4
        temp = str(temp)
        print "True temperature value: %s.%s (C)" % (temp[0:2], temp[2])

    def get_register(self, address):
        """
        Get's a register value from the BMP085.
        """
        data = [0xee, address]
        self.i2c.send_start_bit()
        self.i2c.bulk_trans(len(data),data)
        self.i2c.send_start_bit()
        self.i2c.bulk_trans(len([0xef]),[0xef])
        out = struct.unpack('b', self.i2c.read_byte())[0]
        self.i2c.send_stop_bit()
        return out
    
    def control_register(self, register, value):
        """
        Write's a value to a control register.
        """
        data = [0xee, register, value]
        self.i2c.send_start_bit()
        self.i2c.bulk_trans(len(data),data)
        self.i2c.send_stop_bit()

if __name__ == '__main__':
    bmp085 = BMP085("COM8", 0xee, 0xef)
    bmp085.start()
    bmp085.get_calibration()
    bmp085.read_temp_raw()
    bmp085.calculate_temp()
    bmp085.read_raw_pressure()