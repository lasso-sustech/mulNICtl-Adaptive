from tap import Connector
from util.trans_graph import LINK_NAME_TO_TX_NAME
import util.ctl as ctl
from tools.read_graph import construct_graph
from util.solver import channelBalanceSolver, channelSwitchSolver
from util import stream
from typing import List
from schema import Schema, And, Use, Optional, Or
import os, json

import util.constHead as constHead

PARSESINGLEIPDEVICE = lambda x: [x, x]

S2MS_LIST = lambda x: [i * 1000 for i in x]

element_schema = Schema({
    'thru': int,
    'link': str,
    'port': int,
    'file_type': Or('file', 'proj'),
    'ip_addrs': list[str], 
})

target_schema = Schema({
    'file'          : Or(element_schema, None),
    'proj'          : Or(element_schema, None),
    'interference'  : Or(element_schema, None),
    'interference2' : Or(element_schema, None),
})

TARGET_RTT = 16

def create_logger_file(filename:str):
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    f = open(filename, 'w')
    f.write('[')
    return f

def create_transmission(trans_manifests, arrivalGap = 16):
    proj_stream = None
    for name in trans_manifests:
        trans_manifest = trans_manifests[name]
        if trans_manifest is None:
            continue
        conn = Connector()
        sender = LINK_NAME_TO_TX_NAME(trans_manifest['link'])
        file_name = f'{name}.npy'
        print(f"Creating transmission file {file_name} with {trans_manifest['thru']} at {sender}")
        conn.batch(sender, "create_file", {"thru": trans_manifest['thru'], "arrivalGap": arrivalGap, "name": f'{name}.npy', "num": 20000}).wait(0.5).apply()
        
        temp = stream.stream()
        file_type = trans_manifest['file_type']
        if file_type == 'file':
            temp = temp.read_from_manifest('./config/stream/file.json')
            temp.tos = 128
        else:
            temp = temp.read_from_manifest('./config/stream/proj.json')
            temp.calc_rtt = True
            
        temp.npy_file = file_name
        temp.tx_ipaddrs = trans_manifest['ip_addrs']; 
        temp.tx_parts = [0.8, 0.8]; 
        temp.port = trans_manifest['port']
        topo.ADD_STREAM(trans_manifest['link'], temp, target_rtt=TARGET_RTT)
        
        if name == 'proj':
            proj_stream = temp
    return proj_stream

def log_write(f, res, rtts, tx_parts):
    f.write(',\n')
    if res:
        for _res in res:
            if _res:
                f.write(json.dumps(_res, indent=2))
                f.write(',\n')
                
    f.write(json.dumps({'tx_parts': tx_parts}, indent=2))
    f.write(',\n')       
    
    for rtt in rtts[:-1]:
        rtt_return = rtt.to_dict(); rtt_return.update(trans_manifests)
        f.write(json.dumps(rtt_return, indent=2))
        f.write(',\n')
    
    rtt_return = rtts[-1].to_dict(); rtt_return.update(trans_manifests)
    f.write(json.dumps(rtt_return, indent=2))
    f.flush()
    
f       = create_logger_file('expSrc/2024-5-5/experiment2/exp-result.json')
topo    = construct_graph("./config/topo/2024-5-5.txt") # Graph
links   = topo.get_links()

arrivalGap  = 16    #ms
fthru       = 600   #Mbps
pthru       = 50    #Mbps
ithru       = 470   #Mbps

channel_switch_solver   = channelSwitchSolver(TARGET_RTT)
channel_switch_solver.switch_state = constHead.MUL_CHAN
channel_switch_solver.islog = True
channel_balance_solver  = channelBalanceSolver()

trans_manifests = {
    'file': None,
    'proj': {
        'thru': pthru,
        'link': links[1],
        'port': 6204,
        'file_type': 'proj',
        'ip_addrs': ['192.168.3.27', '192.168.3.29'],
    },
    'interference': {
        'thru': ithru,
        'link': links[2],
        'port': 6205,
        'file_type': 'file',
        'ip_addrs': PARSESINGLEIPDEVICE('192.168.3.18'),
    },
    'interference2': None
}
trans_manifests = target_schema.validate(trans_manifests)

ip_table = ctl._ip_extract_all(topo)
ctl._ip_associate(topo, ip_table)

proj_stream = create_transmission(trans_manifests, arrivalGap)
assert proj_stream is not None

channel_balance_solver.update_tx_parts(proj_stream.tx_parts)

topo.show()
# ctl.write_remote_stream(topo)
# ctl.validate_ip_addr(topo)

test_state = True

for test in range(0, 10):
    
    print(proj_stream.tx_parts)
    ctl.create_tx_manifest(topo)
    ctl.validate_ip_addr(topo)
    conn    = ctl.start_transmission(graph=topo, DURATION = 15)
    res     = ctl.read_thu(conn)
    rtts    = ctl.read_rtt(topo)
    
    log_write(f, res, rtts, proj_stream.tx_parts)
    channel_balance_solver.update( rtts[0] )
    
    print(S2MS_LIST(channel_balance_solver.correct_channel_rtt()))
    
    ## Control Part
    if test >= 1:
        try:
            res = channel_switch_solver.switch(
                channel_balance_solver.tx_parts, S2MS_LIST(channel_balance_solver.correct_channel_rtt()) 
            ).switch_state
        except Exception as e:
            print(e)
            res = None

        # channel_balance_solver.load_balance()
        if res == constHead.CHANNEL0:
            proj_stream.tx_parts = [0, 0]
        elif res == constHead.CHANNEL1:
            proj_stream.tx_parts = [1, 1]
    else:
        channel_switch_solver.rtt_predict.update(channel_balance_solver.tx_parts, S2MS_LIST(channel_balance_solver.correct_channel_rtt()))
            
    if test < 1:
        tx_parts = [proj_stream.tx_parts[0] - 0.2, proj_stream.tx_parts[1] - 0.2]
        proj_stream.tx_parts = tx_parts
    
f.write(']')

