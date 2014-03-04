#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 2013-1-24
@author: changshuai
'''

import sys, socket
import email
import mimetypes
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
import smtplib
import ConfigParser

def sendEmail(authInfo, fromAdd, toAdd, subject, plainText, htmlText):
	server = authInfo.get('server')
	user = authInfo.get('user')
	passwd = authInfo.get('password')

	if not (server and user and passwd) :
		print 'incomplete login info, exit now'
		return

	# 设定root信息
	msgRoot = MIMEMultipart('related')
	msgRoot['Subject'] = subject
	msgRoot['From'] = fromAdd
	msgRoot['To'] = toAdd
	msgRoot.preamble = 'This is a multi-part message in MIME format.'

	# Encapsulate the plain and HTML versions of the message body in an
	# 'alternative' part, so message agents can decide which they want to display.
	msgAlternative = MIMEMultipart('alternative')
	msgRoot.attach(msgAlternative)

	#设定纯文本信息
	msgText = MIMEText(plainText, 'plain', 'utf-8')
	msgAlternative.attach(msgText)

	#设定HTML信息
	msgText = MIMEText(htmlText, 'html', 'utf-8')
	msgAlternative.attach(msgText)

	#设定内置图片信息
	#fp = open('test.jpg', 'rb')
	#msgImage = MIMEImage(fp.read())
	#fp.close()
	#msgImage.add_header('Content-ID', '<image1>')
	#msgRoot.attach(msgImage)

	#发送邮件
	#print "server:%s,user:%s, password:%s" % (server, user, passwd)
	#pdb.set_trace()
	smtp = smtplib.SMTP(server)
	smtp.set_debuglevel(1)
	#smtp.ehlo_or_helo_if_needed()
	smtp.ehlo() 
	smtp.starttls() 
	smtp.ehlo() 
	smtp.login(user, passwd)
	smtp.sendmail(fromAdd, toAdd, msgRoot.as_string())
	smtp.quit()
	return

class AlarmSender:
	'''
	AlarmSender is use to send mail & sms to users
	complicated configure supported by using cfg file, 
	plz refer to ./conf/alarm.cfg
	'''
	def parse_cfg(self, file_name):
		parser = ConfigParser.ConfigParser()
		parser.read(file_name)
		self.auth_info = {}
		self.auth_info['server'] = parser.get("auth", "server")
		self.auth_info['user'] = parser.get("auth", "user")
		self.auth_info['password'] = parser.get("auth", "password")

		self.from_addr = parser.get("content", "from_addr")
		self.info_subject = parser.get("content", "info_subject")
		self.warn_subject= parser.get("content", "warn_subject")

		self.mail_info_recipients = parser.get("mail", "info_recipients")
		self.mail_warn_recipients = parser.get("mail", "warn_recipients")

		self.sms_info_recipients = parser.get("sms", "info_recipients")
		self.sms_warn_recipients = parser.get("sms", "warn_recipients")

		if not (self.auth_info.get('server') and self.auth_info.get('user') and self.auth_info.get('password') \
			and self.from_addr and self.info_subject and self.warn_subject \
			and self.mail_info_recipients and self.mail_warn_recipients \
			and self.sms_info_recipients and self.sms_warn_recipients):
			return -1
		return 0

	def info(self, msg):
		#msg = " repory by host:" + socket.gethostname() + "\n\r" + msg
		sendEmail(self.auth_info, self.from_addr, self.mail_info_recipients, self.info_subject, "", msg)

	def warn(self, msg):
		#msg = " repory by host:" + socket.gethostname() + "\n\r" + msg
		sendEmail(self.auth_info, self.from_addr, self.mail_warn_recipients, self.warn_subject, "", msg)
		#sendSms

if __name__ == '__main__' :
	print "TestAlarmSender"
	alarm = AlarmSender()
	cfg = './conf/alarm.cfg'
	ret = alarm.parse_cfg(cfg)
	if ret != 0:
		print "parse cfg:%s failed" % (cfg)
		sys.exit(1)
	print "parse cfg:%s succ" % (cfg)
	alarm.info('hello zcs')
	sys.exit(0)
	

