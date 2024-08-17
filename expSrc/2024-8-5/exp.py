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
#############################################################
        # conn.batch(sender, "create_file", {"thru": trans_manifest['thru'], "arrivalGap": arrivalGap, "name": f'{name}.npy', "num": 20000}).wait(0.5).apply()
        
        temp        = stream.stream()
        file_type   = trans_manifest['file_type']
        if file_type == 'file':
            conn.batch(sender, "create_file", {"thru": trans_manifest['thru'], "arrivalGap": arrivalGap, "name": f'{name}.npy', "num": 20000}).wait(0.5).apply()
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
        temp.throttle   = trans_manifest['thru'] + 30
        
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


fileList = os.listdir('dpScript/2024-8-5/rtt/')
txtIndex = 0
tempTxtName = f'output{txtIndex}.txt'
while tempTxtName in fileList:
    txtIndex += 1
    tempTxtName = f'output{txtIndex}.txt'

topo,links        = construct_graph("./config/topo/2024-8-5.txt")
# print("topo: ", topo)
ip_table    = ctl._ip_extract_all(topo)
ctl._ip_associate(topo, ip_table)

taskNum = 4
thru = 16
filethru = 100
interthru = 80
# links       = topo.get_links()
# print('links: ', links)
pthru       = 50    # Mbps
ithru       = 30   # Mbps
intertos = 96


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
    '0804testvideo16_1': {

        'thru'      : thru,
        'file_type' : 'proj',
        'link'      : links[0],
        'port'      : 6205,
        'links'     : [topo.get_link_ips(links[1]),topo.get_link_ips(links[0])],
        'tx_parts'  : [1,1],
        'tos'       : 128,
        'channels'  : [constHead.CHANNEL0, constHead.CHANNEL1],
    },
    '0804testvideo16_2': {

        'thru'      : thru,
        'file_type' : 'proj',
        'link'      : links[2],
        'port'      : 6206,
        'links'     : [topo.get_link_ips(links[3]),topo.get_link_ips(links[2])],
        'tx_parts'  : [1,1],
        'tos'       : 128,
        'channels'  : [constHead.CHANNEL0, constHead.CHANNEL1],
    },
    '0804testvideo16_3': {

        'thru'      : thru,
        'file_type' : 'proj',
        'link'      : links[4],
        'port'      : 6207,
        'links'     : [topo.get_link_ips(links[5]),topo.get_link_ips(links[4])],
        'tx_parts'  : [1,1],
        'tos'       : 128,
        'channels'  : [constHead.CHANNEL0, constHead.CHANNEL1],
    },
    '0804testvideo16_4': {

        'thru'      : thru,
        'file_type' : 'proj',
        'link'      : links[6],
        'port'      : 6208,
        'links'     : [topo.get_link_ips(links[7]),topo.get_link_ips(links[6])],
        'tx_parts'  : [1,1],
        'tos'       : 128,
        'channels'  : [constHead.CHANNEL0, constHead.CHANNEL1],
    },
    # '0804testfile_1': {

    #     'thru'      : 100,
    #     'file_type' : 'file',
    #     'link'      : links[18],
    #     'port'      : 6209,
    #     'links'     : [topo.get_link_ips(links[19]),topo.get_link_ips(links[18])],
    #     'tx_parts'  : [1,1],
    #     'tos'       : 96,
    #     'channels'  : [constHead.CHANNEL0, constHead.CHANNEL1],
    # },
    # '0804testfile_2': {

    #     'thru'      : 100,
    #     'file_type' : 'file',
    #     'link'      : links[18],
    #     'port'      : 6210,
    #     'links'     : [topo.get_link_ips(links[19]),topo.get_link_ips(links[18])],
    #     'tx_parts'  : [1,1],
    #     'tos'       : 96,
    #     'channels'  : [constHead.CHANNEL0, constHead.CHANNEL1],
    # },
    # '0804testfile100_3': {

    #     'thru'      : 100,
    #     'file_type' : 'proj',
    #     'link'      : links[4],
    #     'port'      : 6211,
    #     'links'     : [topo.get_link_ips(links[5]),topo.get_link_ips(links[4])],
    #     'tx_parts'  : [1,1],
    #     'tos'       : 96,
    #     'channels'  : [constHead.CHANNEL0, constHead.CHANNEL1],
    # },
    # '0804testfile100_4': {

    #     'thru'      : 100,
    #     'file_type' : 'proj',
    #     'link'      : links[4],
    #     'port'      : 6212,
    #     'links'     : [topo.get_link_ips(links[5]),topo.get_link_ips(links[4])],
    #     'tx_parts'  : [1,1],
    #     'tos'       : 96,
    #     'channels'  : [constHead.CHANNEL0, constHead.CHANNEL1],
    # },
    # 'file2': {
    #     'thru'      : thru,
    #     'file_type' : 'proj',
    #     'link'      : links[2],
    #     'port'      : 6206,
    #     'links'     : [topo.get_link_ips(links[3]),topo.get_link_ips(links[2])],
    #     'tx_parts'  : [1,1],
    #     'tos'       : 128,
    #     'channels'  : [constHead.CHANNEL0, constHead.CHANNEL1],
    # },

    # 'file3': {
    #     'thru'      : thru,
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
    #     'file_type' : 'proj',
    #     'link'      : links[6],
    #     'port'      : 6208,
    #     'links'     : [topo.get_link_ips(links[7]),topo.get_link_ips(links[6])],
    #     'tx_parts'  : [1,1],
    #     'tos'       : 128,
    #     'channels'  : [constHead.CHANNEL0,constHead.CHANNEL1],
    # },
    # 'file5': {
    #     'thru'      : filethru,
    #     'file_type' : 'file',
    #     'link'      : links[8],
    #     'port'      : 6209,
    #     'links'     : [topo.get_link_ips(links[9])],
    #     'tx_parts'  : [1],
    #     'tos'       : intertos,
    #     'channels'  : [constHead.CHANNEL0],
    # },
    # 'file6': {
    #     'thru'      : filethru,
    #     'file_type' : 'file',
    #     'link'      : links[10],
    #     'port'      : 6210,
    #     'links'     : [topo.get_link_ips(links[11])],
    #     'tx_parts'  : [1],
    #     'tos'       : intertos,
    #     'channels'  : [constHead.CHANNEL0],
    # },
}



