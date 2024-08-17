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

# def create_transmission(trans_manifests, topo, arrivalGap = 16):
def create_transmission(trans_manifests, topo):
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


        arrivalGap = trans_manifest['arrivalGap']###########################################


        conn.batch(sender, "create_file", {"thru": trans_manifest['thru'], "arrivalGap": arrivalGap, "name": f'{name}.npy', "num": 20000}).wait(0.5).apply()
        
        temp        = stream.stream()
        file_type   = trans_manifest['file_type']
        if file_type == 'file':
            # conn.batch(sender, "create_file", {"thru": trans_manifest['thru'], "arrivalGap": arrivalGap, "name": f'{name}.npy', "num": 20000}).wait(0.5).apply()
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
        temp.throttle   = int(trans_manifest['thru']) + 10
        # temp.throttle   = 0
        temp.target_rtt = 0.022
        
        ## Local test
        temp.channels = trans_manifest['channels']

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


fileList = os.listdir('dpScript/2024-8-14/rtt/')
txtIndex = 0
tempTxtName = f'output{txtIndex}.txt'
while tempTxtName in fileList:
    txtIndex += 1
    tempTxtName = f'output{txtIndex}.txt'

topo,links        = construct_graph("./config/topo/2024-8-14.txt")
# print("topo: ", topo)
ip_table    = ctl._ip_extract_all(topo)
ctl._ip_associate(topo, ip_table)

taskNum = 1
thru = 24
filethru = 240
# interthru = 100
# links       = topo.get_links()
# print('links: ', links)
pthru       = 50    # Mbps
ithru       = 30   # Mbps
intertos    = 96


