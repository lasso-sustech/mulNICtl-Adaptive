from tap import Connector
from util.trans_graph import LINK_NAME_TO_TX_NAME
import util.ctl as ctl
from tools.read_graph import construct_graph
from util.solver import channelBalanceSolver
from util import stream
from typing import List
from schema import Schema, And, Use, Optional, Or
import os, json

PARSESINGLEIPDEVICE = lambda x: [x, x]

element_schema = Schema({
    str: {
        'thru': int,
        'link': str,
        'port': int,
        'file_type': Or('file', 'proj'),
        'ip_addrs': list[str],    
    }
})

target_schema = Schema({
    'file'          : Or(element_schema, None),
    'proj'          : Or(element_schema, None),
    'interference'  : Or(element_schema, None),
})

def create_logger_file(filename:str):
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    f = open(filename, 'w')
    f.write('[')
    return f

def create_transmission(trans_manifests, arrivalGap = 16):
    for name in trans_manifests:
        trans_manifest = trans_manifests[name]
        conn = Connector()
        sender = LINK_NAME_TO_TX_NAME(trans_manifest['link'])
        file_name = f'{name}.npy'
        print(f"Creating transmission file {file_name} with {trans_manifest['thru']} at {sender}")
        conn.batch(sender, "create_file", {"thru": trans_manifest['thru'], "arrivalGap": arrivalGap, "name": f'{name}.npy', "num": 20000}).wait(0.5).apply()
        
        temp = stream.stream()
        file_type = trans_manifest['file_type']
        if file_type == 'file':
            temp = temp.read_from_manifest('./config/stream/file.json')
        else:
            temp = temp.read_from_manifest('./config/stream/proj.json')
            temp.calc_rtt = True
            
        temp.npy_file = file_name
        temp.tx_ipaddrs = trans_manifest['ip_addrs']; 
        temp.tx_parts = [1, 1]; 
        temp.port = trans_manifest['port']
        topo.ADD_STREAM(trans_manifest['link'], temp, target_rtt=16)

f = create_logger_file('expSrc/2024-4-29/experiment4/exp-result.json')
topo    = construct_graph("./config/topo/interference_graph.txt") # Graph
links   = topo.get_links()

arrivalGap  = 16 #ms
fthru       = 600 #Mbps
pthru       = 600 #Mbps
ithru       = 100 #Mbps

for fthru in range(600, 300, -50):
    trans_manifests = {
        'file': {
            'thru': fthru,
            'link': links[0],
            'port': 6203,
            'file_type': 'file',
            'ip_addrs': PARSESINGLEIPDEVICE('127.0.0.1'),
        },
        'proj': {
            'thru': pthru,
            'link': links[1],
            'port': 6204,
            'file_type': 'file',
            'ip_addrs': PARSESINGLEIPDEVICE('127.0.0.1'),
        },
        'interference': {
            'thru': ithru,
            'link': links[2],
            'port': 6205,
            'file_type': 'proj',
            'ip_addrs': PARSESINGLEIPDEVICE('127.0.0.1'),
        }
        
    }
    trans_manifests = element_schema.validate(trans_manifests)
        
    ip_table = ctl._ip_extract_all(topo)
    ctl._ip_associate(topo, ip_table)

    create_transmission(trans_manifests, arrivalGap)
    topo.show()

    ctl.create_tx_manifest(topo)
    ctl.validate_ip_addr(topo)
    conn = ctl.start_transmission(graph=topo, DURATION = 10)
    res = ctl.read_thu(conn)
    rtts = ctl.read_rtt(topo)
    print(res)

    for rtt in rtts[:-1]:
        rtt_return = rtt.to_dict(); rtt_return.update(trans_manifests)
        f.write(json.dumps(rtt_return, indent=2))
        f.write(',\n')
    rtt_return = rtts[-1].to_dict(); rtt_return.update(trans_manifests)
    f.write(json.dumps(rtt_return, indent=2))
    f.flush()
f.write(']')

