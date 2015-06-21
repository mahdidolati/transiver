import subprocess

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
  if eth_ip[3] == '0':
    cmd = "sh ~/transiver/mk_ovs/mk_ovs.sh %s %s" %(eth_num,eth_ip)
    print cmd
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)

