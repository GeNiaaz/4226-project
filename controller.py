'''
Please add your name:
Please add your matric number: 
'''

import sys
import os
from sets import Set

from pox.core import core

import pox.openflow.libopenflow_01 as of
import pox.openflow.discovery
import pox.openflow.spanning_forest

from pox.lib.revent import *
from pox.lib.util import dpid_to_str
from pox.lib.addresses import IPAddr, EthAddr

log = core.getLogger()


input_file_name = "topology.in"


class Controller(EventMixin):
    def __init__(self):
        self.listenTo(core.openflow)
        core.openflow_discovery.addListeners(self)

        ''' added by me '''
        self.mac_port_dic = {}


        
    # You can write other functions as you need.
        
    def _handle_PacketIn (self, event):    
    	# install entries to the route table


        ''' SETUP '''
        # to allow further parsing
        packet = event.parsed

        # test what is parsed
        # print(packet)

        # throw error if parsing failed
        if not packet.type:
            log.warning("parse of event failed")
            raise Exception("parse event failure")

        # id of switch
        dpid = packet.dpid
        
        # mac addresses
        src_mac = packet.src
        dst_mac = packet.dst

        # port 
        port_entry = event.port

        # test
        log.debug("Switch " + dpid + " got " + packet + " from port " + port_entry)

        
        ''' LOGIC '''

        # check switch in dic
        if dpid not in self.mac_port_dic:
            self.mac_port_dic[dpid] = {}

        # check mac in switch dic
        self.mac_port_dic[dpid][src_mac] = port_entry
        





        def install_enqueue(event, packet, outport, q_id):

            # placeholder
            pass

    	# Check the packet and decide how to route the packet
        def forward(message = None):

            # multicast
            if dst_mac.is_multicast:
                flood("Multicast >> Switch " + dpid)
                return

            # not saved, flood
            elif dst_mac not in self.mac_port_dic[dpid]:
                flood("Unknown, flooding >> Switch " + dpid + " on port " + dst_mac)
                return

            # saved, can access saved info
            else:
                print("Saved >> Switch " + dpid + " on port " + dst_mac)

                # install enqueue to do here >>
                # install_enqueue(event, packet, outport, q_id)


        # When it knows nothing about the destination, flood but don't install the rule
        def flood (message = None):
            log.info("Packet flooding: ")

            # init msg
            msg = of.ofp_packet_out()
            # flood msg
            msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))

            msg.data = event.ofp
            msg.in_port = event.port
            event.connection.send(msg)

            
            # define your message here

            # ofp_action_output: forwarding packets out of a physical or virtual port
            # OFPP_FLOOD: output all openflow ports expect the input port and those with 
            #    flooding disabled via the OFPPC_NO_FLOOD port config bit
            # msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
        
        forward()


    def _handle_ConnectionUp(self, event):
        dpid = dpid_to_str(event.dpid)
        log.debug("Switch %s has come up.", dpid)
        
        # Send the firewall policies to the switch
        def sendFirewallPolicy(connection, policy):
            # define your message here
            pass
            
            # OFPP_NONE: outputting to nowhere
            # msg.actions.append(of.ofp_action_output(port = of.OFPP_NONE))

        # for i in [FIREWALL POLICIES]:
        #     sendFirewallPolicy(event.connection, i)
            
''' DONT TOUCH THIS THING!! '''
def launch():
    # Run discovery and spanning tree modules
    pox.openflow.discovery.launch()
    pox.openflow.spanning_forest.launch()

    # Starting the controller module
    core.registerNew(Controller)
