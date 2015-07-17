#!/usr/bin/python

import random
from struct import pack
from zlib import crc32
# for flow_stats_to_list
from pox.openflow.of_json import *

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpid_to_str
from pox.lib.util import str_to_bool
import time
import threading
from thread import *
# from httplib2 import Http
from urllib import urlencode
import sys
import math
# sending feedback to clients
import socket

log = core.getLogger()

switch_num_detected = 0
switches_detected = {}
TOPO_LINK_NUM = 12
link_num_detected = 0
h_sw = {}

class DeviceStat:

  def __init__( self, ports ):
    self.ports = ports

  def addPort(self, port, extra):
    self.ports[port] = extra

class PortStat:

  def __init__( self, rx, tx ):
    self.rx = rx
    self.tx = tx

  def updateRx( self, rx ):
    self.rx = rx

  def updateTx( self, tx ):
    self.tx = tx

  def periodRx( self, rx ):
    ret = rx - self.rx
    self.rx = rx
    return ret

  def periodTx( self, tx ):
    ret = tx - self.tx
    self.tx = tx
    return ret

def sendR(ip, port, defPort, rate):
  try:
    s = socket.socket()
    s.connect((str(ip),defPort))
    try:
      s.sendall(""+str(port)+","+str(rate))
      log.warning("\n\tsendR: " + str(port) + ':' + str(ip) + ':' + str(int(rate)) )
    except socket.error:
      log.warning("send failed")
    finally:
      s.close()
  except:
    log.warning("\n\tError connecting to %s:%s" %(ip,port))
  '''
  try:
    h = Http()
    mes = 'r'+str(port)+','+str(int(rate))
    url = "http://127.0.0.1:8089/regulate/"+mes+"/"+str(ip)
    h.request(url, "GET")
  except:
    log.warning('error in sending congestion info to hosts' + str(sys.exc_info()[0]))
  '''

statsDict = {}
congestedDict = {}

class FlowDicto(object):

  def __init__(self, dicto):
    self.flowDicto = dicto

  def addFlow(self, k, v):
    if k in self.flowDicto:
      cur = self.flowDicto[k]
      if cur[2] < v[2]:
        self.flowDicto[k] = v
    else:
      self.flowDicto[k] = v

  def getFlowDicto(self):
    return self.flowDicto

  def resetFlowDicto(self):
    self.flowDicto={}

def _timer_func ():
  defVal = 20
  defPort = 8080 
  ddd = core.flowDicto.getFlowDicto()
  #log.warning("-------------------- %s -------" %len(ddd))
  for f in ddd:
    v = ddd[f]
    rIp = v[0]
    rPort = v[1]
    defVal = v[2]
    if defVal != 0.0: 
      start_new_thread(sendR ,(rIp, rPort, defPort, defVal,))
    # CHERA INJA BREAK BOOOOOOOD??????? :((((((((
  core.flowDicto.resetFlowDicto()
  if core.cong == True:
    core.cong = False
    core.congRounds += 0.3
  else:
    core.congRounds = 0
  for connection in core.openflow._connections.values():
    # connection.send(of.ofp_stats_request(body=of.ofp_flow_stats_request()))
    connection.send(of.ofp_stats_request(body=of.ofp_port_stats_request()))
  # log.debug("Sent %i port stats request(s)", len(core.openflow._connections))
  
