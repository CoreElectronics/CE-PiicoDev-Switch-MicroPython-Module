# A simple class to read data from a Core Electronics PiicoDev switch
# Peter Johnston at Core Electronics
# 2022 APR 06 - Initial release

from PiicoDev_Unified import *

compat_str = '\nUnified PiicoDev library out of date.  Get the latest module: https://piico.dev/unified \n'

_BASE_ADDRESS = 0x42
_DEVICE_ID    = 409

_REG_STATUS                = 0x01
_REG_FIRM_MAJ              = 0x02
_REG_FIRM_MIN              = 0x03
_REG_I2C_ADDRESS           = 0x04
_REG_PRESS_COUNT           = 0x05
_REG_LED                   = 0x07
_REG_STATE                 = 0x08
_REG_DOUBLE_CLICK_DETECTED = 0x09
_REG_DEV_ID                = 0x11
_REG_DEBUG                 = 0x12
_REG_DOUBLE_CLICK_DURATION = 0x21
_REG_DEBOUNCE_WINDOW       = 0x23

def _read_bit(x, n):
    return x & 1 << n != 0

def _set_bit(x, n):
    return x | (1 << n)

class PiicoDev_Switch(object):
    @property
    def double_click_duration(self):
        return self._readInt(_REG_DOUBLE_CLICK_DURATION, 2)
    
    @double_click_duration.setter
    def double_click_duration(self, value):
        self._writeInt(_set_bit(_REG_DOUBLE_CLICK_DURATION, 7), value, 2)
        
    @property
    def debounce_window(self):
        return self._readInt(_REG_DEBOUNCE_WINDOW, 2)
    
    @debounce_window.setter
    def debounce_window(self, value):
        self._writeInt(_set_bit(_REG_DEBOUNCE_WINDOW, 7), value, 2)
    
    def __init__(self, bus=None, freq=None, sda=None, scl=None, address=_BASE_ADDRESS, id=None, double_click_duration=300, debounce_window=40):
        try:
            if compat_ind >= 1:
                pass
            else:
                print(compat_str)
        except:
            print(compat_str)
        self.i2c = create_unified_i2c(bus=bus, freq=freq, sda=sda, scl=scl)
        self.address = address
        self.double_click_duration = double_click_duration
        self.debounce_window = debounce_window
        self.last_command_known = False
        self.last_command_success = False
        if type(id) is list and not all(v == 0 for v in id): # preference using the ID argument. ignore id if all elements zero
            assert _max(id) <= 1 and _min(id) >= 0 and len(id) == 4, "id must be a list of 1/0, length=4"
            self.address=8+id[0]+2*id[1]+4*id[2]+8*id[3] # select address from pool
        else: self.address = address # accept an integer
        try:
            if self.readID() != _DEVICE_ID:
                print("* Incorrect device found at address {}".format(address))   
        except:
            print("* Couldn't find a device - check switches and wiring")   

    def _read(self, register, length=1):
        try:
            return self.i2c.readfrom_mem(self.address, register, length)
        except:
            print(i2c_err_str.format(self.address))
            return None
    
    def _write(self, register, data):
        try:
            self.i2c.writeto_mem(self.address, register, data)
        except:
            print(i2c_err_str.format(self.address))
    
    def _readInt(self, register, length=1):
        data = self._read(register, length)
        if data is None:
            return None
        else:
            return int.from_bytes(data, 'big')
        
    def _writeInt(self, register, integer, length=1):
        self._write(register, int.to_bytes(integer, length, 'big'))

    def setI2Caddr(self, newAddr):
        x=int(newAddr)
        assert 8 <= x <= 0x77, 'address must be >=0x08 and <=0x77'
        self._writeInt(_REG_I2C_ADDRESS, x)
        self.addr = x
        sleep_ms(5)
        return 0

    def readFirmware(self):
        v=[0,0]
        v[1]=self._readInt(_REG_FIRM_MAJ)
        v[0]=self._readInt(_REG_FIRM_MIN)
        self.readStatus()
        return (v[1],v[0])

    def readStatus(self):
        sts=self._readInt(_REG_STATUS)
        if sts is not None:
            self.last_command_known = _read_bit(sts, 2)
            self.last_command_success = _read_bit(sts, 1)
    
    def readID(self):
        x=self._readInt(_REG_DEV_ID, 2)
        self.readStatus()
        return x
    
    def readDebug(self):
        x=self._readInt(_REG_DEBUG)
        self.readStatus()
        return x

    def pwrLED(self, x):
        self._writeInt(_REG_LED, int(x)); return 0
            
    def read(self):
        raw_value = self._readInt(_REG_PRESS_COUNT, 2)
        self.readStatus()
        if raw_value is None:
            return(float('NaN'))
        else:
            return raw_value
        
    def read_state(self):
        if self._readInt(_REG_STATE, 1) == 1:
            return False
        else:
            return True
        
    def double_click_detected(self):
        if self._readInt(_REG_DOUBLE_CLICK_DETECTED, 1) == 1:
            return True
        else:
            return False
