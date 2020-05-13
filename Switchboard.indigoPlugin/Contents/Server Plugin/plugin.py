#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2010, Benjamin Schollnick. All rights reserved.
# http://www.schollnick.net/wordpress

################################################################################
# Python imports
import operator
import os
import sys
import time
################################################################################
# Globals
################################################################################

usable_plugin_types = ["com.schollnick.indigoplugin.switchboard",]
usable_model_types = ["Remote Button", "TriggerLinc", "Indigo Security Sensor"]

plugin_id = "com.schollnick.indigoplugin.switchboard"
insteon   = 0
x10		  = 1

time_translation	 = { 	'000' 	: 10, 		'015' 	: 15,
							'030' 	: 30,		'1'	  	: 60,
							'2'	  	: 120,		'5'	  	: 300,
							'7'   	: 420,		'10'	: 600,
							'15'	: 900,		'30'	: 1800,
							'60'	: 3600,		'300'	: 18000,
							'1440'	: 86400,	'0'		: 0}

email_template = '''Indigo Switchboard Email Report

Time & Date - %s

The %s Monitored Device Group has been triggered.
The device that triggered this report was %s.
'''

#	X10Device, MonitoredDeviceGroup
################################################################################
class Plugin(indigo.PluginBase):
	########################################
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		# Setting debug to True will show you verbose debugging information in the Indigo Event Log
		self.debug = pluginPrefs.get("showDebugInfo", False)
#		self.debug = True
		#
		#	SecurityZones is a dictionary, that consists of each enrolled Security device
		#
		#	SecurityZones [<Device ID>] = <Security Zone / Device ID>
		#
		self.ZoneList = {}
		self.X10List  = {}
		self.InsteonList = {}
		self.SecurityCenter = {}
		for dev in indigo.devices.iter():
			if dev.protocol.name == "Insteon":
				self.InsteonList [dev.address.strip().upper()] = dev.id


	########################################

	def __del__(self):
		indigo.PluginBase.__del__(self)



	########################################
	def shutdown(self):
		# Nothing to do since deviceStopComm will be called for each of our
		# devices and that's how we'll clean up
		#self.pluginPrefs["ZoneList"] = self.ZoneList
		#self.pluginPrefs["X10List"]  = self.X10List
		pass

	def closedPrefsConfigUi(self, valuesDict, userCancelled):
		self.debug = self.pluginPrefs.get("showDebugInfo", False)


	def	deviceStopComm (self, dev):
		self.debugLog ("Removing %s from Switchboard Devices List" % dev.name)
		if dev.deviceTypeId == "MonitoredDeviceGroup":
			if self.ZoneList.has_key ( str(dev.id) ):
				del self.ZoneList [ str(dev.id) ]
		elif dev.deviceTypeId == "X10Device":
			# self.X10List [ <X10 Sensor ID> ] = X10 Monitored Device ID
			X10Security = str(indigo.devices[dev].globalProps[plugin_id]["X10Security"]).upper()
			if X10Security <> "":
				del self.X10List [ X10Security ]
		elif dev.deviceTypeId == "SecurityCenter":
			if self.SecurityCenter.has_key ( str(dev.id) ):
				del self.SecurityCenter [ str(dev.id) ]

	def	verify_device_properties ( self, dev, propertyname, boolean = False) :
		if indigo.devices[dev].globalProps[plugin_id].has_key (propertyname):
			return
		else:
			newProps = dev.pluginProps
			if boolean:
				newProps[propertyname] = True
			else:
				newProps[propertyname] = ""

			dev.replacePluginPropsOnServer(newProps)


	def	deviceStartComm (self, dev):
		self.debugLog ("Adding %s to Switchboard Devices List" % dev.name)
		dev.stateListOrDisplayStateIdChanged()

		if dev.deviceTypeId == "MonitoredDeviceGroup":
			self.verify_device_properties (dev, "Usetimed", boolean = True)
			self.verify_device_properties (dev, "UseActionGroup", boolean = True)
			self.verify_device_properties (dev, "Email")
			self.verify_device_properties (dev, "EmailOnOpen", boolean = True)
			self.verify_device_properties (dev, "EmailOnClose", boolean = True)
			self.verify_device_properties (dev, "CustomEmailEnabled", boolean = True)
			self.verify_device_properties (dev, "CustomEmailText")
			self.verify_device_properties (dev, "UseSpeech", boolean = True)
			self.verify_device_properties (dev, "Speech")
			self.verify_device_properties (dev, "SayOnOpen")
			self.verify_device_properties (dev, "SayOnClose")
			self.verify_device_properties (dev, "ActionOnOpen", boolean = True)
			self.verify_device_properties (dev, "ActionOnClose", boolean = True)
			if not self.ZoneList.has_key ( str(dev.id) ):
				self.ZoneList [ str(dev.id) ] = []
			self.ZoneList [ str(dev.id) ].append ( dev.id )
		elif dev.deviceTypeId == "X10Device":
			self.verify_device_properties (dev, "IgnoreDevice", boolean = True)
			self.verify_device_properties (dev, "IgnoreOrphan", boolean = True)
			self.verify_device_properties (dev, "IgnoreHeartbeats", boolean = True)
			self.verify_device_properties (dev, "OverrideHeartbeatTimeout", boolean = True)
			self.verify_device_properties (dev, "X10HeartBeatTimeOut")

			# self.X10List [ <X10 Sensor ID> ] = X10 Monitored Device ID
			#
			#	Get Security ID from the device
			#
			X10Security = str(indigo.devices[dev].globalProps[plugin_id]["X10Security"]).upper()

			#
			#	Assign the Security ID to the Address field on the server
			#
			X10_props = indigo.devices[dev].pluginProps
			X10_props['address'] = X10Security
			indigo.devices[dev].replacePluginPropsOnServer(X10_props)

			#
			#	Write the "pointer" to the X10 device list
			#
			if X10Security <> "":
				self.X10List [ X10Security ] = str(dev.id)
		elif dev.deviceTypeId == "SecurityCenter":
			if not self.SecurityCenter.has_key ( str(dev.id) ):
				self.SecurityCenter [ str(dev.id) ] = []
			self.SecurityCenter [ str(dev.id) ].append ( dev.id )

	def	return_security_center ( self ):
		if self.SecurityCenter <> {}:
			return self.SecurityCenter.keys()[0]
		return None
	#
	#
	#	User Interface Code
	#

