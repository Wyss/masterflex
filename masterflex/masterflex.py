import serial
import sys
import glob

# From http://stackoverflow.com/questions/12090503/
#      listing-available-com-ports-with-python
def listSerialPorts():
    """Lists serial ports
    :raises EnvironmentError:
        On unsupported or unknown platforms
    :returns:
        A list of available serial ports
    """
    if sys.platform.startswith('win'):
        ports = ['COM' + str(i + 1) for i in range(256)]

    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this is to exclude your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')

    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')

    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

class MasterflexSerial():
    
    @classmethod
    def findSerialPumps(cls, pump_addrs=[1]):
        ''' Finds any enumerated syringe pumps on the local com / serial ports.
        Returns list of (<ser_port>, <status>) tuples.
        '''
        found_devices = []
        for port_path in listSerialPorts():
            for pump_addr in pump_addrs:
                try:
                    p = cls(pump_addr, port_path)
                    status = p.requestStatus()
                    if status:
                        found_devices.append((p, port_path, status))
                except OSError as e:
                    if e.errno != 16:   # Resource busy
                        raise
                except:
                    pass
        return found_devices
    
    SERIAL_CONFIG = {
        'bytesize': serial.SEVENBITS, 
        'baudrate': 4800, 
        'parity': serial.PARITY_ODD,
        'timeout': 1
    }
    
    # Control Codes
    STX = '\x02'
    ACK = '\x06'    
    ENQ = '\x05'
    CR = '\x0D'
    NAK = '\x15'
    CAN = '\x18'
    
    def __init__(self, pump_addr, ser_port, configs=None):
        self.initialized = False
        self.pump_addr = pump_addr
        self.ser_port = ser_port
        self.ser = None
        self._registerSer(configs or MasterflexSerial.SERIAL_CONFIG)
        self.enquire()
        self._assignNumber()
        self.initialized = True
        
    ################ Serial port handling ###############
        
    def _registerSer(self, configs):
        ''' Initializes the Serial object '''
        self.ser = serial.Serial(port=self.ser_port, **configs)
        
    def __del__(self):
        ''' Ensures that the Serial object is closed before deletion '''
        self.ser.close()
        
    ################ Communication with satellite ################
        
    def _sendReceive(self, cmd):
        ''' Sends a command to the satellite and returns the response '''
        try:
            frame_out = bytearray([bytes(c) for c in cmd])
            self._sendFrame(frame_out)
            frame_in = self._receiveFrame()
            if frame_in:
                return frame_in
        except serial.SerialException:
            return
        
    def _sendFrame(self, frame):
        ''' Writes the command to the port '''
        self.ser.write(frame)
    
    def _receiveFrame(self):
        ''' Reads the response from the satellite from the port
            and returns it '''
        raw_data = b''
        raw_byte = self.ser.read()
        if raw_byte == MasterflexSerial.STX:    # Standard response, starts with <STX>
            while raw_byte:
                raw_data += raw_byte
                raw_byte = self.ser.read()
            return raw_data
        else:   # In the case of <ACK> or <NAK>   
            raw_data += raw_byte 
            return raw_data
        
    ################ Commands ################
    
    def _standardCommand(self, cmd_char, *params):
        ''' Builds and returns a formatted string 
            representation of a standard command '''
        cmd = "P%02d" % self.pump_addr + cmd_char
        for param in params:
            cmd += "%s" % param
        return MasterflexSerial.STX + cmd + MasterflexSerial.CR
        
    def _assignNumber(self):
        ''' On startup, set the pump number '''
        if not self.initialized:
            cmd = self._standardCommand('')
            return self._sendReceive(cmd)
    
    def requestAuxiliaryInputStatus(self):
        ''' (A) Request auxiliary input status
            Note: Currently untested '''
        cmd = self._standardCommand('A')
        return self._sendReceive(cmd)
    
    def controlAuxiliaryOutputsOnG(self, aux1, aux2):
        ''' (B) Control auxiliary outputs when G command executed
            Note: Currently untested '''
        cmd = self._standardCommand('B', aux1, aux2)
        return self._sendReceive(cmd)
    
    def requestCumulative(self):
        ''' (C) Request cumulative revolution counter '''
        cmd = self._standardCommand('C')
        return self._sendReceive(cmd)
    
    def requestToGo(self):
        ''' (E) Request revolutions to go '''
        cmd = self._standardCommand('E')
        return self._sendReceive(cmd)
    
    def go(self):
        ''' (G) Go Turn pump on and auxiliary output if preset,
            run for number of revolutions set by V command '''
        cmd = self._standardCommand('G')
        if abs(int(float(self.requestMotorSpeed()[2:-1]))) <= 0.1:
            return self.halt()
        else:        
            return self._sendReceive(cmd)
    
    def goContinuous(self):
        ''' (G) Go Turn pump on and auxiliary output if preset, 
            run continuously until Halt '''
        cmd = self._standardCommand('G', 0)
        if int(float(self.requestMotorSpeed()[2:-1])) == 0:
            return self.halt()
        else:
            return self._sendReceive(cmd)
    
    def halt(self):
        ''' (H) Halt (turn pump off) '''
        cmd = self._standardCommand('H')
        return self._sendReceive(cmd)
    
    def requestStatus(self):
        ''' (I) Request status data '''
        cmd = self._standardCommand('I')
        return self._sendReceive(cmd)
    
    def requestFrontPanelSwitch(self):
        ''' (K) Request front panel switch pressed since last K command '''
        cmd = self._standardCommand('K')
        return self._sendReceive(cmd)
    
    def enableLocal(self):
        ''' (L) Enable local operation '''
        cmd = self._standardCommand('L')
        return self._sendReceive(cmd)
        
    def controlAuxiliaryOutputs(self, aux1, aux2):
        ''' (O) Control auxiliary outputs immediately without affecting drive
            Note: Currently untested '''
        cmd = self._standardCommand('O', aux1, aux2)
        return self._sendReceive(cmd)
    
    def enableRemote(self):
        ''' (R) Enable remote operation '''
        cmd = self._standardCommand('R')
        response = self._sendReceive(cmd)
        return response
        
    def requestMotorSpeed(self):
        ''' (S) Request motor direction and rpm '''
        cmd = self._standardCommand('S')
        return self._sendReceive(cmd)
    
    def setMotorSpeed(self, rpm):
        ''' (S) Set motor direction and rpm 
            Note: Input MUST be a string, 
            format is +xxx.x, -xxx.x, +xxxx, -xxxx (+ is CW, - is CCW)
            Value must be -100 <= x <= 100 '''
        cmd = self._standardCommand('S', rpm)
        return self._sendReceive(cmd)        
    
    def renumber(self, pump_number):
        ''' (U) Change satellite number (<= 89) '''
        if pump_number < 100:
            cmd = self._standardCommand('U', pump_number)
            response = self._sendReceive(cmd)
            if response == MasterflexSerial.ACK:
                self.pump_addr = int(pump_number)
            return response
        else:
            return MasterflexSerial.NAK
    
    def setRevolutions(self, revolutions):
        ''' (V) Set number of revolutions to run (< 99999.99) '''
        cmd = self._standardCommand('V', revolutions)
        return self._sendReceive(cmd)
    
    def zeroToGo(self):
        ''' (Z) Zero revolutions to go counter '''
        cmd = self._standardCommand('Z')
        return self._sendReceive(cmd)
    
    def zeroCumulative(self):
        ''' (Z) Zero cumulative revolutions '''
        cmd = self._standardCommand('Z', 0)
        return self._sendReceive(cmd)
    
    def cancel(self):
        ''' (<CAN>) Terminates line of data up to and including 
            STX (used primarily for keyboard input)
            Note: Currently untested '''
        return self._sendReceive(MasterflexSerial.CAN)
    
    def enquire(self):
        ''' (<ENQ>) Enquire which satellite has activated its RTS line
            Functions like an "I" command after startup
            FIX: Tested, but doesn't receive status consistently after startup '''
        return self._sendReceive(MasterflexSerial.ENQ) or self.requestStatus()
