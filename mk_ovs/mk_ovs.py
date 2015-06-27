import subprocess
import sys
import logging
import threading
#
PATH_TO_FILE = "/users/mdolati/transiver/mk_ovs/"
LOG_FILE = "log.log"
CTRL_IP_FILE = "ctrl_ip"
LOG_PATH = PATH_TO_FILE + LOG_FILE
CTRL_IP_PATH = PATH_TO_FILE + CTRL_IP_FILE
#
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler(LOG_PATH)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
#
class runPox(threading.Thread):
  def run(self):
    cmd = "sudo netstat -lnp | grep 6633"
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    logger.info("is another ctrl running %s" %output)
    if len(output) > 4:
      l1 = output.split("/")
      if len(l1) > 0:
        l2 = l1[0].split(" ")
        pid = l2[len(l2)-1]
        cmd = "sudo kill -9 %s" %pid
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        logger.info("killed %s" %pid)
      #endIf,if
    cmd = "sudo sh ~/transiver/mk_ovs/run_pox.sh &"
    p = subprocess.Popen(cmd, shell=True)
    logger.info('ran pox')   
# w for switch, s for server and c for controller
s_mode = sys.argv[1]
if "-s" == s_mode:
  s_ip = sys.argv[2]
#
logger.info("starting mk_ovs for a %s" %s_mode)
#
cmd = "ifconfig"
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
(output, err) = p.communicate()
output.replace("Ethernet", " ")
eth_list = output.split("eth")
# obtain ctrl ip
if s_mode == "-w":
 fr = open(CTRL_IP_PATH, "r")
 while True:
   ctrl_ip = fr.read()
   if len(ctrl_ip) < 5:
     fr.close()
     fr = open("ctrl_ip", "r")
     continue
   else:
     ctrl_net = ctrl_ip.split(".")[2]
     logger.info("ctrl ip is %s beg" %ctrl_ip)
     break
#endIf,while,if
#
isPoxRunning = False
for intf in eth_list:
  if len(intf) == 0:
    continue
  eth_num = intf[0]
  if eth_num == "0":
    continue
  eth_ip = intf.split("inet addr:")[1].split("  Bcast")[0]
  logger.info("observing eth%s with ip %s" %(eth_num, eth_ip))
  if s_mode == "-c":
    logger.info('in controller')         
    fw = open(CTRL_IP_PATH, "w")
    fw.write(eth_ip)
    fw.close()
    logger.info('ctrl ip is %s\nend of controller' %eth_ip)
    if isPoxRunning == False:
      isPoxRunning = True
      runPoxInst = runPox()
      runPoxInst.start()
    #endIf
  #endIF
  if s_mode == "-w":
    logger.info('in switch')
    eth_net = eth_ip.split(".")[2]
    if eth_net == ctrl_net:
      logger.info("same net as ctrl %s with eth%s" %(eth_net,eth_num))
      continue
    logger.info('remote ip is %s' %ctrl_ip)
    cmd = "sudo sh ~/transiver/mk_ovs/mk_ovs.sh %s %s %s" %(eth_num,eth_ip,ctrl_ip)
    logger.info(cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    logger.info('end of switch')
  if s_mode == "-s":
    cmd = "sudo ifconfig eth%s %s netmask 255.255.255.0" %(eth_num, s_ip)
    subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)