#	def	return_device_id ( self ):
#		#
#		#	Find the device ID for the plugin device.
#		#
#		for devId in indigo.devices.iter (plugin_id):
#			return devId.id

 	def return_eligible_devices (self, filter="", valuesDict=None, typeId="", targetId=0):
 		#
 		#	Used in the SecuritySensors list.
 		#
 		#	This produces the list of eligible devices to be added into a security zone.
 		#
 		deviceArray = []
 		devices_already_in_zone = valuesDict.get ("StoredDeviceList","").split(",")
 		#self.debugLog ("-%s" % devices_already_in_zone)
 		for x in indigo.devices:
 				if devices_already_in_zone.count ( str(x.id) ) == 0:
 					deviceArray.append ( (x.id, x.name) )
 				else:
 					pass
 		sorted_da = sorted ( deviceArray, key = operator.itemgetter(1))
 		return sorted_da

 	def return_devices_in_zone (self, filter="", valuesDict=None, typeId="", targetId=0):
 		#
 		#	Return the list of devices that have already been assigned to the Zone
 		#
 		deviceArray = []
 		devices_already_in_zone = valuesDict.get ("StoredDeviceList", "").split(",")

 		for x in devices_already_in_zone:
 			if x <> u'' and int(x) in indigo.devices:
 				deviceArray.append ( (indigo.devices[int(x)].id, indigo.devices[int(x)].name) )

 		sorted_da = sorted (deviceArray, key = operator.itemgetter(1))

 		valuesDict ["RegisteredDevices"] = sorted_da
 		return sorted_da

 	def	add_device_to_zone ( self, configscreen, typeId, devId):
 		#
 		#	Add a device to the Zone's device list
 		#
 		devices_already_in_zone = configscreen["StoredDeviceList"].split(",")
 		for x in configscreen["Device_List"]:
 			#
 			#	Grab the selected Devices in the available Device_List
 			#
 			if  str(indigo.devices[int(x)].id) in devices_already_in_zone:
 				#	Device Already exists in the Zone
 				pass
 			else:
 				devices_already_in_zone.append ( str(indigo.devices[int(x)].id ) )

 		temp = "%s" % ",".join ( devices_already_in_zone )
 		if temp.startswith (","):
 			temp = temp[1:len(temp)]
 		configscreen["StoredDeviceList"] = temp

 		del configscreen["Device_List"]
 		del configscreen["RegisteredDevices"]
 		return configscreen


	def	Remove_from_Zone ( self, configscreen, typeId, devId):
		#
		#	Remove a device from the Zone list
		#
		devices_already_in_zone = configscreen["StoredDeviceList"].split(",")
		for x in configscreen["RegisteredDevices"]:
			#
			#	Grab the selected Devices in the registered Device_List
			#
				if str(x) in devices_already_in_zone:
					devices_already_in_zone.remove ( str(x) )

		temp = "%s" % ",".join ( devices_already_in_zone )
		if temp.startswith (","):
			temp = temp[1:len(temp)]
		configscreen["StoredDeviceList"] = temp

		del configscreen["Device_List"]
		del configscreen["RegisteredDevices"]
		return configscreen

