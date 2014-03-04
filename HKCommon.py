#!/usr/bin/env python

'''
Created on 2013-1-24
@author: changshuai
'''
import logging
import paramiko
import time
import pdb
from AlarmSender import *
from Analyzer import *
import Analyzer

logger = None
alarm = None
analyzer = None

class MLoggerFilter(logging.Filter):
	def __init__(self, name=''):
		logging.Filter.__init__(self, name)
	def filter(self, record):
		if record.__str__().find("transport:_log") == -1:
			return 1
		return 0

def init_analyzer():
    global analyzer
    analyzer = Analyzer.Analyzer()

def init_log(log_file):
	global logger
	logger = logging.getLogger('sonny')
	hdlr = logging.FileHandler(log_file)
	formatter = logging.Formatter('%(asctime)s %(levelname)s [%(module)s:%(funcName)s:%(lineno)d] %(message)s')
	hdlr.setFormatter(formatter)
	logger.addHandler(hdlr)
	logger.setLevel(logging.INFO)
	filter = MLoggerFilter('sonny')
	logger.addFilter(filter)

class ExitCode:
	E_SUC = 0
	E_PARAM = -1
	E_TIMEOUT = -2
	E_ERR = -3
	repr_info = {E_SUC: "success", E_PARAM: "param error", E_TIMEOUT: "timeout error", E_ERR: "default error"}
	
def init_alarm(cfg_file):
	global alarm
	alarm = AlarmSender()
	ret = alarm.parse_cfg(cfg_file)
	if ret != 0:
		return ExitCode.E_ERR
	return ExitCode.E_SUC

class StageMode:
	S_COLLECT_FINDEX = 1
	S_SET_FINDEX = 2
	S_HUANKU = 3
	S_ROLLBACK = 4
	repr_info = {S_HUANKU: "HUANKU", S_ROLLBACK: "ROLLBACK", S_COLLECT_FINDEX: "COLLECT_FINDEX", S_SET_FINDEX: "SET_FINDEX"}

def ssh_execute_only_info(host, port, cmd):
	logger.info("host:%s exec cmd:%s" % (host, cmd))
	ssh = paramiko.SSHClient();
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect(hostname=host, port=22, username="img", password="MhxzKhl")
	stdin, stdout, stderr = ssh.exec_command(cmd)
	outstr = stdout.read()
	errstr = stderr.read()
	ssh.close()
	return (outstr, errstr)

def ssh_execute_only_code(host, port, cmd):
	logger.info("host:%s exec cmd:%s" % (host, cmd))
	ssh = paramiko.SSHClient();
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect(hostname=host, port=22, username="img", password="MhxzKhl")
	chan = ssh.get_transport().open_session() 
	chan.exec_command(cmd)
	ret = chan.recv_exit_status()  
	ssh.close()
	logger.info("host:%s exec cmd:%s, ret=%d" % (host, cmd, ret))
	if ret == 0:
		return ExitCode.E_SUC
	return ExitCode.E_ERR 

def ssh_execute(host, port, cmd, buf_size=1024):
	logger.info("host:%s exec cmd:%s" % (host, cmd))
	ret = ExitCode.E_SUC
	ssh = paramiko.SSHClient();
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect(hostname=host, port=22, username="img", password="MhxzKhl")
	chan = ssh.get_transport().open_session() 
	chan.exec_command(cmd)
	#stdin = chan.makefile('wb', buf_size)  
	stdout = chan.makefile('rb', buf_size)  
	stderr = chan.makefile_stderr('rb', buf_size)  
	outstr = stdout.read()
	errstr = stderr.read()
	ret = chan.recv_exit_status()  
	#logger.info("exec output code:%d, outstr:%s, errstr:%s" % (ret,outstr,errstr))
	if ret == 0:
		logger.info("host:%s exec cmd:%s, ret=%d" % (host, cmd, ret))
	else:
		logger.warn("host:%s exec cmd:%s, ret=%d, stdout:%s, stderr:%s" % (host, cmd, ret, outstr, errstr))
	ssh.close()
	if ret == 0:
		ret = ExitCode.E_SUC
	else:
		ret = ExitCode.E_ERR
	return (ret, outstr)#, stderr)

