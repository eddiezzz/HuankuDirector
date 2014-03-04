#!/usr/bin/env python

'''
Created on 2013-1-24
@author: changshuai
'''
import threading
import time

class Demo(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		try:
			self.host
		except:
			self.host = ""

		print "Demo init"

	def __str__(self):
		return self.host
	
	def set_cfg_file(self, cfg_file):
		self.cfg_file = cfg_file

	def run(self):
		print "Demo::run: %d" % (time.time())
		time.sleep(3)

if __name__ == '__main__':
	demo = Demo()
	demo.host = "127.0.0.1"

	demo.start()
	demo.join()
	print demo
	demo.__init__()

	demo.start()
	demo.join()
	print demo

	demo.set_cfg_file("haha")
	print demo.cfg_file
