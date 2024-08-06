from tap import Connector
from util.trans_graph import LINK_NAME_TO_TX_NAME
import util.ctl as ctl
import util.qos as qos
from tools.read_graph import construct_graph
from util.solver import channelBalanceSolver, channelSwitchSolver, singleDirFlowTransSolver, gb_state
from util.logger import QosLogger
from util import stream
from typing import List
import os, json

import util.constHead as constHead

parseSingleIpDevice = lambda x: [x, x]

def create_transmission(trans_manifests, arrivalGap = 16):
    streams = []
    for name in trans_manifests:
        trans_manifest = trans_manifests[name]
        if trans_manifest is None:
            continue
        conn            = Connector()
        sender          = LINK_NAME_TO_TX_NAME(trans_manifest['link'])
        file_name       = f'{name}.npy'
        print(f"Creating transmission file {file_name} with {trans_manifest['thru']} at {sender}")
        conn.batch(sender, "create_file", {"thru": trans_manifest['thru'], "arrivalGap": arrivalGap, "name": f'{name}.npy', "num": 20000}).wait(0.5).apply()
        
        temp        = stream.stream()
        file_type   = trans_manifest['file_type']
        if file_type == 'file':
            temp            = temp.read_from_manifest('./config/stream/file.json')
            temp.tos        = 128
        else:
            temp            = temp.read_from_manifest('./config/stream/proj.json')
            temp.calc_rtt   = True
        
            
        temp.npy_file   = file_name
        temp.tx_ipaddrs = trans_manifest['ip_addrs']
        temp.name       = trans_manifest['name']
        temp.tx_parts   = trans_manifest['tx_parts']
        temp.port       = trans_manifest['port']
        
        topo.ADD_STREAM(trans_manifest['link'], temp)
        
        streams.append(temp)
    return streams

def get_stream_by_name(streams, name):
    for stream in streams:
        if stream.name == name:
            return stream
    raise ValueError(f"Stream {name} not found")

def get_qos_by_name(qoses, name):
    for qos in qoses:
        if qos['name'] == name:
            return qos
    raise ValueError(f"Qos {name} not found")
    
logger      = QosLogger('expSrc/2024-5-7/experiment2/exp-result.json')
topo        = construct_graph("./config/topo/2024-5-5.txt") # Graph
ip_table    = ctl._ip_extract_all(topo)
ctl._ip_associate(topo, ip_table)

links       = topo.get_links()

arrivalGap  = 16    #ms
fthru       = 600   #Mbps
pthru       = 50    #Mbps
ithru       = 100   #Mbps

target_name = 'proj1'
trans_manifests = {
    'proj1': {
        'thru'      : pthru,
        'file_type' : 'proj',
        
        'link'      : links[1],
        'port'      : 6204,
        'ip_addrs'  : [ topo.link_to_tx_ip(links[1]), topo.link_to_tx_ip(links[0]) ],
        'tx_parts'  : [ 0, 0 ],
        'name'      : target_name,
    },
    'interference': {
        'thru'      : ithru,
        'file_type' : 'file',
        
        'link'      : links[2],
        'port'      : 6205,
        'ip_addrs'  : parseSingleIpDevice(topo.link_to_tx_ip(links[2])),
        'tx_parts'  : [ 0, 0 ],
        'name'      : 'interference',
    },
}

for key, manifest in trans_manifests.items():
    constHead.traffic_config_schema.validate(manifest)

streams = create_transmission(trans_manifests, arrivalGap)
topo.show()

lighter                 = gb_state()
channel_balance_solver  = channelBalanceSolver()
channel_balance_solver.update_tx_parts(get_stream_by_name(streams, target_name).tx_parts)


for test in range(0, 5):
    
    ctl.create_tx_manifest(topo)
    
    conn    = ctl.start_transmission(graph=topo, DURATION = 15)
    thrus   = ctl.read_thu( conn )
    rtts    = ctl.read_rtt( topo )    
    qoses   = qos.get_qoss( topo, thrus, rtts )
    
    # channel_balance_solver.update( get_qos_by_name(qoses, target_name) )
    
    logger.log_write(qoses)
    
    # channel_balance_solver.solve_by_rtt_balance()
    # channel_balance_solver.apply(get_stream_by_name(streams, target_name))
    
    # print(channel_balance_solver.channel_rtts)
    # print(channel_balance_solver.tx_parts)
    
logger.log_close()

    # channel_lights  = lighter.update_gb_state(qoses)
    # actions         = lighter.policy()
    # controls        = singleDirFlowTransSolver(actions[constHead.FLOW_DIR]).solve(qoses)
    # print(controls)
    