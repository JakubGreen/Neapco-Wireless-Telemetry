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
import tkMessageBox
from tkFileDialog import asksaveasfilename
from tkFileDialog import askopenfilename
from tkFileDialog import askdirectory
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
		self.folder = StringVar()
		
		###### GUI Initialization
		Frame.__init__(self,master, bd = 10)
		self.pack(side = TOP)
		#self.wm_title("Feather Receiver")
		
		
		
		self.topFrame = Frame(master=self, padx = 8,pady = 8, bd = 2, relief = GROOVE)
		self.topFrame.pack(side = TOP, fill = X)
		self.startButton = Button(self.topFrame, text = "Start Logging", command = self.startLogging, width = 14)
		self.startButton.pack(side = LEFT)
		
		self.stopButton = Button(self.topFrame, text = "Stop Logging", command = self.stopLogging, width = 14, state = DISABLED)
		self.stopButton.pack(side = RIGHT)
		
		#Button(self.topFrame, text = "Multi-Plot", command = self.plotMultiple).pack(side = LEFT)
		Button(self.topFrame, text = "Plot...", command = self.plot).pack(side = LEFT)
		
		Label(self.topFrame, text = "Log Folder: ").pack(side = LEFT)
		Entry(self.topFrame, width = 30, textvariable = self.folder, text = self.folder.get(), state = DISABLED).pack(side = LEFT)
		Button(self.topFrame, text = "Browse...", command = self.browseFolder).pack(side = LEFT)
		
		self.bottomFrame = Frame(master=self,padx = 8, pady = 8, bd = 2, relief = GROOVE)
		self.bottomFrame.pack(side = BOTTOM, fill = X)
		self.bridgeButton = Button(self.bottomFrame, text = "Add Bridge", command = self.addBridge, width = 14)
		self.bridgeButton.pack(side = LEFT)
		self.bridgeRemove = Button(self.bottomFrame, text = "Remove Bridge", command = self.removeBridge, width = 14)
		self.bridgeRemove.pack(side = RIGHT)	
		
		#self.addBridge() # Initialize with one bridge
		
		Label(self.bottomFrame, text = "Neapco Components LLC: Charles Lee\t2016", font = ("Helvetica","12"), padx = 50).pack(side = BOTTOM)
		
		menubar = Menu(self)
		master.config(menu=menubar)
		
		filemenu = Menu(menubar, tearoff=0)
		master.config(menu=filemenu)
		filemenu.add_command(label = "Save", command = self.saveFile)
		filemenu.add_command(label = "Open", command = self.openFile)
		
	def browseFolder(self):
		path = askdirectory()
		self.folder.set(path)
		print self.folder.get()
		os.chdir("/")
		if os.path.exists(self.folder.get()) is False:
			os.mkdir(self.folder.get())
		os.chdir(self.folder.get())
	def addBridge(self):
		a = Bridge(self.ip.get(),0, self.folder.get(),master=self) # Create new bridge object
		a.x.pack(side = TOP) # Pack it to the top of the window
		self.bridges.append(a) # Add the object to self.bridges
		return a
	def removeBridge(self):
		self.bridges.pop().x.pack_forget()
		
	### Simultaneously starts logging for all selected bridges
	def startLogging(self):
		if not tkMessageBox.askyesno("Start Logging","Are you sure?\nFiles may be overwritten"):
			return
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
			p.terminate() ### Terminate each process
			p.join()		
	def singlePlot(self, path):
		f = open(path, "r")
		content = f.readlines()
		time  = []
		torque = []
		
		counter = 0
		for line in content: ### Find which line the data starts on
			counter = counter + 1
			if line.find("DM_Start=") != -1:
				break
				
		for x in xrange(counter,len(content)-1): ### Starting on the line number found from previous loop
			y = content[x].split("\t") 
			time.append(y[0])
			torque.append(y[1])	
		#if show:		
		plt.plot(time,torque)
		#plt.xlabel("Time (microseconds)")
		#plt.ylabel("Torque (inch-pounds)")
		#plt.title("Time vs. Torque")
		#plt.show()
		return (time,torque)		
	def plotMultiple(self):
		for b in self.bridges:
			if b.checkVar.get():
				xy = b.singlePlot(False) ### Call the singlePlot method for each instance
				plt.plot(xy[0],xy[1]) ### Show the plot
		plt.xlabel("Time (microseconds)")
		plt.ylabel("Torque (inch-pounds)")
		plt.title("Time vs. Torque")
		plt.show()
	def plot(self):
		paths = askopenfilename(defaultextension = ".txt", multiple = True)
		for p in paths:
			self.singlePlot(p)
		plt.xlabel("Time (microseconds)")
		plt.ylabel("Torque (inch-pounds)")
		plt.title("Time vs. Torque")
		plt.show()
	def saveFile(self):
		path = asksaveasfilename(defaultextension = '.lee', filetypes = [('Configuration Files','.lee')])
		config = open(path, "w")
		config.write(self.folder.get()+ n)
		for x in self.bridges :
			config.write(str(x) + n)
		config.close()
	def openFile(self):
		path = askopenfilename(defaultextension = ".lee", filetypes = [('Configuration Files','.lee')])
		config = open(path, "r")
		lines = config.read().split(n)
		self.folder.set(lines[0])
		
		os.chdir("/")
		if os.path.exists(self.folder.get()) is False:
			os.mkdir(self.folder.get())
		os.chdir(self.folder.get())
		
		for b in xrange(len(self.bridges)):
			self.removeBridge()
		for l in range(1,len(lines)-1):
			fields = lines[l].split(",")
			b = self.addBridge()
			b.portVar.set(int(fields[0]))
			b.name.set(fields[1])
			b.mSlope.set(float(fields[2]))
			b.yIntercept.set(float(fields[3]))	
			b.ip = self.ip.get()
			b.folder = str(lines[0])
		config.close()
		