#
#
#		Plugin Logic
#

	def	re_init_zones_with_trigger_status ( self ):
 		for zdev 	in 	indigo.devices:
			if zdev.deviceTypeId == "MonitoredDeviceGroup":
				indigo.server.log ("Updating Monitored Device Zone '%s'" % zdev.name)
				triggered = []
				reg_devices = self._return_devices_in_zone ( zdev.id )
				for idev in reg_devices:
					#
					#	Insteon
					#
					if hasattr(indigo.devices[int(idev)], "onState"):
						if indigo.devices[int(idev)].onState == True:
							triggered.append ( indigo.devices[int(idev)].name.strip() )

					#
					#	X10
					#
					if indigo.devices[int(idev)].deviceTypeId == "X10Device":
						if indigo.devices[int(idev)].states.has_key ("onState"):
#							indigo.server.log ("%s" % indigo.devices[int(idev)].name)
							if indigo.devices[int(idev)].states["onState"] == True:
								triggered.append ( indigo.devices[int(idev)].name.strip() )
						else:
							indigo.server.log ("Device: %s is not updated.  Please open the device, and resave it to update" % indigo.devices[int(idev)].name, isError = True)

				zdev.updateStateOnServer ("Triggered_In_Group", ",".join(triggered) )
				if zdev.states["Triggered_In_Group"].startswith (","):
						zdev.updateStateOnServer ("Triggered_In_Group", zdev.states["Triggered_In_Group"][1:])
				zdev.updateStateOnServer ("Number_Triggered_Devices", len(triggered) )
				zdev.updateStateOnServer ("Devices_Triggered", len(triggered) >= 1 )




	def	_return_devices_in_zone ( self, zoneid):
		zone_data = indigo.devices[int(zoneid) ]
		registered_devs = zone_data.globalProps[plugin_id]["StoredDeviceList"].split(",")
		return registered_devs

	def	indigo_device_in_zone ( self, i_id):
	#
	#	Return the (first found) Zone ID that an Indigo device is associated with.
	#
 		for zn in 	self.ZoneList.keys():
 			if int(zn) in indigo.devices:
				registered_devs = indigo.devices[int(zn)].globalProps[plugin_id]["StoredDeviceList"].split(",")
				if str(i_id) in registered_devs:
					return zn
		return None

	def	timed_device ( self, timedDev ):
	#
	#
	#	Activate a timed Device, per the timed Device Device Record information.
	#
	#	This obeys the Last Triggered, and
	#
		timed_Ignore = timedDev.globalProps[plugin_id]["Ignoretimed"]
		timed_Length = timedDev.globalProps[plugin_id]["timedDuration"]
		timed_List 	 = timedDev.globalProps[plugin_id]["timedDeviceToUse"]
		if timedDev.states.get ("Last_Triggered", "") == "":
			timedDev.updateStateOnServer ("Last_Triggered", time.asctime(time.localtime ( 0 )) )
		Last_Triggered  = time.mktime ( time.strptime (timedDev.states["Last_Triggered"]) )
		if time.mktime( time.localtime ( )) >= Last_Triggered + int(time_translation[timed_Ignore]):
			self.debugLog ("Triggering timed Device %s (%s)" % (timedDev.name, timedDev.id) )
			indigo.device.removeDelayedActions(int(timed_List))
			timed_Length_in_sec = time_translation[timed_Length]
			indigo.device.turnOn(int(timed_List), delay=0, duration=timed_Length_in_sec)
			timedDev.updateStateOnServer("Last_Updated", time.asctime ( time.localtime()))
			timedDev.updateStateOnServer("Last_Triggered", 	time.asctime ( time.localtime()))
		else:
			indigo.server.log ("\tIgnoring Timed Device Request, due to Ignore Setting")


	def	trigger_actiongroup ( self, actiongroup):
	#
	#	Trigger an Action group
	#
		indigo.actionGroup.execute ( actiongroup.id )

	def	return_x10_action_state ( self, X10_Action):
	#
	#	Return the stateString (eg _Open, _Closed, etc) and the True/False OnState from the X10 Command string.
	#
		stateString = ""
		onState = False
		if X10_Action <> None:
				if X10_Action.upper() in ["SENSOR ALERT (MAX DELAY)", "SENSOR ALERT (MIN DELAY)"]:
					self.debugLog ("OPEN")
					stateString = "_Open"
					onState = True
				elif X10_Action.upper() in ["SENSOR NORMAL (MAX DELAY)", "SENSOR NORMAL (MIN DELAY)"]:
					self.debugLog ("CLOSED")
					stateString = "_Closed"
					onState = False
				elif X10_Action.upper() in ["ARM AWAY (MIN DELAY)", "ARM AWAY (MAX DELAY)"]:
					self.debugLog ("Armed")
					stateString = "_Armed"
					onState = None
				elif X10_Action.upper() == "DISARM":
					self.debugLog ("Disarmed")
					stateString = "_Disarm"
					onState = False
				elif X10_Action.upper() == "PANIC PRESSED":
					self.debugLog ("Panic!")
					stateString = "_Panic"
					onState = False
				elif X10_Action.upper() == "LIGHTS ON":
					self.debugLog ("X10 Lights On")
					stateString = "_LightsOn"
					onState = False
				elif X10_Action.upper() == "LIGHTS OFF":
					self.debugLog ("X10 Lights Off")
					stateString = "_LightsOff"
					onState = False
				else:
					self.debugLog ("Unknown X10 SecFunc - %s" % X10_Action)
		return (stateString, onState)

	def	trigger_zone ( self, zoneRec = None, deviceRec = None, X10_Action = None):
	#
	#	Trigger the Zone actions associated with a zone.
	#
		if zoneRec <> None:
	 		ZoneName   = zoneRec.name
	 		DeviceName = deviceRec.name
			self.debugLog ("\tDevice (%s) is in Monitored Group '%s'" % (DeviceName, zoneRec.name) )
			onState = None
			stateString = ""
			if hasattr(deviceRec, "onState"):
			#
			#	If the device has a onState, use that for the result....
			#
				onState = deviceRec.onState
				if onState == True:
					stateString = "_On"
				elif onState == False:
					stateString = "_Off"

			else:
				#
				# Otherwise we will check X10 action codes...
				#
				stateString, onState = self.return_x10_action_state ( X10_Action )
				displayState = stateString.replace ("_","")

			#
			#	Check Use Action Group Status
			#
			if zoneRec.globalProps[plugin_id]["UseActionGroup"] == True:
				#
				#	Get the basename, and the only_on_open / only_on_close status from the Monitored Device Group
				#
				basename = zoneRec.globalProps[plugin_id]["ActionGroup"].strip()
				actiongroup_name = basename+stateString
				only_on_open = zoneRec.globalProps[plugin_id]["ActionOnOpen"]
				only_on_close = zoneRec.globalProps[plugin_id]["ActionOnClose"]

