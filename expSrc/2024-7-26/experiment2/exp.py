
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

        arrivalGap = trans_manifest['arrivalGap']
        is_file_created = trans_manifest['is_file_created'] if 'is_file_created' in trans_manifest else False

        if not is_file_created:
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
        print("temp links:",temp.links)
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

# thru_list = [50,40,30,20,10]
fileList = os.listdir('dpScript/2024-7-26/experiment2/NoAda')
txtIndex = 101
tempTxtName = f'output{txtIndex}.txt'
while tempTxtName in fileList:
    txtIndex += 1
    tempTxtName = f'output{txtIndex}.txt'

print(tempTxtName)
thru_list = [50,40,30,20,16]
# thru_list = [50]
taskNum = 4  #stream number
interNum = 0  #interference number
inter_gap = 0  #interference packetage gap


    # inter_thru = int((totalthru - target_thru*taskNum)/(interNum*2))
inter_thru = 1
topo        = construct_graph("./config/topo/2024-7-26-2.txt")
ipcc    = ctl.ipcManager(topo)
intertos = 96

for target_thru in thru_list:
    # target_thru = 32
    totalthru = target_thru*taskNum
    ip_table    = ctl._ip_extract_all(topo)
    ctl._ip_associate(topo, ip_table)

    links       = topo.get_links()
    print("links ",links)
    fthru       = 600   # Mbps
    pthru       = 50    # Mbps
    ithru       = 30   # Mbps
    trans_manifests = {
    # git
    # 'file_inter1': {
    #         'thru'      : inter_thru,
    #         'file_type' : 'file',
    #         'is_file_created': False,
    #         'arrivalGap' : inter_gap,
    #         'link'      : links[4],
    #         'port'      : 6305,
    #         'links'     : [topo.get_link_ips(links[4])],
    #         'tx_parts'  : [1],
    #         'tos'       : 128,
    #     },
    # 'file_inter2': {
    #         'thru'      : inter_thru,
    #         'file_type' : 'file',
    #         'is_file_created': False,
    #         'arrivalGap' : inter_gap,
    #         'link'      : links[5],
    #         'port'      : 6306,
    #         'links'     : [topo.get_link_ips(links[5])],
    #         'tx_parts'  : [1],
    #         'tos'       : intertos,
    #     },
    # 'file_inter3': {
    #         'thru'      : inter_thru,
    #         'file_type' : 'file',
    #         'is_file_created': False,
    #         'arrivalGap' : inter_gap,
    #         'link'      : links[6],
    #         'port'      : 6307,
    #         'links'     : [topo.get_link_ips(links[6])],
    #         'tx_parts'  : [1],
    #         'tos'       : intertos,
    # },
    # 'file_inter4': {
    #         'thru'      : inter_thru,
    #         'file_type' : 'file',
    #         'is_file_created': False,
    #         'arrivalGap' : inter_gap,
    #         'link'      : links[7],
    #         'port'      : 6308,
    #         'links'     : [topo.get_link_ips(links[7])],
    #         'tx_parts'  : [1],
    #         'tos'       : intertos,
    #     },
    # 'file_inter5': {
    #         'thru'      : inter_thru,
    #         'file_type' : 'file',
    #         'is_file_created': False,
    #         'arrivalGap' : inter_gap,
    #         'link'      : links[4],
    #         'port'      : 6309,
    #         'links'     : [topo.get_link_ips(links[4])],
    #         'tx_parts'  : [1],
    #         'tos'       : intertos,
    #     },
    # 'file_inter6': {
    #         'thru'      : inter_thru,
    #         'file_type' : 'file',
    #         'is_file_created': False,
    #         'arrivalGap' : inter_gap,
    #         'link'      : links[5],
    #         'port'      : 6310,
    #         'links'     : [topo.get_link_ips(links[5])],
    #         'tx_parts'  : [1],
    #         'tos'       : intertos,
    #     },
    # 'file_inter7': {
    #         'thru'      : inter_thru,
    #         'file_type' : 'file',
    #         'is_file_created': False,
    #         'arrivalGap' : inter_gap,
    #         'link'      : links[6],
    #         'port'      : 6311,
    #         'links'     : [topo.get_link_ips(links[6])],
    #         'tx_parts'  : [1],
    #         'tos'       : intertos,
    # },
    # 'file_inter8': {
    #         'thru'      : inter_thru,
    #         'file_type' : 'file',
    #         'is_file_created': False,
    #         'arrivalGap' : inter_gap,
    #         'link'      : links[7],
    #         'port'      : 6312,
    #         'links'     : [topo.get_link_ips(links[7])],
    #         'tx_parts'  : [1],
    #         'tos'       : intertos,
    #     },
    'file1': {
            'thru'      : target_thru,
            'file_type' : 'proj',
            'is_file_created': False,
            'arrivalGap' : 16,
            'link'      : links[0],
            'port'      : 6205,
            'links'     : [topo.get_link_ips(links[0]), topo.get_link_ips(links[1])],
            'tx_parts'  : [0,0],
            'tos'       : 128,
        },
    'file2': {
            'thru'      : target_thru,
            'file_type' : 'proj',
            'is_file_created': False,
            'arrivalGap' : 16,
            'link'      : links[2],
            'port'      : 6206,
            'links'     : [topo.get_link_ips(links[2]),topo.get_link_ips(links[3])],
            'tx_parts'  : [0, 0],
            'tos'       : 128,
        },
    'file3': {
            'thru'      : target_thru,
            'file_type' : 'proj',
            'is_file_created': False,
            'arrivalGap' : 16,
            'link'      : links[4],
            'port'      : 6207,
            'links'     : [topo.get_link_ips(links[4]), topo.get_link_ips(links[5])],
            'tx_parts'  : [0, 0],
            'tos'       : 128,
        },
    'file4': {
            'thru'      : target_thru,
            'file_type' : 'proj',
            'is_file_created': False,
            'arrivalGap' : 16,
            'link'      : links[6],
            'port'      : 6208,
            'links'     : [topo.get_link_ips(links[6]),topo.get_link_ips(links[7])],
            'tx_parts'  : [0, 0],
            'tos'       : 128,
        },
    # 'file5': {
    #         'thru'      : target_thru,
    #         'file_type' : 'proj',
    #         'is_file_created': False,
    #         'arrivalGap' : 16,
    #         'link'      : links[0],
    #         'port'      : 6209,
    #         'links'     : [topo.get_link_ips(links[0]), topo.get_link_ips(links[1])],
    #         'tx_parts'  : [0, 0],
    #         'tos'       : 128,
    #     },
    # 'file6': {
    #         'thru'      : target_thru,
    #         'file_type' : 'proj',
    #         'is_file_created': False,
    #         'arrivalGap' : 16,
    #         'link'      : links[2],
    #         'port'      : 6210,
    #         'links'     : [topo.get_link_ips(links[2]),topo.get_link_ips(links[3])],
    #         'tx_parts'  : [0, 0],
    #         'tos'       : 128,
    #     },

    }

    # ================
    streams = create_transmission(trans_manifests, topo)

    # ================

    topo.show()

    ctrller = ctl.CtlManager()
    # ipcc    = ctl.ipcManager(topo)
    import threading
    # import solver

    # Create jsonlist log file

    # logger = open(f'dpScript/2024-7-26/experiment1/Interference-{target_thru}_Totalthru{totalthru}_2x8x2x{inter_thru}M_149_gap{inter_gap}_TaskNum{taskNum}_{txtIndex}.jsonl', 'w')

    # def get_statistics(logger):
    #     base_info = ctl.graph_qos_collections(topo)
    #     exp_solver = solver.Controller()
    #     time.sleep(2) 
    #     for i in range(40): #ctl Num
    #         qos = ipcc.ipc_qos_collection()
    #         # print("qos ",qos)
    #         qos.pop(f'6305@{128}', None)
    #         qos.pop(f'6306@{intertos}', None)
    #         qos.pop(f'6307@{intertos}', None)
    #         qos.pop(f'6308@{intertos}', None)
    #         qos.pop(f'6309@{intertos}', None)
    #         qos.pop(f'6310@{intertos}', None)
    #         qos.pop(f'6311@{intertos}', None)
    #         qos.pop(f'6312@{intertos}', None)
    #         for k in qos:
    #             for sub_key, sub_value in base_info[k].items():
    #                 if sub_key not in qos[k]:
    #                     qos[k][sub_key] = sub_value
    #         logger.write(json.dumps(qos) + '\n')
    #         control = exp_solver.control(qos)
    #         print(control)
    #         ipcc.ipc_tx_part_ctrl(control)
    #         time.sleep(1)#ctl step

    # import threading
    ctrller.duration = 30
    ctrller.exp_thread(topo)
    # time.sleep(5)


    # # # packet Loss
    packetFileName = f"dpScript/2024-7-26/experiment2/PacketLoss/packetLoss{target_thru}_{txtIndex}.txt"
    packetFile = open(packetFileName,"w")
    packetFile.write(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())+'\n')
    packetFile.write("interference : R*2+2+2F (5G)\n")
    packetFile.write(f'Task number : {taskNum}\n')
    packetFile.write(f'Task throughput : {target_thru}\n')
    packetFile.write(f'Interference number : {interNum}\n')
    packetFile.write(f'Interference throughput : {inter_thru}\n')
    packetFile.write(f'Interference gap : {inter_gap}\n')
    packetFile.write(f'Interference tos : {intertos}\n')
    packetFile.write(f'Total throughput : {totalthru}\n')
    packetFile.write(f'NoAda duration: {ctrller.duration}\n')

    packetLoss = ctrller.info_queue.get(block=True, timeout= ctrller.duration + 20)
    print("packetLoss ", packetLoss)
    for list_item in packetLoss:
        packetFile.write(str(list_item)+'\n')

    res = ctl.read_rtt(topo)
    for k, v in res.items():
        print(k , v.channel_rtts)
        print(k , v.rtt)


    targetIP = "192.168.3.32"
    NoAdapath = "dpScript/2024-7-26/experiment2/NoAda"
    # Adapath = "dpScript/2024-7-25/experiment1/Ada"
    portlist = [x for x in range(6205,6205+taskNum)]
    for port in portlist:
        ctl.fileTransfer(topo, targetIP,  NoAdapath, f"../stream-replay/logs/rtt-{port}*128.txt" , links[0])
        time.sleep(5)
    print("throughput: ",target_thru)
    print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()))

    txtIndex += 1


