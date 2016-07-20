# Created By: Charles Lee
# Date: 7/16/2016
# Description: The program reads wirelessly transmitted data from multiple sensors and saves it on the local SD card.
# Usage: The program simultaneously reads multiple UDP streams and writes them to ".txt" files.
#	The output files are formatted to be imported into the InField data analysis software.


import socket
import serial # import Serial Library
from numpy import array, ones, linalg # Import numpy
import sys
import os
from Tkinter import * 
from tkFileDialog import asksaveasfilename
import datetime
import thread
from functools import partial
import matplotlib.pyplot as plt
from multiprocessing import Process

n = chr(13) + chr(10) + ""


class SensorNetwork(Frame):
	def __init__(self,master=None):
		
		### List of process objects for parallel computing
		self.processes = []
		
		### List of bridges
		self.bridges = []
		
		###### Tkinter variables
		self.ip = StringVar()
		self.ip.set("0.0.0.0")	
		self.isLogging = BooleanVar()
		
		###### GUI Initialization
		Frame.__init__(self,master, bd = 10)
		self.pack(side = TOP)
		#self.wm_title("Feather Receiver")
		
		self.topFrame = Frame(master=self, padx = 8,pady = 8, bd = 2, relief = GROOVE)
		self.topFrame.pack(side = TOP, fill = X)
		self.startButton = Button(self.topFrame, text = "Start Logging", command = self.startLogging, width = 18)
		self.startButton.pack(side = LEFT)
		
		self.stopButton = Button(self.topFrame, text = "Stop Logging", command = self.stopLogging, width = 18, state = DISABLED)
		self.stopButton.pack(side = RIGHT)
		
		Button(self.topFrame, text = "Multi-Plot", command = self.plotMultiple).pack(side = LEFT)
		
		self.bottomFrame = Frame(master=self,padx = 8, pady = 8, bd = 2, relief = GROOVE)
		self.bottomFrame.pack(side = BOTTOM, fill = X)
		self.bridgeButton = Button(self.bottomFrame, text = "Add Bridge", command = self.addBridge, width = 18)
		self.bridgeButton.pack(side = LEFT)
		self.bridgeRemove = Button(self.bottomFrame, text = "Remove Bridge", command = self.removeBridge, width = 18)
		self.bridgeRemove.pack(side = RIGHT)	
		
		self.addBridge() # Initialize with one bridge
	
		
	def addBridge(self):
		a = Bridge(self.ip.get(),0, master=self) # Create new bridge object
		a.x.pack(side = TOP) # Pack it to the top of the window
		self.bridges.append(a) # Add the object to self.bridges
	def removeBridge(self):
		self.bridges.pop().x.pack_forget()
		
	### Simultaneously starts logging for all selected bridges
	def startLogging(self):
		self.startButton.configure(state = DISABLED)
		self.stopButton.configure(state = NORMAL)
		for b in self.bridges: ### Loop through list of sensors
			if b.checkVar.get(): ### if box is checked
				p = Process(target = b.startLogging)
				self.processes.append(p)
				p.start()

		
	
	def stopLogging(self):
		print ("Stopping Data Collection")
		self.startButton.configure(state = NORMAL)
		self.stopButton.configure(state = DISABLED)
		for p in self.processes: ### Iterate through list of process objects
			p.terminate()
			p.join()
			
			
	def plotMultiple(self):
		for b in self.bridges:
			if b.checkVar.get():
				xy = b.singlePlot(False) ### Call the singlePlot method for each instance
				plt.plot(xy[0],xy[1]) ### Show the plot
		plt.xlabel("Time (microseconds)")
		plt.ylabel("Torque (inch-pounds)")
		plt.title("Time vs. Torque")
		plt.show()
		