#				if only_on_open and only_on_close:
#					indigo.server.log ("Caution, both Only On Open and Close, have been selected for Action Group Support. This may cause unexpected behavior!", isError=True)

				#
				#	Check Only_on_open status, and if necessary trigger action group
				#
				if only_on_open and onState <> False and stateString <> u"":
					if indigo.actionGroups.has_key ( actiongroup_name ):
						indigo.server.log ("Triggering actiongroup: %s" % actiongroup_name)
						actiongroup = indigo.actionGroups.get ( actiongroup_name )
						self.trigger_actiongroup ( actiongroup )
					else:
						indigo.server.log ("Unable to Find the Action Group for this group. [%s]" % actiongroup_name)

				#
				#	Check Only_on_close status, and if necessary trigger action group
				#
				if only_on_close and onState == False and stateString <> u"":
					if indigo.actionGroups.has_key ( actiongroup_name ):
						indigo.server.log ("Triggering actiongroup: %s" % actiongroup_name)
						actiongroup = indigo.actionGroups.get ( actiongroup_name )
						self.trigger_actiongroup ( actiongroup )
					else:
						indigo.server.log ("Unable to Find the Action Group for this group. [%s]" % actiongroup_name)

				#
				#	neither only_on_xxxx options have been checked, if necessary trigger action group
				#
				if not only_on_open and not only_on_close and stateString <> u"":
					if indigo.actionGroups.has_key ( actiongroup_name ):
						indigo.server.log ("Triggering actiongroup: %s" % actiongroup_name)
						actiongroup = indigo.actionGroups.get ( actiongroup_name )
						self.trigger_actiongroup ( actiongroup )
					else:
						indigo.server.log ("Unable to Find the Action Group for this group. [%s]" % actiongroup_name)

			if zoneRec.states["Number_Triggered_Devices"] in ["", None, "None", "False"]:
				#
				#	Ensure that the Number_Triggered_Devices is in an Integer "ready" state
				#
				zoneRec.updateStateOnServer ("Number_Triggered_Devices", "0" )

			#
			#	Setup the list of Devices_Already_Triggered and test to see if it needs to be added to
			#
			devices_already_triggered = zoneRec.states["Triggered_In_Group"].split(",")
			if devices_already_triggered[0] == u'':
				devices_already_triggered.remove (u'')
			if onState == True:
				#
				#	Update Zone Record to show device triggered / Open
				#
				if devices_already_triggered.count (DeviceName.strip()) == 0:
					#
					#	Device is not registered as on in the Monitored Device Group
					#
					devices_already_triggered.append ( DeviceName)
					zoneRec.updateStateOnServer ("Triggered_In_Group", ",".join(devices_already_triggered) )
					if zoneRec.states["Triggered_In_Group"][0] == ",":
						zoneRec.updateStateOnServer ("Triggered_In_Group", zoneRec.states["Triggered_In_Group"][1:])
					zoneRec.updateStateOnServer ("Number_Triggered_Devices", len(devices_already_triggered) )
					zoneRec.updateStateOnServer ("Devices_Triggered", len(devices_already_triggered) >= 1 )

			#
			#	Check to see if the device needs to be removed from the Devices_Already_Triggered state list
			#
			if onState == False and devices_already_triggered.count (DeviceName.strip()) == 1:
					#
					#	Device *is* registered as on in the Monitored Device Group
					#
					devices_already_triggered.remove ( DeviceName )
					zoneRec.updateStateOnServer ("Triggered_In_Group", ",".join(devices_already_triggered) )
					if zoneRec.states["Triggered_In_Group"] <> "" and zoneRec.states["Triggered_In_Group"][0] == ",":
						zoneRec.updateStateOnServer ("Triggered_In_Group", zoneRec.states["Triggered_In_Group"][1:])

					if zoneRec.states["Triggered_In_Group"] == "":
						zoneRec.updateStateOnServer ("Number_Triggered_Devices", "0" )
					else:
						zoneRec.updateStateOnServer ("Number_Triggered_Devices", len(devices_already_triggered) )
					zoneRec.updateStateOnServer ("Devices_Triggered", len(devices_already_triggered) >= 1 )



			if onState <> None:
					#
					#	Timed Profile Activation
					#
					if zoneRec.globalProps[plugin_id]["Usetimed"]:
						#
						#	Load the Timed_Device data
						#
						timed_devices = zoneRec.globalProps[plugin_id]["timedDeviceID"]
						for timed_device in timed_devices:
							if int(timed_device) in indigo.devices:
								tdevice = indigo.devices[int(timed_device)]
								if tdevice.globalProps[plugin_id]["var_controller"]==True:
									bnd_variable = indigo.variables[ int(tdevice.globalProps[plugin_id]["Bound_Variable"][0]) ]
									if bnd_variable.value == "true":
										self.trigger_timed_device ( tdevice, onState )
								else:
									self.trigger_timed_device ( tdevice, onState )


					if zoneRec.globalProps[plugin_id]["UseSpeech"]:
					#
					#	Trigger Speech Text
					#
						text_to_say = zoneRec.globalProps[plugin_id]["Speech"]
                        #
                        #   substitute for text_to_speech
                        #
						text_to_say = self.substitute(text_to_say)
						only_on_open = zoneRec.globalProps[plugin_id]["SayOnOpen"]
						only_on_close = zoneRec.globalProps[plugin_id]["SayOnClose"]
						if only_on_open == True:
							if onState == True:
								indigo.server.speak(text_to_say, waitUntilDone=False)
							else:
								pass
						elif only_on_close == True:
							if onState == False:
								indigo.server.speak (text_to_say, waitUntilDone=False)
							else:
								pass
						else:
							indigo.server.speak(text_to_say, waitUntilDone=False)

					if (zoneRec.globalProps[plugin_id]["SendEmail"] == True):
					#
					#	Email options have been enabled
					#
						self.send_emails ( zoneRec, deviceRec )
			else:
				indigo.server.log ( "No onState, detected from : %s " % deviceRec.name)

			zoneRec.updateStateOnServer ("Last_Updated", time.asctime(time.localtime ( )) )
			zoneRec.updateStateOnServer ("Last_Triggered", time.asctime(time.localtime ( )) )
			zoneRec.updateStateOnServer ("DeviceName_Last_Triggered", DeviceName )
			zoneRec.updateStateOnServer ("DeviceID_Last_Triggered", deviceRec.id )

	def		send_emails ( self, zonerec, devicerec ):
			email_addrs = zonerec.globalProps[plugin_id]["Email"].split(",")
	 		ZoneName   = zonerec.name
	 		DeviceName = devicerec.name

			for email in email_addrs:
				indigo.server.log ("Sending Emails to: %s", email)

			if devicerec.globalProps[plugin_id]["CustomEmailEnabled"]:
				# Send a custom Email

				#
				# email substitute
				#
				email_text = self.substitute(devicerec.globalProps[plugin_id]["CustomEmailText"])
				indigo.server.sendEmailTo ( ";".join(email_addrs), "Switchboard Alert - %s..." % ZoneName , email_text )
			else:
				# Send the standard Email Template
				indigo.server.sendEmailTo ( ";".join(email_addrs), "Switchboard Alert - %s..." % ZoneName , email_template % ( time.asctime ( time.localtime()), ZoneName, DeviceName) )

			if devicerec.globalProps[plugin_id]["RepeatEmailEnabler"]:
				#
				#	Repeat email
				#
				pass

	def		custom_send_emails ( self, subject="Hello!", email_addrs="", mail_message="Hi!"):
			for email in email_addrs.split (","):
				indigo.server.log ("Sending Emails to: %s" % email)
				indigo.server.sendEmailTo ( email, subject, mail_message)

	def	trigger_timed_device ( self, timed_device, onState ):
	#
	#	Run Timed Device.
	#
			if timed_device.globalProps[plugin_id]["Trigger_On_Open"] == True:
				if onState == True:
					self.debugLog ("Running Timed Device (On Open) - %s" % timed_device.name)
					self.timed_device ( timed_device )
			if timed_device.globalProps[plugin_id]["Trigger_On_Close"] == True:
				if onState == False:
					self.debugLog ("Running Timed Device (On Close) - %s" % timed_device.name)
					self.timed_device ( timed_device )
			if timed_device.globalProps[plugin_id]["Trigger_On_Close"] == False and timed_device.globalProps[plugin_id]["Trigger_On_Open"] == False:
				self.debugLog ("Running Timed Device (Always) - %s" % timed_device.name)
				self.timed_device ( timed_device )


 	def deviceUpdated(self, origDev, newDev):
 		#
 		#	This should only occur for Insteon Devices...  Since the X10 devices are custom
 		#	Devices, and have no real state for modification.
 		#
		kIgnoreKeyList = [u"lastupdated", u"Last_Updated", u"Last_Triggered",
							u'Display_onState', u'Last_X10Command', u'Last_X10HeartBeat',
							u"updatetime", u"updatetimestamp", u"timestamp"]

		if origDev.deviceTypeId == "X10Device":
			# self.X10List [ <X10 Sensor ID> ] = X10 Monitored Device ID
			if str(origDev.globalProps[plugin_id]["X10Security"]).upper() <> str(newDev.globalProps[plugin_id]["X10Security"]).upper():
				X10Security = str(origDev.globalProps[plugin_id]["X10Security"]).upper()
				if X10Security <> "":
					del self.X10List [ X10Security ]

				X10Security = str(newDev.globalProps[plugin_id]["X10Security"]).upper()
				if X10Security <> "":
					self.X10List [ X10Security ] = str(dev.id)
