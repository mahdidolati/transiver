from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpid_to_str
from pox.lib.util import str_to_bool
import time
import threading
from thread import *
from httplib2 import Http
from urllib import urlencode
import sys
import math

log = core.getLogger()

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
  log.info("--------------------=-=-=-=-=-=--==sending congestion info to: " + str(port) + ':' + str(ip) + ':' + str(int(rate)) )
  try:
    h = Http()
    mes = 'r'+str(port)+','+str(int(rate))
    url = "http://127.0.0.1:8089/regulate/"+mes+"/"+str(ip)
    h.request(url, "GET")
  except:
    log.info('error in sending congestion info to hosts' + str(sys.exc_info()[0]))

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
  '''defVal = 20
  defPort = 5769
  ddd = core.flowDicto.getFlowDicto()
  log.info('>>>>>>>Sending congestion info...'+str(len(ddd)))
  for f in ddd:
    v = ddd[f]
    rIp = v[0]
    rPort = v[1]
    defVal = v[2]
    start_new_thread(sendR ,(rIp, rPort, defPort, defVal,))
    break
  core.flowDicto.resetFlowDicto()
  log.info('<<<<<<<Sending congestion info...'+str(len(ddd)))'''
  for connection in core.openflow._connections.values():
    # connection.send(of.ofp_stats_request(body=of.ofp_flow_stats_request()))
    connection.send(of.ofp_stats_request(body=of.ofp_port_stats_request()))
  # log.debug("Sent %i port stats request(s)", len(core.openflow._connections))
  
# handler to display flow statistics received in JSON format
# structure of event.stats is defined by ofp_flow_stats()
def _handle_flowstats_received (event):
  return

  log.info( "--------Congestion in device ") 
  device = dpidToStr(event.connection.dpid)
  
  stats = flow_stats_to_list(event.stats)
  conn = event.connection

  if (device in congestedDict)==False:
    log.debug( "Congestion in device %s already has been taken care of!", device ) 
    return
  
  flowUsageRatio = {}
  totalKilo = 0.0

  log.info( "+++++++++++Congestion in device ")
  return

  for f in event.stats:
    for ac in f.actions:
      if ac.port in congestedDict[device].ports:
        # 0x0800 shows IP packet type
        if f.match.dl_type == 0x0800:
          # log.debug( "Flow %s %s is a potential responsible of the congestion!", f.match.nw_src, f.match.tp_src )
          log.debug("registered flows: " + str(core.regFlows.getFlows()))
          # search over registered flows that want their rate to be regulated
          for reg in core.regFlows.getFlows():
            log.debug( "%s %s", reg[0], reg[1] )
            # log.debug('%% number of bytes this flow send: ' + ' ' + str(f.actions[0].port))
            if str(reg[0])==str(f.match.nw_src) and str(reg[1]) == str(f.match.tp_src):
              valKilo = f.byte_count/1000.0
              totalKilo += valKilo
              flowUsageRatio[str(f.match.nw_src)+str(f.match.tp_src)] = (f.match.nw_src, f.match.tp_src, valKilo, f.actions[0].port)
            else:
              log.debug("these two are not equal: " + str(reg[0]) + str(f.match.nw_src) + str(reg[1]) + str(f.match.tp_src))
        else:
          log.debug( "Flow of type %s is responsible", f.match.dl_type )
  log.info( ")))))))))))))))))))Congestion in device ")
  for n in flowUsageRatio:
    ratio = flowUsageRatio[n][2]/totalKilo
    ratio = ratio/100.0
    overUse = 0
    # over use over port 
    if flowUsageRatio[n][3] in congestedDict[device].ports:
      overUse = congestedDict[device].ports[flowUsageRatio[n][3]]
      log.info( 'found flow for port : ' + str(flowUsageRatio[n][3]) + ' with over use: ' + str(overUse) )
    # if flow floods here pick up a port randomly
    if flowUsageRatio[n][3] == of.OFPP_FLOOD:
      for p in congestedDict[device].ports:
        overUse = congestedDict[device].ports[p]
        break
      log.info( 'found flow for flood port : ' + str(of.OFPP_FLOOD) + ' with over use: ' + str(overUse) )
    # add flow for later treatment
    if overUse != 0:
      log.info( 'sending request for: ' +  str(overUse*ratio) )
      core.flowDicto.addFlow( n, (flowUsageRatio[n][0], flowUsageRatio[n][1], overUse*ratio) )

  del congestedDict[device]
  log.info( "((((((()))))))Congestion in device ")
  return
  #log.info("FlowStatsReceived from %s: %s",
  #  dpidToStr(event.connection.dpid), stats)

  #for fl in event.stats:
  #  if fl.packet_count > 0:
  #    log.info("\nflow during: %s sec, with byte: %s", 
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
  #log.info("Web traffic from %s: %s bytes (%s packets) over %s flows",
  #  dpidToStr(event.connection.dpid), web_bytes, web_packet, web_flows)

# handler to display port statistics received in JSON format
def _handle_portstats_received (event):
  return
  
  stats = flow_stats_to_list(event.stats)
  device = dpidToStr(event.connection.dpid)
  conn = event.connection
  
  if (device in statsDict) == False:
    statsDict[device] = DeviceStat( {} )
   
  congestion = False

  for pStat in stats:
    portNo = pStat['port_no']
    if (portNo in statsDict[device].ports) == False:
      statsDict[device].ports[portNo] = PortStat(pStat['rx_bytes'], pStat['tx_bytes'])
    else:
      perRx = statsDict[device].ports[portNo].periodRx(pStat['rx_bytes'])
      perTx = statsDict[device].ports[portNo].periodTx(pStat['tx_bytes'])
      if perRx != 0 or perTx != 0:
        log.debug( "period rx: %s and tx: %s", perRx, perTx )
      if perTx > 1000000:
        log.info( "congestion in device %s with tx: %s", device, perTx )
        log.debug( "congestion over switch %s and port %s detected!", device, portNo )
        congestion = True
        log.info('there is usage over 90000 ' + str(perTx-90000) + ' over port: ' + str(portNo) )
        if (device in congestedDict)==False:
          congestedDict[device] = DeviceStat({portNo:perTx-90000})
        else:
          congestedDict[device].addPort(portNo, perTx-90000)
      else:
        log.debug( "every thing is goooood on switch %s and port %s!", dpidToStr(conn.dpid), portNo )  

  # log.info('congcongcongocngocngoncogncongocngocnognc')
  if congestion == True:
    conn.send(of.ofp_stats_request(body=of.ofp_flow_stats_request()))

class RegFlows( object ):
  def __init__( self, fls ):
    self.fls  = fls

  def addFlow(self, f):
    self.fls += [f]

  def getFlows(self):
    return self.fls

def launch(topo = None, routing = None, mode = None):
  
  regFlows = RegFlows([])
  core.register( 'regFlows', regFlows )
  flowDicto = FlowDicto({})
  core.register( 'flowDicto', flowDicto )
  
  # core.registeredFlows = []

  from pox.lib.recoco import Timer
  
  # attach handsers to listners
  core.openflow.addListenerByName("FlowStatsReceived", _handle_flowstats_received)
  core.openflow.addListenerByName("PortStatsReceived", _handle_portstats_received) 

  # timer set
  Timer(15, _timer_func, recurring=True)