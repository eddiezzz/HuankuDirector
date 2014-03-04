#!/usr/bin/env python

'''
Created on 2013-1-24
@author: changshuai
'''

import os, time
from HKCommon import *
import HKCommon

class Appas:
	'''
	appas clean actor
	'''
	def __init__(self):
		self.host = ""
		self.port = -1
	
	def do_clean(self, tool):
		cmd = "%s -t 0 -s %s -p %d" % (tool, self.host, self.port)
		ret = os.system(cmd)
		ret >>= 8
		if ret == 0:
			HKCommon.logger.info("appas(%s:%d) clean succ" %(self.host, self.port))
			return ExitCode.E_SUC
		HKCommon.logger.info("appas(%s:%d) clean fail" %(self.host, self.port))
		return ExitCode.E_ERR

class AppasCollector:
	'''
	A collector for appas instance, also record what happened during clean cache by Analyzer
	'''
	def __init__(self):
		self.instance_list = []
		self.clean_interval = 0
		self.clean_tool = ""
		self.name = ""
	
	def add(self, appas):
		self.instance_list.append(appas)

	def do_clean(self):
		HKCommon.logger.info("goto clean all appas cache")
		ret = 0
		succ = 0
		failed_as = ""
		for appas in self.instance_list:
			ret = appas.do_clean(self.clean_tool)
			if ret == ExitCode.E_SUC:
				succ += 1
			else:
				failed_as += appas.host + ','
			time.sleep(self.clean_interval)
		HKCommon.logger.info("total %d appas, succ %d" % (len(self.instance_list), succ))
		sub_analyzer = HKCommon.analyzer.get_sub_analyzer(self.name)
		sub_analyzer.add_tuple(("failed as", failed_as))
		if succ == len(self.instance_list):
			return ExitCode.E_SUC
		return ExitCode.E_ERR
		

