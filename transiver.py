#!/usr/bin/python

import socket
import os
import sys
import getopt
import threading
import subprocess
from utility.utility import *
import logging

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
    p = subprocess.Popen(cmd, shell=True)
    # (output, err) = p.communicate()
    # print "iperf out", output

class runIperfClient(threading.Thread):
  def __init__(self, threadID, name, ip, port, sock_server, bw, logger):
    threading.Thread.__init__(self)
    self.threadID = threadID
    self.ip = ip
    self.port = port
    self.bw = bw
    self.t = 10
    self.sock_server = sock_server
    self.my_port = 0
    self.quit = False
    self.logger = logger
  def run(self):
    while self.quit == False:
      print "connecting to iperf server"
      cmd = "sudo iperf -c %s -p %s -u -b %sm -t 15 -l 1500" %(self.ip,self.port,self.bw)
      print cmd
      cmd = "sudo sh /users/mdolati/transiver/my_iperf.sh %s %s %s" %(self.ip,self.bw, self.t)
      p = subprocess.check_output(cmd, shell=True)
      self.bw += 0.1
      # (output, err) = p.communicate()
      p = str(p)
      loss_perc = p.split("%")[0].split("(")
      loss_perc = loss_perc[len(loss_perc)-1]
      logger.info("%s,%s" %("time",loss_perc))
      #print "/n--iperf out--/n",output
      o_list = p.split(']')
      o_list = o_list[1].split(' ')
      for i in range(len(o_list)):
        if o_list[i] == "port":
          self.my_port = int(o_list[i+1])
          break
          #endIf
      #endFor
      print "my_port",self.my_port
  def print_msg(self, msg):
    print "message from controller to application",msg    
  def instruct_app(self, msg):
    if msg[0] == "quit":
      self.quit = True
    self.print_msg(msg)
    if int(msg[0]) == self.my_port:
      self.bw -= float(msg[1])

'''class acceptCtrlFeedback(threading.Thread):
  def __init__(self, s):
    threading.Thread.__init__(self)
    self.s = s
  def run(self):
    return self.s.accept()'''

class sockServer(threading.Thread):
  def __init__(self, ip, sock_port, iperf_port, logger):
    threading.Thread.__init__(self)
    self.threadID = 2
    self.ip = ip
    self.sock_port = sock_port
    self.iperf_port = iperf_port
    self.logger = logger
    print "start sock server..."
  def run(self):
    kill_port_listener(self.sock_port)
    s = socket.socket()
    s.bind((self.ip, self.sock_port))
    print 'listening to controller to send feed back message'
    s.listen(10)
    self.clients = []
    print "spawn clients"
    '''ips = get_other_ips(self.get_right_most_ip_digit())
    bws = get_ip_bw(self.get_right_most_ip_digit())'''
    ips = ["10.1.66.3"]
    bws = [9.0]
    counter = 0
    for iperf_ip in ips:
      thread1 = runIperfClient(1, "Thread-1", iperf_ip, self.iperf_port, self, bws[counter], self.logger)
      counter += 1
      self.clients += [thread1]
      thread1.start()
    #endFor
    print "starting socket while accept..."
    while True:
      c, addr = s.accept()
      print "Got connection from controller", addr
      msg = c.recv(1024)
      #quickly close port
      c.close()
      msg_list = msg.split(',')
      for th in self.clients:
        th.instruct_app(msg_list)
      #endFor
    #endWhile
  def change_iperf_port(self, old_port, new_port):
    pass
  def get_right_most_ip_digit(self):
    return int(self.ip.split(".")[3])

# class nonBlocingSockServer

def run_client(ip, iperf_port):
  s = socket.socket()
  s.connect((ip, port))
  print s.recv(1024)
  s.close()

'''
getopt(
     sys_args,
     short_args_with_required_folloowed_by_:,
     long_args)
'''
long_opts = ["mode=","ip=","sock_port=","ips=","iperf_port="]
short_opts = ""
try:
  opts,args = getopt.getopt(sys.argv[1:], short_opts, long_opts)
  print opts
  print args
except getopt.GetoptError as err:
  print(err)
  usage()
  sys.exit(2)
mode="server"
ip="127.0.0.1"
sock_port=8080
ips=["127.0.0.1"]
iperf_port=12345
for o,a in opts:
  print o
  print a
  if o == "--mode":
    mode=a
  elif o == "--ip":
    ip=a
  elif o == "--sock_port":
    sock_port = int(a)
  elif o == "--ips":
    ips=a.split(',')
  elif o == "--iperf_port":
    iperf_port = int(a)
  else:
    assert False, "unhandled option"

cmd = "sudo apt-get install iperf"
p = subprocess.Popen(cmd, shell=True)
p.communicate()
if mode == "server":
  eth_num = get_eth_ip()[0][0]
  eth_ip = get_eth_ip()[0][1]
  logger = logging.getLogger(__name__)
  logger.setLevel(logging.INFO)
  handler = logging.FileHandler("/users/mdolati/transiver/results/results%s.log" %eth_ip)
  handler.setLevel(logging.INFO)
  # formatter = logging.Formatter('%(message)')
  # handler.setFormatter(formatter)
  logger.addHandler(handler)
  logger.info("hello")
  sock_server = sockServer(eth_ip, sock_port, iperf_port, logger) 
  sock_server.start()
  print "creating and running sock server finished..."
else:
  th1 = runIperfServer(1, "iperfServer", iperf_port)
  th1.start()
  print "finish..."