'''
######### s1 no inter
# trans_manifests = {
#     'file1': {
#         'thru'      : thru,
#         'file_type' : 'proj',
#         'link'      : links[0],
#         'port'      : 6205,
#         'links'     : [topo.get_link_ips(links[0]),topo.get_link_ips(links[1])],
#         'tx_parts'  : [0,0],
#         'tos'       : 128,
#         'channels'  : [constHead.CHANNEL0, constHead.CHANNEL1],
#     },
#     'file5': {
#         'thru'      : interthru,
#         'file_type' : 'file',

#         'link'      : links[8],
#         'port'      : 6209,
#         'links'     : [topo.get_link_ips(links[8])],
#         'tx_parts'  : [0],
#         'tos'       : intertos,
#         'channels'  : [constHead.CHANNEL0],
#     },
#     'file6': {
#         'thru'      : interthru,
#         'file_type' : 'file',

#         'link'      : links[9],
#         'port'      : 6210,
#         'links'     : [topo.get_link_ips(links[9])],
#         'tx_parts'  : [0],
#         'tos'       : intertos,
#         'channels'  : [constHead.CHANNEL0],
#     },
#     'file7': {
#         'thru'      : interthru,
#         'file_type' : 'file',

#         'link'      : links[10],
#         'port'      : 6211,
#         'links'     : [topo.get_link_ips(links[10])],
#         'tx_parts'  : [0],
#         'tos'       : intertos,
#         'channels'  : [constHead.CHANNEL0],
#     },
#     'file8': {
#         'thru'      : interthru,
#         'file_type' : 'file',

#         'link'      : links[11],
#         'port'      : 6212,
#         'links'     : [topo.get_link_ips(links[11])],
#         'tx_parts'  : [0],
#         'tos'       : intertos,
#         'channels'  : [constHead.CHANNEL0],
#     },
# }

######## S2 
# trans_manifests = {
#     'file1': {
#         'thru'      : thru,
#         'file_type' : 'proj',

#         'link'      : links[0],
#         'port'      : 6205,
#         'links'     : [topo.get_link_ips(links[0]),topo.get_link_ips(links[1])],
#         'tx_parts'  : [0,0],
#         'tos'       : 128,
#         'channels'  : [constHead.CHANNEL0, constHead.CHANNEL1],
#     },
#     'file2': {
#         'thru'      : thru,
#         'file_type' : 'proj',

#         'link'      : links[2],
#         'port'      : 6206,
#         'links'     : [topo.get_link_ips(links[2]),topo.get_link_ips(links[3])],
#         'tx_parts'  : [0,0],
#         'tos'       : 128,
#         'channels'  : [constHead.CHANNEL0, constHead.CHANNEL1],
#     },
#     'file3': {
#         'thru'      : thru,
#         'file_type' : 'proj',
#         'link'      : links[0],
#         'port'      : 6207,
#         'links'     : [topo.get_link_ips(links[0]),topo.get_link_ips(links[1])],
#         'tx_parts'  : [0,0],
#         'tos'       : 128,
#         'channels'  : [constHead.CHANNEL0, constHead.CHANNEL1],
#     },
#     'file4': {
#         'thru'      : thru,
#         'file_type' : 'proj',

#         'link'      : links[2],
#         'port'      : 6208,
#         'links'     : [topo.get_link_ips(links[2]),topo.get_link_ips(links[3])],
#         'tx_parts'  : [0,0],
#         'tos'       : 128,
#         'channels'  : [constHead.CHANNEL0, constHead.CHANNEL1],
#     },
#     'file5': {
#         'thru'      : interthru,
#         'file_type' : 'file',

#         'link'      : links[8],
#         'port'      : 6209,
#         'links'     : [topo.get_link_ips(links[8])],
#         'tx_parts'  : [0],
#         'tos'       : intertos,
#         'channels'  : [constHead.CHANNEL0],
#     },
#     'file6': {
#         'thru'      : interthru,
#         'file_type' : 'file',

#         'link'      : links[9],
#         'port'      : 6210,
#         'links'     : [topo.get_link_ips(links[9])],
#         'tx_parts'  : [0],
#         'tos'       : intertos,
#         'channels'  : [constHead.CHANNEL0],
#     },
#     'file7': {
#         'thru'      : interthru,
#         'file_type' : 'file',

#         'link'      : links[10],
#         'port'      : 6211,
#         'links'     : [topo.get_link_ips(links[10])],
#         'tx_parts'  : [0],
#         'tos'       : intertos,
#         'channels'  : [constHead.CHANNEL0],
#     },
#     'file8': {
#         'thru'      : interthru,
#         'file_type' : 'file',

#         'link'      : links[11],
#         'port'      : 6212,
#         'links'     : [topo.get_link_ips(links[11])],
#         'tx_parts'  : [0],
#         'tos'       : intertos,
#         'channels'  : [constHead.CHANNEL0],
#     },
# }
'''

