
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

logger      = QosLogger(os.path.join(os.path.dirname(__file__), 'expRes_3_1.json'))
topo        = construct_graph("./config/topo/2024-5-13.txt")

ip_table    = ctl._ip_extract_all(topo)

ctl._ip_associate(topo, ip_table)

while ip_table['SoftAP']['eth0'] != '192.168.3.72':
    ip_table    = ctl._ip_extract_all(topo)
    ctl._ip_associate(topo, ip_table)

links       = topo.get_links()

fthru       = 600   # Mbps
pthru       = 50    # Mbps


ithru       = 50   # Mbps

trans_manifests = {
    'proj1': {
        'thru'      : pthru,
        'file_type' : 'proj',

        'link'      : links[1],
        'port'      : 6204,
        'ip_addrs'  : [ topo.link_to_tx_ip(links[1]), topo.link_to_tx_ip(links[0]) ],
        'tx_parts'  : [ 0.15, 0.15 ],
        'name'      : 'proj1',
    },
    'proj2': {
        'thru'      : pthru,
        'file_type' : 'proj',

        'link'      : links[3],
        'port'      : 6205,
        'ip_addrs'  : [ topo.link_to_tx_ip(links[2]), topo.link_to_tx_ip(links[3]) ],
        'tx_parts'  : [ 0.1, 0.1],
        'name'      : 'proj2',
    },
    'interference': {
        'thru'      : ithru,
        'file_type' : 'file',

        'link'      : links[5],
        'port'      : 6207,
        'ip_addrs'  : [ topo.link_to_tx_ip(links[5]), topo.link_to_tx_ip(links[5]) ],
        'tx_parts'  : [ 0, 0 ],
        'name'      : 'interference',
    },

}

# ================
streams = create_transmission(trans_manifests, topo)
# ================
topo.show()

from util.solver import channelBalanceSolver
from util.solver import channelSwitchSolver

target_stream_name = ['proj1', 'proj2']

channel_solvers = [channelBalanceSolver() for _ in range(len(target_stream_name))]
[ channel_solver.update_tx_parts(get_stream_by_name(streams, name).tx_parts) for channel_solver, name in zip(channel_solvers, target_stream_name) ]

channel_switch_solvers = [channelSwitchSolver(switch_state = constHead.MUL_CHAN) for _ in range(len(target_stream_name))]

lighter = gb_state()

import time

backoff_device = None

for test_idx in range(0, 20):
    print(test_idx)
    # =================
    ## Transmission
    ctl.create_tx_manifest(topo)
    time.sleep(1)
    conn    = ctl.start_transmission(graph = topo, DURATION = 15)

    ## Read Qos
    thrus   = ctl.read_thu( conn )
    print('read qos')
    try:
        rtts    = ctl.read_rtt( topo )
        qoses   = qos.get_qoss( topo, thrus, rtts ); logger.log_write(qoses)
    except:
        continue
    # =================

    rtts = []
    for qosVal in qoses:
        try:
            constHead.PROJ_QOS_SCHEMA.validate(qosVal)
            rtts.append({qosVal['name'] : qosVal[constHead.CHANNEL_RTTS]})
        except Exception as e:
            continue
    print(rtts)

    rtts = []
    for qosVal in qoses:
        try:
            constHead.PROJ_QOS_SCHEMA.validate(qosVal)
            rtts.append({qosVal['name'] : qosVal[constHead.RTT]})
        except Exception as e:
            continue
    print(rtts)

    #############################(2)
    # if backoff_device is not None:
    #     for channel_switch_solver, name  in zip(channel_switch_solvers, target_stream_name):
    #         if name == backoff_device:
    #             last_tx_parts = channel_switch_solver.last_tx_parts
    #             switch_state = channel_switch_solver.switch( get_stream_by_name(streams, name).tx_parts, get_qos_by_name(qoses, name)[constHead.CHANNEL_RTTS] ).switch_state
    #             if switch_state == constHead.MUL_CHAN:
    #                 get_stream_by_name(streams, name).tx_parts = last_tx_parts
    #             elif switch_state == constHead.CHANNEL0:
    #                 get_stream_by_name(streams, name).tx_parts = [0, 0]
    #             elif switch_state == constHead.CHANNEL1:
    #                 get_stream_by_name(streams, name).tx_parts = [1, 1]
    #     backoff_device = None
    #     continue

    # for channel_switch_solver, name  in zip(channel_switch_solvers, target_stream_name):
    #     if channel_switch_solver.is_switch(get_qos_by_name(qoses, name)):
    #         channel_switch_solver.switch( get_stream_by_name(streams, name).tx_parts, get_qos_by_name(qoses, name)[constHead.CHANNEL_RTTS] )
    #         get_stream_by_name(streams, name).tx_parts = channel_switch_solver.next_parts()
    #         backoff_device = name
    #         print(f"Backoff device: {backoff_device}, tx_parts: {channel_switch_solver.next_parts()}")

    # if backoff_device is not None:
    #     continue

    ##########################(1)
    [ channel_solver.update( get_qos_by_name(qoses, name) ) for channel_solver, name in zip(channel_solvers, target_stream_name) ]

    [ channel_solver.solve_by_rtt_balance() for channel_solver in channel_solvers ]

    # trans_manifests.update({'interference':None})
    # for name in target_stream_name:
    #     tx_parts = get_stream_by_name(streams, name).tx_parts
    #     trans_manifests[name].update({constHead.CHANNEL_RTTS: tx_parts} )
    # streams = create_transmission(trans_manifests, topo)

logger.log_close()
