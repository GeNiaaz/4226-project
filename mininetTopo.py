'''
Please add your name: Muhammad Niaaz Wahab
Please add your matric number: A0200161E
'''

import os
import sys
import atexit
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.topo import Topo
from mininet.link import Link
from mininet.node import RemoteController

net = None
input_file_name = "topology.in"
class TreeTopo(Topo):
			
	def __init__(self):
		# Initialize topology
		Topo.__init__(self)        

                num_hosts = -1
                num_switches = -1
                num_links = -1

                # debugging
                hosts_input = []
                switches_input = []
                links_input = []

            
                with open(input_file_name) as f:

                    # Read first line ti get quantities
                    quantities = f.readline().split(" ")

                    amt_hosts = int(quantities[0])
                    amt_switches = int(quantities[1])
                    amt_links = int(quantities[2])

                    # initialise hosts
                    for host_index in range(amt_hosts):
                        hosts_input.append('h%d' % (host_index + 1))

                        self.addHost('h%d' % (host_index + 1))

                    # initialise switches
                    for switch_index in range(amt_switches):
                        switches_input.append('s%d' % (switch_index + 1))

                        self.addSwitch('s%d' % [switch_index + 1])

                    # initialise links
                    for link_index in range(amt_links):
                        link_input = f.readline().strip().split(',')
                        dev1 = link_input[0]
                        dev2 = link_input[1]
                        bandwidth = link_input[2]

                        self.addLink(dev1, dev2)


                    ''' printing stuff to check '''

                    # print hosts
                    for host in hosts_input:
                        print("host: ", host)

                    # print switches
                    for switch in switches_input:
                        print("switch: ", switch)

                    # print links
                    print("input links: ")
                    for link in self.links:
                        print(link)

                    # sort | with keys | with info
                    print self.links(True, False, True)
                    



	# Add hosts
    # > self.addHost('h%d' % [HOST NUMBER])

	# Add switches
    # > sconfig = {'dpid': "%016x" % [SWITCH NUMBER]}
    # > self.addSwitch('s%d' % [SWITCH NUMBER], **sconfig)

	# Add links
	# > self.addLink([HOST1], [HOST2])

def startNetwork():
    info('** Creating the tree network\n')
    topo = TreeTopo()

    global net
    net = Mininet(topo=topo, link = Link,
                  controller=lambda name: RemoteController(name, ip='SERVER IP'),
                  listenPort=6633, autoSetMacs=True)

    info('** Starting the network\n')
    net.start()

    ''' LOGIC HERE '''

    

    info('** Running \n')
    CLI(net)

    # Create QoS Queues
    os.system('sudo ovs-vsctl -- set Port [INTERFACE] qos=@newqos \
            -- --id=@newqos create QoS type=linux-htb other-config:max-rate=[LINK SPEED] queues=0=@q0,1=@q1,2=@q2 \
            -- --id=@q0 create queue other-config:max-rate=[LINK SPEED] other-config:min-rate=[LINK SPEED] \
            -- --id=@q1 create queue other-config:min-rate=[X] \
            -- --id=@q2 create queue other-config:max-rate=[Y]')

    info('** Running CLI\n')
    CLI(net)

def stopNetwork():
    if net is not None:
        net.stop()
        # Remove QoS and Queues
        os.system('sudo ovs-vsctl --all destroy Qos')
        os.system('sudo ovs-vsctl --all destroy Queue')


if __name__ == '__main__':
    # Force cleanup on exit by registering a cleanup function
    atexit.register(stopNetwork)

    # Tell mininet to print useful information
    setLogLevel('info')
    startNetwork()
