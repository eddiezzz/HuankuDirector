#!/usr/bin/env python

'''
Created on 2013-1-24
@author: changshuai
'''
import time
import socket
import pdb

class TableFormater:
	'''
	TableFormater is a simple class to manage structured data into table format, 
	then generate html str
	'''
	def __init__(self):
		self.content = ""
	def set_title(self, title):
		self.title = title
	def gen_row(self, cols):
		return "<td>" + "</td><td>".join(cols) + "</td>"
	def add_row(self, row):
		self.content += "<tr>" + row + "</tr>"
	def toString(self):
		return "<div style='color:blue'>" + self.title + "</div>" \
				"<table border = 1 bgcolor=#eeeeee>" \
				+ self.content \
				+ "</table>"

class SubAnalyzer:
	'''
	SubAnalyzer is used to record what had happen in one warehouse
	different SubAnalyzer is identified by self.name
	'''
	def __init__(self, name):
		self.room_name = name
		empty = ('','')
		self.tuples = [empty,]
	def start(self):
		self.time_start = time.time()
		self.time_start_str = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(self.time_start)) 
	def stop(self):
		self.time_end = time.time()
		self.time_end_str = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(self.time_end)) 
	def add_tuple(self, tuple):
		self.tuples.append(tuple)
	def gen_report(self):
		table = TableFormater()
		title = "[%s warehouse] huanku use %d seconds: From %s to %s" \
				  % (self.room_name, int(self.time_end) - int(self.time_start), self.time_start_str, self.time_end_str)
		table.set_title(title)
		for tuple in self.tuples:
			table.add_row(table.gen_row(tuple))
		return table.toString()

class Analyzer:
	'''
	SubAnalyzer aggregator
	gen all SubAnalyzer to one report string 
	'''
	def __init__(self):
		self.analyzer_dict = {}
	def add_sub_analyzer(self, name, sub_analyzer):
		self.analyzer_dict[name] = sub_analyzer
	def get_sub_analyzer(self, name):
		return self.analyzer_dict.get(name)
	def gen_report(self, prefix=""):
		report = prefix
		for name,sub in self.analyzer_dict.iteritems():
			report += "<br>------------------" + name + " start-----------------<br>"
			report += sub.gen_report()
			report += "<br>------------------" + name + " end-------------------<br>"
		return report