class Bridge():
	stringFormat = "{} \t {}"
	def __init__(self,ip,port,folderPath,master):
		###### Tkinter Varibales
		self.x = Frame()
		self.isLogging = BooleanVar()
		self.checkVar = IntVar()
		self.portVar = IntVar()
		self.portVar.set(port)
		self.filePathVar = StringVar()
		self.name = StringVar()
		
		###### Variables
		self.ip = ip
		self.folder = folderPath
		
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
	def __repr__(self):
		return str(self.portVar.get()) + "," + self.name.get() + "," + str(self.mSlope.get()) + "," + str(self.yIntercept.get())
		
	#### Starts Writing to File
	def startLogging(self):
		print('Sampling system on Port: ' + str(self.portVar.get()))
		self.isLogging.set(True)
		date = datetime.datetime.now()
		date = str(date).split(".")[0]
		space = date.split(" ")
		date = space[0] + "_" + space[1]
		colons = date.split(":")
		date = colons[0]+ "." + colons[1] + "." + colons[2]
		
		### Network Connection
		sock = socket.socket(socket.AF_INET, # Internet
								socket.SOCK_DGRAM) # UDP
		sock.bind((self.ip, (self.portVar.get())))
		
		### File Setup
		nameString = str(date) + "_" + self.name.get()
		fileLog = open(nameString, "w+")
		
		### Necessary formatting for InField compatibility
		fileLog.write("DM_TestTitle=" + n)
		fileLog.write(self.filePathVar.get() + n + 'Program Start Time: ' + str(date) + n)
		fileLog.write("Calibration Values: Slope = " + str(self.mSlope.get()) + ", Y-Intercept = " + str(self.yIntercept.get()) + n
			+ "Port: " +  str(self.portVar.get()) + n)
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
		prevAdjusted = 0
		while True: ### Read packets until told to stop
			data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
			packetSplit = data.decode('utf-8')
			lineSplit = packetSplit.split('\n')
			for line in lineSplit:				
				fields = line.split(',')
				calibratedData = round(self.mSlope.get()*float(fields[1]) + self.yIntercept.get(),1)
				if isFirst:
					timeOffset = (-1)*int(fields[0]) # Take the time on the very first packet and store it in to timeOffset
					isFirst = False
				if(int(fields[0]) < prevTime): # If the processor clock has overflowed
					timeOffset = prevAdjusted # Then edit the time offset value
				adjustedTime = int(fields[0])+timeOffset # Shift every subsequent packet by the timeOffset
				fileLog.write(str(adjustedTime) + '\t' + str(calibratedData) + n) 
				
				prevTime = int(fields[0]) 
				prevAdjusted = adjustedTime					
	def createWidgets(self): 
		check = Checkbutton(self.x,text = "Include\t\t",variable = self.checkVar)	
		check.pack(side=LEFT)
	
		Label(self.x, text = "Name").pack(side = LEFT)
		Entry(self.x, textvariable = self.name, width = 35).pack(side = LEFT)
		

				
		L1 = Label(self.x, text = "  PORT")
		L1.pack(side=LEFT)
		portEntry = Entry(self.x, width = 5, textvariable = self.portVar) 
		portEntry.pack(side=LEFT)
		
		
		#L1 = Label(self.x, text = "   File")
		#L1.pack(side=LEFT)
		#fileEntry = Entry(self.x,width = 35,textvariable = self.filePathVar, text = self.filePathVar.get()) 
		#fileEntry.pack(side=LEFT)
		
		#browseButton = Button(self.x, command = self.saveAs, text = "Browse...")
		#browseButton.pack(side = LEFT)
		
		calibrateButton = Button(self.x, command = self.calibrate, text = "Calibrate")
		calibrateButton.pack(side = LEFT)
		
		#Button(self.x, command = partial(self.singlePlot,True), text = "Plot").pack(side = LEFT)
		
	def calibrate(self):
		#if len(self.pointList) is not 0:
					
		t = Toplevel(self.x) # Open window
		t.wm_title("\tPORT: " + str(self.portVar.get()) + " Calibration")
		
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
		Button(master = b, command = partial(self.linReg), text = "Calibrate!").pack(side = TOP)
		
		Label(b, text = "Slope", padx = 15).pack(side = TOP)
		Entry(b, textvariable = self.mSlope).pack(side = TOP)
		Label(b, text = "Y Intercept", padx = 15).pack(side = TOP)
		Entry(b, textvariable = self.yIntercept).pack(side = TOP)
		
		Button(b, command = partial(self.exitWindow,t), text = "OK").pack(side = BOTTOM)

		
	def saveAs(self):
		print 'Please Select File:'
		file_path = asksaveasfilename(defaultextension = '.txt', filetypes = [('Text Files','.txt')])
		self.filePathVar.set(file_path)
	
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
	root.wm_title("Gage Logger")
		
	app = SensorNetwork(master=root)
	app.mainloop()