#			return None

		changeList = [(key, val) for key, val in newDev.states.iteritems()
		if key not in origDev.states
			or (key not in kIgnoreKeyList and val != origDev.states[key])
		]
		if len(changeList) == 0:
			self.debugLog("no state change for \"%s\" (ignoring update)" % newDev.name)
			return

		self.debugLog("state change list for \"%s\": %s" % (newDev.name, str(changeList)))
		ZoneID = self.indigo_device_in_zone ( newDev.id )
		if ZoneID == None:
			return
		ZoneRecord = indigo.devices[ int(ZoneID) ]
		self.trigger_zone ( zoneRec = ZoneRecord, deviceRec = newDev, X10_Action = None)
		return None

	def startup(self):
		#indigo.devices.subscribeToChanges()
		if self.pluginPrefs.get("enableX10", False):
			self.monitor_x10 = True
			indigo.server.log ("Switchboard is Monitoring X10 communications")
			indigo.x10.subscribeToIncoming()


		if self.pluginPrefs.get("enableInsteon", False):
			self.monitor_insteon = True
			indigo.server.log ("Switchboard is Monitoring Insteon communications")
			indigo.devices.subscribeToChanges()


		self.debugLog ("Debug Mode is activated.  (Only use if testing...)")
		self.re_init_zones_with_trigger_status ( )

	def insteonCommandSent(self, cmd):
	#
	#	Not used, example code
	#
		self.debugLog(u"insteonCommandSent: \n" + str(cmd))

	def insteonCommandReceived(self, cmd):
	#
	#	Any Insteon command that is received will pass through this function...
	#
	#
		#self.debugLog(u"insteonCommandReceived: \n" + str(cmd))
