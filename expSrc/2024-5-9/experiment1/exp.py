
import os
import json
import util.ctl as ctl
import util.qos as qos
import util.constHead as constHead

from tap import Connector
from util import stream
from util.solver import singleDirFlowTransSolver, gb_state
from util.logger import QosLogger

from util.trans_graph import LINK_NAME_TO_TX_NAME
from tools.read_graph import construct_graph

from typing import List




parseSingleIpDevice = lambda x: [x, x]

def create_transmission(trans_manifests, topo, arrivalGap = 16):
    [ constHead.traffic_config_schema.validate(manifest) for _, manifest in trans_manifests.items() ] 
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
    for estream in streams:
        if estream.name == name:
            assert isinstance(estream, stream.stream)
            return estream
    raise ValueError(f"Stream {name} not found")

def get_qos_by_name(qoses, name):
    for qos in qoses:
        if qos['name'] == name:
            return qos
    raise ValueError(f"Qos {name} not found")

def apply_control_to_stream_by_name(streams, controls):
    for control in controls:
        estream = get_stream_by_name(streams, control['name'])
        estream.tx_parts = control['tx_parts']
    
logger      = QosLogger(os.path.join(os.path.dirname(__file__), 'expRes.json'))
topo        = construct_graph("./config/topo/2024-5-9.txt")

ip_table    = ctl._ip_extract_all(topo)
exit()
ctl._ip_associate(topo, ip_table)

while ip_table['SoftAP']['eth0'] != '192.168.3.72':
    ip_table    = ctl._ip_extract_all(topo)
    ctl._ip_associate(topo, ip_table)

links       = topo.get_links()

fthru       = 600   # Mbps
pthru       = 50    # Mbps


ithru       = 470   # Mbps 

trans_manifests = {
    'proj1': {
        'thru'      : pthru,
        'file_type' : 'proj',
        
        'link'      : links[1],
        'port'      : 6204,
        'ip_addrs'  : [ topo.link_to_tx_ip(links[0]), topo.link_to_tx_ip(links[1]) ],
        'tx_parts'  : [ 0, 0 ],
        'name'      : 'proj1',
    },
    'interference': {
        'thru'      : ithru,
        'file_type' : 'file',
        
        'link'      : links[1],
        'port'      : 6205,
        'ip_addrs'  : [ topo.link_to_tx_ip(links[0]), topo.link_to_tx_ip(links[0]) ],
        'tx_parts'  : [ 0, 0 ],
        'name'      : 'interference',
    },
}

streams = create_transmission(trans_manifests, topo)
topo.show()
from util.solver import channelBalanceSolver
channel_balance_solver  = channelBalanceSolver()
channel_balance_solver.update_tx_parts(get_stream_by_name(streams, 'proj1').tx_parts)

lighter = gb_state()
import time
for test_idx in range(0, 15):
    ## Transmission
    ctl.create_tx_manifest(topo)
    time.sleep(1)
    conn    = ctl.start_transmission(graph = topo, DURATION = 15)
    
    ## Read Qos
    thrus   = ctl.read_thu( conn )
    rtts    = ctl.read_rtt( topo )    
    qoses   = qos.get_qoss( topo, thrus, rtts ); logger.log_write(qoses)

    # for qosVal in qoses:
    #     print(json.dumps(qosVal, indent = 4))
    
    channel_balance_solver.update( get_qos_by_name(qoses, 'proj1') )
    
    logger.log_write(qoses)
    
    # channel_balance_solver.solve_by_rtt_balance()
    # channel_balance_solver.apply(get_stream_by_name(streams, 'proj1'))
    
    # print(channel_balance_solver.channel_rtts)
    # print(channel_balance_solver.tx_parts)
    
    # ## Compute global state & control
    lighter.update_gb_state( qoses )
    
    rtts = []
    for qosVal in qoses:
        try:
            constHead.PROJ_QOS_SCHEMA.validate(qosVal)
            rtts.append({qosVal['name'] : qosVal[constHead.CHANNEL_RTTS]})
        except Exception as e:
            continue
    print(rtts)
    
    control = singleDirFlowTransSolver( direction = lighter.flow_flag(), islog = True ).solve( qoses )
    print(lighter.flow_flag())
    

    ## Apply control
    apply_control_to_stream_by_name(streams, control)
    
    
logger.log_close()
    