class Bridge():
	stringFormat = "{} \t {}"
	def __init__(self,ip,port,master):
		###### Tkinter Varibales
		self.x = Frame()
		self.isLogging = BooleanVar()
		self.checkVar = IntVar()
		self.portVar = IntVar()
		self.portVar.set(port)
		self.filePathVar = StringVar()
		
		###### Variables
		self.ip = ip
		
		###### Interface Initialization
		Frame.__init__(self.x,master, bd = 2, padx = 3, pady = 3)
		self.x.pack(side=LEFT)
		self.createWidgets()
		
		
		###### linear Calibration coefficents
		###### Calibrated = mSlope * Uncalibrated + yIntercept
		self.mSlope = DoubleVar()
		self.mSlope.set(1)
		self.yIntercept = DoubleVar(0)
		self.pointCount = 0
		self.bitPoints = []
		self.torquePoints = []
		self.isFirstCalib = True
		self.bitEntryList = []
		self.torqueEntryList = []
		self.pointList = []
		
		
	#### Starts Writing to File
	def startLogging(self):
		print('Sampling system on Port: ' + str(self.portVar.get()))
		self.isLogging.set(True)
		
	
		
		### Network Connection
		sock = socket.socket(socket.AF_INET, # Internet
								socket.SOCK_DGRAM) # UDP
		sock.bind((self.ip, (self.portVar.get())))
		
		### File Setup
		fileLog = open(self.filePathVar.get(), "wb")
		
		### Necessary formatting for InField compatibility
		fileLog.write("DM_TestTitle=" + n)
		fileLog.write(str(self.file_path) +'\n' + 'Program Start Time: ' + str(datetime.datetime.now()) + n)
		fileLog.write("Calibration Values: Slope = " + str(self.mSlope.get()) + ", Y-Intercept = " + str(self.yIntercept.get()) + n)
		fileLog.write("DM_Operator=" + n)
		fileLog.write("DM_NumLogChans=2" + n)
		fileLog.write("DM_NumDataModes=1" + n)
		
		fileLog.write("DM_LogicalChan=1" + n)
		fileLog.write("DM_ChanType=SEQUENTIAL" + n)
		fileLog.write("DM_ChanName=1" + n)
		fileLog.write("DM_NumDims=2" + n)
		fileLog.write("DM_DataMode=1" + n)
		fileLog.write("DM_DataModeType=TIMHIS" + n)
		fileLog.write("DM_AxisLabel.Dim1=[]" + n)
		fileLog.write("DM_AxisLabel.Dim2=Time" + n)
		fileLog.write("DM_AxisUnits.Dim1=[]" + n)
		fileLog.write("DM_AxisUnits.Dim2=us" + n)
		
		fileLog.write("DM_LogicalChan=2" + n)
		fileLog.write("DM_ChanType=SEQUENTIAL" + n)
		fileLog.write("DM_ChanName=1" + n)
		fileLog.write("DM_NumDims=2" + n)
		fileLog.write("DM_DataMode=1" + n)
		fileLog.write("DM_DataModeType=TIMHIS" + n)
		fileLog.write("DM_AxisLabel.Dim1=[]" + n)
		fileLog.write("DM_AxisLabel.Dim2=Torque" + n)
		fileLog.write("DM_AxisUnits.Dim1=[]" + n)
		fileLog.write("DM_AxisUnits.Dim2=in-lb" + n)
		
		fileLog.write("DM_Start=" + n)
		
		isFirst = True ### Boolean to track start time (time offset)
		timeOffset = 0
		prevTime = 0		
		while True: ### Read packets until told to stop
			if self.isLogging.get():
				data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
				packetSplit = data.decode('utf-8')
				lineSplit = packetSplit.split('\n')
				
				for line in lineSplit:
					fields = line.split(',')
					if isFirst:
						timeOffset = int(fields[0]) # Take the time on the very first packet and store it in to timeOffset
						isFirst = False
					calibratedData = round(self.mSlope.get()*int(fields[1]) + self.yIntercept.get(),1)
					adjustedTime = int(fields[0])-timeOffset # Subtracting every subsequent packet by the timeOffset
					if(adjustedTime < prevTime): # If the processor clock has overflowed
						timeOffset = timeOffset - prevTime
					prevTime = adjustedTime
					fileLog.write(str(adjustedTime) + '\t' + str(calibratedData) + n) # Writing each datapoint to file
					#print(self.stringFormat.format(str(adjustedTime),calibratedData))	# Live output for diagnostics			
			else:		
				fileLog.close()	
				sock.close()
				return				
	def createWidgets(self): 
		check = Checkbutton(self.x,text = "Include",variable = self.checkVar)	
		check.pack(side=LEFT)
				
		L1 = Label(self.x, text = "  PORT")
		L1.pack(side=LEFT)
		portEntry = Entry(self.x, width = 5, textvariable = self.portVar) 
		portEntry.pack(side=LEFT)
		
		
		L1 = Label(self.x, text = "   File")
		L1.pack(side=LEFT)
		fileEntry = Entry(self.x,width = 35,textvariable = self.filePathVar, text = self.filePathVar.get()) 
		fileEntry.pack(side=LEFT)
		
		browseButton = Button(self.x, command = self.saveAs, text = "Browse...")
		browseButton.pack(side = LEFT)
		
		calibrateButton = Button(self.x, command = self.calibrate, text = "Calibrate")
		calibrateButton.pack(side = LEFT)
		
		Button(self.x, command = partial(self.singlePlot,True), text = "Plot").pack(side = LEFT)
		
	def calibrate(self):
		#if len(self.pointList) is not 0:
					
		t = Toplevel(self.x) # Open window
		t.wm_title("PORT: " + str(self.portVar.get()) + " Calibration")
		
		a = Frame(t)
		a.pack(side = LEFT)
		
		b = Frame(t)
		b.pack(side = RIGHT)

		c = Frame(a)
		c.pack(side = TOP)
		
		d = Frame(a)
		d.pack(side = BOTTOM)
		
		Label(c, text = "Bit Value", padx = 15).grid(column = 0,row = 0)
		Label(c, text = "Torque (in-lbs)", padx = 15).grid(column = 2, row = 0)
	
			
		if len(self.pointList) == 0: # If the list of calibration points is empty
			for i in xrange(3):
				self.addPoint(a)
		else:
			tempList = self.pointList # Store points in temporary list
			self.pointList = [] # Empty out list
			for x in tempList: # Copy points over
				temp = calibrationPoint(a)
				temp.bitValue.set(x.bitValue.get())
				temp.torqueValue.set(x.torqueValue.get())
				self.pointList.append(temp)
		
		Button(master = d, command = partial(self.addPoint,a), text = "Add Point").pack(side = LEFT,fill = X, padx = 10)	
		Button(master = d, command = partial(self.removePoint), text = "Remove Point").pack(side = LEFT, fill = X, padx = 10)
		#Button(master = b, command = self.printEntry, text = "show values").pack(side = TOP)				
		Button(master = b, command = partial(self.linReg), text = "Calibrate!").pack(side = TOP)
		
		Label(b, text = "Slope", padx = 15).pack(side = TOP)
		Entry(b, textvariable = self.mSlope).pack(side = TOP)
		Label(b, text = "Y Intercept", padx = 15).pack(side = TOP)
		Entry(b, textvariable = self.yIntercept).pack(side = TOP)
		
		Button(b, command = partial(self.exitWindow,t), text = "OK").pack(side = BOTTOM)
	def singlePlot(self, show):
		f = open(self.filePathVar.get())
		content = f.readlines()
		time  = []
		torque = []
		
		counter = 0
		for line in content: ### Find which line the data starts on
			counter = counter + 1
			if line.find("DM_Start=") != -1:
				break
				
		for x in xrange(counter,len(content)-1):
			y = content[x].split("\t")
			time.append(y[0])
			torque.append(y[1])	
		if show:		
			plt.plot(time,torque)
			plt.xlabel("Time (microseconds)")
			plt.ylabel("Torque (inch-pounds)")
			plt.title("Time vs. Torque")
			plt.show()
		return (time,torque)
		
	def saveAs(self):
		print 'Please Select File:'
		self.file_path = asksaveasfilename(defaultextension = '.txt', filetypes = [('Text Files','.txt')])
		self.filePathVar.set(self.file_path)
	
	def addPoint(self, frame):
		x = calibrationPoint(frame)
		self.pointList.append(x)
	
	def removePoint(self):
		self.pointList.pop().pack_forget()
		
	# Used for debugging only
	def printEntry(self):
		for x in self.pointList:
			print("bit value: "+ str(x.bitValue.get()))
			print("Torque Value value: "+ str(x.torqueValue.get()))
	
	# Finds slope and y intercept from calibration point cloud		
	def linReg(self):		
		temp1 = []
		temp2 = []
		for x in self.pointList:
			temp1.append(x.bitValue.get())
			temp2.append(x.torqueValue.get())
			
		A = array([temp1,ones(len(temp1))])
		B = array([temp2])
		w = linalg.lstsq(A.T,B.T)[0]
		
		m = round(float(w[0]),3)
		y = round(float(w[1]),3)
		
		self.mSlope.set(m)
		self.yIntercept.set(y)
		
	# Exits a top level window
	def exitWindow(self, frame):
		frame.withdraw()
	def reopenWindow(self, frame):
		frame.update()
		frame.reiconify()
		
	def plot(self) :
		t = Toplevel()
		t.wm_title("PORT: " + str(self.portVar.get()) + " Plot")
		
		
class calibrationPoint(Frame) :
	def __init__(self, master):
		self.bitValue = DoubleVar(0)
		self.torqueValue = DoubleVar(0)
		
		Frame.__init__(self,master)
		self.pack(side = TOP)
		
		self.createWidgets()
	def createWidgets(self) :
		x = Entry(self, textvariable = self.bitValue, width = 8)
		x.pack(side = LEFT, padx = 10, pady = 2)
		y = Entry(self, textvariable = self.torqueValue, width = 8)
		y.pack(side = LEFT, padx = 10, pady = 2)
		return
		
		
###### Running code
if __name__ == '__main__':
	root = Tk()
	root.wm_title("Feather Receiver")
	app = SensorNetwork(master=root)
	app.mainloop()






