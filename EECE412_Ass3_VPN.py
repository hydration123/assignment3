#!/bin/env python
#----------------------------------------------------------------------------
# Name:			EECE412_Ass3_VPN.py
#
# Program:		Simple implementation of VPN using
#				Diffie-Hellman key enchange protocol
#
# Authors:		Jobin Ansari-Gilani	  jobinansari@hotmail.com
#				Ivan Cherapau	cherapau@gmail.com
#				Scott Hazlett	scotthazlett@gmail.com
#				Mina Savovic   minasavovic@gmail.com
#
# Created:		13 Oct 2013
#----------------------------------------------------------------------------

import wx, sys
from socket import *
from EECE412_Ass3_VPN_wdr import *
from EECE412_Ass3_Server import ServerThread
from EECE412_Ass3_Client import ClientThread

# CONSTANTS -- we use functions because Python does not understand constants
def STR_NOT_CONNECTED(): return "Not Connected."
def STR_SERVER_USAGE():
	return "Usage: provide valid IPv4 destination address and a destination port between 1024 and 49151 inclusive\n"
def STR_CLIENT_USAGE():
	return """Usage: provide valid localhost port between 1024 and 49151 inclusive,
	and provide valid IPv4 destination address and a destination port between 1024 and 49151 inclusive\n"""
def BUFFER_SIZE(): return 65535

# WDR: classes

class MyFrame(wx.Frame):
	# Constructor
	def __init__(self, parent, id, title,
		pos = wx.DefaultPosition, size = wx.DefaultSize,
		style = wx.DEFAULT_FRAME_STYLE ):
		wx.Frame.__init__(self, parent, id, title, pos, size, style)
																				 
		# Instantiate MenuBar and ToolBar
		self.CreateMyMenuBar()
		self.CreateMyToolBar()
		
		self.CreateStatusBar(1)
		self.SetStatusText(STR_NOT_CONNECTED())
		
		# This took a while to figure out ...
		self.sizer = MainSizer(self, -1, "Blah")
		self.SetSizer(self.sizer)
		self.GetSizer().Fit( self )
		
		# Obtain references to the elements inside of MainSizer
		# that we just attached to the wx.Frame
		# These are the GUI objects that we click on
		self.mode		 = self.FindWindowById(ID_CHOICE_MODE)
		self.remote_ip	 = self.FindWindowById(ID_TEXTCTRL_REMOTE_SERVER_IP)
		self.remote_port = self.FindWindowById(ID_TEXTCTRL_REMOTE_SERVER_PORT)
		self.local_port	 = self.FindWindowById(ID_TEXTCTRL_LOCAL_PORT)
		self.shared_key	 = self.FindWindowById(ID_TEXTCTRL_SHARED_KEY)
		self.data		 = self.FindWindowById(ID_TEXTCTRL_DATA)
		self.console	 = self.FindWindowById(ID_TEXTCTRL_CONSOLE)
		self.step		 = self.FindWindowById(ID_BUTTON_STEP)
		self.connect	 = self.FindWindowById(ID_BUTTON_CONNECT)
		self.send        = self.FindWindowById(ID_BUTTON_SEND)
		
		# The client or server thread
		self.mythread = None
		
		# Functions (or "CallBack"s) that we call when
		# something important has been clicked on
		# I think we can also capture asynchornous events
		# WDR: handler declarations for MyFrame
		wx.EVT_BUTTON(self, ID_BUTTON_STEP, self.ButtonStepCB)
		wx.EVT_BUTTON(self, ID_BUTTON_SEND, self.ButtonSendCB)
		wx.EVT_BUTTON(self, ID_BUTTON_CONNECT, self.ButtonConnectCB)
		wx.EVT_CHOICE(self, ID_CHOICE_MODE, self.ChoiceModeCB)
		wx.EVT_MENU(self, wx.ID_ABOUT, self.OnAbout)
		wx.EVT_MENU(self, wx.ID_EXIT, self.OnQuit)
		wx.EVT_CLOSE(self, self.OnCloseWindow)
		
		# Set selection of "mode" to "Server"
		self.mode.SetSelection(0)

		self.SetServerModeDetails()

	def SetClientModeDetails(self):
		self.remote_port.SetValue("12345")
		self.remote_ip.SetValue(gethostbyname(getfqdn())) # xx.xx.xx.xx format
		self.local_port.SetValue("12399")

	def SetServerModeDetails(self):
		self.local_port.SetValue("12345")

	# WDR: methods for MyFrame
	def CreateMyMenuBar(self):
		self.SetMenuBar( MyMenuBarFunc() )
	
	def CreateMyToolBar(self):
		tb = self.CreateToolBar(wx.TB_HORIZONTAL|wx.NO_BORDER)
		MyToolBarFunc( tb )
	
	# WDR: handler implementations for MyFrame
	
	def ButtonSendCB(self, event):
		if(self.mythread == None):
			print "Send called on null thread"
		elif(self.mythread.isAlive() == False):
			print "Send called on dead thread"
		else:
			self.mythread.nextstep()
		

	def ButtonStepCB(self, event):
		if(self.mythread == None):
			print "Step called on null thread"
		elif(self.mythread.isAlive() == False):
			print "Step called on dead thread"
		else:
			self.mythread.nextstep()

	def ButtonConnectCB(self, event):
		selection = self.mode.GetSelection()
		print "selection is " + str(selection)
		
		# Is it client or server mode?
		if selection == 0 :	 # Server
			# Setup server for listening mode
			port = self.local_port.GetValue()
			print "Listening for client on port:" + port
			
			if self.IsValidPort( port ):
				# we can now attempt to bind to port and
				# start listening for incoming clients
				self.console.AppendText("Binding to port " + port + " ...\n")
				self.SetStatusText("Binding to port " + port + "...")
				
				 ###################################################
				# BEGIN SOCKET CODE TO BIND AND LISTEN
				###################################################
				
				#from EECE412_Ass3_Server import ServerThread
				self.KillThread()
				self.mythread = ServerThread(frame=self, port=port, buffersize=BUFFER_SIZE())
				self.mythread.start() 
				
				
					###################################################
					# END SOCKET CODE TO BIND AND LISTEN
					###################################################
					
			else:
				# local port is invalid range; show usage
				self.console.AppendText(STR_SERVER_USAGE())
				return
		
			

