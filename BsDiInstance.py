#!/usr/bin/env python

'''
Created on 2013-1-24
@author: changshuai
'''
import threading
from HKCommon import *
import HKCommon
from Analyzer import *
import Analyzer

class Instance(threading.Thread):
	'''
	Instance is appbs or appdi, there is no difference between if we abstract the data_path and proc_path .etc
	support multi-stage for weak transaction, 
	also self-threading by derived from threading.Thread as you see
	'''
	def __init__(self):
		threading.Thread.__init__(self)

	def __str__(self):
		print "host:%s, tran_path:%s, data_path:%s, proc_path:%s, control_file:%s, mode:%s, findex:%d" \
			% (self.host, self.tran_path, self.data_path, self.proc_path, self.control_file, StageMode.repr_info(self.mode), self.findex)

	def set_mode(self, mode):
		self.mode = mode

	def set_findex(self, findex):
		self.findex = findex

	def execute_cmd(self, scmd):
		return ssh_execute(host=self.host, port=22, cmd=scmd)
		
	#panpan: transfer to index.new
	def execute_huanku(self):
		cmd = "cd %s && rm -rf index.old && mv index index.old && mv %s index" % (self.data_path, self.tran_path) 
		cmd += " && cd %s && ./bin/%s restart" % (self.proc_path, self.control_file)
		return self.execute_cmd(cmd)[0]

	def execute_rollback(self):
		cmd = "cd %s && mv index %s; mv index.old index" % (self.data_path, self.tran_path)
		#directly restart is ok? nearly no rollback in new huanku strategy
		cmd += " && cd %s && ./bin/%s restart" % (self.proc_path, self.control_file)
		return self.execute_cmd(cmd)[0]
	
	def execute_collect_findex(self):
		cmd = "grep findex %s/index/version.txt" % (self.data_path)
		ret, msgout = self.execute_cmd(cmd)
		if ret != ExitCode.E_SUC:
			return ret
		findex = int(msgout.split(':')[1])
		return findex
	
	def execute_set_findex(self, new=None):
		if new == None:
			cmd = "echo 'findex:%d'>%s/index/version.txt" % (self.findex, self.data_path)
			cmd += "&& echo \"version_flag:$(date +%%s)\">>%s/index/version.txt" % (self.data_path)
			return self.execute_cmd(cmd)[0]
		else:
			cmd = "echo 'findex:%d'>%s/version.txt" % (self.findex, self.tran_path)
			cmd += "&& echo \"version_flag:$(date +%%s)\">>%s/version.txt" % (self.tran_path)
			return self.execute_cmd(cmd)[0]
	
	def run(self):
		if self.mode == StageMode.S_COLLECT_FINDEX:
			self.result = self.execute_collect_findex()
			HKCommon.logger.info("host:%s datapath:%s findex:%d" %(self.host, self.data_path, self.result))
		elif self.mode == StageMode.S_SET_FINDEX:
			self.result = self.execute_set_findex()
		elif self.mode == StageMode.S_HUANKU:
			self.result = self.execute_set_findex(True)
			if self.result != ExitCode.E_SUC:
				return self.result
			self.result = self.execute_huanku()
		elif self.mode == StageMode.S_ROLLBACK:
			self.result = self.execute_rollback()		
		else:
			self.result = ExitCode.E_PARAM
			HKCommon.logger.error("mode: %d error" %(self.mode))
			
		return self.result

	def get_result(self):
		return self.result


class LevelInstances:
	'''
	LevelInstances is used to manage one level instances(appbs|appdi), in one level there is a weak transaction,
	which means any instance failed, the whole level will rollback.
	instances in LevelInstances is parallelly executed.
	and we record many details in this transaction by using Analyzer
	
	'''
	def __init__(self):
		self.instances = []
		self.curr_findex = 0
		self.name = ""
	
	def add_instance(self, instance):
		self.instances.append(instance)
		
	def parallel_execute(self):
		HKCommon.logger.info("LevelInstances contains %d instances, goto parallel execute" % (len(self.instances)))
		rets = []

		for instance in self.instances:
			instance.start()
		for instance in self.instances:
			instance.join()
			rets.append(instance.get_result())
		for instance in self.instances:
			instance.__init__()# for next thread start
		return rets
	
	def set_mode(self, mode):
		for instance in self.instances:
			instance.set_mode(mode)
		HKCommon.logger.info("stage: %s" % (StageMode.repr_info[mode]))
			
	def set_findex(self, findex):
		for instance in self.instances:
			instance.set_findex(findex)
		self.curr_findex = findex
		
				
	def execute(self):
		sub_analyzer = HKCommon.analyzer.get_sub_analyzer(self.name)
		sub_analyzer.add_tuple(('bs&di instances to exec', ','.join(self.instances[id].host for id in range(len(self.instances)))))

		self.set_mode(StageMode.S_COLLECT_FINDEX)
		findexs = self.parallel_execute()
		sub_analyzer.add_tuple(('stage:S_COLLECT_FINDEX rets', ','.join(str(x) for x in findexs)))
		findexs.sort()
		if findexs[0] < 0 or findexs[0] != findexs[len(findexs)-1]:
			self.set_mode(StageMode.S_SET_FINDEX)
			self.set_findex(0)
			rets = self.parallel_execute()
			sub_analyzer.add_tuple(('stage:S_SET_FINDEX rets', ','.join(str(x) for x in rets)))
			if rets.count(ExitCode.E_SUC) != len(rets):
				HKCommon.logger.error("set findex to %d error: %s" % (self.curr_findex, rets.__str__()))
				return ExitCode.E_ERR
		else:
			self.set_findex(1 - findexs[0])
				
		self.set_mode(StageMode.S_HUANKU)
		rets = self.parallel_execute()
		sub_analyzer.add_tuple(('stage:S_HUANKU rets', ','.join(str(x) for x in rets)))
		if rets.count(ExitCode.E_SUC) == len(rets):
			return ExitCode.E_SUC
		HKCommon.logger.warn("huanku rets:%s" % (rets.__str__()))
		self.set_mode(StageMode.S_ROLLBACK)
		rets = self.parallel_execute()
		sub_analyzer.add_tuple(('stage:S_ROLLBACK rets', ','.join(str(x) for x in rets)))
		HKCommon.logger.info("rollback rets:%s" % (rets.__str__()))
		return ExitCode.E_ERR
 
