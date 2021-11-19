'''
Please add your name:
Please add your matric number: 
'''

import sys
import os
import datetime
from sets import Set

from pox.core import core

import pox.openflow.libopenflow_01 as of
import pox.openflow.discovery
import pox.openflow.spanning_forest

from pox.lib.revent import *
from pox.lib.util import dpid_to_str
from pox.lib.addresses import IPAddr, EthAddr

log = core.getLogger()



''' CONSTANTS '''
# in seconds
TTL = 10
input_file_name = "topology.in"
Q_NORMAL = 0
Q_PREMIUM = 1

P_NORMAL = 100
P_FIREWALL = 200



class Controller(EventMixin):
    def __init__(self):
        self.listenTo(core.openflow)
        core.openflow_discovery.addListeners(self)

        ''' added by me '''
        self.mac_port_dic = {}
        self.mac_port_ttl_dic = {}


        
    # You can write other functions as you need.
        
    def _handle_PacketIn (self, event):    
    	# install entries to the route table


        ''' SETUP '''
        # to allow further parsing
        packet = event.parsed

        # test what is parsed
        # print(packet)

        # throw error if parsing failed
        # if not packet.type:
        #     log.warning("parse of event failed")
        #     raise Exception("parse event failure")

        # id of switch
        dpid = event.dpid

        # port 
        port_entry = event.port
        
        # mac addresses
        src_mac = packet.src
        dst_mac = packet.dst

        # test
        log.debug("Switch %s got %s from port %s" % (dpid, packet, port_entry))

        
        ''' LOGIC '''

        # # check switch in dic
        # if dpid not in self.mac_port_dic:
        #     self.mac_port_dic[dpid] = {}

        # # check switch in ttl dic
        # if dpid not in self.mac_port_dic:
        #     self.mac_port_ttl_dic[dpid] = {}

        # # check mac in switch dic
        # self.mac_port_dic[dpid][src_mac] = port_entry

        # # check mac in switch dic
        # self.mac_port_ttl_dic[dpid][src_mac] = datetime.datetime.now()

        def update_info():

            # check switch in dic
            if dpid not in self.mac_port_dic:
                self.mac_port_dic[dpid] = {} # update mac-port 
                self.mac_port_ttl_dic[dpid] = {} # update ttl

            # check if mac exists
            # overwrite previous info and timings, regardless of expiry
            if src_mac not in self.mac_port_dic[dpid]:
                self.mac_port_dic[dpid][src_mac] = port_entry # update mac-port
                self.mac_port_ttl_dic[dpid][src_mac] = datetime.datetime.now() # update ttl
            
        def remove_expired_ttl():
            if dst_mac in self.mac_port_ttl_dic[dpid]:
                time_now = datetime.datetime.now()
                time_to_compare =  self.mac_port_ttl_dic[dpid][dst_mac]
                ttl_time_format = datetime.timedelta(seconds=TTL)

                time_diff = time_now - time_to_compare

                if time_diff > ttl_time_format:
                    log.info("TTL expired, entry removed %s from switch %s" % (dst_mac, dpid))

                    # remove from mac-port
                    self.mac_port_dic[dpid].pop(dst_mac)

                    # remove from ttl
                    self.mac_port_ttl_dic[dpid].pop(dst_mac)

            # dest mac not in dict, do nth
            else:
                return


        def install_enqueue(event, packet, outport, q_id):
            # log.debug("** Switch %i: Installing flow %s.%i -> %s.%i", dpid, src_mac, inport, dst_mac, outport)
            msg = of.ofp_flow_mod()

            msg.idle_timeout = TTL 
            msg.hard_timeout = TTL
            msg.priority = P_NORMAL

            msg.match = of.ofp_match.from_packet(packet, port_entry)
            msg.actions.append(of.ofp_action_enqueue(port = outport, queue_id = q_id))
            msg.data = event.ofp
            event.connection.send(msg)
            # log.debug("** Switch %i: Rule sent: Outport %i, Queue %i\n", dpid, outport, q_id)

    	# Check the packet and decide how to route the packet
        def forward(message = None):

            # update info before processing pkt
            update_info()

            # multicast
            if dst_mac.is_multicast:
                flood("Multicast >> Switch %s" % (dpid))
                return

            # not saved, flood
            elif dst_mac not in self.mac_port_dic[dpid]:
                flood("Unknown, flooding >> Switch  %s on mac %s" % (dpid, dst_mac))
                return

            # saved, can access saved info
            else:
                # flood_curr_info(event, packet)  

                # install enqueue to do here >>
                outport = self.mac_port_dic[dpid][dst_mac]
                q_id = Q_NORMAL

                install_enqueue(event, packet, outport, q_id)

            # remove expired before returning

        # flood based on current info
        def flood_curr_info(event, packet):

            curr_port = self.mac_port_dic[dpid][dst_mac]
            log.debug("Known, flooding >> Switch  %s on mac %s on port %s" % (dpid, dst_mac, curr_port))
            
            # define your message here
            msg = of.ofp_packet_out()
            # flood msg
            msg.actions.append(of.ofp_action_output(port = curr_port))
            msg.match = of.ofp_match.from_packet(packet, port_entry)

            msg.data = event.ofp
            msg.in_port = event.port
            event.connection.send(msg)



        # When it knows nothing about the destination, flood but don't install the rule
        def flood (message = None):
            log.info("Packet flooding: ")

            # define your message here
            msg = of.ofp_packet_out()
            # flood msg
            msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))

            msg.data = event.ofp
            msg.in_port = event.port
            event.connection.send(msg)

            return
            
            # ofp_action_output: forwarding packets out of a physical or virtual port
            # OFPP_FLOOD: output all openflow ports expect the input port and those with 
            #    flooding disabled via the OFPPC_NO_FLOOD port config bit
            # msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
        
        forward()
        remove_expired_ttl()


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
