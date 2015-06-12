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
    cmd = "iperf -c %s -p %s -u -b %sm -t 10 -l 1500" %(self.ip,self.port,self.bw)
    print cmd
    p = subprocess.Popen("sh ~/transiver/my_iperf.sh", stdout=subprocess.PIPE, shell=True)
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
    if self.quit == False:
      self.run()
  def print_msg(self, msg):
    print "message from controller to application",msg    
  def instruct_app(self, msg):
    if msg[0] == "quit":
      self.quit = True
    self.print_msg(msg)
    if int(msg[0]) == self.my_port:
      self.bw -= float(msg[1])

class sockServer:
  def __init__(self):
    pass
  def run_server(self, ip, sock_port, ips, iperf_port):
    s = socket.socket()
    s.bind((ip, sock_port))
    print 'listening to controller to send feed back message'
    s.listen(10)
    self.clients = []
    print "spawn clients"
    for iperf_ip in ips:
      thread1 = runIperfClient(1, "Thread-1", iperf_ip, iperf_port, self)
      self.clients += [thread1]
      thread1.start()
    #endFor
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

if mode == "server":
  sock_server = sockServer()  
  sock_server.run_server(ip, sock_port, ips, iperf_port)
else:
  th1 = runIperfServer(1, "iperfServer", iperf_port)
  th1.start()


