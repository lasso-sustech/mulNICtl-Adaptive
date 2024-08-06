
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


        temp.npy_file   = file_name
        temp.links      = trans_manifest['links']
        print(temp.links)
        temp.name       = '{}@{}'.format(trans_manifest['port'], trans_manifest['tos'])
        temp.tx_parts   = trans_manifest['tx_parts']
        temp.port       = trans_manifest['port']
        temp.tos        = trans_manifest['tos']
        temp.target_rtt = 1000
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

thru_list = [50,40,30,20,10]

for target_thru in thru_list:

    topo        = construct_graph("./config/topo/2024-7-19.txt")
    ip_table    = ctl._ip_extract_all(topo)
    ctl._ip_associate(topo, ip_table)

    links       = topo.get_links()
    fthru       = 600   # Mbps
    pthru       = 50    # Mbps
    ithru       = 30   # Mbps
    trans_manifests = {
    'file1': {
            'thru'      : target_thru,
            'file_type' : 'proj',

            'link'      : links[0],
            'port'      : 6205,
            'links'     : [topo.get_link_ips(links[0]), topo.get_link_ips(links[1])],
            'tx_parts'  : [0, 0],
            'tos'       : 128,
        },
        # 'file2': {
        #     'thru'      : 0.01,
        #     'file_type' : 'file',

        #     'link'      : links[0],
        #     'port'      : 6206,
        #     'links'     : [topo.get_link_ips(links[2])],
        #     'tx_parts'  : [1],
        #     'tos'       : 128,
        # }
    }

    # ================
    streams = create_transmission(trans_manifests, topo)
    # ================

    topo.show()

    ctrller = ctl.CtlManager()
    # ipcc    = ctl.ipcManager(topo)


    # import threading

    # import solver

    ## Create jsonlist log file
    # logger = open(f'dpScript/2024-7-19/if-{target_thru}.jsonl', 'w')

    # def get_statistics(logger):
    #     base_info = ctl.graph_qos_collections(topo)
    #     exp_solver = solver.Controller()
    #     time.sleep(2)
    #     for i in range(50):
    #         qos = ipcc.ipc_qos_collection()
    #         for k in qos:
    #             for sub_key, sub_value in base_info[k].items():
    #                 if sub_key not in qos[k]:
    #                     qos[k][sub_key] = sub_value
    #         logger.write(json.dumps(qos) + '\n')
    #         if '6205@128' in qos:
    #             # print(qos['6205@128'])
    #             qos = {'6205@128': qos['6205@128']}
    #             control = exp_solver.control(qos)
    #             # print(control)
    #             ipcc.ipc_tx_part_ctrl(control)
    #         time.sleep(2)

    import threading
    ctrller.duration = 10
    ctrller.exp_thread(topo)

    # ctrller.exp_thread(topo)
    print(ctrller.info_queue.get(block=True, timeout= ctrller.duration + 10))
    res = ctl.read_rtt(topo)
    for k, v in res.items():
        print(k , v.channel_rtts)
        print(k , v.rtt)

    
    ctl.fileTransfer(topo, "192.168.3.72",  "dpScript/2024-7-19/lib", "../stream-replay/logs/rtt-6205*128.txt" , isSend=True)
    print("throughput: ",target_thru)
    print(time.localtime(time.time()))
    time.sleep(5)
    # ctrller.duration = 120
    # statistic_thread = threading.Thread(target=get_statistics, args=(logger,)) 
    # ctrller.exp_thread(topo, [statistic_thread])

    # # ctrller.exp_thread(topo)
    # print(ctrller.info_queue.get(block=True, timeout= ctrller.duration + 10))
    # res = ctl.read_rtt(topo)
    # for k, v in res.items():
    #     print(k , v.channel_rtts)
    #     print(k , v.rtt)

    # for k, ipcCtl in ipcc.ipc_handles.items():
    #     ipcCtl.release()

# logger.close()