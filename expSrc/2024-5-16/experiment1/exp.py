
import os
import json

import numpy as np
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
        assert trans_manifest['thru'] > 0
        conn.batch(sender, "create_file", {"thru": trans_manifest['thru'], "arrivalGap": arrivalGap, "name": f'{name}.npy', "num": 20000}).wait(0.5).apply()

        temp        = stream.stream()
        file_type   = trans_manifest['file_type']
        if file_type == 'file':
            temp            = temp.read_from_manifest('./config/stream/file.json')
        else:
            temp            = temp.read_from_manifest('./config/stream/proj.json')
            temp.calc_rtt   = True


        temp.npy_file   = file_name
        temp.tx_ipaddrs = trans_manifest['ip_addrs']
        temp.name       = trans_manifest['name']
        temp.tx_parts   = trans_manifest['tx_parts']
        temp.port       = trans_manifest['port']
        temp.tos        = trans_manifest['tos']

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
topo        = construct_graph("./config/topo/2024-5-16.txt")

ip_table    = ctl._ip_extract_all(topo)

ctl._ip_associate(topo, ip_table)

while ip_table['SoftAP']['eth0'] != '192.168.3.72':
    ip_table    = ctl._ip_extract_all(topo)
    ctl._ip_associate(topo, ip_table)

links       = topo.get_links()

fthru       = 600   # Mbps
pthru       = 50    # Mbps


ithru       = 20   # Mbps

tos_values = [96, 128]

ithru_candidates = list(range(20, 200, 40))

from schema import Schema, And, Use, Optional, Or
tos_thru_schema = Schema({
    'thru': And(Use(int), lambda n: 0 <= n <= 200),
    'tos': And(Use(int), lambda n: n in tos_values)
})

user_defined_qos_shcema = Or(constHead.QOS_SCHEMA, tos_thru_schema)
import time
for _ in range(0, 50):
    ithru = int(np.random.choice(ithru_candidates))
    itos  = int(np.random.choice(tos_values))
    
    print(ithru, itos)    
    # ctl.clean_up_receiver( topo, 'lablab' )
    topo        = construct_graph("./config/topo/2024-5-16.txt")
    ctl._ip_associate(topo, ip_table)
    
    trans_manifests = {
        'proj1': {
            'thru'      : pthru,
            'file_type' : 'proj',

            'link'      : links[0],
            'port'      : 6204,
            'ip_addrs'  : [ topo.link_to_tx_ip(links[0]), topo.link_to_tx_ip(links[0]) ],
            'tx_parts'  : [ 0, 0 ],
            'name'      : 'proj1',
            'tos'       : 128,
        },
        'file':{
            'thru'      : fthru,
            'file_type' : 'file',

            'link'      : links[1],
            'port'      : 6205,
            'ip_addrs'  : [ topo.link_to_tx_ip(links[1]), topo.link_to_tx_ip(links[1]) ],
            'tx_parts'  : [ 0, 0 ],
            'name'      : 'file',
            'tos'       : 96,
        },
        'interference': {
            'thru'      : ithru,
            'file_type' : 'file',

            'link'      : links[2],
            'port'      : 6207,
            'ip_addrs'  : [ topo.link_to_tx_ip(links[2]), topo.link_to_tx_ip(links[2]) ],
            'tx_parts'  : [ 0, 0 ],
            'name'      : 'interference',
            'tos'       : itos,
        },
    }
    
    streams = create_transmission(trans_manifests, topo)
    ## Transmission
    print("Creating transmission")
    ctl.create_tx_manifest(topo)
    time.sleep(1)
    conn    = ctl.start_transmission(graph = topo, DURATION = 15)

    ## Read Qos
    thrus   = ctl.read_thu( conn )

    ## todo clean up stream-replay rx
    try:
        rtts    = ctl.read_rtt( topo )
        qoses   = qos.get_qoss( topo, thrus, rtts )
        qoses.append({'tos': itos, 'thru': ithru})
        logger.log_write(qoses, user_defined_qos_shcema)
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


logger.log_close()