#####$############## s3 : inter 'video_play_test100' 'video_play_NS_60_res30000'
trans_manifests = {
    # '0804testvideo16_1': {
    'file1': {
        'thru'      : thru,
        'arrivalGap': 16,
        'file_type' : 'proj',
        'link'      : links[0],
        'port'      : 6205,
        'links'     : [topo.get_link_ips(links[1]),topo.get_link_ips(links[0])],
        'tx_parts'  : [1,1],
        'tos'       : 128,
        'channels'  : [constHead.CHANNEL0, constHead.CHANNEL1],
    },
    # 'file2': {
    #     'thru'      : thru,
    #     'arrivalGap': 16,
    #     'file_type' : 'proj',
    #     'link'      : links[0],
    #     'port'      : 6206,
    #     'links'     : [topo.get_link_ips(links[1]),topo.get_link_ips(links[0])],
    #     'tx_parts'  : [1,1],
    #     'tos'       : 128,
    #     'channels'  : [constHead.CHANNEL0, constHead.CHANNEL1],
    # },
    # 'file3': {
    #     'thru'      : thru,
    #     'arrivalGap': 16,
    #     'file_type' : 'proj',
    #     'link'      : links[4],
    #     'port'      : 6207,
    #     'links'     : [topo.get_link_ips(links[5]),topo.get_link_ips(links[4])],
    #     'tx_parts'  : [1,1],
    #     'tos'       : 128,
    #     'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
    # },
    # 'file4': {
    #     'thru'      : thru,
    #     'arrivalGap': 16,
    #     'file_type' : 'proj',
    #     'link'      : links[4],
    #     'port'      : 6208,
    #     'links'     : [topo.get_link_ips(links[5]),topo.get_link_ips(links[4])],
    #     'tx_parts'  : [1,1],
    #     'tos'       : 128,
    #     'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
    # },
    # 'audio_1': {
    #     'thru'      : 0.1452,
    #     'arrivalGap': 20,
    #     'file_type' : 'proj',
    #     'link'      : links[0],
    #     'port'      : 6209,
    #     'links'     : [topo.get_link_ips(links[1]),topo.get_link_ips(links[0])],
    #     'tx_parts'  : [1,1],
    #     'tos'       : 192,
    #     'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
    # },
    # 'keyMouse_1': {
    #     'thru'      : 0.048,
    #     'arrivalGap': 4,
    #     'file_type' : 'proj',
    #     'link'      : links[0],
    #     'port'      : 6210,
    #     'links'     : [topo.get_link_ips(links[1]),topo.get_link_ips(links[0])],
    #     'tx_parts'  : [1,1],
    #     'tos'       : 192,
    #     'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
    # },
    # 'message_1': {
    #     'thru'      : 0.016,
    #     'arrivalGap': 1000,
    #     'file_type' : 'proj',
    #     'link'      : links[0],
    #     'port'      : 6211,
    #     'links'     : [topo.get_link_ips(links[1]),topo.get_link_ips(links[0])],
    #     'tx_parts'  : [1,1],
    #     'tos'       : 192,
    #     'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
    # },
    # 'file8': {
    #     'thru'      : filethru,
    #     'arrivalGap': 16,
    #     'file_type' : 'file',
    #     'link'      : links[10],
    #     'port'      : 6212,
    #     'links'     : [topo.get_link_ips(links[11])],
    #     'tx_parts'  : [1],
    #     'tos'       : 96,
    #     'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
    # },
    # 'file9': {
    #     'thru'      : filethru,
    #     'arrivalGap': 16,
    #     'file_type' : 'file',
    #     'link'      : links[10],
    #     'port'      : 6213,
    #     'links'     : [topo.get_link_ips(links[11])],
    #     'tx_parts'  : [1],
    #     'tos'       : 96,
    #     'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
    # },
    # 'file10': {
    #     'thru'      : filethru,
    #     'arrivalGap': 16,
    #     'file_type' : 'file',
    #     'link'      : links[10],
    #     'port'      : 6214,
    #     'links'     : [topo.get_link_ips(links[11])],
    #     'tx_parts'  : [1],
    #     'tos'       : 96,
    #     'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
    # },
    # 'file11': {
    #     'thru'      : filethru,
    #     'arrivalGap': 16,
    #     'file_type' : 'file',
    #     'link'      : links[10],
    #     'port'      : 6215,
    #     'links'     : [topo.get_link_ips(links[11])],
    #     'tx_parts'  : [1],
    #     'tos'       : 96,
    #     'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
    # },
    # 'file12': {
    #     'thru'      : filethru,
    #     'arrivalGap': 16,
    #     'file_type' : 'file',
    #     'link'      : links[10],
    #     'port'      : 6216,
    #     'links'     : [topo.get_link_ips(links[11])],
    #     'tx_parts'  : [1],
    #     'tos'       : 96,
    #     'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
    # },
    #  'file13': {
    #     'thru'      : filethru,
    #     'arrivalGap': 16,
    #     'file_type' : 'file',
    #     'link'      : links[10],
    #     'port'      : 6217,
    #     'links'     : [topo.get_link_ips(links[11])],
    #     'tx_parts'  : [1],
    #     'tos'       : 96,
    #     'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
    # },
    # 'file14': {
    #     'thru'      : filethru,
    #     'arrivalGap': 16,
    #     'file_type' : 'file',
    #     'link'      : links[10],
    #     'port'      : 6218,
    #     'links'     : [topo.get_link_ips(links[11])],
    #     'tx_parts'  : [1],
    #     'tos'       : 96,
    #     'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
    # },
    # 'file15': {
    #     'thru'      : filethru,
    #     'arrivalGap': 16,
    #     'file_type' : 'file',
    #     'link'      : links[10],
    #     'port'      : 6219,
    #     'links'     : [topo.get_link_ips(links[11])],
    #     'tx_parts'  : [1],
    #     'tos'       : 96,
    #     'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
    # },
#######################################interference_5G##############################################

#     'interproj1_5g': {
#         'thru'      : 16,
#         'arrivalGap': 16,
#         'file_type' : 'file',
#         'link'      : links[12],
#         'port'      : 6501,
#         'links'     : [topo.get_link_ips(links[12]),topo.get_link_ips(links[12])],
#         'tx_parts'  : [1,1],
#         'tos'       : 128,
#         'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
#     },
#     'interproj2_5g': {
#         'thru'      : 16,
#         'arrivalGap': 16,
#         'file_type' : 'file',
#         'link'      : links[12],
#         'port'      : 6502,
#         'links'     : [topo.get_link_ips(links[12]),topo.get_link_ips(links[12])],
#         'tx_parts'  : [1,1],
#         'tos'       : 128,
#         'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
#     },
#    'interproj3_5g': {
#         'thru'      : 16,
#         'arrivalGap': 16,
#         'file_type' : 'file',
#         'link'      : links[12],
#         'port'      : 6503,
#         'links'     : [topo.get_link_ips(links[12]),topo.get_link_ips(links[12])],
#         'tx_parts'  : [1,1],
#         'tos'       : 128,
#         'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
#     },
#     'interproj4_5g': {
#         'thru'      : 16,
#         'arrivalGap': 16,
#         'file_type' : 'file',
#         'link'      : links[12],
#         'port'      : 6504,
#         'links'     : [topo.get_link_ips(links[12]),topo.get_link_ips(links[12])],
#         'tx_parts'  : [1,1],
#         'tos'       : 128,
#         'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
#     },
#     'interfile1_5g': {
#         'thru'      : 100,
#         'arrivalGap': 16,
#         'file_type' : 'file',
#         'link'      : links[12],
#         'port'      : 6511,
#         'links'     : [topo.get_link_ips(links[12]),topo.get_link_ips(links[12])],
#         'tx_parts'  : [1,1],
#         'tos'       : 96,
#         'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
#     },
#     'interfile2_5g': {
#         'thru'      : 100,
#         'arrivalGap': 16,
#         'file_type' : 'file',
#         'link'      : links[12],
#         'port'      : 6512,
#         'links'     : [topo.get_link_ips(links[12]),topo.get_link_ips(links[12])],
#         'tx_parts'  : [1,1],
#         'tos'       : 96,
#         'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
#     },
# #     # 'interfile3_5g': {
# #     #     'thru'      : 30,
# #     #     'arrivalGap': 16,
# #     #     'file_type' : 'file',
# #     #     'link'      : links[12],
# #     #     'port'      : 6513,
# #     #     'links'     : [topo.get_link_ips(links[12]),topo.get_link_ips(links[12])],
# #     #     'tx_parts'  : [1,1],
# #     #     'tos'       : 96,
# #     #     'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
# #     # },
# #     # 'interfile4_5g': {
# #     #     'thru'      : 30,
# #     #     'arrivalGap': 16,
# #     #     'file_type' : 'file',
# #     #     'link'      : links[13],
# #     #     'port'      : 6514,
# #     #     'links'     : [topo.get_link_ips(links[13]),topo.get_link_ips(links[13])],
# #     #     'tx_parts'  : [1,1],
# #     #     'tos'       : 96,
# #     #     'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
# #     # },

 #######################################interference_2.4G##############################################
    # 'interproj1_2_4g': {
    #     'thru'      : 5,
    #     'arrivalGap': 16,
    #     'file_type' : 'file',
    #     'link'      : links[14],
    #     'port'      : 6521,
    #     'links'     : [topo.get_link_ips(links[14]),topo.get_link_ips(links[14])],
    #     'tx_parts'  : [1,1],
    #     'tos'       : 128,
    #     'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
    # },
    # 'interproj2_2_4g': {
    #     'thru'      : 12,
    #     'arrivalGap': 16,
    #     'file_type' : 'file',
    #     'link'      : links[14],
    #     'port'      : 6522,
    #     'links'     : [topo.get_link_ips(links[14]),topo.get_link_ips(links[14])],
    #     'tx_parts'  : [1,1],
    #     'tos'       : 128,
    #     'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
    # },
    # 'interfile1_2_4g': {
    #     'thru'      : 10,
    #     'arrivalGap': 16,
    #     'file_type' : 'file',
    #     'link'      : links[14],
    #     'port'      : 6531,
    #     'links'     : [topo.get_link_ips(links[14]),topo.get_link_ips(links[14])],
    #     'tx_parts'  : [1,1],
    #     'tos'       : 96,
    #     'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
    # },
    # 'interfile2_2_4g': {
    #     'thru'      : 10,
    #     'arrivalGap': 16,
    #     'file_type' : 'file',
    #     'link'      : links[14],
    #     'port'      : 6532,
    #     'links'     : [topo.get_link_ips(links[14]),topo.get_link_ips(links[14])],
    #     'tx_parts'  : [1,1],
    #     'tos'       : 96,
    #     'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
    # },
}



