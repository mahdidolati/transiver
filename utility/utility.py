import subprocess

def get_eth_ip():
  cmd = "ifconfig"
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
  (output, err) = p.communicate()
  output.replace("Ethernet", " ")
  eth_list = output.split("eth")
  #endIf,while,if
  eth_ip_list = []
  for intf in eth_list:
    if len(intf) == 0:
      continue
    eth_num = intf[0]
    if eth_num == "0":
      continue
    eth_ip = intf.split("inet addr:")[1].split("  Bcast")[0]
    eth_ip_list.append((eth_num,eth_ip))
  return eth_ip_list

def get_ip_bw(my_ip, file_addr="/users/mdolati/transiver/tr_mx"):
  fr = open(file_addr,"r")
  ip_base = 3
  my_ip -= ip_base
  if my_ip < 0:
    return
  l = []
  for i in range(my_ip+1):
    line = fr.readline()
  counter = 0
  for v in line.split(" "):
    try:
      if counter != my_ip:
        l.append(float(v))
      counter += 1
    except ValueError:
      print "no float"
  return l

def get_other_ips(my_ip, all=8, base_ip=3, base_net="66"):
  l = []
  my_ip -= base_ip
  for i in range(all):
    if my_ip != i:
      l.append("10.1.%s.%s" %(base_net,i+base_ip))
  return l

print get_ip_bw(4)
print get_other_ips(5)
