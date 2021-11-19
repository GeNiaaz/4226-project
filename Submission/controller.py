'''
Please add your name: Muhammad Niaaz Wahab
Please add your matric number: A0200161E
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
policy_file_name = "policy.in"

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
        self.premium_hosts = []


        
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

        # ip
        src_ip = None
        dst_ip = None


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

        def get_q_id(src_ip, dst_ip):

            log.info("ip saved is %s", src_ip)
            

            q_id = Q_NORMAL
            if src_ip in self.premium_hosts or dst_ip in self.premium_hosts:
                q_id = Q_PREMIUM

            log.info("service is %s" % (q_id))

            return q_id

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

                if packet.type == packet.IP_TYPE:
                    src_ip = packet.payload.srcip
                    dst_ip = packet.payload.dstip
                elif packet.type == packet.ARP_TYPE:
                    src_ip = packet.payload.protosrc
                    dst_ip = packet.payload.protodst

                # q_id = get_q_id()

                # q_id = Q_NORMAL
                # if src_ip in self.premium_hosts or dst_ip in self.premium_hosts:
                #     q_id = Q_PREMIUM

                q_id = get_q_id(src_ip, dst_ip)

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

        # set_ip()
        forward()
        remove_expired_ttl()


    def _handle_ConnectionUp(self, event):
        # dpid = dpid_to_str(event.dpid)
        # log.debug("Switch %s has come up.", dpid)
        
        # Send the firewall policies to the switch
        def sendFirewallPolicy(connection, policy):
            # define your message here
            src_ip = policy[0]
            dst_ip = policy[1]
            dst_port = policy[2]

            msg = of.ofp_flow_mod()

            msg.priority = P_FIREWALL

            # IP header for tcp
            msg.match.nw_proto = 6 

            msg.match.dl_type = 0x800

            # set to ofpp_none, cannot send out
            # msg.actions.append(of.ofp_action_output(port = of.OFPP_NONE))

            # 2/3 policy
            if src_ip == None:

                # src
                # msg.match.nw_src = IPAddr(src_ip)
                msg.match.nw_src = None

                #dst
                msg.match.nw_dst = IPAddr(dst_ip)
                msg.match.tp_dst = int(dst_port)
            
            # 3/3 policy
            else:

                # src
                msg.match.nw_src = IPAddr(src_ip)

                # dst
                msg.match.nw_dst = IPAddr(dst_ip)
                msg.match.tp_dst = int(dst_port)



            connection.send(msg)
            log.debug("Firewall rule added")
            
            
            # OFPP_NONE: outputting to nowhere
            # msg.actions.append(of.ofp_action_output(port = of.OFPP_NONE))

        def parse_policies_file(policy_input_name):
            firewall_policies = []

            with open(policy_input_name) as policies_f:
                quantity = policies_f.readline().split(" ")
                number_of_firewall_policies = int(quantity[0])
                number_of_premium_hosts = int(quantity[1])


                # saving policies
                for policy_index in range(number_of_firewall_policies):
                    policy_input = policies_f.readline().strip().split(',')

                    # only dst_ip, p | 2/3 policy
                    if len(policy_input) == 2:
                        dst_ip = policy_input[0]
                        dst_port = policy_input[1]

                        # saving to policy arr
                        policy = [None, dst_ip, dst_port]
                        firewall_policies.append(policy)
                    
                    # src_ip, dst_ip, p | 3/3 policy
                    elif len(policy_input) == 3:
                        src_ip = policy_input[0]
                        dst_ip = policy_input[1]
                        dst_port = policy_input[2]   

                        # saving to policy arr
                        policy = [src_ip, dst_ip, dst_port]
                        firewall_policies.append(policy)

                    # SHOULD NOT REACH HERE
                    else:
                        log.debug("policy length wrong")
                        return -1
                

                # saving hosts
                for host_index in range(number_of_premium_hosts):
                    host_input = policies_f.readline().strip()
                    self.premium_hosts.append(host_input)

            return firewall_policies


        # ... 
        dpid = dpid_to_str(event.dpid)
        log.debug("Switch %s has come up.", dpid)

        FIREWALL_POLICIES = parse_policies_file(policy_file_name)
        for policy in FIREWALL_POLICIES:
            sendFirewallPolicy(event.connection, policy)
            
''' DONT TOUCH THIS THING!! '''
def launch():
    # Run discovery and spanning tree modules
    pox.openflow.discovery.launch()
    pox.openflow.spanning_forest.launch()

    # Starting the controller module
    core.registerNew(Controller)
