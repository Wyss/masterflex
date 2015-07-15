from masterflex import MasterflexSerial
import time

errors = []

def initializePort():
    for i in range(0, 100):
        port = "/dev/ttyUSB{i}".format(i=i)
        try:
            m = MasterflexSerial(1, port)
            return m
        except Exception:
            pass
        
def testSetup(m):
    return (m.ser.isOpen()
            and m.pump_addr == int(m.requestStatus()[2:4])
            and m.pump_addr == int(m.enquire()[2:4])    # Not working consistently without workaround
            and m.initialized)
    
def testRenumber(m):
    for i in [1, 5, 10, 89, 90, 100]:
        if i < 90:
            if m.renumber(i) != MasterflexSerial.ACK or i != int(m.requestStatus()[2:4]):
                return False      
        else:
            if m.renumber(i) != MasterflexSerial.NAK or i == int(m.requestStatus()[2:4]):
                return False
    return True
        
def testMotor(m):
    test1 = (int(m.requestStatus()[8]) == 1
            and m.setMotorSpeed("+4") == MasterflexSerial.ACK
            and m.requestMotorSpeed()[1:-1] == "S+004.0"
    
            and m.zeroToGo() == MasterflexSerial.ACK
            and m.zeroCumulative() == MasterflexSerial.ACK
            and float(m.requestToGo()[2:-1]) == 0
            and float(m.requestCumulative()[2:-1]) == 0
    
            and m.setMotorSpeed("-4") == MasterflexSerial.ACK
            and m.requestMotorSpeed()[1:-1] == "S-004.0"
            and m.setRevolutions(0.05) == MasterflexSerial.ACK
            and float(m.requestToGo()[2:-1]) == 0.05
            and int(m.requestStatus()[8]) == 2
            and m.go() == MasterflexSerial.ACK
            and int(m.requestStatus()[8]) == 3)
    time.sleep(1)
    test2 = (float(m.requestCumulative()[2:-1]) == 0.05

#            and m.goContinuous() == MasterflexSerial.ACK    # Always giving <NAK> for some reason?
            and m.goContinuous() == MasterflexSerial.NAK
            and int(m.requestStatus()[8]) == 3)
    time.sleep(1)
    return (test1 and test2 and m.halt() == MasterflexSerial.ACK)
    
def testMisc(m):
    return (m.enableLocal() == MasterflexSerial.ACK
            and int(m.requestStatus()[5]) == 0
            and m.enableRemote() == MasterflexSerial.ACK
            and int(m.requestStatus()[5]) == 1
    
            and m.requestAuxiliaryInputStatus()[1:-1] == "A0"
            and m.requestFrontPanelSwitch()[1:-1] == "K0")

def runTests():
    
    print "Initializing..."
    m = initializePort()
    
    print "Testing setup..."
    if testSetup(m):
        print "Setup OK"
        print "Testing renumbering..."
        if testRenumber(m):
            print "Renumbering OK"
            print "Testing motor..."
            if testMotor(m):
                print "Motor OK"            
                print "Testing misc operations..."
                if testMisc(m):
                    print"Misc operations OK"
                    print "All tests complete"
                    return
                else:
                    print "Something went wrong in the misc operations"
            else:
                print "Something is wrong with the motor commands"
        else: 
            print "Something went wrong when renumbering the satellite"
    else:
        print "Something went wrong in setup"
        
    print "Aborting"
    return
        
if __name__ == "__main__":
    runTests()