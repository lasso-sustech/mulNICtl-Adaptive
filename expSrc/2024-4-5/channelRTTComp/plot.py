import os
data_path = os.path.join(os.path.dirname(__file__), 'data.json')
import json

class dataStruct:
    def __init__(self, rttDict):
        if rttDict == {}:
            self.data_frac = 0
            self.rtt = 0
            self.channel_rtts = [0, 0]
            self.channel_probabilities = [0, 0]
            return
        self.data_frac = float(rttDict['rtt'][0])
        self.rtt = float(rttDict['rtt'][1])
        self.channel_rtts = [float(rttDict['rtt'][2]), float(rttDict['rtt'][3])]
        self.channel_probabilities = [float(rttDict['rtt'][4]), float(rttDict['rtt'][5])]

    def __str__(self) -> str:
        return json.dumps(self.__dict__, indent=2)
    
    def to_dict(self):
        return self.__dict__
    
    def from_dict(dict):
        data_struct = dataStruct({})
        for key, value in dict.items():
            if key in data_struct.__dict__:
                setattr(data_struct, key, value)
        return data_struct

def read_data(filename):
    with open(os.path.join(data_path, filename)) as f:
        temps = json.load(f)
    datas = []
    for temp in temps:
        datas.append(dataStruct.from_dict(temp))
    return datas

def plot_data(datas):
    import matplotlib.pyplot as plt
    import numpy as np

    device_num = 5
    fig, ax = plt.subplots()
    rtts = [data.rtt for data in datas]
    rtts_per_device = np.array(rtts).reshape(-1, device_num).T * 1000
    
    throughput = np.array(range(1, 100, 3)) * 5
    rtt_sum = rtts_per_device.sum(axis=0)
    ax.plot(throughput, rtt_sum)
    ax.grid( True, ls = '--', lw = 0.5)
    ax.set_xlabel('Sum Rate (Mbps)')
    ax.set_ylabel('Sum Channel RTT (ms)')
    plt.savefig('plot.png')

datas = read_data(data_path)
plot_data(datas)

    
