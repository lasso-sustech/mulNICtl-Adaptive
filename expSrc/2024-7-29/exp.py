
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
        'links'     : [topo.get_link_ips(links[0]),topo.get_link_ips(links[1])],
        'tx_parts'  : [0,0],
        'tos'       : 128,
        'channels'  : [constHead.CHANNEL0, constHead.CHANNEL1],
    }
}

# print("link 0 ",topo.get_link_ips(links[0]))
# ================
streams = create_transmission(trans_manifests, topo)
# ================

topo.show()

ctrller = ctl.CtlManager()
target_ips, name2ipc = ctl.ipcManager.prepare_ipc(topo)
base_info = ctl.graph_qos_collections(topo)



# print(1111)

# txIp = "192.168.1.110"
conn = Connector()
control = "STA132"
monitor_ip = "192.168.1.111:6405"
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

import multiprocessing
def start_comm_process():
    result_queue = multiprocessing.Queue()
    comm_process = multiprocessing.Process(target=ctrller._communication_thread, args=(topo,result_queue,))
    comm_process.start()
    # return result_queue.get()

start_comm_process()

import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("192.168.1.111",6405))


import matplotlib.pyplot as plt
from matplotlib import rcParams
import numpy as np
rcParams['font.family'] ='sans-serif'
# rcParams['font.sans-serif'] = ['Arial']
rcParams['font.size'] = 16
channel_rtts = {}
rtts = {}
tx_parts = {}
outage_rates = {}
fig, axs = plt.subplots(2, 1, figsize=(20, 20))
plt.ion()
logger = open(f'dpScript/2024-7-29/test.jsonl', 'w')
index = 0
while True:
    data  = s.recvfrom(1024)
    if type(data) == bytes:
        continue
    elif type(data) == tuple:
        datas = json.loads(data[0].decode("utf-8"))
        if len(datas) == 0:
            continue
        else:
            for task, vals in datas.items():
                # print("task",task,vals)
                if "channel_rtts" not in vals:
                    continue
                else:
                    if task not in channel_rtts:
                        channel_rtts[task] = []
                    channel_rtts[task].append(np.array(vals['channel_rtts']) * 1000)

                    if task not in tx_parts:
                        tx_parts[task] = []
                    tx_parts[task].append(np.array(vals['tx_parts']))

    task_list = ["6206"]
    channel_idx = ['2.4GHz', '5GHz']
    color_list = ['r','b','y','g','k','c','m','w']
    print("channel rtts",channel_rtts)


    # Plot channel RTTs
    for task_idx, (task, c_rtts) in enumerate(channel_rtts.items()):
        c_rtts = np.array(c_rtts).T
        print("crtts",c_rtts)
        for idx, rtt in enumerate(c_rtts):
            print("rtt:",rtt)
            IdxTimertt1 = range(0,len(rtt)*2,2)
            line1 = axs[0].plot(IdxTimertt1,rtt, '-+',  label=task + ' channel ' + channel_idx[idx])
    
    # axs[0].set_yscale('custom', threshold=40)
    axs[0].grid(linestyle='--')
    axs[0].set_ylabel('Channel RTT (ms)')
    axs[0].set_xlabel('Time (s)')
    if index == 0:
        axs[0].legend(loc = "upper center",bbox_to_anchor=(0.5, 1.1),
            ncol=4, fancybox=True, shadow=True)
   


    
    # targetRtt = 22
    # # Plot RTTs
    
    # for task_idx, (task, rtt) in enumerate(rtts.items()):
    #     rtt = np.array(rtt)
    #     axs[1].plot(rtt, '-+',color=color_list[task_idx], label=task_list[task_idx]+"avg RTT: %.2f"%np.mean(rtt[5:]))
    # axs[1].set_yscale('custom', threshold=40)
    # axs[1].grid(linestyle='--')
    # # axs[1].set_xlim(0, 25)
    # axs[1].set_ylabel('RTT (ms)')
    # axs[1].set_xlabel('Time (s)')
    # axs[1].legend(loc = "upper center",bbox_to_anchor=(0.5, 1.1),
    #       ncol=4, fancybox=True, shadow=True)

    
    # # Plot TX Parts
    for task_idx, (task, tx_part) in enumerate(tx_parts.items()):
        tx_part = np.array(tx_part) * 100
        tx_part[:,1] = 100 - tx_part[:, 1]
        tx_part = tx_part.T
        line2 = axs[1].plot(tx_part[1,:], '-+',color=color_list[task_idx], label=task_list[task_idx])

    axs[1].grid(linestyle='--')
    axs[1].set_ylabel('TX Parts')
    axs[1].set(ylim=(0,100))
    axs[1].set_xlabel('Time (s)')
    if index == 0:
        axs[1].legend()
    

    # Save the combined plot
    plt.tight_layout()
    plt.pause(0.5)
    plt.ioff()
    index += 1
    # plt.clf()
    # line1.remove()
    # line2.remove()
    
    # print(data)



