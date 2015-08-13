#!/usr/bin/python

import socket
import os
import sys
import getopt
import threading
import subprocess
from utility.utility import *
import logging
import time
from time import sleep
import random

class runIperfServer(threading.Thread):
  def __init__(self, threadID, name, port, tcp_server):
    threading.Thread.__init__(self)
    self.threadID = threadID
    self.name = name
    self.port = port
    self.ip = ip
    self.tcp_server = tcp_server
  def run(self):
    #print "starting thread"
    cmd = "iperf -s"
    if self.tcp_server == False:
      cmd = "iperf -s -u -p %s" %(self.port)
    #print 'cmd to run iperf server',cmd
    p = subprocess.Popen(cmd, shell=True)
    # (output, err) = p.communicate()
    # print "iperf out", output

class runPing(threading.Thread):
  def __init__(self, threadID, name, ip, my_ip):
    threading.Thread.__init__(self)
    self.threadID = threadID
    self.ip = ip
    self.quit = False
    self.my_ip = my_ip
    logger = logging.getLogger("d%s%s" %(my_ip,ip))
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler("/users/mdolati/transiver/results/d-results%s-%s.csv" %(my_ip,ip))
    handler.setLevel(logging.INFO)
    # formatter = logging.Formatter('%(message)')
    # handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info("hello")
    self.logger = logger
  def run(self):
    while self.quit == False:
      cmd = "ping %s -c 20" %self.ip
      count = 0.0
      #print cmd
      p = subprocess.check_output(cmd, shell=True)
      try:
        p = p.split("time=")
        flag = True
        ping_avg = 0
        for tt in p:
          if flag:
            flag = False
            continue
          ping_res = tt.split(" ms")
          if len(ping_res) > 0:
            p_time = float(ping_res[0].split(" ms")[0])
            ping_avg += p_time
            count += 1.0
        #print ping_avg/20
        self.logger.info("delay,%s,%s" %(time.time()*1000, (ping_avg/count)))
      except:
        pass
  def quit_thread(self):
    self.quit = True

class runIperfClient(threading.Thread):
  def __init__(self, threadID, name, ip, port, sock_server, bw, my_ip, tcp_server):
    threading.Thread.__init__(self)
    self.threadID = threadID
    self.ip = ip
    self.port = port
    self.init_bw = bw
    self.bw = bw
    self.t = 20
    self.sock_server = sock_server
    self.tcp_server = tcp_server
    #
    self.my_ports = {}
    self.my_ports_index = 0
    self.my_ports_len = 30
    #
    self.quit = False
    self.my_ip = my_ip
    logger = logging.getLogger("l%s%s" %(my_ip,ip))
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler("/users/mdolati/transiver/results/l-results%s-%s.csv" %(my_ip,ip))
    handler.setLevel(logging.INFO)
    # formatter = logging.Formatter('%(message)')
    # handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info("hello")
    self.logger = logger
    self.incPeriod = 0
  def run(self):
    if self.tcp_server:
      self.run_tcp()
    while self.quit == False:
      excess = random.randint(100,1500)/100.0
      #print "connecting to iperf server"
      params = (self.ip,self.port,self.bw,(self.t+excess))
      cmd = "sudo iperf -c %s -p %s -u -b %sm -t %s" %params
      #print cmd
      # cmd = "sudo sh /users/mdolati/transiver/my_iperf.sh %s %s %s" %(self.ip,self.bw, self.t)
      p = subprocess.check_output(cmd, shell=True)
      # self.bw += 0.03
      # (output, err) = p.communicate()
      p = str(p)
      try:
        if p.find("%") == -1:
          continue
        loss_perc = p.split("%")[0].split("(")
        loss_perc = loss_perc[len(loss_perc)-1]
        #print ("loss", loss_perc)
        #print "/n--iperf out--/n",output
        bw_srv = p.split("Server Report:")
        bw_srv = bw_srv[len(bw_srv)-1].split("/sec")[0].split(" ")
        bw_srv_unit = bw_srv[len(bw_srv)-1]
        bw_srv_val = bw_srv[len(bw_srv)-2]
        #print ("bw", bw_srv_val, bw_srv_unit)
        self.logger.info("loss,%s,%s,%s,%s,%s" %(time.time(),self.bw,bw_srv_val,bw_srv_unit,loss_perc))
        #
        o_list = p.split(']')
        o_list = o_list[1].split(' ')
        for i in range(len(o_list)):
          if o_list[i] == "port":
            self.my_ports[self.my_ports_index] = int(o_list[i+1])
            self.my_ports_index = (self.my_ports_index+1) % self.my_ports_len
            break
            #endIf
        #endFor
        #print "my_port",self.my_port
      except:
        pass
  def run_tcp(self):
    while self.quit == False:
      excess = random.randint(100,1500)/100.0
      params = (self.ip,(self.t+excess))
      cmd = "sudo iperf -c %s -t %s" %params
      p = subprocess.check_output(cmd, shell=True)
      # self.bw += 0.03
      p = str(p)
      if p.find("/sec") == -1:
        continue
      last_line = p.split("]")
      last_line = last_line[len(last_line)-1]
      inf = last_line.split(" ")
      bw_unit = inf[len(inf)-1]
      bw_srv = inf[len(inf)-2]
      self.logger.info("tcp_bw,%s,%s,%s" %(time.time(),bw_srv,bw_unit))

  def print_msg(self, msg):
    print "message from controller to application",msg    
  def instruct_app(self, msg):
    if msg[0] == "quit":
      self.quit = True
    if int(msg[0]) in self.my_ports.values():
      if self.incPeriod < 3:
        self.incPeriod += 1
        return
      else:
        self.incPeriod = 0
      self.print_msg(msg)
      self.bw -= float(msg[1])
      if self.bw < 0.05:
        self.bw = 0.05
  def get_bw(self):
    return self.bw
  def quit_thread(self):
    self.quit = True

