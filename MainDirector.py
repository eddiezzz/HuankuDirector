#!/usr/bin/env python
'''
Created on 2013-1-24
@author: changshuai
'''

import sys, threading
from HKCommon import *
import HKCommon

import InstanceGenerator
from BsDiInstance import LevelInstances

class RoomExecutor(threading.Thread):
	'''
	RoomExecutor is used to parallel executor for different room(warehouse)
	room is identified by cfg file(name)
	'''
	def __init__(self):
		threading.Thread.__init__(self)
	
	def set_property(self, cfg, lvl):
		self.cfg_file = cfg
		self.level = lvl
		self.name = cfg.split('/')[-1].split('.')[0]

	def get_result(self):
		try:
			return self.result
		except:
			return ExitCode.E_ERR

	def run(self):
		sub_analyzer = SubAnalyzer(self.name)
		HKCommon.analyzer.add_sub_analyzer(self.name, sub_analyzer)

		sub_analyzer.start()
		while True:
			HKCommon.logger.info("%s huanku for level:%d start running" % (self.name, self.level))
			levels = InstanceGenerator.generate_bsdi(cfg_file)
			if len(levels) == 0:
				HKCommon.logger.error("%s contain 0 levels appbs & appadi, exit" % (self.name))
				break
			HKCommon.logger.info("%s contains %d levels appbs & appdi" % (self.name, len(levels)))
			sub_analyzer.add_tuple(('bs levels', str(len(levels))))

			as_collector = InstanceGenerator.generate_as(cfg_file)
			if len(as_collector.instance_list) == 0:
				HKCommon.logger.error("%s contain 0 appas, exit" % (self.name))
				break
			as_collector.name = self.name
			HKCommon.logger.info("%s contains %d appas" % (self.name, len(as_collector.instance_list)))
			sub_analyzer.add_tuple(('as num', str(len(as_collector.instance_list))))

			bsdi_start_time = int(time.time())
			level_instances = levels[level]
			level_instances.name = self.name
			self.result = level_instances.execute()
			bsdi_end_time = int(time.time())
			sub_analyzer.add_tuple(('bs di time used(sec)', str(bsdi_end_time - bsdi_start_time)))
			if self.result != ExitCode.E_SUC:
				HKCommon.logger.error("%s huanku fail for %d level" % (self.name, level))
				break

			HKCommon.logger.info("%s appbs & appdi change index succ for level:%d " % (self.name, self.level))
			as_start_time = int(time.time())
			ret = as_collector.do_clean()
			as_end_time = int(time.time())
			sub_analyzer.add_tuple(('clean as cache time used(sec)', str(as_end_time - as_start_time)))
			HKCommon.logger.info("%s appas clean cache over, huanku over" % (self.name))
			sub_analyzer.stop()
			return self.result

		self.result = ExitCode.E_ERR
		sub_analyzer.stop()
		return self.result

	
def usage(name):
	print '''
#Brief: %s is used for xiaoku huanku
#Author: zhengchangshuai@baidu.com

#usage: python HuankuDirector.py level(int) 
	''' % (name)

if __name__ == '__main__':
	name = sys.argv[0]
	if len(sys.argv) < 2:
		usage(name)
		sys.exit(-1)
	
	level = int(sys.argv[1])
	alarm_cfg = "./conf/alarm.cfg"

	init_log("./log/%s.log" % name)
	init_analyzer()
	ret = init_alarm(alarm_cfg)
	if ret != ExitCode.E_SUC:
		HKCommon.logger.error("AlarmSender parse_conf: %s failed" % alarm_cfg)
		#sys.exit(1)
	else:
		HKCommon.logger.info("AlarmSender parse_conf: %s succ" % alarm_cfg)
	HKCommon.logger.info("%s huanku start" % name)

	#cfg_files = ["./conf/hz.cfg", "./conf/jx.cfg", "./conf/tc.cfg"]
	cfg_files = ["./conf/hz.cfg"]
	room_executors = []
	for cfg_file in cfg_files:
		executor = RoomExecutor()
		executor.set_property(cfg=cfg_file, lvl=level)
		room_executors.append(executor)

	for executor in room_executors:
		executor.start()
	for executor in room_executors:
		executor.join()
	
	rets = []
	for executor in room_executors:
		rets.append(executor.get_result())

	suc_count = rets.count(ExitCode.E_SUC)
	msg = "total %d warehouse, %d succ for level:%d <br>" % (len(rets), suc_count, level)

	analyzer_str = HKCommon.analyzer.gen_report(msg)
	HKCommon.logger.info("send analyze content:" + analyzer_str)
	
	if rets.count(ExitCode.E_SUC) == len(rets):
		HKCommon.alarm.info(analyzer_str)
	else:
		HKCommon.alarm.warn(analyzer_str)
	sys.exit(0)
	
