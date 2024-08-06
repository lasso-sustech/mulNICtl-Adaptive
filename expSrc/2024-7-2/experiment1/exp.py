import os
import json
import time

import util.ctl as ctl
import util.qos as qos
import util.constHead as constHead
import util.api.ipc as ipc
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


        temp.npy_file   = file_name
        temp.links      = trans_manifest['links']
        print(temp.links)
        temp.name       = '{}@{}'.format(trans_manifest['port'], trans_manifest['tos'])
        temp.tx_parts   = trans_manifest['tx_parts']
        temp.port       = trans_manifest['port']
        temp.tos        = trans_manifest['tos']
        
        ## Local test
        temp.channels = [constHead.CHANNEL0, constHead.CHANNEL0]

        topo.ADD_STREAM(trans_manifest['link'], temp, validate = False)

        streams.append(temp)
    return streams

logger      = QosLogger(os.path.join(os.path.dirname(__file__), 'expRes.json'))
topo        = construct_graph("./config/topo/2024-7-9.txt")
ip_table    = ctl._ip_extract_all(topo)
ctl._ip_associate(topo, ip_table)

links       = topo.get_links()
fthru       = 600   # Mbps
pthru       = 50    # Mbps
ithru       = 10    # Mbps
trans_manifests = {
  'file1': {
        'thru'      : 25,
        'file_type' : 'proj',

        'link'      : links[0],
        'port'      : 6205,
        'links'     : [topo.get_link_ips(links[0]), topo.get_link_ips(links[1])],
        'tx_parts'  : [0, 0],
        'tos'       : 96,
    },
    # 'file2': {
    #     'thru'      : 25,
    #     'file_type' : 'proj',

    #     'link'      : links[1],
    #     'port'      : 6206,
    #     'links'     : [topo.get_link_ips(links[0]), topo.get_link_ips(links[1])],
    #     'tx_parts'  : [1, 1],
    #     'tos'       : 96,
    # }
}

# ================
streams = create_transmission(trans_manifests, topo)
streams[0].channels = [constHead.CHANNEL0, constHead.CHANNEL1]
# ================

topo.show()

ctrller = ctl.CtlManager()
ipcc    = ctl.ipcManager(topo)
ctrller.duration = 10

# import solver

# def get_statistics():
#     base_info = ctl.graph_qos_collections(topo)
#     exp_solver = solver.Controller()
#     time.sleep(2)
#     for i in range(20):
#         qos = ipcc.ipc_qos_collection()
#         for k in qos:
#             for sub_key, sub_value in base_info[k].items():
#                 if sub_key not in qos[k]:
#                     qos[k][sub_key] = sub_value
#         print(qos)
#         control = exp_solver.control(qos)
#         # print(control)
#         ipcc.ipc_tx_part_ctrl(control)
#         time.sleep(3)

import threading
# statistic_thread = threading.Thread(target=get_statistics) 
# ctrller.exp_thread(topo, [statistic_thread])
for i in range(5) :
    ctrller.exp_thread(topo)
    print(ctrller.info_queue.get(block=True, timeout= ctrller.duration + 10))
    res = ctl.read_rtt(topo)
    for _ in res:
        print(_.channel_rtts)
        print(_.rtt)
logger.log_close()