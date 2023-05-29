## Controller

This part explains the architecture and detailed implementations of  Controller.py.   
Source code: https://github.com/sustechwifi/cs305proj/blob/ljl/controller.py

### Architecture
In the implementation of SDN using Ryu, the controller listens for the events that switch, host, link, port added or deleted, as well as the packet sent in. According to these events that affect the network composition, the relational map dictionaries, and furthermore the topology graph and the flow tables could be updated. When sending data, switches perform actions according to its flowtable, forwarding to the next switch by forwarding rules. If the switch does not know the mac address of the destination host, it will send an ARP request to the controller, and the controller will reply the mac address. The forwarding rule is set by the shortest path.

### Implementation
#### Attributes:
- **switchNum:** the number of switches
- **s_s:** a two-dimensional matrix of switches, recording links of switch id and their distance
- **mac_mac:** a two-dimensional matrix of ports, recording links of port mac
- **numInfo:** record the port mac address of each switch
- **leaveSwitchList:** switches that have left
- **DelPortList:** ports that are closed
- **other dictionaries that maps host ip, host mac, switch id, switch mac, switch port, switch datapath, etc.**
- 
#### Functions:  
- **\_\_init__:**   
  Initialize the arrtibutes. 
- **handle_switch_add:**    
  It is called when a switch is added to the net. Relative tables are updated, including switchNum, s_s, numInfo, and other map dictionaries. The topology graph and the flow table are also updated.
- **handle_switch_delete:**   
  It is called when a switch is shut off. Relative tables are updated, including leaveSwitchList, mac_mac. The topology graph and the flow table are also updated.
- **handle_host_add:**   
  It is called when a host is added to the net. Some map dictionaries are updated. The topology graph and the flow table are also updated.
- **handle_link_add:**   
  It is called when a link is added to the net. The mac_mac is updated, and the topology graph and the flow table are also updated.
- **handle_link_delete:**   
  It is called when a link is deleted. The mac_mac is updated, and the topology graph and the flow table are also updated.
- **handle_port_modify:**   
  It is called when a port is shut off or opened. The DelPortList and s_s is updated. The topology graph and the flow table are also updated.
- **packet_in_handler:**   
  It is called when a packet is received by the controller. The controller will firstly extract informations of the packet, then handle it according to its ptotocol type. If it is a DHCP request, DHCPServer.handle_dhcp will be called; if is is a ARP request, the shortest path will be calculated using get_path function, and the mac address of the destination host will be returned.
- **update:**    
  It is called by other event-triggered functions, and used to update the topology graph and flow tables. To update the topology graph, it firstly initialize the topology graph, in which every node has a distance 0 to itself, and a big enough distance to other nodes. Secondly, it iterates through the mac_mac to get link informations, according which to update s_s. Thirdly, it compute the distance between any two switches using Floyd-Warshall algorithm. That is, in the nested loop, it iterates over all pairs of switches and compares the distances between the paths that pass through the k-th switch and those that do not. If the path through the k-th switch is shorter, it updates the value of self.s_s[i][j] to the new shortest distance. To update the flow tables, it calls set_flowtable function.
- **add_forwarding_rule:**   
  It is called to add a fowarding rule in the flow table. OfCtl is used here to communicate.
- **delete_forwarding_rule:**   
  It is similar to the previous method, but to delete a forwarding rule.
- **print_path:**   
  It is a method to print path, making the implementation intuitive.
- **get_path:**   
  It is used to get the shortest path between two hosts. To achieve this, it uses an iterative approach to find the path from the source switch to the destination switch. In each iteration, it searches for the switches connected to the current temp_Num, which represents the current switch identifier. It selects the next switch and the corresponding output port for the path. During this process, it compares the distances of the shortest paths and chooses the shorter path to update nextNum and outputPort. Then, it appends the output result to the ans_list. If, during the iteration, it finds that testNum (used to detect if it is trapped in an infinite loop) is equal to temp_Num, it means that it is unable to find the next node and complete the path. In such cases, it returns an empty list.
- **set_flowtable:**   
  It sets the forwarding rule for every two switches, by calling delete_forwarding_rule function followed by add_forwarding_rule function iteratively. 
- **get_linkTable:**   
  It returns the information that for each switch, it links to which other switches through which port.
- **get_hostTable:**   
  It returns the information that for each host, it links to which switche through which port.

### TestCase
The result of the basic testcase:

We also created a more complex testcase as the diagram below:

And the the controller successfully passed it as well:
