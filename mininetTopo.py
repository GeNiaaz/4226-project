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

FIRST = 0
SECOND = 1

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
        self.links_input = []

    
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

                self.addSwitch('s%d' % (switch_index + 1))

            # initialise links
            for link_index in range(amt_links):
                link_input = f.readline().strip().split(',')
                self.links_input.append(link_input)
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
            for link in self.links_input:
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
                  controller=lambda name: RemoteController(name, ip='127.0.0.1'),
                  listenPort=6633, autoSetMacs=True)

    info('** Starting the network\n')
    net.start()
    

    def getBandwidth(switch, otherNode):
        for link in net.topo.links_input:
            if ((link[0] == switch and link[1] == otherNode) or (link[0] == otherNode and link[1] == switch)):
                return int(link[2]) * 1000000

    def get_node(interface, num):
        if num == FIRST:
            return interface.link.intf1.node
        elif num == SECOND:
            return interface.link.intf2.node
        else:
            return -1

    # initialise queues
    for switch in net.switches:
        for intf in switch.intfList():
            if intf.link:

                # variables
                firstNode = get_node(intf, FIRST)
                secondNode = get_node(intf, SECOND)
                bw = -1

                if firstNode == switch:
                    port_name = intf.link.intf1.name
                    bw = getBandwidth(switch.name, secondNode.name)
                else:
                    port_name = intf.link.intf2.name
                    bw = getBandwidth(switch.name, firstNode.name)

                NORMAL_MAX = 0.5 * bw
                PREMIUM_MIN = 0.8 * bw

                info('** Running \n')

                os.system('sudo ovs-vsctl -- set Port %s qos=@newqos \
                -- --id=@newqos create QoS type=linux-htb other-config:max-rate=%d queues=0=@q0,1=@q1 \
                -- --id=@q0 create queue other-config:max-rate=%d \
                -- --id=@q1 create queue other-config:min-rate=%d' % (port_name, bw, NORMAL_MAX, PREMIUM_MIN))

    CLI(net)

    ''' LOGIC HERE '''

    
    info('** Running \n')
    # CLI(net)

    # Create QoS Queues
    # os.system('sudo ovs-vsctl -- set Port [INTERFACE] qos=@newqos \
    #         -- --id=@newqos create QoS type=linux-htb other-config:max-rate=[LINK SPEED] queues=0=@q0,1=@q1,2=@q2 \
    #         -- --id=@q0 create queue other-config:max-rate=[LINK SPEED] other-config:min-rate=[LINK SPEED] \
    #         -- --id=@q1 create queue other-config:min-rate=[X] \
    #         -- --id=@q2 create queue other-config:max-rate=[Y]')



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