# Here is my rudimentary server code from my socket programming assignment
#  serverSocket = socket(AF_INET, SOCK_STREAM) 
#  port = 12373;
#  host = getfqdn()
#
#  print "Server listening on ", (host, port)
#
#  #Prepare a sever socket on localhost on port 'port'
#  serverSocket.bind( (host, port) )
#
#  # start listening with a maximum number of queued connections of 1
#  serverSocket.listen(1)
#
#  while True: 
#	 #Establish the connection 
#	 print 'Ready to serve...' 
#	 connectionSocket, addr = serverSocket.accept()
#	 try: 
#	   # Receive data from the socket and place into 'message'
#	   message = connectionSocket.recv(65536)
#
#	   # parse the second token for the filename using default delimiter
#	   # assumes the first token is GET
#	   filename = message.split()[1] 
#
#	   print "Opening file", filename
#
#	   # remove the leading slash
#	   f = open(filename[1:]) 
#
#	   # regurgitate file back to client
#	   outputdata = f.read()
#
#	   #Send one HTTP header line into socket 
#	   connectionSocket.send( REQ_OK )
#
#	   #Send the content of the requested file to the client 
#	   for i in range(0, len(outputdata)): 
#		 connectionSocket.send(outputdata[i]) 
#
#	 except IOError: 
#	   #Send response message for file not found 
#	   print "Not found"
#	   # First line is HTTP header
#	   connectionSocket.send( REQ_NOT_FOUND )
#	   connectionSocket.send( REQ_NOT_FOUND_TEXT )
#
#	 finally:
#	   #Close client socket 
#	   connectionSocket.close() 
#
#  serverSocket.close();

		
		else:	# client connect to server
			ip = self.remote_ip.GetValue()
			port = self.remote_port.GetValue()
			local_port = self.local_port.GetValue()
			
			print "Connecting to server at ip: " + ip + " and port:" + port

			# Then connect to remote host address + port
			if self.IsValidIP( ip ) and self.IsValidPort( port ) and self.IsValidPort( local_port ):
				# we can attempt to connect
				self.console.AppendText("Connecting to server at " + ip + ":" + port + " ...\n")
				self.SetStatusText("Connecting to server at " + ip + ":" + port + "...")
		
				###################################################
				# BEGIN SOCKET CODE FOR CLIENT
				###################################################
				
				self.KillThread()
				self.mythread = ClientThread(frame=self, port=port, ip=ip, buffersize=BUFFER_SIZE())
				self.mythread.start() 
				
				###################################################
				# END SOCKET CODE FOR CLIENT
				###################################################
				
			else:
				self.console.AppendText(STR_CLIENT_USAGE())
				
				