# handler to display flow statistics received in JSON format
# structure of event.stats is defined by ofp_flow_stats()
def _handle_flowstats_received (event):
  # unit is Mb and statistics give Byte, so need division
  BW_UNIT = (1000000.0/8.0)
  device = dpidToStr(event.connection.dpid)
  stats = flow_stats_to_list(event.stats)
  conn = event.connection

  if (device in congestedDict)==False:
    log.debug( "Congestion in device %s already has been taken care of!", device ) 
    return
  
  flowUsageRatio = {}
  totalKilo = 0.0

  for f in event.stats:
    for ac in f.actions:
      if ac.port in congestedDict[device].ports:
        # 0x0800 shows IP packet type
        if f.match.dl_type == 0x0800:
          # log.debug( "Flow %s %s is a potential responsible of the congestion!", f.match.nw_src, f.match.tp_src )
          # search over registered flows that want their rate to be regulated
          valKilo = f.byte_count/BW_UNIT
          totalKilo += valKilo
          flowUsageRatio[str(f.match.nw_src)+str(f.match.tp_src)] = (f.match.nw_src, f.match.tp_src, valKilo, ac.port)
          #log.warning("\n\tOn device %s port %s\n\tIP flow with tp: %s and usage: %s" %(device,ac.port,f.match.tp_src,valKilo))
          #ignore registration
          ''' 
          for reg in core.regFlows.getFlows():
            log.debug( "%s %s", reg[0], reg[1] )
            # log.debug('%% number of bytes this flow send: ' + ' ' + str(f.actions[0].port))
            if str(reg[0])==str(f.match.nw_src) and str(reg[1]) == str(f.match.tp_src):
              valKilo = f.byte_count/1000.0
              totalKilo += valKilo
              flowUsageRatio[str(f.match.nw_src)+str(f.match.tp_src)] = (f.match.nw_src, f.match.tp_src, valKilo, f.actions[0].port)
            else:
              log.debug("these two are not equal: " + str(reg[0]) + str(f.match.nw_src) + str(reg[1]) + str(f.match.tp_src))
          '''
        else:
          log.debug( "Flow of type %s is responsible", f.match.dl_type )

  if totalKilo == 0.0:
    return

  for n in flowUsageRatio:
    ratio = flowUsageRatio[n][2]/totalKilo
    overUse = 0
    # over use over port 
    if flowUsageRatio[n][3] in congestedDict[device].ports:
      overUse = congestedDict[device].ports[flowUsageRatio[n][3]]
    # if flow floods here pick up a port randomly
    if flowUsageRatio[n][3] == of.OFPP_FLOOD:
      for p in congestedDict[device].ports:
        overUse = congestedDict[device].ports[p]
        break
    # add flow for later treatment
    if overUse != 0:
      #log.warning("\n\tsending request to %s for: %s" %(n,overUse*ratio))
      val_to_reduce = overUse*ratio*core.congRounds
      core.flowDicto.addFlow( n, (flowUsageRatio[n][0], flowUsageRatio[n][1], val_to_reduce) )

  del congestedDict[device]
  return
  #log.warning("FlowStatsReceived from %s: %s",
  #  dpidToStr(event.connection.dpid), stats)

  #for fl in event.stats:
  #  if fl.packet_count > 0:
  #    log.warning("\nflow during: %s sec, with byte: %s", 
  #      fl.duration_sec, fl.packet_count)

  # Get number of bytes/packets in flows for web traffic only
  web_bytes = 0
  web_flows = 0
  web_packet = 0
  for f in event.stats:
    if f.match.tp_dst == 80 or f.match.tp_src == 80:
      web_bytes += f.byte_count
      web_packet += f.packet_count
      web_flows += 1
  #log.warning("Web traffic from %s: %s bytes (%s packets) over %s flows",
  #  dpidToStr(event.connection.dpid), web_bytes, web_packet, web_flows)

def get_intf_capa(device, port):
  H_TO_E = E_TO_H = 4.3
  E_TO_A = A_TO_E = 8.6
  A_TO_C = C_TO_A = 17.2
  DEFF = 20
  if device not in switches_detected:
    return DEFF
  print "G: %s" %(switches_detected[device])
  for l in switches_detected[device]:
    if l[0] == port:
      print "H: %s %s %s %s" %(port,type(port),l[0],type(l[0]))
      oth = h_sw[l[1]]
      print "I: %s" %oth[0]
      if h_sw[device][0] == "EDGE" and h_sw[l[1]][0] == "AGG":
        return E_TO_A
      if h_sw[device][0] == "AGG" and h_sw[l[1]][0] == "EDGE":
        return A_TO_E
      if h_sw[device][0] == "AGG" and h_sw[l[1]][0] == "CORE":
        return A_TO_C
      if h_sw[device][0] == "CORE" and h_sw[l[1]][0] == "AGG":
        return C_TO_A
  if h_sw[device][0] == "EDGE":
    return E_TO_H
  else:
    return DEFF

