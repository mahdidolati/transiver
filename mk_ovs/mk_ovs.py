import subprocess
import sys

s_mode = False
if "-s" == sys.argv[1]:
  s_mode = True
  s_ip = sys.argv[2]

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
  if int(eth_num) == 0:
    continue
  eth_ip = intf.split("inet addr:")[1].split("  Bcast")[0]
  print eth_ip
  if eth_ip[3] == '1' and s_mode == False:
    cmd = "sudo sh ~/transiver/mk_ovs/mk_ovs.sh %s %s" %(eth_num,eth_ip)
    print cmd
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
  if eth_ip[3] == '1' and s_mode == True:
    cmd = "sudo ifconfig eth%s %s netmask 255.255.255.0" %(eth_num, s_ip)
    subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)


