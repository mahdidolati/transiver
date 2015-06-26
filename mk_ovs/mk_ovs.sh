addPort() {
  ifconfig eth$1 0
  ovs-vsctl -- --may-exist add-port br0 eth$1
}

ovs-vsctl -- --may-exist add-br br0
addPort $1

ovs-vsctl set-controller br0 tcp:155.98.39.40:6633
ovs-vsctl set-fail-mode br0 secure

# ifconfig br0 $2 netmask 255.255.255.0
