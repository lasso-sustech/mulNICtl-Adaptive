
import os
import json
import time
import util.ctl as ctl
import util.qos as qos
import util.constHead as constHead
import traceback

from tap import Connector
from util import stream
from util.solver import globalSolver, balanceSolver
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
        print(temp.calc_rtt)

        temp.npy_file   = file_name
        temp.links      = trans_manifest['links']
        print(temp.links)
        temp.name       = '{}@{}'.format(trans_manifest['port'], trans_manifest['tos'])
        temp.tx_parts   = trans_manifest['tx_parts']
        temp.port       = trans_manifest['port']
        temp.tos        = trans_manifest['tos']
        
        ## Local test
        temp.channels = [constHead.CHANNEL1, constHead.CHANNEL0]

        topo.ADD_STREAM(trans_manifest['link'], temp, validate = False)

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

topo        = construct_graph("./config/topo/2024-7-29.txt")
ip_table    = ctl._ip_extract_all(topo)
ctl._ip_associate(topo, ip_table)

links       = topo.get_links()
fthru       = 600   # Mbps
pthru       = 50    # Mbps
ithru       = 30   # Mbps
trans_manifests = {
    'file1': {
        'thru'      : 50,
        'file_type' : 'proj',

        'link'      : links[0],
        'port'      : 6206,
        'links'     : [topo.get_link_ips(links[1]), topo.get_link_ips(links[0])],
        'tx_parts'  : [0.1, 0.1],
        'tos'       : 128,
        'channels'  : [constHead.CHANNEL0, constHead.CHANNEL1],
    }
}


# ================
streams = create_transmission(trans_manifests, topo)
# ================

topo.show()

ctrller = ctl.CtlManager()
target_ips, name2ipc = ctl.ipcManager.prepare_ipc(topo)
base_info = ctl.graph_qos_collections(topo)

# _conn = Connector('controller')
# _conn.execute('')

print(target_ips, name2ipc, base_info)

ctrller.duration = 20

# import threading

# import solver

# ## Create jsonlist log file
# logger = open('test.jsonl', 'w')

# def get_statistics(logger, target_ips, name2ipc):
#     print('start optimize')
#     solver.optimize(base_info, target_ips, name2ipc)

# import multiprocessing
# def start_statistic_process():
#     statistic_process = multiprocessing.Process(target=get_statistics, args=(logger, target_ips, name2ipc))
#     statistic_process.start()
#     return statistic_process

# # Function to start the communication process
# # def start_comm_process():
# #     result_queue = multiprocessing.Queue()
# #     comm_process = multiprocessing.Process(target=ctrller._communication_thread, args=(topo,result_queue,))
# #     comm_process.start()
# #     return result_queue.get()

# # Start both processes and return them
# statistic_process = start_statistic_process()
# # res = start_comm_process()


# print(res)

# # ctrller.exp_thread(topo)
# res = ctl.read_rtt(topo)
# for k, v in res.items():
#     print(k , v.channel_rtts)
#     print(k , v.rtt)

# logger.close()