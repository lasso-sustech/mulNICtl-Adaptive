
import os
import json
import time
import util.ctl as ctl
import util.qos as qos
import util.constHead as constHead
import traceback

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
        if constHead.TX_PARTS in control:
            estream.tx_parts = control[constHead.TX_PARTS]
        if constHead.THRU_CONTROL in control:
            estream.throttle = control[constHead.THRU_CONTROL]

def print_rtt(qoses, key = constHead.RTT):
    rtts = []
    for qosVal in qoses:
        try:
            constHead.PROJ_QOS_SCHEMA.validate(qosVal)
            rtts.append({qosVal['name'] : qosVal[key]})
        except Exception as e:
            continue
    print(rtts)

logger      = QosLogger(os.path.join(os.path.dirname(__file__), 'expRes.json'))
topo        = construct_graph("./config/topo/2024-5-20.txt")
ip_table    = ctl._ip_extract_all(topo)
ctl._ip_associate(topo, ip_table)
while ip_table['SoftAP']['eth0'] != '192.168.3.72':
    ip_table    = ctl._ip_extract_all(topo)
    ctl._ip_associate(topo, ip_table)
res = ctl.read_mcs(topo)
links       = topo.get_links()
fthru       = 600   # Mbps
pthru       = 50    # Mbps
ithru       = 100   # Mbps
trans_manifests = {
    'proj1': {
        'thru'      : pthru,
        'file_type' : 'proj',
        'link'      : links[1],
        'port'      : 6204,
        'ip_addrs'  : [ topo.link_to_tx_ip(links[0]), topo.link_to_tx_ip(links[1]) ],
        'tx_parts'  : [ 0.3, 0.3 ],
        'name'      : 'proj1',
        'tos'       : 128,
    },
    'proj2': {
        'thru'      : pthru,
        'file_type' : 'proj',

        'link'      : links[3],
        'port'      : 6205,
        'ip_addrs'  : [ topo.link_to_tx_ip(links[2]), topo.link_to_tx_ip(links[3]) ],
        'tx_parts'  : [0.3, 0.3],
        'name'      : 'proj2',
        'tos'       : 128,
    },
    'file1': {
        'thru'      : fthru,
        'file_type' : 'file',

        'link'      : links[1],
        'port'      : 6206,
        'ip_addrs'  : [ topo.link_to_tx_ip(links[1]), topo.link_to_tx_ip(links[1]) ],
        'tx_parts'  : [ 0, 0],
        'name'      : 'file1',
        'tos'       : 96,
    },
    'file2': {
        'thru'      : fthru,
        'file_type' : 'file',

        'link'      : links[3],
        'port'      : 6207,
        'ip_addrs'  : [ topo.link_to_tx_ip(links[2]), topo.link_to_tx_ip(links[2]) ],
        'tx_parts'  : [ 0, 0],
        'name'      : 'file2',
        'tos'       : 96,
    },
    # 'interference': {
    #     'thru'      : ithru,
    #     'file_type' : 'file',

    #     'link'      : links[4],
    #     'port'      : 6208,
    #     'ip_addrs'  : [ topo.link_to_tx_ip(links[4]), topo.link_to_tx_ip(links[4]) ],
    #     'tx_parts'  : [ 0, 0 ],
    #     'name'      : 'interference',
    #     'tos'       : 128,
    # },

}

# ================
streams = create_transmission(trans_manifests, topo)
# ================


# from util.solver import channelBalanceSolver
# from util.solver import channelSwitchSolver
# from util.solver import channelS2DAppSolver
from util.solver import thruSolver

target_stream_name  = ['file1', 'file2']
initial_throttle    = [30, 300]
for idx, target_name in enumerate(target_stream_name):
    get_stream_by_name(streams, target_name).throttle = initial_throttle[idx]

lighter = gb_state()

qos_recorders = []
start_auto = False
backoff_device = None

topo.show()
last_qos = None; target_qos = None
test_idx = 0
while True:
    print(test_idx)
    if test_idx == 20:
        break
    ##########################
    ## Transmission
    ctl.create_tx_manifest(topo)
    time.sleep(1)
    conn        = ctl.start_transmission(graph = topo, DURATION = 15)

    ## Read Qos
    thrus       = ctl.read_thu( conn )
    print('read qos')
    try:
        rtts    = ctl.read_rtt( topo )
        qoses   = qos.get_qoss( topo, thrus, rtts ); logger.log_write(qoses)
    except:
        print(traceback.format_exc())
        continue
    ##########################
    print_rtt(qoses, key = constHead.CHANNEL_RTTS)
    print_rtt(qoses, key = constHead.RTT)
    
    if test_idx == 0:
        thru_ctl = [ thruSolver().next_thru_control(qoses, file_name) for file_name in  target_stream_name]
        print(thru_ctl)
        apply_control_to_stream_by_name(streams, thru_ctl)
        last_qos = qoses
    if test_idx == 1:
        target_qos = qoses
        thru_ctl =[ thruSolver().solve(last_qos, target_qos, file_name) for file_name in  target_stream_name]
        print(thru_ctl)
        apply_control_to_stream_by_name(streams, thru_ctl)
    test_idx  += 1
logger.log_close()