logger1 = open(f'dpScript/2024-8-14/TaskAll_{txtIndex}.jsonl', 'w')
logger2 = open(f'dpScript/2024-8-14/Qos_{txtIndex}.jsonl', 'w')
logger1.write("trans_manifests: "+str(trans_manifests)+'\n')
# print(trans_manifests)
# exit()
# logger1.close()
# exit()
# print("link 0 ",topo.get_link_ips(links[0]))

# ================
streams = create_transmission(trans_manifests, topo)
topo.show()
print("trans_manifests: ",trans_manifests)
# exit()
ctrller = ctl.CtlManager()
ctrller.duration = 150
target_ips, name2ipc = ctl.ipcManager.prepare_ipc(topo)
base_info = ctl.graph_qos_collections(topo)


# ###############proj_configure############
# target_ips['wlan0_wlan0_STA4_STA13'] =  ('192.168.3.26', 11112)
# name2ipc['stream://test'] = 'wlan0_wlan0_STA4_STA13'
# base_info['stream://test'] = {
#                                 'type': 'UDP', 
#                                 'npy_file': '0000.npy', 
#                                 'tos': 128, 
#                                 'port': 6204, 
#                                 'throttle': 0, 
#                                 'start_offset': 0, 
#                                 'priority': '', 
#                                 'calc_rtt': True, 
#                                 'no_logging': True, 
#                                 'links': [['192.168.49.107', '192.168.49.1'], ['192.168.3.26', '192.168.3.30']], 
#                                 'tx_parts': [1, 1], 
#                                 'target_rtt': 0.022, 
#                                 'channels': ['5 GHz', '2.4 GHz'], 
#                                 'name': 'stream://test', 
#                                 'duration': [0.0, 1000000.0]
#                             }
# target_ips = target_ips({: ('192.168.3.26', 11112)})
# name2ipc = {'stream://text': 'wlan0_wlan0_STA4_STA13'}
# base_info = {'stream://text': 