# # #
# ctrller.duration = 60
# statistic_thread = threading.Thread(target=get_statistics, args=(logger,)) 
# ctrller.exp_thread(topo, [statistic_thread])

# # ctrller.exp_thread(topo)
# AdaPacketLoss = ctrller.info_queue.get(block=True, timeout= ctrller.duration + 20)
# print(AdaPacketLoss)
# packetFile.write("Adaptive:\n")
# for list_item in AdaPacketLoss:
#     packetFile.write(str(list_item)+'\n')
# packetFile.write(f'Ada duration: {ctrller.duration}\n')
# packetFile.close()

# res = ctl.read_rtt(topo)
# for k, v in res.items():
#     print(k , v.channel_rtts)
#     print(k , v.rtt)

# for port in portlist:
#     ctl.fileTransfer(topo, targetIP,  Adapath, f"../stream-replay/logs/rtt-{port}*128.txt" , links[0])
#     time.sleep(5)







# ctl.fileTransfer(topo, "192.168.3.72",  "dpScript/2024-7-24/experiment2/Ada", "../stream-replay/logs/rtt-6205*128.txt" , links[0])
# time.sleep(5)
# ctl.fileTransfer(topo, "192.168.3.72",  "dpScript/2024-7-24/experiment2/Ada", "../stream-replay/logs/rtt-6206*128.txt" , links[2])
# time.sleep(5)
# ctl.fileTransfer(topo, "192.168.3.72",  "dpScript/2024-7-24/experiment2/Ada", "../stream-replay/logs/rtt-6207*128.txt" , links[0])
# time.sleep(5)
# ctl.fileTransfer(topo, "192.168.3.72",  "dpScript/2024-7-24/experiment2/Ada", "../stream-replay/logs/rtt-6208*128.txt" , links[2])
# time.sleep(5)
# ctl.fileTransfer(topo, "192.168.3.72",  "dpScript/2024-7-24/experiment2/Ada", "../stream-replay/logs/rtt-6209*128.txt" , links[0])
# time.sleep(5)
# ctl.fileTransfer(topo, "192.168.3.72",  "dpScript/2024-7-24/experiment2/Ada", "../stream-replay/logs/rtt-6210*128.txt" , links[2])
# time.sleep(5)
# ctl.fileTransfer(topo, "192.168.3.72",  "dpScript/2024-7-24/experiment2/Ada", "../stream-replay/logs/rtt-6211*128.txt" , links[0])
# time.sleep(5)
# ctl.fileTransfer(topo, "192.168.3.72",  "dpScript/2024-7-24/experiment2/Ada", "../stream-replay/logs/rtt-6212*128.txt" , links[2])
# time.sleep(5)