# handler to display port statistics received in JSON format
def _handle_portstats_received (event):
  # unit is byte and max is 10MB
  BW_UNIT = 1000000.0
  MAX_ALLOWED_BW = 4.3
  MONIT_PERIOD = 10.0

  stats = flow_stats_to_list(event.stats)
  device = dpidToStr(event.connection.dpid)
  conn = event.connection
  
  if (device in statsDict) == False:
    statsDict[device] = DeviceStat( {} )
   
  congestion = False

  for pStat in stats:
    portNo = pStat['port_no']
    if (portNo in statsDict[device].ports) == False:
      statsDict[device].ports[portNo] = PortStat(pStat['rx_bytes']*8, pStat['tx_bytes']*8)
    else:
      perRx = statsDict[device].ports[portNo].periodRx(pStat['rx_bytes']*8)
      perTx = statsDict[device].ports[portNo].periodTx(pStat['tx_bytes']*8)
      if perRx != 0 or perTx != 0:
        log.debug( "period rx: %s and tx: %s", perRx, perTx )
      tx_rate = (perTx/BW_UNIT)/MONIT_PERIOD
      #log.warning("\n\ton device %s, port %s. tx: %s. rate: %s" %(device,portNo,perTx,tx_rate))
      maxx = get_intf_capa(device, portNo)
      log.warning("d: %s, p: %s, m: %s" %(device,portNo,maxx))
      if tx_rate> MAX_ALLOWED_BW:
        congestion = True
        core.cong = True
        over_use = tx_rate - maxx
        #log.warning("\n\t!!CONGESTION!!\n\tin device %s rate: %s\n\toveruse: %s" %(device,tx_rate,over_use))
        if (device in congestedDict)==False:
          congestedDict[device] = DeviceStat({portNo:over_use})
        else:
          congestedDict[device].addPort(portNo, over_use)
      else:
        log.debug( "every thing is goooood on switch %s and port %s!", dpidToStr(conn.dpid), portNo )  

  if congestion == True:
    conn.send(of.ofp_stats_request(body=of.ofp_flow_stats_request()))

class RegFlows( object ):
  def __init__( self, fls ):
    self.fls  = fls

  def addFlow(self, f):
    self.fls += [f]

  def getFlows(self):
    return self.fls

def find_core():
  #height from core is 2 for all branches
  global h_sw
  for n in switches_detected:
    print "%s .. %s" %(n,switches_detected[n])
  for n in switches_detected:
    if len(switches_detected[n]) == 1:
      h_sw[n] = ("EDGE", 4.3)
  for n in switches_detected:
    for oth in switches_detected[n]:
      if n not in h_sw and oth[1] in h_sw and h_sw[oth[1]][0] == "EDGE":
        h_sw[n] = ("AGG", 8.6)
  for n in switches_detected:
    for oth in switches_detected[n]:
      if n not in h_sw and oth[1] in h_sw and h_sw[oth[1]][0] == "AGG":
        h_sw[n] = ("CORE", 17.2)
  print ">>>>> %s" % h_sw

def _handle_openflow_discovery_LinkEvent (event): 
  global link_num_detected
  global switches_detected
  s1 = event.link.dpid1 
  s2 = event.link.dpid2
  s1 = dpidToStr(s1)
  s2 = dpidToStr(s2)
  #port type is int
  p1 = event.link.port1
  p2 = event.link.port2
  if s1 not in switches_detected:
    switches_detected[s1] = [(p1,s2)]
  else:
    if (p1,s2) not in switches_detected[s1]:
      switches_detected[s1] += [(p1,s2)]
  if s2 not in switches_detected:
    switches_detected[s2] = [(p2,s1)]
  else:
    if (p2,s1) not in switches_detected[s2]:
      switches_detected[s2] += [(p2,s1)]
  #
  link_num_detected += 1
  if link_num_detected == TOPO_LINK_NUM:
    print find_core()
  #print "%s %s %s %s" %(s1,p1,s2,p2)

def launch(topo = None, routing = None, mode = None):
  log.warning("starting monitoring module")

  regFlows = RegFlows([])
  core.register( 'regFlows', regFlows )
  flowDicto = FlowDicto({})
  core.register( 'flowDicto', flowDicto )
  congRounds = 0
  core.register( 'congRounds', congRounds )
  cong = False
  core.register( 'cong', cong )
  # core.registeredFlows = []

  from pox.lib.recoco import Timer
  
  # attach handsers to listners
  core.openflow.addListenerByName("FlowStatsReceived", _handle_flowstats_received)
  core.openflow.addListenerByName("PortStatsReceived", _handle_portstats_received) 
  core.openflow_discovery.addListenerByName("LinkEvent", _handle_openflow_discovery_LinkEvent)
  # timer set
  Timer(10, _timer_func, recurring=True)