# print('base info: ', base_info)


#########interference##################################################################################333
# interList = ["6501@128","6502@128","6503@128","6504@128","6511@96","6512@96","6513@96","6514@96","6521@128","6522@128","6531@96","6532@96"]
# for key in interList:
#     base_info.pop(key, None)
#     name2ipc.pop(key, None)

# target_ips.pop(links[12], None)
# target_ips.pop(links[14], None)
# target_ips.pop(links[13], None)
##############################################################################################################

# print('11111:',name2ipc)
# print('22222:',base_info)
# print('target_ips:',target_ips)
# exit()

# print(1111)

# txIp = "192.168.1.110"
conn = Connector()
control = "STA132"
# monitor_ip = "192.168.3.32:6405"
monitor_ip = "192.168.3.72:6305"
# monitor_ip = "192.168.1.111:6405"
import base64
ips = base64.b64encode( json.dumps(target_ips).encode() ).decode()
command = f"cargo run -- --target-ips={ips} --name2ipc={base64.b64encode( json.dumps(name2ipc).encode() ).decode()} --base-info={base64.b64encode( json.dumps(base_info).encode() ).decode()} --monitor-ip {monitor_ip}"
print(f"cargo run -- --target-ips={ips} --name2ipc={base64.b64encode( json.dumps(name2ipc).encode() ).decode()} --base-info={base64.b64encode( json.dumps(base_info).encode() ).decode()} --monitor-ip {monitor_ip}")
commandfile = open(f'./solver/command.txt', 'w')
commandfile.write(command)
commandfile.close()

