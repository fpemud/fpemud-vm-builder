#!/usr/bin/python2
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-
#
#class FvmVirtService:
#	"""Encapsulate the DBUS-API of VirtService"""
#
#	def __init__(self, param):
#		self.param = param
#
#	def start(self):
#		pass
#		assert self.connPtr is None
#
#		self.connPtr = libvirt.open("qemu:///system")
#		if self.connPtr is None:
#			raise Exception("can not open libvirt connection \"qemu:///system\"")
#
#		self.netPtr = self.connPtr.networkLookupByName("windows-virtmanager-network-%s"%(self.param.username))
#		if self.netPtr is None:
#			# Generate xml file
#			libvirtXml = self._generateLibvirtNetworkXml()
#			FvmUtil.writeFile("libvirt-network.xml", libvirtXml)
#
#			# create virtual network
#			self.netPtr = self.connPtr.networkCreateXML(libvirtXml)
#			assert self.netPtr is not None
#
#	def stop(self):
#		pass
#		if self.netPtr is not None:
#			self.netPtr.free()
#			self.netPtr = None
#
#		if self.connPtr is not None:
#			ret = self.connPtr.close()
#			assert ret >= 0
#
#	def getLibvirtConnectionPtr(self):
#		assert self.connPtr is not None
#		return self.connPtr
#
#	def _generateLibvirtNetworkXml(self):
#
#		n3 = self.param.uid / 256
#		n4 = self.param.uid % 256
#
#		dom = xml.dom.minidom.getDOMImplementation().createDocument(None, "network", None)
#		network = dom.documentElement
#
#		self._newXmlNode(dom, network, "name", "network-%s"%(self.param.username))
#
#		self._newXmlNode(dom, network, "bridge", "", "name=vir-%s"%(self.param.username), "stp=off")
#		self._newXmlNode(dom, network, "forward", "", "mode=nat")
#
#		self._newXmlNode(dom, network, "mac", "", "address=%s:%02x:%02x:01"%(self.param.macOuiBr, n3, n4))
#
#		node = self._newXmlNode(dom, network, "ip", "", "address=10.%d.%d.1"%(n3, n4), "netmask=255.255.255.0")
#		if True:
#			node2 = self._newXmlNode(dom, node, "dhcp", "")
#			if True:
#				self._newXmlNode(dom, node2, "range", "start=10.%d.%d.3"%(n3, n4), "end=10.%d.%d.254"%(n3, n4))
#
#		return dom.toprettyxml(encoding="UTF-8")
#
#	def _newXmlNode(self, dom, parent, tagName, textStr="", *attrList):
#		"""returns the newly created xml node"""
#
#		# if textStr is not a string, convert it
#		textStr = str(textStr)
#
#		ret = dom.createElement(tagName)
#
#		for attr in attrList:
#			m = re.search(r"^(\S+)=(.*)$", attr)
#			key = m.group(1)
#			value = m.group(2)
#			ret.setAttribute(key, value)
#
#		if textStr != "":
#			text = dom.createTextNode(textStr)
#			ret.appendChild(text)
#
#		parent.appendChild(ret)
#		return ret

