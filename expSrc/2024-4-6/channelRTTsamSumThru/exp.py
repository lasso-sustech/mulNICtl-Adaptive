from tap import Connector
from util.trans_graph import LINK_NAME_TO_TX_NAME
import util.ctl as ctl
from tools.read_graph import construct_graph
from util.solver import channelBalanceSolver
from util import stream
from typing import List
import time, random
import os
def create_logger_file(filename:str):
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    f = open(filename, 'w')
    f.write('[')
    return f

f = create_logger_file('logs/2024-4-6/exp:compare-average-rtt.json')

for thru in range(1, 30, 3):
    arrivalGap = 16 #ms
    # thru = 5 # Mbps
    inter_names = [f"dtMbps_{thru}.npy", f"rttMbps_{30 - thru}.npy"]
    task_num = 2
    
    topo = construct_graph("./config/topo/graph_4.txt") # Graph
    links = topo.get_links()
    ip_table = ctl._ip_extract_all(topo)
    ctl._ip_associate(topo, ip_table)
    
    for inter_name in inter_names:
        conn = Connector()
        sender = LINK_NAME_TO_TX_NAME(links[0])
        conn.batch(sender, "create_file", {"thru": thru, "arrivalGap": arrivalGap, "name": inter_name, "num": 20000}).wait(0.5).apply()
    
    for idx in range(task_num):
        temp = stream.stream().read_from_manifest('./config/stream/proj.json')
        temp.npy_file = inter_names[idx]
        temp.calc_rtt = True
        temp.tx_ipaddrs = ['192.168.3.57', '192.168.3.59']; temp.tx_parts = [1, 1]; temp.port = 6203 + idx
        topo.ADD_STREAM(links[0], temp, target_rtt=16)
    
    ctl.create_tx_manifest(topo)
    conn = ctl.start_transmission(graph=topo, DURATION = 30)
    res = ctl.read_thu(conn)
    rtts = ctl.read_rtt(topo)
    print(res)
    for rtt in rtts:
        print(rtt)
        f.write(rtt.__str__())
        f.write(',\n')
    f.flush()
    
f.write(']')