# 		ackValue : 0
# 		address : 01.7D.D8
# 		cmdBytes : [17, 0]
# 		cmdFunc : on
# 		cmdScene : 2				# button number
# 		cmdSuccess : True
# 		cmdValue : 0
# 		replyBytes : []
		insteon_address = str(cmd.address)
		insteon_cmd = cmd.cmdFunc
		insteon_Value = cmd.cmdValue
		id = self.InsteonList [ insteon_address.strip().upper() ]
		newDev = indigo.devices [ id ]
 		ZoneID = self.indigo_device_in_zone ( newDev.id )
 		if ZoneID == None:
 			return
		ZoneRecord = indigo.devices[ int(ZoneID) ]
		#
		#	InsteonCommandReceived is called by the Insteon command being received.  If the trigger isn't here,
		#	then it won't be triggered when a Insteon Command is received.
		#
		self.trigger_zone ( zoneRec = ZoneRecord, deviceRec = newDev, X10_Action = None)


	def	find_x10_securitysensor_enrollment ( self, secCodeId = "", housecode = None, devicecode = None):
		#
		#	Does an X10 Device exist?
		#	If so, is it registered with Switchboard?
		#
		#
		# self.X10List [ <X10 Sensor ID> ] = Monitored Device Group ID
		# self.X10List [ indigo.devices[dev].globalProps[plugin_id]["X10Security"] ] = str(dev.id)

		zoneid = None
		deviceid = None

		if secCodeId == "":
			return (None, None)

		if self.X10List.has_key ( str(secCodeId).upper() ):
			deviceid = self.X10List [ str(secCodeId).upper() ]

		elif secCodeId <> None:
			indigo.server.log ("An unregistered X10 device has been detected.  Security ID is %s" % secCodeId, isError=True)

		if deviceid <> None:
			zoneid = self.indigo_device_in_zone ( deviceid )
			if zoneid == None:
				if not indigo.devices[int(deviceid)].globalProps[plugin_id]["IgnoreOrphan"]:
					indigo.server.log ("%s [%s] not been assigned a Monitored Device Group." % (indigo.devices[int(deviceid)].name, deviceid), isError=True)

		return (zoneid, deviceid)

	def	check_X10_Heartbeats ( self ):
		email_template = '''Switchboard Alert - Heartbeat for %s is overdue!

Time & Date - %s

The Heartbeat for Device %s, is overdue.

The Last Reported Heartbeat was on %s.

Please check the device and/or batteries.
'''

		for X10_ID in self.X10List.keys():
			Indigo_Device_ID = int(self.X10List[ X10_ID ])
			if indigo.devices[Indigo_Device_ID].globalProps[plugin_id]["IgnoreHeartbeats"]  == False:
				timeout = float(indigo.devices[Indigo_Device_ID].globalProps[plugin_id]["X10HeartBeatTimeOut"]) * 60.0
				last_heartbeat_string = indigo.devices[Indigo_Device_ID].states["Last_X10HeartBeat"]
				if last_heartbeat_string == "":
					indigo.server.log ("Warning, %s, has no known heartbeat.  Please check sensor!" % indigo.devices[Indigo_Device_ID].name)
				else:
					last_heartbeat = time.mktime ( time.strptime ( last_heartbeat_string) )
					if time.mktime( time.localtime ( )) >=  last_heartbeat + timeout:
						indigo.server.log ("Watchdog error.  No Heartbeat for Sensor: %s, please check sensor battery." % indigo.devices[Indigo_Device_ID].name, isError = True)
						if self.pluginPrefs.get("sendHeartBeatEmails", False):
							#
							#	We are to send heartbeat email alerts
							#
							Email_Addresses = self.pluginPrefs.get("EmailAddresses", "")
							if len(Email_Addresses.split(",")) >= 1:
								#
								#	There is people to send alerts to
								#
								device_name = indigo.devices[Indigo_Device_ID].name
								alert_subject = "OverDue HeartBeat for X10 Device - %s" % device_name
								last_heartbeat = last_heartbeat_string
								current_time = time.ctime ()
								self.custom_send_emails ( subject=alert_subject, email_addrs=Email_Addresses, mail_message=email_template % (device_name, current_time, device_name, last_heartbeat) )

	def x10CommandReceived(self, cmd):
		self.debugLog  (u"x10CommandReceived: \n" + str(cmd))
			#Security Devices Debug          x10CommandReceived:
			#address :
			#cmdSuccess : True
			#cmdType : sec
			#secCodeId : 193
			#secFunc : sensor alert (min delay)
		housecode = None
		devicecode = None

		if cmd.address == "":
			self.debugLog  ("No X10 Address was received (but it might have a Security ID)")
		else:
			housecode = cmd.address[0]
			devicecode= cmd.address[1:2]

		zoneID, deviceID = self.find_x10_securitysensor_enrollment ( secCodeId = cmd.secCodeId, housecode = housecode, devicecode = devicecode)
		self.debugLog ("X10 - Zone %s, Device %s " % (zoneID, deviceID) )
		if zoneID <> None:
			zonerecord = indigo.devices[ int(zoneID) ]

		if deviceID == None:
			#
			#	Device was not found, we can't proceed, since there is no device record for this X10 ID.
			#	So Abort.  The Device has already been announced as being unknown, since that is part of
			#	find_x10_securitysensor_enrollment's job.
			#
			return
		#
		#	Change in v0.51, moved devicerecord and heartbeat code independent of zoneID test.
		#	This way the heartbeat and last_X10 code will process even if there is no zone id, if it is a heartbeat.
		#	Need to follow up with Trigger_Zone to see we can make it zone independent...
		#
		devicerecord = indigo.devices[int(deviceID)]
		stateString, onState = self.return_x10_action_state ( cmd.secFunc.strip() )
		if devicerecord.states.get ("Last_X10Command","").upper() == cmd.secFunc.strip().upper() and not(stateString in ["_Armed", "_Disarm", "_Panic"]):
			self.debugLog ("\tX10 Heartbeat detected")
			devicerecord.updateStateOnServer ("Last_X10HeartBeat", time.asctime(time.localtime ( )) )
			devicerecord.updateStateOnServer ("Last_X10Command", cmd.secFunc.strip() )
			heartbeat = True
		else:
			heartbeat = False
			displayState = stateString.replace ("_","")

		self.check_X10_Heartbeats ()

		if heartbeat <> True:
			if zoneID <> None:
				#
				#	X10CommandReceived is called by the X10 command being received.  Trigger Zone is necessary to allow
				#	Functional triggers on the zones.
				#
				self.trigger_zone ( zoneRec = zonerecord, deviceRec = devicerecord, X10_Action = cmd.secFunc )

			if stateString in ["_Armed", "_Disarm", "_Panic"]:
				SC_id = self.return_security_center ()
				if SC_id <> None:
					SecDev = indigo.devices [ int(SC_id) ]
					if stateString == "_Armed":
						SecDev.updateStateOnServer ("Armed", "Armed")
						SecDev.updateStateOnServer ("Last_Updated", time.asctime(time.localtime ( )) )
					elif stateString == "_Disarm":
						SecDev.updateStateOnServer ("Armed", "Disarmed")
						SecDev.updateStateOnServer ("Last_Updated", time.asctime(time.localtime ( )) )
					elif stateString == "_Panic":
						old_panic_state = SecDev.states["Panic"]
						SecDev.updateStateOnServer ("Panic", not(old_panic_state) )
						SecDev.updateStateOnServer ("Last_Updated", time.asctime(time.localtime ( )) )
			else:
				devicerecord.updateStateOnServer ("Last_X10Command", cmd.secFunc.strip() )
				devicerecord.updateStateOnServer ("Last_Triggered", time.asctime(time.localtime ( )) )
				devicerecord.updateStateOnServer ("Last_Updated", time.asctime(time.localtime ( )) )
				devicerecord.updateStateOnServer ("onState", onState )
				devicerecord.updateStateOnServer ("Display_onState", displayState)
			#
			# User Feedback indicates that a busy X10 device might fool Switchboard into missing a heartbeat.
			#
			#	Also, Heartbeat is used to ensure device is active.  If an X10 device command is received,
			#	obviously the device is active.
			#
			devicerecord.updateStateOnServer ("Last_X10HeartBeat", time.asctime(time.localtime ( )) )
