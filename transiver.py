#!/usr/bin/python

import socket
import os
import sys
import getopt
import threading
import subprocess

class runIperfServer(threading.Thread):
  def __init__(self, threadID, name, port):
    threading.Thread.__init__(self)
    self.threadID = threadID
    self.name = name
    self.port = port
    self.ip = ip
  def run(self):
    print "starting thread"
    cmd = "iperf -s -u -p %s" %(self.port)
    print 'cmd to run iperf server',cmd
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    print "iperf out", output

class runIperfClient(threading.Thread):
  def __init__(self, threadID, name, ip, port, sock_server):
    threading.Thread.__init__(self)
    self.threadID = threadID
    self.ip = ip
    self.port = port
    self.bw = 10.0
    self.sock_server = sock_server
    self.my_port = 0
    self.quit = False
  def run(self):
    print "connecting to iperf server"
    cmd = "iperf -c %s -p %s -u -b %sm -t 10" %(self.ip,self.port,self.bw)
    print cmd
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    #print "/n--iperf out--/n",output
    o_list = output.split(']')
    o_list = o_list[1].split(' ')
    for i in range(len(o_list)):
      if o_list[i] == "port":
        self.my_port = int(o_list[i+1])
        break
        #endIf
    #endFor
    print "my_port",self.my_port