# exit()
# ================

# exit()
# conn.batch(control, "control_info", 
#     {
#         "target-ips" : base64.b64encode( json.dumps(target_ips).encode() ).decode(),
#         "name2ipc" : base64.b64encode( json.dumps(name2ipc).encode() ).decode(),
#         "base-info" : base64.b64encode( json.dumps(base_info).encode() ).decode(),
#         "monitor-ip" : monitor_ip,
#     }).wait(0.5).apply()



# exit()
def colors_cal(tempcolors):
    colorlist = []
    for _,vallist in tempcolors.items():
        temp = []
        for colorval in vallist:
            match colorval:
                case "Red": temp.append(1)
                case "Yellow": temp.append(0.5)
                case "Green": temp.append(0)
        # print(max(temp))
        colorlist.append(max(temp))
    return colorlist

def datatransfer():
    print("data transfer")
    import socket
    import scale
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # s.bind(("192.168.3.32",6405))
    s.bind(("192.168.3.72",6305))
    # s.bind(("192.168.1.111",6405))
    import matplotlib.pyplot as plt
    from matplotlib import rcParams
    import numpy as np
    rcParams['font.family'] ='sans-serif'
    rcParams['font.size'] = 16
    task_list = []
    channel_colors = {"2.4G":[0],"5G":[0],"Index":[0]}
    channel_rtts = {}
    rtts = {}
    tx_parts = {}
    TimeIndexlist= {}
    TimeIndex = 0
    fig, axs = plt.subplots(4, 1, figsize=(15, 15))
    plt.ion()
    index = 0
    zeroIndex = 0
    logger1.write(f"No interference: scenery 2; proj_thru {thru};file_thru {filethru}; stream num: {taskNum}"+ '\n')
    # logger1.write(f"inter_thru:{interthru}; inter num: {len(interList)}; inter_tos: {intertos}"+ '\n')
    data_idx = 0
    portlist = ["6212@96","6213@96","6214@96","6215@96","6216@96","6217@96","6218@96","6219@96","6220@96","6221@96","6222@96","6223@96","6224@96","6225@96","6226@96","6227@96","6228@96","6229@96","6230@96","6231@96","6501@128","6502@128","6503@128","6504@128","6511@96","6512@96","6513@96","6514@96","6521@128","6522@128","6531@96","6532@96"]###############################################
    while zeroIndex < 10:
        print('ZEROiNDEX:',zeroIndex)
        data  = s.recvfrom(10240)
        data_idx += 1
        tempcolors = {"2.4G":[],"5G":[]}
        if type(data) == bytes:
            zeroIndex += 1
        elif type(data) == tuple:
            # print("tuple:", data[0],'\n')
            datas = json.loads(data[0].decode("utf-8"))
            logger1.write(json.dumps(datas) + '\n')
            # print("datas",datas)
            if len(datas) == 0:
                zeroIndex += 1
            else:
                for port in portlist:
                    datas.pop(port, None)
                #sort task_name
                sorted(datas)
                #################
                logger2.write(json.dumps(datas) + '\n')
                datasindex = 0
                for task, vals in datas.items():
                    if task not in task_list:
                        task_list.append(task)
                    # print("task",task,vals)
                    if "channel_rtts" not in vals:
                        try:
                            tempcolors["2.4G"].append(vals['channel_colors'][1])
                            tempcolors["5G"].append(vals['channel_colors'][0])
                        except:
                            continue
                    elif "channel_rtts" in vals:
                        # print("task:", task)
                        if datasindex == 0:
                            TimeIndex += 1
                            # print("TimeIndex: ",TimeIndexlist)
                        # print("datasindex:", datasindex)
                        if task not in channel_rtts:
                            channel_rtts[task] = []
                        channel_rtts[task].append(np.array(vals['channel_rtts']) * 1000)
                        if task not in rtts:
                            rtts[task] = []
                        rtts[task].append(np.array(vals['rtt']) * 1000)

                        if task not in tx_parts:
                            tx_parts[task] = []
                        tx_parts[task].append(np.array(vals['tx_parts']))

                        if task not in TimeIndexlist:
                            TimeIndexlist[task] = []
                        TimeIndexlist[task].append(TimeIndex)
                        datasindex += 1
        if tempcolors["2.4G"]:
            color = colors_cal(tempcolors)
            channel_colors["2.4G"].append(color[0])
            channel_colors["5G"].append(color[1])
            channel_colors["Index"].append(TimeIndex)
        # if tempcolors["2.4G"]:
        #     channel_colors["2.4G"].append(tempcolors["2.4G"][0])
        #     channel_colors["5G"].append(tempcolors["5G"][0])
        #     channel_colors["Index"].append(TimeIndex)
                        # print("datasindexList:", datasindexList)
        # exit()
        # labelList = []
        channel_idx = ['5GHz', '2.4GHz']
        color_list = ['b','y','g','k','c','m','r']
        # print("channel rtts",channel_rtts)

        axs[0].cla()
        axs[1].cla()
        axs[2].cla()
        axs[3].cla()
        # Plot channel RTTs
        targetRtt = 22
        for _, (task, c_rtts) in enumerate(channel_rtts.items()):
            task_idx = task_list.index(task)
            c_rtts = np.array(c_rtts).T
            for idx, rtt in enumerate(c_rtts):
                # IdxTimertt1 = range(0,len(rtt),1)
                IdxTimertt1 = TimeIndexlist[task]
                if idx == 0:
                    axs[0].plot(IdxTimertt1,rtt, '-+',color = color_list[task_idx],  label=task + ' channel ' + channel_idx[idx])
                else:
                    axs[0].plot(IdxTimertt1,rtt, ':o',color = color_list[task_idx],  label=task + ' channel ' + channel_idx[idx])
            # if index == 0:
        axs[0].axhline(y=targetRtt, color = 'r',linestyle = '--', label='Target RTT (22ms)')
        axs[0].set_yscale('custom', threshold=50)
        axs[0].grid(linestyle='--')
        axs[0].set_ylabel('Channel RTT (ms)')
        axs[0].set_xlabel('Time (s)')
        axs[0].set_xlim(0, ctrller.duration)
        # axs[0].set_ylim(0, 100)

        
        # # Plot RTTs
        for _idx, (task, rtt) in enumerate(rtts.items()):
            task_idx = task_list.index(task)
            # Idxrtt = range(0,len(rtt),1)
            Idxrtt = TimeIndexlist[task]
            rtt = np.array(rtt)
            axs[1].plot(Idxrtt,rtt, '-+',color=color_list[task_idx], label=task_list[task_idx])
        axs[1].axhline(y=targetRtt, color = 'r',linestyle = '--', label='Target RTT (22ms)')
        axs[1].set_yscale('custom', threshold=60)
        axs[1].grid(linestyle='--')
        axs[1].set_xlim(0, ctrller.duration)
        # axs[1].set_ylim(0, 100)
        # axs[1].set_ylim(0, 60)
        axs[1].set_ylabel('RTT (ms)')
        axs[1].set_xlabel('Time (s)')
        # axs[1].legend(loc = "upper center",bbox_to_anchor=(0.5, 1.1),
        #     ncol=4, fancybox=True, shadow=True)
        
        # # Plot TX Parts
        for idx, (task, tx_part) in enumerate(tx_parts.items()):
            task_idx = task_list.index(task)
            IdxTxPart = TimeIndexlist[task]
            tx_part = np.array(tx_part) * 100
            # axs[2].plot(IdxTxPart,tx_part[:,1].T, '--',color=color_list[task_idx], label=task_list[task_idx])
            # tx_part[:,1] = 100 - tx_part[:, 1]
            tx_part = tx_part.T
            axs[2].plot(IdxTxPart,tx_part[1,:], '-+',color=color_list[task_idx], label=task_list[task_idx])
            

        axs[2].grid(linestyle='--')
        axs[2].set_ylabel('TX Parts')
        axs[2].set(ylim=(0,100))
        axs[2].set_xlim(0, ctrller.duration)
        axs[2].set_xlabel('Time (s)')
        # if index == 0:
        axs[2].legend()

        axs[3].plot(channel_colors["Index"],channel_colors["2.4G"],'--', marker = 'v', color='r', linewidth = 2, label="2.4G")
        axs[3].plot(channel_colors["Index"],channel_colors["5G"],'-',marker = "o", color='g',linewidth = 2, label="5G")
        axs[3].grid(linestyle='--')
        axs[3].set_ylabel('Channel color')
        axs[3].set_yticks([0,0.5,1])
        axs[3].set(ylim=(-0.1,1.1))
        axs[3].set_xlabel('Time (s)')
        axs[3].set_xlim(0, ctrller.duration)
        axs[3].legend()
        plt.tight_layout()
        plt.pause(0.01)
        index += 1
        plt.savefig(f"dpScript/2024-8-14/rtt_{txtIndex}.png")  
    plt.ioff()
    # plt.close()
    

