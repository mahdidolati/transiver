import subprocess
import sys
import logging
import threading
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler('log.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class runPox(threading.Thread):
  def run(self):
    cmd = "sudo sh run_pox.sh &"
    p = subprocess.Popen(cmd, shell=True)
    logger.info('ran pox')
    
# w for switch, s for server and c for controller
s_mode = "-w"
if "-s" == sys.argv[1]:
  s_mode = sys.argv[1]
  s_ip = sys.argv[2]
elif "-c" == sys.argv[1]:
  s_mode = sys.argv[1]
  # currently is hardcoded, but make it dynamic
  #c_ip = sys.argv[2]

cmd = "ifconfig"
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
(output, err) = p.communicate()
output.replace("Ethernet", " ")
eth_list = output.split("eth")
for intf in eth_list:
  if len(intf) == 0:
    continue
  eth_num = intf[0]
  print eth_num
  eth_ip = intf.split("inet addr:")[1].split("  Bcast")[0]
  print eth_ip
  if int(eth_num) == 0 and s_mode == "-c":
    logger.info('in controller')
    # cmd = "sudo ~/pox/pox.py forwarding.l2_learning &"
    # p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    # logger.info('ran pox')
    # (output, err) = p.communicate()
    # logger.info("run pox out %s\nrun pox err %s" %(output,err))
    runPoxInst = runPox()
    runPoxInst.start()
    fw = open("ctrl_ip", "w")
    fw.write(eth_ip)
    fw.close()
    logger.info('ctrl ip is %s\nend of controller' %eth_ip)
    continue
  if eth_ip[3] == '1' and s_mode != "-s":
    logger.info('in switch')
    fr = open("ctrl_ip", "r")
    while True:
      ctrl_ip = fr.read()
      print (str(ctrl_ip[2]), str(len(ctrl_ip)>3))
      if len(ctrl_ip) > 3 and ctrl_ip[2] == '5':
        print ("this is ip:", ctrl_ip)
        break
      else:
        print ("no ip for remote yet...", ctrl_ip)
      # fr.seek(0,0)
      fr.close()
      fr = open("ctrl_ip", "r")
    # end of while
    logger.info('remote ip is %s' %ctrl_ip)
    cmd = "sudo sh ~/transiver/mk_ovs/mk_ovs.sh %s %s %s" %(eth_num,eth_ip,ctrl_ip)
    logger.info(cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    logger.info('end of switch')
  if eth_ip[3] == '1' and s_mode == "-s":
    cmd = "sudo ifconfig eth%s %s netmask 255.255.255.0" %(eth_num, s_ip)
    subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)