logger1 = open(f'dpScript/2024-8-5/TaskAll_{txtIndex}.jsonl', 'w')
logger2 = open(f'dpScript/2024-8-5/Qos_{txtIndex}.jsonl', 'w')
logger1.write("trans_manifests: "+str(trans_manifests)+'\n')
print(trans_manifests)
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
ctrller.duration = 100
target_ips, name2ipc = ctl.ipcManager.prepare_ipc(topo)
base_info = ctl.graph_qos_collections(topo)

#########interference
# interList = [f'{x}@96' for x in range(6211,6214)]
# for key in interList:
#     base_info.pop(key, None)
#     name2ipc.pop(key, None)
    # target_ips.popitem()

# target_ips.pop('wlan0_wlan0_STA3_STA4', None)

# print(target_ips)
# exit()

# print(1111)

# txIp = "192.168.1.110"
conn = Connector()
control = "STA132"
# monitor_ip = "192.168.3.72:6405"
monitor_ip = "192.168.3.72:6405"
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

def datatransfer():
    print("data transfer")
    import socket
    import scale
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # s.bind(("192.168.3.72",6405))
    s.bind(("192.168.3.72",6405))
    import matplotlib.pyplot as plt
    from matplotlib import rcParams
    import numpy as np
    rcParams['font.family'] ='sans-serif'
    rcParams['font.size'] = 16
    task_list = []
    channel_rtts = {}
    rtts = {}
    tx_parts = {}
    TimeIndexlist= {}
    TimeIndex = 0
    fig, axs = plt.subplots(3, 1, figsize=(15, 15))
    plt.ion()
    index = 0
    zeroIndex = 0
    logger1.write(f"No interference: scenery 2; proj_thru {thru};file_thru {filethru}; stream num: {taskNum}"+ '\n')
    # logger1.write(f"inter_thru:{interthru}; inter num: {len(interList)}; inter_tos: {intertos}"+ '\n')
    data_idx = 0
    portlist = ["6209@96","6210@96","6211@96","6212@96"]###############################################
    while zeroIndex < 10:
        print('ZEROiNDEX:',zeroIndex)
        data  = s.recvfrom(10240)
        data_idx += 1

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
                logger2.write(json.dumps(datas) + '\n')
                datasindex = 0
                for task, vals in datas.items():
                    if task not in task_list:
                        task_list.append(task)
                    # print("task",task,vals)
                    if "channel_rtts" not in vals:
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
                
                        # print("datasindexList:", datasindexList)
        # exit()
        # labelList = []
        channel_idx = ['2.4GHz', '5GHz']
        color_list = ['b','y','g','k','c','m','w','r']
        # print("channel rtts",channel_rtts)

        axs[0].cla()
        axs[1].cla()
        axs[2].cla()
        # Plot channel RTTs
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
            #     axs[0].legend(loc = "upper center",bbox_to_anchor=(0.5, 1.1),
            #         ncol=4, fancybox=True, shadow=True)
        axs[0].set_yscale('custom', threshold=60)
        axs[0].grid(linestyle='--')
        axs[0].set_ylabel('Channel RTT (ms)')
        axs[0].set_xlabel('Time (s)')
        axs[0].set_xlim(0, ctrller.duration)
        # if index == 2:
        # axs[0].legend(loc = "upper center",bbox_to_anchor=(0.5, 1.1),
        #     ncol=4, fancybox=True, shadow=True)
    

        targetRtt = 22
        # # Plot RTTs
        for _idx, (task, rtt) in enumerate(rtts.items()):
            task_idx = task_list.index(task)
            # Idxrtt = range(0,len(rtt),1)
            Idxrtt = TimeIndexlist[task]
            rtt = np.array(rtt)
            axs[1].plot(Idxrtt,rtt, '-+',color=color_list[task_idx], label=task_list[task_idx])
        if index == 0:
            axs[1].axhline(y=targetRtt, color = 'r',linestyle = '--', label='Target RTT (22ms)')
        else:
            axs[1].axhline(y=targetRtt, color = 'r',linestyle = '--')
        axs[1].set_yscale('custom', threshold=60)
        axs[1].grid(linestyle='--')
        axs[1].set_xlim(0, ctrller.duration)
        # axs[1].set_ylim(0, 60)
        axs[1].set_ylabel('RTT (ms)')
        axs[1].set_xlabel('Time (s)')
        
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
        plt.tight_layout()
        plt.pause(0.01)
        index += 1
        plt.savefig(f"dpScript/2024-8-5/rtt_{txtIndex}.png")  
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
    linkList = [links[0], links[2], links[4],links[6]] #######################################
    for linkidx,port in enumerate(portlist):
        print("port: ", port)
        ctl.RxfileTransfer(topo, targetIP,  filepath+"stuttering/", f"../stream-replay/logs/stuttering-{port}.txt" , linkList[linkidx])
        time.sleep(5)
        ctl.fileTransfer(topo, targetIP,  filepath+"rtt/", f"../stream-replay/logs/rtt-{port}*128.txt" , linkList[linkidx])
        time.sleep(5)
    print("file transfer done")


queueResult = start_comm_process()
print("queueResult",queueResult)
logger1.write("queueResult: "+str(queueResult)+'\n')



# exit()


time.sleep(5)
targetIP = monitor_ip.split(":")[0]
filepath = "dpScript/2024-8-5/"       #############################################
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


