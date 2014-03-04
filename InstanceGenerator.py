#!/usr/bin/env python

'''
Created on 2013-1-24
@author: changshuai
'''
import pdb
import sys
import ConfigParser
from BsDiInstance import LevelInstances, Instance
from HKCommon import *
import HKCommon 
from AsInstance import *


def generate_bsdi(file_name):
	parser = ConfigParser.ConfigParser()
	levels = []
	try:
		parser.read(file_name)
		level_num = parser.getint("global", "level_num")
		HKCommon.logger.info("level num is:%d" % (level_num))
		if level_num <= 0:
			HKCommon.logger.fatal("level_num:" + level_num +" in " + file_name + "illegal")
			return ExitCode.E_PARAM
		
		for level_idx in range(0, level_num):
			section_str = "level%d" % (level_idx)
			slave_num = parser.getint(section_str, "instance_num")
			if slave_num <= 0:
				HKCommon.logger.fatal("[%s] slave_num:%d illegal" % (section_str, slave_num))
				return ExitCode.E_PARAM
			level_instances = LevelInstances()
			for slave_idx in range(0, slave_num):
				instance = Instance()
				instance.host = parser.get(section_str, "host_%d" % (slave_idx))
				instance.tran_path = parser.get(section_str, "tran_%d" % (slave_idx))
				instance.data_path = parser.get(section_str, "data_%d" % (slave_idx))
				instance.proc_path = parser.get(section_str, "proc_%d" % (slave_idx))
				instance.control_file = parser.get(section_str, "ctrl_%d" % (slave_idx))
				level_instances.add_instance(instance)
			
			levels.append(level_instances)
	except:
		HKCommon.logger.error(sys.exc_info())
		levels = []
	finally:
		return levels

def generate_as(file_name):
	parser = ConfigParser.ConfigParser()
	as_collector = AppasCollector()
	try:
		parser.read(file_name)
		section_str = "appas"
		instance_num = parser.getint(section_str, "instance_num")
		as_collector.clean_interval = parser.getint(section_str, "clean_interval")
		as_collector.clean_tool = parser.get(section_str, "clean_tool")
		port = parser.getint(section_str, "instance_port")
		for idx in range(0, instance_num):
			instance = Appas()
			instance.host = parser.get(section_str, "instance_%d" % (idx))
			instance.port = port
			as_collector.add(instance)
	except:
		HKCommon.logger.error(sys.exc_info())
		as_collector.__init__()
	finally:
		return as_collector

