
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

fileList = os.listdir('dpScript/2024-7-30/experiment2/')
txtIndex = 0
tempTxtName = f'output{txtIndex}.txt'
while tempTxtName in fileList:
    txtIndex += 1
    tempTxtName = f'output{txtIndex}.txt'

topo        = construct_graph("./config/topo/2024-7-30.txt")
ip_table    = ctl._ip_extract_all(topo)
ctl._ip_associate(topo, ip_table)

taskNum = 1
thru = 16
interthru = 80
links       = topo.get_links()
fthru       = 600   # Mbps
pthru       = 50    # Mbps
ithru       = 30   # Mbps
intertos = 96

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
trans_manifests = {
    'file1': {
        'thru'      : thru,
        'file_type' : 'proj',

        'link'      : links[0],
        'port'      : 6205,
        'links'     : [topo.get_link_ips(links[0]),topo.get_link_ips(links[1])],
        'tx_parts'  : [0,0],
        'tos'       : 128,
        'channels'  : [constHead.CHANNEL1, constHead.CHANNEL0],
    },
    'file2': {
        'thru'      : thru,
        'file_type' : 'proj',

        'link'      : links[2],
        'port'      : 6206,
        'links'     : [topo.get_link_ips(links[2]),topo.get_link_ips(links[3])],
        'tx_parts'  : [0,0],
        'tos'       : 128,
        'channels'  : [constHead.CHANNEL1, constHead.CHANNEL0],
    },
    'file3': {
        'thru'      : thru,
        'file_type' : 'proj',
        'link'      : links[0],
        'port'      : 6207,
        'links'     : [topo.get_link_ips(links[0]),topo.get_link_ips(links[1])],
        'tx_parts'  : [0,0],
        'tos'       : 128,
        'channels'  : [constHead.CHANNEL1, constHead.CHANNEL0],
    },
    'file4': {
        'thru'      : thru,
        'file_type' : 'proj',

        'link'      : links[2],
        'port'      : 6208,
        'links'     : [topo.get_link_ips(links[2]),topo.get_link_ips(links[3])],
        'tx_parts'  : [0,0],
        'tos'       : 128,
        'channels'  : [constHead.CHANNEL1, constHead.CHANNEL0],
    },
    'file5': {
        'thru'      : interthru,
        'file_type' : 'file',

        'link'      : links[4],
        'port'      : 6209,
        'links'     : [topo.get_link_ips(links[5])],
        'tx_parts'  : [0],
        'tos'       : intertos,
        'channels'  : [constHead.CHANNEL0],
    },
    'file6': {
        'thru'      : interthru,
        'file_type' : 'file',

        'link'      : links[4],
        'port'      : 6210,
        'links'     : [topo.get_link_ips(links[5])],
        'tx_parts'  : [0],
        'tos'       : intertos,
        'channels'  : [constHead.CHANNEL0],
    },
    'file7': {
        'thru'      : interthru,
        'file_type' : 'file',

        'link'      : links[6],
        'port'      : 6211,
        'links'     : [topo.get_link_ips(links[7])],
        'tx_parts'  : [0],
        'tos'       : intertos,
        'channels'  : [constHead.CHANNEL0],
    },
    'file8': {
        'thru'      : interthru,
        'file_type' : 'file',

        'link'      : links[6],
        'port'      : 6212,
        'links'     : [topo.get_link_ips(links[7])],
        'tx_parts'  : [0],
        'tos'       : intertos,
        'channels'  : [constHead.CHANNEL0],
    },
}
##### s3 : inter
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
#         'link'      : links[4],
#         'port'      : 6207,
#         'links'     : [topo.get_link_ips(links[4]),topo.get_link_ips(links[5])],
#         'tx_parts'  : [0,0],
#         'tos'       : 128,
#         'channels'  : [constHead.CHANNEL0, constHead.CHANNEL1],
#     },
#     'file4': {
#         'thru'      : thru,
#         'file_type' : 'proj',

#         'link'      : links[6],
#         'port'      : 6208,
#         'links'     : [topo.get_link_ips(links[6]),topo.get_link_ips(links[7])],
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




# print("link 0 ",topo.get_link_ips(links[0]))
# ================
streams = create_transmission(trans_manifests, topo)
# ================

topo.show()

ctrller = ctl.CtlManager()
ctrller.duration = 70
target_ips, name2ipc = ctl.ipcManager.prepare_ipc(topo)
base_info = ctl.graph_qos_collections(topo)
interList = [f'{x}@96' for x in range(6209,6213)]
for key in interList:
    base_info.pop(key)
    name2ipc.pop(key)
    target_ips.popitem()


# exit()

# print(1111)

# txIp = "192.168.1.110"
conn = Connector()
control = "STA132"
monitor_ip = "192.168.3.72:6405"
# monitor_ip = "192.168.1.111:6405"
import base64

ips = base64.b64encode( json.dumps(target_ips).encode() ).decode()
# print(f"cargo run -- --target-ips={ips} --name2ipc={base64.b64encode( json.dumps(name2ipc).encode() ).decode()} --base-info={base64.b64encode( json.dumps(base_info).encode() ).decode()} --monitor-ip {monitor_ip}")



conn.batch(control, "control_info", 
        {
            "target-ips" : base64.b64encode( json.dumps(target_ips).encode() ).decode(),
            "name2ipc" : base64.b64encode( json.dumps(name2ipc).encode() ).decode(),
            "base-info" : base64.b64encode( json.dumps(base_info).encode() ).decode(),
            "monitor-ip" : monitor_ip,
        }).wait(0.5).apply()




