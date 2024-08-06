
import os
import json
import util.ctl as ctl
import util.qos as qos
import util.constHead as constHead
import numpy as np

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
        temp.target_rtt = 16

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
topo        = construct_graph("./config/topo/2024-5-13.txt")

ip_table    = ctl._ip_extract_all(topo)

ctl._ip_associate(topo, ip_table)

while ip_table['SoftAP']['eth0'] != '192.168.3.72':
    ip_table    = ctl._ip_extract_all(topo)
    ctl._ip_associate(topo, ip_table)

links       = topo.get_links()

fthru       = 600   # Mbps
pthru       = 50    # Mbps

ithru       = 330  # Mbps
while True:


    trans_manifests = {
        'proj1': {
            'thru'      : pthru,
            'file_type' : 'proj',

            'link'      : links[1],
            'port'      : 6204,
            'ip_addrs'  : [ topo.link_to_tx_ip(links[1]), topo.link_to_tx_ip(links[0]) ],
            'tx_parts'  : [0.05, 0.05],
            'name'      : 'proj1',
        },
        'proj2': {
            'thru'      : pthru,
            'file_type' : 'proj',

            'link'      : links[3],
            'port'      : 6205,
            'ip_addrs'  : [ topo.link_to_tx_ip(links[2]), topo.link_to_tx_ip(links[3]) ],
            'tx_parts'  : [0.05, 0.05],
            'name'      : 'proj2',
        },
        'proj3': {
            'thru'      : pthru,
            'file_type' : 'proj',

            'link'      : links[3],
            'port'      : 6206,
            'ip_addrs'  : [ topo.link_to_tx_ip(links[2]), topo.link_to_tx_ip(links[3]) ],
            'tx_parts'  : [0.05, 0.05],
            'name'      : 'proj3',
        },
        'interference': {
            'thru'      : ithru,
            'file_type' : 'file',

            'link'      : links[4],
            'port'      : 6207,
            'ip_addrs'  : [ topo.link_to_tx_ip(links[4]), topo.link_to_tx_ip(links[4]) ],
            'tx_parts'  : [ 0, 0 ],
            'name'      : 'interference',
        },

    }

    streams = create_transmission(trans_manifests, topo)
    # topo.show()
    from util.solver import channelBalanceSolver

    # target_stream_name = ['proj1', 'proj2', 'proj3']
    # channel_solvers = [channelBalanceSolver() for _ in range(len(target_stream_name))]
    # [ channel_solver.update_tx_parts(get_stream_by_name(streams, name).tx_parts) for channel_solver, name in zip(channel_solvers, target_stream_name) ]

    lighter = gb_state()
    import time
    # for test_idx in range(0, 5):
    ## Transmission
    ctl.create_tx_manifest(topo)
    time.sleep(1)
    conn    = ctl.start_transmission(graph = topo, DURATION = 30)

    ## Read Qos
    thrus   = ctl.read_thu( conn )
    rtts    = ctl.read_rtt( topo )
    qoses   = qos.get_qoss( topo, thrus, rtts ); logger.log_write(qoses)


    logger.log_write(qoses)

    # ## Compute global state & control
    # lighter.update_gb_state( qoses )

    rtts = []
    for qosVal in qoses:
        try:
            constHead.PROJ_QOS_SCHEMA.validate(qosVal)
            rtts.append({qosVal['name'] : qosVal[constHead.CHANNEL_RTTS]})
        except Exception as e:
            continue
    print(rtts)

    # # ## Compute global state & control
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

    if lighter.flow_flag() == 'stop':
        is_turn_small = False
        for qosVal in qoses:
            try:
                if any(np.array(qosVal[constHead.CHANNEL_RTTS]) > 16):
                    is_turn_small = True
            except:
                continue
        if is_turn_small:
            ithru -= 10
        else:
            ithru += 10
    else:
        exit()
    print(ithru)

    ## Apply control
    apply_control_to_stream_by_name(streams, control)



logger.log_close()
