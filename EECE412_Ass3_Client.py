#!/usr/bin/python

import chilkat
import sys
import threading
import time
from socket import *
#from EECE412_Ass3_VPN import *

class ClientThread (threading.Thread):
	
	def __init__(self, frame, ip, port, buffersize):
		
		threading.Thread.__init__(self)
		
		self._stop = threading.Event()
		self.ip = ip
		self.port = port
		self.frame = frame
		self._step = threading.Event()
		self.step = None
		self.bufferSize = buffersize
		
		# Relevant to authentication
		self.received = None
		self.toSend = None

		self.dhClient = chilkat.CkDh()
		success = self.dhClient.UnlockComponent("Anything for 30-day trial")
		if not success:
			print self.dhClient.lastErrorText()
			print "Uh oh this trial won't work for us"

		#  Server will choose to use the 2nd of our 8 pre-chosen safe primes.
		#  It is the Prime for the 2nd Oakley Group (RFC 2409) --
		#  1024-bit MODP Group.  Generator is 2.
		#  The prime is: 2^1024 - 2^960 - 1 + 2^64 * { [2^894 pi] + 129093 }
		self.dhClient.UseKnownPrime(2)

		#  The computed shared secret will be equal to the size of the prime (in bits).
		#  In this case the prime is 1024 bits, so the shared secret will be 128 bytes (128 * 8 = 1024).
		#  However, the result is returned as an SSH1-encoded bignum in hex string format.
		#  The SSH1-encoding prepends a 2-byte count, so the result is going  to be 2 bytes
		#  longer: 130 bytes.  This results in a hex string that is 260 characters long (two chars
		#  per byte for the hex encoding).

		#  Bob will now send P and G to Alice.
		self.p = self.dhClient.p()
		print "p is " + str(self.p)
		self.g = self.dhClient.get_G()
		print "g is " + str(self.g)

		#  Each side begins by generating an "E"
		#  value.  The CreateE method has one argument: numBits.
		#  It should be set to twice the size of the number of bits
		#  in the session key.

		#  Let's say we want to generate a 128-bit session key
		#  for AES encryption.  The shared secret generated by the Diffie-Hellman
		#  algorithm will be longer, so we'll hash the result to arrive at the
		#  desired session key length.  However, the length of the session
		#  key we'll utlimately produce determines the value that should be
		#  passed to the CreateE method.

		#  In this case, we'll be creating a 128-bit session key, so pass 256 to CreateE.
		#  This setting is for security purposes only -- the value
		#  passed to CreateE does not change the length of the shared secret
		#  that is produced by Diffie-Hellman.
		#  Also, there is no need to pass in a value larger
		#  than 2 times the expected session key length.  It suffices to
		#  pass exactly 2 times the session key length.

		#  Server generates a random E (which has the mathematical
		#  properties required for DH).
		#eServer = dhClient.createE(256) 
		#print "E is " + str(eServer)
		
		
		
	###################################################
	# BEGIN AUTHENTICATION CODE
	###################################################
	
	def DoStep(self):
    
		if(self.step == 1):
			self.toSend = str(self.p) + str(self.g) 
			#self.frame.console.AppendText("Sending p||g to server\np is "+str(self.p)+"\ng is "+str(self.g)+"\n")

		elif(self.step == 2):
			self.eServer = self.received
			#self.frame.console.AppendText("Received server's e " + str(self.eServer))

		elif(self.step == 3):
			self.eClient = self.dhClient.createE(256)

			self.toSend = str(self.eClient)
			#self.frame.console.AppendText("Created and sending to server client's e " + str(self.eClient))

		elif(self.step == 4):
			self.clientkey = self.dhClient.findK(self.eServer)

			#self.frame.console.AppendText("Calculated session key is "+str(self.clientkey)+"\n")

			self.crypt = chilkat.CkCrypt2()
			success = self.crypt.UnlockComponent("Anything for 30-day trial.")

			if (success != True):
				print self.crypt.lastErrorText()

			self.crypt.put_EncodingMode("hex")
			self.crypt.put_HashAlgorithm("md5")

			sessionkey = self.crypt.hashStringENC(self.clientkey)
			#self.frame.console.AppendText("128-bit session key is "+str(sessionkey)+"\n")

			self.crypt.put_CryptAlgorithm("aes")
			self.crypt.put_KeyLength(128)
			self.crypt.put_CipherMode("cbc")

      #iv = self.crypt.hashStringENC(sessionkey)
			##self.frame.console.AppendText("iv used in AES/CBC is "+str(iv)+"\n")

			self.crypt.SetEncodedKey(sessionkey, "hex")
      #self.crypt.SetEncodedIV(iv,"hex")
			self.crypt.put_EncodingMode("base64")

			cipherText64 = self.received
			#self.frame.console.AppendText("Ciphertext is "+cipherText64+"\n")

			plainText = self.crypt.decryptStringENC( cipherText64 )
			print "plainText is " + plainText.decode("utf-8")
			#self.frame.console.AppendText("Plaintext is " + plainText )
			#self.frame.data.AppendText( plainText )

		elif(self.step == 5):
			self.toSend = "Client msg of step 5"
			
	###################################################
	# END AUTHENTICATION CODE
	###################################################	
			
		else:
			#self.frame.console.AppendText("Error: client does not know what step it's on. ")
			self.DisconnectText()
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
		
	def DisconnectText(self):
		pass
		#self.frame.console.AppendText("Client will now disconnect.\n")
		#self.frame.SetStatusText("Disconnected.")
		
	def ThreadType(self):
		return 1
	
	def stop(self):
		self._stop.set()
	
	def stopped(self):
		return self._stop.isSet()
	
	def nextstep(self):
		self._step.set()
	
	def stepped(self):
		return self._step.isSet()
		
	
	def SendData(self, clientSocket, data):
		if(type(data) is not str):
			#self.frame.console.AppendText("Error: client attempted to send data that is not a string. ")
			self.DisconnectText()
			return False 
			
		if(len(data) > self.bufferSize):
			#self.frame.console.AppendText("Error: client attempted to send data that is too long. ")
			self.DisconnectText()
			return False
		
		try:
			clientSocket.sendall(data) 
		except error, (value, errmsg):
			#self.frame.console.AppendText("Client failed to send data. Error was: " + errmsg)
			self.DisconnectText()
			return False
			
		print "Sent " +  data
		return True
		
	def ReceiveData(self, connectionSocket):
		data = None
		try:
			data = connectionSocket.recv(self.bufferSize)
		except error, (value, errmsg):
			#connectionSocket.shutdown(2)
			connectionSocket.close()
			#self.frame.console.AppendText("Transmission over: lost connection.\n")
			#self.frame.SetStatusText("Disconnected.")
			return None
							
		# server disconnected
		if(data == None or len(data) < 2):
			#connectionSocket.shutdown(2)
			connectionSocket.close()
			#self.frame.console.AppendText("Transmission over: server disconnected.\n")
			#self.frame.SetStatusText("Disconnected.")
			return None
		
		print "Received " + data
		return data
	
	def run(self):
		clientSocket = None
		# We should already have checked that the port was valid
		iport = int(self.port)
		
		#Prepare a client TCP socket on localhost on port 'port'
		
		try:
			print "getfqdn() output: " + getfqdn() + " = " + gethostbyname(getfqdn())
			clientSocket = socket(AF_INET, SOCK_STREAM)
			print "Attempting to connect to " + self.ip
			clientSocket.connect( (self.ip, iport) )
			print "connect successful\n"
		except error, (value, errmsg):
			print "er: " + errmsg
			if(clientSocket != None):
				#clientSocket.shutdown(2)
				clientSocket.close()
			#self.frame.console.AppendText("Connection failed: " + errmsg + "\n")
			#self.frame.SetStatusText("Connection failed.")
			exit(1)
		
		# If connect successful...
		#self.frame.console.AppendText("Connection success with server " + self.ip + ":" + self.port + ".\n")
		#self.SetStatusText("Connected with server " + self.ip + ":" + self.port)
		
		#clientSocket.settimeout(60)
		
		# Enable the step button for the TA to step through the transaction
		self.step = 1
		self.frame.step.Enable()
		
		while not self.stopped(): 
			if(self.stepped()):
				if(self.step == 5):
					self.frame.send.Disable()
				else:
					self.frame.step.Disable()
					
				self.StepInProgressText()
				
				# Receive data on even steps
				if(self.step % 2 == 0):
					while(self.SendData(clientSocket, "step") == False):
						pass
					self.received = self.ReceiveData(clientSocket)
					
					# server disconnected
					if(self.received == None):
						break
							
					# display received data
					#self.frame.console.AppendText("Received: " + self.received)
						
				if(self.DoStep() == False):
					break
					
				# Send data on odd steps
				if(self.step % 2 == 1):
					if(self.SendData(clientSocket, self.toSend) == False): 
						break
					else:
						pass
						# display sent data
						#self.frame.console.AppendText("Sent: " + self.toSend + "\n")
				
				if(self.step == 5):
					#self.frame.console.AppendText("\nTransmission complete. ")
					self.DisconnectText()
					break
					
				self.StepCompleteText()
				self.step = self.step + 1
				self._step.clear()
				
				if(self.step == 5):
					self.frame.send.Enable()
				else:
					self.frame.step.Enable()
				
				
		
		#self.frame.step.Disable()
		#self.frame.send.Disable()
		#clientSocket.shutdown(2)
		clientSocket.close()
