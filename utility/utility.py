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
  yadi_ips = ['6','7','9','10','13','14','15','17']
  counter = 0
  for a in yadi_ips:
    if str(my_ip) == a:
      break
    counter += 1
  fr = open(file_addr,"r")
  ip_base = 3
  my_ip = counter
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
  yadi_ips = ['6','7','9','10','13','14','15','17']
  ret_l = []
  for a in yadi_ips:
    if a != str(my_ip):
      ret_l.append("10.1.66.%s" %a)
  return ret_l
  '''l = []
  my_ip -= base_ip
  for i in range(all):
    if my_ip != i:
      l.append("10.1.%s.%s" %(base_net,i+base_ip))
  return l'''

def kill_port_listener(port):
  cmd = "sudo netstat -lnp | grep %s" %port
  cond = True
  while cond:
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    if len(output) > 4:
      l1 = output.split("/")
      if len(l1) > 0:
        l2 = l1[0].split(" ")
        pid = l2[len(l2)-1]
        cmd = "sudo kill -9 %s" %pid
        print ("in utility", cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    else:
      cond = False

print get_ip_bw(13)
print get_other_ips(14)
# kill_port_listener(8080)
