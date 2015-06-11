addPort() {
  ifconfig eth$1 0
  ovs-vsctl -- --may-exist add-port br0 eth$1
}

ovs-vsctl -- --may-exist add-br br0
addPort $1
addPort $2


ovs-vsctl set-controller br0 tcp:127.0.0.1:6633
ovs-vsctl set-fail-mode br0 secure

ifconfig br0 10.1.1.3 netmask 255.255.255.0
