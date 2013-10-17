#!/usr/bin/python

import chilkat
import threading
import time
from socket import *
#from EECE412_Ass3_VPN import *

class ServerThread (threading.Thread):
	
	def __init__(self, frame, port, buffersize):
		
		threading.Thread.__init__(self)
		
		self._stop = threading.Event()
		self.port = port
		self.frame = frame
		self._step = threading.Event()
		self.step = None
		self.bufferSize = buffersize
		
		# Relevant to authentication
		self.received = None
		self.toSend = None
		
		self.dhServer = chilkat.CkDh()
		success = self.dhServer.UnlockComponent("Anything for 30-day trial")
		if not success:
			print self.dhServer.lastErrorText()
			print "Uh oh this trial won't work for us"
		
	###################################################
	# BEGIN AUTHENTICATION CODE
	###################################################
	
	def DoStep(self):
		if(self.step == 1):
			#  Server calls SetPG to set P and G.  SetPG checks
			#  the values to make sure it's a safe prime and will
			#  return False if not.
			# Note, we do NOT save p and g.  Instead we throw away.
			pClient = self.received[:-1]
			gClient = self.received[-1:]
			#self.frame.console.AppendText("Received p||g from client\np is "+str(pClient)+"\ng is "+str(gClient)+"\n")

			success = self.dhServer.SetPG(str(pClient),int(gClient))

			if (success != True):
				print " ************ p is not a safe prime"

		elif(self.step == 2):
			self.eServer = self.dhServer.createE(256)

			self.toSend = str(self.eServer);
			#self.frame.console.AppendText("Created and sending to client server's e " + str(self.eServer))

		elif(self.step == 3):
			self.eClient = self.received;
			#self.frame.console.AppendText("Received client's e " + str(self.eClient))

		elif(self.step == 4):
			self.crypt = chilkat.CkCrypt2()
			self.serverkey = self.dhServer.findK(self.eClient)
			#self.frame.console.AppendText("Calculated server key is "+str(self.serverkey)+"\n")
			
			success = self.crypt.UnlockComponent("Anything for 30-day trial.")

			if (success != True):
				print self.crypt.lastErrorText()

			self.crypt.put_EncodingMode("hex")
			self.crypt.put_HashAlgorithm("md5")

			sessionkey = self.crypt.hashStringENC(self.serverkey)
			#self.frame.console.AppendText("128-bit session key is "+str(sessionkey)+"\n")

			self.crypt.put_CryptAlgorithm("aes")
			self.crypt.put_KeyLength(128)
			self.crypt.put_CipherMode("cbc")

			iv = self.crypt.hashStringENC(sessionkey)
			#self.frame.console.AppendText("iv used in AES/CBC is "+str(iv)+"\n")

			self.crypt.SetEncodedKey(sessionkey, "hex")
			self.crypt.SetEncodedIV(iv,"hex")

			self.crypt.put_EncodingMode("base64")
		
			plain = "THIS IS MY SECRET MESSAGE"
			cipherText64 = self.crypt.encryptStringENC(plain)
			#self.frame.console.AppendText("Plaintext is "+self.frame.data.GetValue()+"\n")
			#self.frame.console.AppendText("Ciphertext is "+cipherText64+"\n")

			self.toSend = cipherText64

		elif(self.step == 5):
			pass
			
	###################################################
	# END AUTHENTICATION CODE
	###################################################	
			
		else:
			#self.frame.console.AppendText("Error: server does not know what step it's on. Server will now disconnect.\n")
			self.ListeningText()
			return False
			
		return True
	 
	def StepInProgressText(self):
		print "on a step with mod "
		print self.step%2
		#self.frame.console.AppendText("\nStep " + str(self.step) + ":\n")
		#self.frame.SetStatusText("Step " + str(self.step) + " in progress")
		
	
	def StepCompleteText(self):
		pass
		#self.frame.console.AppendText("\nStep " + str(self.step) + " complete.\n")
		#self.frame.SetStatusText("Step " + str(self.step) + " completed")
		
	
	def ListeningText(self):
		#self.frame.console.AppendText("\nServer is listening on port " + self.port + " ...\n")
		#self.frame.SetStatusText("Listening for connections on port " + self.port + " ...")
		self._step.clear()
		
	def ThreadType(self):
		return 0
	
	def stop(self):
		self._stop.set()
	
	def stopped(self):
		return self._stop.isSet()
	
	def nextstep(self):
		self._step.set()
	
	def stepped(self):
		return self._step.isSet()
		
	
	def SendData(self, connectionSocket, data):
		if(type(data) is not str):
			#self.frame.console.AppendText("Error: server attempted to send data that is not a string. Server will now disconnect.\n")
			self.ListeningText()
			return False 
			
		if(len(data) > self.bufferSize):
			#self.frame.console.AppendText("Error: server attempted to send data that is too long. Server will now disconnect.\n")
			self.ListeningText()
			return False
		
		try:
			connectionSocket.sendall(data) 
		except error, (value, errmsg):
			#self.frame.console.AppendText("Server failed to send data. Error was: " + errmsg + "\nServer will now disconnect.\n")
			self.ListeningText()
			return False
		
		print "Sent " + data
		return True
		
	def ReceiveData(self, connectionSocket):
		data = None
		try:
			data = connectionSocket.recv(self.bufferSize)
		except error, (value, errmsg):
			#connectionSocket.shutdown(2)
			connectionSocket.close()
			#self.frame.console.AppendText("Transmission over: lost connection.\n")
			self.ListeningText()
			return None
							
		# client disconnected
		if(data == None or len(data) < 2):
			#connectionSocket.shutdown(2)
			connectionSocket.close()
			#self.frame.console.AppendText("Transmission over: client disconnected.\n")
			self.ListeningText()
			return None
			
		print "Received " + data
		return data
	
	def run(self):
		serverSocket = None
		# We should already have checked that the port was valid
		iport = int(self.port)
		
		#Prepare a server TCP socket on localhost on port 'port'
		
		try: 
			serverSocket = socket(AF_INET, SOCK_STREAM)
			serverSocket.bind( (getfqdn(), iport) )
			print "sock name: " 
			print serverSocket.getsockname()
		except error, (value, errmsg):
			if(serverSocket != None):
				#serverSocket.shutdown(2)
				serverSocket.close()
			#self.frame.console.AppendText("Could not open socket: " + errmsg + "\n")
			#self.frame.SetStatusText("Bind failed.")
			exit(1)
		
		print "bind successful\n"
		# If bind successful...
		#self.frame.console.AppendText("Bind success. Listening to connections on port " + self.port + " ...\n")
		#self.frame.SetStatusText("Listening for connections on port " + self.port + " ...")
		
		# start listening with a maximum number of queued connections of 1
		serverSocket.listen(1)
		print "I'm listening ...\n"
		
		while not self.stopped(): 
			
			# Set timeout b/c we want to occasionally check if thread should be stopped
			#serverSocket.settimeout(5);
			
			try:
				#Establish the connection 
				print "Ready to accept"
				connectionSocket, addr = serverSocket.accept()
				print "connection success at: " 
				print addr
			except error, (value, errmsg):
				print "er: " + errmsg
				if connectionSocket:
					#connectionSocket.shutdown(2)
					connectionSocket.close()
				#self.frame.console.AppendText("Connection failed: " + errmsg + "\n")
				self.ListeningText()
				continue
				
			self.step = 1
			#self.frame.console.AppendText("Connection success with client \n")
			#self.frame.SetStatusText("Connected")
			
			#connectionSocket.settimeout(60)
			self.nextstep()
			
			while not self.stopped(): 
				#if(self.stepped()):
					self.StepInProgressText()
					
					# Receive data on odd steps
					if(self.step % 2 == 1):
						self.received = self.ReceiveData(connectionSocket)
							
						# client disconnected
						if(self.received == None):
							break
							
						# display received data
						#self.frame.console.AppendText("Received: " + self.received)
						
					if(self.DoStep() == False):
						break
						
					# Send data on even steps
					if(self.step % 2 == 0):
						while(self.ReceiveData(connectionSocket) == None):
							pass
						if(self.SendData(connectionSocket, self.toSend) == False):
							break
							
						else:
							pass
							# display sent data
							#self.frame.console.AppendText("Sent: " + self.toSend + "\n")
						
					if(self.step == 5):
						#self.frame.console.AppendText("\nTransmission complete. Server will now disconnect.\n" )
						self.ListeningText()
						break
					
					self.StepCompleteText()
					self.step = self.step + 1
					
		# let garbage collection close connectionSocket
		#serverSocket.shutdown(2)
		serverSocket.close()