'''class acceptCtrlFeedback(threading.Thread):
  def __init__(self, s):
    threading.Thread.__init__(self)
    self.s = s
  def run(self):
    return self.s.accept()'''

class utilPrinter(threading.Thread):
  def __init__(self, server, ip):
    threading.Thread.__init__(self)
    self.server = server
    self.ip = ip
    logger = logging.getLogger("u%s" %ip)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler("/users/mdolati/transiver/results/u-results%s.csv" %ip)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    self.logger = logger
    self.quit = False
  def run(self):
    while self.quit == False:
      sum_bw = 0.0
      for th in self.server.clients:
        sum_bw += th.get_bw()
      self.logger.info("%s, %s" %(time.time(), sum_bw))
      sleep(20.0)
  def quit_thread(self):
    self.quit = True

class sockServer(threading.Thread):
  def __init__(self, ip, sock_port, iperf_port, tcp_server):
    threading.Thread.__init__(self)
    self.threadID = 2
    self.ip = ip
    self.sock_port = sock_port
    self.iperf_port = iperf_port
    self.tcp_server = tcp_server
    print "start sock server..."
  def run(self):
    kill_port_listener(self.sock_port)
    s = socket.socket()
    s.bind((self.ip, self.sock_port))
    print 'listening to controller to send feed back message'
    s.listen(20)
    self.clients = []
    self.pingers = []
    print "meeee %s" %self.get_right_most_ip_digit()
    ips = get_other_ips(self.get_right_most_ip_digit())
    bws = get_ip_bw(self.get_right_most_ip_digit())
    print "A: %s" %ips
    print "B: %s" %bws
    # ips = ["10.1.66.5"]
    # bws = [9.0]
    counter = 0
    for iperf_ip in ips:
      well_bw = bws[counter]
      if well_bw == 0.0:
        counter += 1
        continue
      if well_bw < 0.05:
        well_bw = 0.05
      thread1 = runIperfClient(1, "Thread-1", iperf_ip, self.iperf_port, self, well_bw, self.ip, tcp_server)
      counter += 1
      self.clients += [thread1]
      thread1.start()
      pinger = runPing(1, "t", iperf_ip, self.ip)
      self.pingers += [pinger]
      pinger.start()
      #sleep(random.randint(5,26)
    #endFor
    #print "starting socket while accept..."
    self.utiler = utilPrinter(self,self.ip)
    self.utiler.start()
    while True:
      c, addr = s.accept()
      #print "Got connection from controller", addr
      msg = c.recv(1024)
      c.close()
      quit_msg = ['quit','quit\n','quit\r\n']
      if msg in quit_msg:
        for cl in self.clients:
          print "%s" %cl
          cl.quit_thread()
        for pg in self.pingers:
          print "%s" %pg
          pg.quit_thread()
        self.utiler.quit_thread()
        break
      #quickly close port
      #c.close()
      msg_list = msg.split(',')
      #sum_bw = 0.0
      for th in self.clients:
        th.instruct_app(msg_list)
        #sum_bw += th.get_bw()
      #print "Current Outgoing Traffic from %s is %s" %(self.ip, sum_bw)
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
long_opts = ["mode=","ip=","sock_port=","ips=","iperf_port=","s_type="]
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
s_type="UDP"
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
  elif o == "--s_type":
    s_type=a
  else:
    assert False, "unhandled option"

cmd = "sudo apt-get install iperf"
p = subprocess.Popen(cmd, shell=True)
p.communicate()

tcp_server = False
if s_type == "TCP":
  tcp_server = True

if mode == "server":
  eth_num = get_eth_ip()[0][0]
  eth_ip = get_eth_ip()[0][1]
  sock_server = sockServer(eth_ip, sock_port, iperf_port, tcp_server) 
  sock_server.start()
  print "creating and running sock server finished..."
else:
  th1 = runIperfServer(1, "tIperfServer", iperf_port, True)
  th1.start()
  th1 = runIperfServer(2, "uIperfServer", iperf_port, False)
  th1.start()
  print "finish..."