import multiprocessing
def start_comm_process():
    result_queue = multiprocessing.Queue()
    comm_process = multiprocessing.Process(target=ctrller._communication_thread, args=(topo,result_queue,))
    datatransfer_process = multiprocessing.Process(target=datatransfer)
    comm_process.start()
    datatransfer_process.start()
    return result_queue.get()
def fileTransfer(targetIP,filepath):
    portlist = [x for x in range(6205,6205+taskNum)]
    linkList = [links[0]] #######################################
    for linkidx,port in enumerate(portlist):
        print("port: ", port)
        ctl.RxfileTransfer(topo, targetIP,  filepath+"stuttering/", f"../stream-replay/logs/stuttering-{port}.txt" , linkList[linkidx])
        time.sleep(5)
        ctl.fileTransfer(topo, targetIP,  filepath+"rtt/", f"../stream-replay/logs/rtt-{port}*128.txt" , linkList[linkidx])
        time.sleep(5)
    print("file transfer done")


queueResult = start_comm_process()
print("queueResult",queueResult)

sumval = 0
for val in queueResult:
    if 'throughput' in val: 
        sumval += eval(val['throughput'])

print("summation value", sumval)

# exit()

logger1.write("queueResult: "+str(queueResult)+'\n')



# exit()


time.sleep(5)
targetIP = monitor_ip.split(":")[0]
filepath = "dpScript/2024-8-14/"       #############################################
fileTransfer(targetIP,filepath) 
import read_txt as rt

taskList = []
taskRttlist = {}
Stutteringlist = {}
jsonlfilename = filepath+f"Qos_{txtIndex}.jsonl"
for idxstream in range(txtIndex,txtIndex+taskNum):
    taskList.append(f"output{idxstream}.txt")
for txtName in taskList:
    temptxtName = filepath+ 'rtt/' + txtName
    tempstutteringfileName = filepath + "stuttering/" + txtName
    if os.path.exists(temptxtName):
        rt.delLastLine(temptxtName)
        port,temprttArray = rt.txtRead_multiChannel_port(temptxtName)
        taskRttlist[port] = temprttArray
    if os.path.exists(tempstutteringfileName):
        port,NA_stuttering,Ada_stuttering,stuttering_gain = rt.Stuttering_cal(filename=tempstutteringfileName)
        Stutteringlist[port] = [NA_stuttering,Ada_stuttering,stuttering_gain]
rt.plot_rtt_stuttering(temptxtName,taskRttlist,Stutteringlist,part = 0.4)
rt.plot_json(jsonlfilename)


