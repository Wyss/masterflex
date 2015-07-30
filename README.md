# masterflex
This is a Python library for communicating with Cole-Parmer Masterflex L/S pumps models 07523-80, 07523-90, 07551-00, 07551-10, and 07575-10. Please see the [device manual](http://www.coleparmer.com/Assets/manual_pdfs/07523-80,-90.pdf) for further reference.

## Quick Start
1. Install the package and its dependencies. Dependencies can be found under the requirements .txt file.

			pip install -r requirements.txt
		
2. Connect the satellite pump to the control computer.

3. Find available ports by calling the class method `findSerialPumps()`.

4. Initialize a `MasterflexSerial` object using a pump address and one of these available ports. Pump addresses are integers from 1 through 89, and may be reassigned at a later time. The class itself will take care of establishing and managing the serial connection. Default configurations are provided as part of the class, but these may be overwritten. When a successful connection is established, the satellite will display the pump number on its screen.

			mf = MasterflexSerial(1, '/dev/ttyUSB0')    # Creates a MasterflexSerial object 
	                                                    # with pump address 01 at port /dev/ttyUSB0

5. Commands are issued via the `MasterflexSerial` object and are listed below.

			mf.renumber(2)    # Changes the pump number of mf to 2
			mf.goContinuous() # Runs the pump until prompted to stop
			mf.halt()         # Stops the pump

## Commands List
TODO

## Known Issues
- Commands that involve auxiliary input and output are currently untested.
- The goContinuous command always returns a `<NAK>`, despite being successful in operating the motor.
- After the initial startup step, the enquire command is not working consistently without the workaround (falling back on requestStatus, which should be identical to its default behavior)