# Here is my rudimentary client socket code from previous socket assignment
#s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#HOST = socket.getfqdn()	# The remote host
#PORT = 12373			   # The same port as used by the server
#
#print "client connecting to ", (HOST, PORT)
#s.connect((HOST, PORT))
#
#s.sendall('GET /HelloWorld.html HTML/1.1')
#data = s.recv(1024)
#s.close()
#print 'Received', repr(data)
		

	def ChoiceModeCB(self, event):
		# On which item is the "Mode" Combo box currently selected?
		selection = self.mode.GetCurrentSelection()
		#print "choiecmodecb "+ str(selection)
		
		# kill thread if mode has changed
		if(self.mythread != None and self.mythread.isAlive() and self.mythread.ThreadType() == selection):
			self.KillThread()
		
		# We have 2 cases:
		# If server, then disable all "remote" fields
		# If Client, then enable all "remote" fields
		if selection == 0:
			#print "server"
			children = self.sizerRemote.GetChildren()
			for child in children:
				child.GetWindow().Disable()

			self.SetServerModeDetails()
		
		elif selection == 1:
			#print "client"
			children = self.sizerRemote.GetChildren() 
			for child in children:
				child.GetWindow().Enable()

			self.SetClientModeDetails()
		
		else:
			print "Syntax error -- Unknown selection!"

	def IsValidPort( self, port ):
		print "port is " + str(port)

		try:
			# First attempt to cast to integer
			port_int = int(port)
			# Cast success.	 Now validate range ...
			return port_int > 1023 and port_int < 49152
		except ValueError as e:
			return False;
		

	def IsValidIP( self, ip ):
		# This validates that the string can be parsed as an IPv4 address
		# This does not support IPv6
		# obtained from 
		# http://stackoverflow.com/questions/319279/how-to-validate-ip-address-in-python
		try:
			inet_aton( ip )
			# legal
			return True
		except error as e:
			# Not legal
			return False

		# Create a pop-up dialog about this application
	# Authors in alphabetical order by last name
	def OnAbout(self, event):
		credits = """
			Simple implementation of VPN using 
			Diffie-Hellman key enchange protocol
			\n
			Authors:
			Jobin Ansari-Gilani	  jobinansari@hotmail.com
			Ivan Cherapau	cherapau@gmail.com
			Scott Hazlett	scotthazlett@gmail.com
			Mina Savovic   minasavovic@gmail.com
			"""
		dialog = wx.MessageDialog(self, credits,
			"EECE412 Assignment #3 VPN", wx.OK|wx.ICON_INFORMATION )
		dialog.CentreOnParent()
		dialog.ShowModal()
		dialog.Destroy()
	
	def OnQuit(self, event):
		self.KillThread()
		self.Close(True)
	
	def OnCloseWindow(self, event):
		self.KillThread()
		self.Destroy()
		
	def KillThread(self):
		if(self.mythread != None and self.mythread.isAlive()):
			self.mythread.stop()
			self.mythread.join()
		
			
		
	

#----------------------------------------------------------------------------

class MyApp(wx.App):
	
	def OnInit(self):
		wx.InitAllImageHandlers()
		frame = MyFrame( None, -1, "VPN Application", [20,20], [500,340] )
		frame.Show(True)
		
		return True

#----------------------------------------------------------------------------


app = MyApp(True)
app.MainLoop()

