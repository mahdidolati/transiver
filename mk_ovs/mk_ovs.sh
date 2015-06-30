addPort() {
  sudo ifconfig eth$1 0
  echo "8"
  sudo ovs-vsctl -- --may-exist add-port br0 eth$1
  echo "9"
}
echo "1"
sudo ovs-vsctl -- --may-exist add-br br0
echo "2"
addPort $1
echo "3"
sudo ovs-vsctl set-controller br0 tcp:$3:6633
echo "4"
sudo ovs-vsctl set-fail-mode br0 secure
echo "5"
sudo ifconfig br0 $2 netmask 255.255.255.0
echo "6"
# sudo route add -net 10.1.0.0 netmask 255.255.0.0 dev br0
echo "7"
