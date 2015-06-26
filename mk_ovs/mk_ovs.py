import subprocess
import sys

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
    cmd = "sudo ~/pox/pox.py forwarding.l2_learning &"
    subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    fw = open("ctrl_ip", "w")
    fw.write(eth_ip)
    fw.close()
    continue
  if eth_ip[3] == '1' and s_mode != "-s":
    fr = open("ctrl_ip", "r")
    while True:
      ctrl_ip = fr.read()
      if ctrl_ip != "":
        break
      fr.seek(0,0)
    # end of while
    cmd = "sudo sh ~/transiver/mk_ovs/mk_ovs.sh %s %s %s" %(eth_num,eth_ip,ctrl_ip)
    print cmd
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
  if eth_ip[3] == '1' and s_mode == "-s":
    cmd = "sudo ifconfig eth%s %s netmask 255.255.255.0" %(eth_num, s_ip)
    subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)