logger1 = open(f'dpScript/2024-7-30/experiment2/TaskAll_{txtIndex}.jsonl', 'w')
def datatransfer():
    print("data transfer")
    import socket
    import scale
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("192.168.3.72",6405))
    # s.bind(("192.168.1.111",6405))
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
    fig, axs = plt.subplots(3, 1, figsize=(20, 20))
    plt.ion()
    index = 0
    zeroIndex = 0
    logger1.write(f"interference: scenery 1; thru {thru}; stream num: {taskNum}"+ '\n')
    logger1.write(f"inter_thru:{interthru}; inter num: {len(interList)}; inter_tos: {intertos}"+ '\n')
    logger2 = open(f'dpScript/2024-7-30/experiment2/Qos_{txtIndex}.jsonl', 'w')
    while zeroIndex < ctrller.duration +20:
        data  = s.recvfrom(10240)
        # print("data",data,'\n')
        if type(data) == bytes:
            zeroIndex += 1
        elif type(data) == tuple:
            print("tuple:", data[0],'\n')
            datas = json.loads(data[0].decode("utf-8"))
            logger1.write(json.dumps(datas) + '\n')
            # print("datas",datas)
            if len(datas) == 0:
                zeroIndex += 1
                # continue
            else:
                logger2.write(json.dumps(datas) + '\n')
                datasindex = 0
                for task, vals in datas.items():
                    if task not in task_list:
                        task_list.append(task)
                    # print("task",task,vals)
                    if "channel_rtts" not in vals:
                        continue
                    else:
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
                        # print("TimeIndexlist",TimeIndexlist)
                        if datasindex == 0:
                            TimeIndex += 1
                        datasindex += 1
        # labelList = []
        channel_idx = ['2.4GHz', '5GHz']
        color_list = ['b','y','g','k','c','m','w','r']
        # print("channel rtts",channel_rtts)


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
        axs[0].set_yscale('custom', threshold=40)
        axs[0].grid(linestyle='--')
        axs[0].set_ylabel('Channel RTT (ms)')
        axs[0].set_xlabel('Time (s)')
        axs[0].set_xlim(0, ctrller.duration)
        # if index == 2:
        #     axs[0].legend(loc = "upper center",bbox_to_anchor=(0.5, 1.1),
        #         ncol=4, fancybox=True, shadow=True)
    


        
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
        axs[1].set_yscale('custom', threshold=40)
        axs[1].grid(linestyle='--')
        axs[1].set_xlim(0, ctrller.duration)
        axs[1].set_ylabel('RTT (ms)')
        axs[1].set_xlabel('Time (s)')
        # if index ==2:
        #     axs[1].legend(loc = "upper center",bbox_to_anchor=(0.5, 1.1),
        #         ncol=4, fancybox=True, shadow=True)

        
        # # Plot TX Parts
        for idx, (task, tx_part) in enumerate(tx_parts.items()):
            task_idx = task_list.index(task)
            IdxTxPart = TimeIndexlist[task]
            tx_part = np.array(tx_part) * 100
            # axs[2].plot(IdxTxPart,tx_part[:,1].T, '--',color=color_list[task_idx], label=task_list[task_idx])
            tx_part[:,1] = 100 - tx_part[:, 1]
            tx_part = tx_part.T
            axs[2].plot(IdxTxPart,tx_part[1,:], '-+',color=color_list[task_idx], label=task_list[task_idx])
            

        axs[2].grid(linestyle='--')
        axs[2].set_ylabel('TX Parts')
        axs[2].set(ylim=(0,100))
        axs[2].set_xlim(0, ctrller.duration)
        axs[2].set_xlabel('Time (s)')
        if index == 1:
            axs[2].legend()
        plt.tight_layout()
        plt.pause(0.5)
        plt.ioff()
        index += 1
        plt.savefig(f"dpScript/2024-7-30/experiment2/rtt_{txtIndex}.png")  
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
    for port in portlist:
        ctl.fileTransfer(topo, targetIP,  filepath, f"../stream-replay/logs/rtt-{port}*128.txt" , links[0])
        time.sleep(5)
    print("file transfer done")


# logger1 = open(f'dpScript/2024-7-30/experiment1/TaskAll_{txtIndex}.jsonl', 'w')
queueResult = start_comm_process()
print("queueResult",queueResult)
logger1.write(json.dumps(queueResult)+'\n')
logger1.write("queueResult: "+str(queueResult)+'\n')

time.sleep(10)
targetIP = monitor_ip.split(":")[0]
filepath = "dpScript/2024-7-30/experiment2/"
fileTransfer(targetIP,filepath) 
txtfileName = filepath + f"output{txtIndex}.txt"
print("filename: ", txtfileName)
import read_txt as rt

taskList = []
taskRttlist = {}
for idxstream in range(txtIndex,txtIndex+taskNum):
    taskList.append(f"output{idxstream}.txt")
for txtName in taskList:
    temptxtName = filepath + txtName
    if os.path.exists(temptxtName):
        rt.delLastLine(temptxtName)
        port,temprttArray = rt.txtRead_multiChannel_port(temptxtName)
        taskRttlist[port] = temprttArray
print("filename:", temptxtName.split('.txt')[0])
rt.rttArrayDictPlot_cdf(temptxtName,taskRttlist)
# rt.rttArrayDictPlot_cdf(temptxtName,taskRttlist,index=1000)


# time.sleep(ctrller.duration)



