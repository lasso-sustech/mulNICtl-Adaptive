import re
import json
import numpy as np
import matplotlib.pyplot as plt
import os

from matplotlib import rcParams
rcParams['font.family'] ='sans-serif'
# rcParams['font.sans-serif'] = ['Arial']
rcParams['font.size'] = 16
import re

import scale

def read_jsonl(file_path):
    json_list = []
    with open(file_path, 'r') as file:
        for line in file:
            data = json.loads(line)
            json_list.append(data)
    return json_list

def result_plot(log_file, save_path):
    data = read_jsonl(log_file)
    # print(log_file)
    # Prepare data for plotting
    channel_rtts = {}
    rtts = {}
    tx_parts = {}
    outage_rates = {}

    for tasks in data:
        for task, vals in tasks.items():
            if task not in channel_rtts:
                channel_rtts[task] = []
            channel_rtts[task].append(np.array(vals['channel_rtts']) * 1000)

            if task not in rtts:
                rtts[task] = []
            rtts[task].append(np.array(vals['rtt']) * 1000)

            if task not in tx_parts:
                tx_parts[task] = []
            tx_parts[task].append(np.array(vals['tx_parts']))
            
            # if task not in outage_rates:
            #     outage_rates[task] = []
            # outage_rates[task].append(np.array(vals['outage_rates']))
            
            

    task_list = ['Task 1', 'Task 2']
    channel_idx = ['2.4GHz', '5GHz']

    # Create subplots
    fig, axs = plt.subplots(3, 1, figsize=(15, 15))

    # Plot channel RTTs
    for task_idx, (task, c_rtts) in enumerate(channel_rtts.items()):
        c_rtts = np.array(c_rtts).T
        for idx, rtt in enumerate(c_rtts):
            IdxTime = range(0,len(rtt)*2,2) #time (s)
            
            axs[0].plot(IdxTime,rtt, '-+', label=task_list[task_idx] + ' channel ' + channel_idx[idx]) 
            
    print("log_file",log_file)
    axs[0].set_yscale('custom', threshold=40)
    axs[0].grid(linestyle='--')
    # axs[0].set(xlim=(0,25))
    # axs[0].set_xlim = (0,25)   
    axs[0].set_ylabel('Channel RTT (ms)')
    axs[0].set_xlabel('Time (s)')
    axs[0].legend()
    # axs[0].set_title("throughput: "+log_file[3:5]+"Mbps")


    

    # Plot RTTs
    for task_idx, (task, rtt) in enumerate(rtts.items()):
        rtt = np.array(rtt)
        axs[1].plot(rtt, '-+', label=task_list[task_idx])

    axs[1].set_yscale('custom', threshold=40)
    axs[1].grid(linestyle='--')
    # axs[1].set_xlim(0, 25)
    axs[1].set_ylabel('RTT (ms)')
    axs[1].set_xlabel('Time (s)')
    axs[1].legend()

    
    # # Plot TX Parts
    for task_idx, (task, tx_part) in enumerate(tx_parts.items()):
        tx_part = np.array(tx_part) * 100
        # print('tx_part',tx_part.shape)
        # tx_part[:, 1] = 100 - tx_part[:, 1]
        tx_part[1, :] = 100 - tx_part[1, :]
        tx_part = tx_part.T
        for idx, part in enumerate(tx_part):
            print(part)
            axs[2].plot(part, '-+', label=task_list[task_idx] + ' channel ' + channel_idx[idx])

    axs[2].grid(linestyle='--')
    axs[2].set_ylabel('TX Parts')
    # axs[2].set(xlim=(0,25))
    axs[2].set_xlabel('Time (s)')
    axs[2].legend()
    

    # # Plot outage rates
    # for task_idx, (task, outage_rate) in enumerate(outage_rates.items()):
    #     outage_rate = np.array(outage_rate) * 100
    #     outage_rate = outage_rate.T
    #     for idx, rate in enumerate(outage_rate):
    #         axs[3].plot(rate, '-+', label=task_list[task_idx] + ' channel ' + channel_idx[idx])

    # axs[3].grid(linestyle='--')
    # axs[3].set(xlim=(0,25))
    # axs[3].set_ylabel('Outage Rates (%)')
    # axs[3].set_xlabel('Time (s)')
    # axs[3].legend()
     
    
    # Save the combined plot
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()



def result_plot_rttseclist(log_file, save_path,rttseclist):
    data = read_jsonl(log_file)
    # print(log_file)
    # Prepare data for plotting
    channel_rtts = {}
    rtts = {}
    tx_parts = {}
    outage_rates = {}

    for tasks in data:
        for task, vals in tasks.items():
            if task not in channel_rtts:
                channel_rtts[task] = []
            channel_rtts[task].append(np.array(vals['channel_rtts']) * 1000)

            if task not in rtts:
                rtts[task] = []
            rtts[task].append(np.array(vals['rtt']) * 1000)

            if task not in tx_parts:
                tx_parts[task] = []
            tx_parts[task].append(np.array(vals['tx_parts']))
            
            # if task not in outage_rates:
            #     outage_rates[task] = []
            # outage_rates[task].append(np.array(vals['outage_rates']))
            
            

    task_list = ['Task 1', 'Task 2']
    channel_idx = ['2.4GHz', '5GHz']

    # Create subplots
    fig, axs = plt.subplots(3, 1, figsize=(15, 15))

    # Plot channel RTTs
    for task_idx, (task, c_rtts) in enumerate(channel_rtts.items()):
        c_rtts = np.array(c_rtts).T
        for idx, rtt in enumerate(c_rtts):
            IdxTimertt = range(0,len(rtt)*2,2)
            axs[0].plot(IdxTimertt,rtt, '-+', label=task_list[task_idx] + ' channel ' + channel_idx[idx])
    
    
    axs[0].set_yscale('custom', threshold=40)
    axs[0].grid(linestyle='--')
    # axs[0].set(xlim=(0,25))
    # axs[0].set_xlim = (0,25)   
    axs[0].set_ylabel('Channel RTT (ms)')
    axs[0].set_xlabel('Time (s)')
    axs[0].legend()
    # axs[0].set_title("throughput: "+log_file[3:5]+"Mbps")


    
    targetRtt = 22
    # Plot RTTs
    IdxTimeSecrtt = range(len(rttseclist))
    for task_idx, (task, rtt) in enumerate(rtts.items()):
        rtt = np.array(rtt)
        IdxTimertt = range(len(rttseclist),len(rtt)*2+len(rttseclist),2) #time (s)
        axs[1].plot(IdxTimertt,rtt, '-+', label=task_list[task_idx]+"avg RTT: %.2f"%np.mean(rtt[5:]))
    IdxAll = list(IdxTimeSecrtt)+list(IdxTimertt)
    rttseclist = np.array(rttseclist)*1000
    axs[1].plot(IdxTimeSecrtt,rttseclist, label='5G RTT')
    axs[1].plot(IdxTimeSecrtt,np.mean(rttseclist)*np.ones(len(IdxTimeSecrtt)), label='5G average RTT %.2f'%np.mean(rttseclist))
    axs[1].plot(IdxAll,targetRtt*np.ones(len(IdxAll)), label='Target RTT (22ms)')
    axs[1].set_yscale('custom', threshold=40)
    axs[1].grid(linestyle='--')
    # axs[1].set_xlim(0, 25)
    axs[1].set_ylabel('RTT (ms)')
    axs[1].set_xlabel('Time (s)')
    axs[1].legend()

    
    # # Plot TX Parts
    for task_idx, (task, tx_part) in enumerate(tx_parts.items()):
        tx_part = np.array(tx_part) * 100
        # print(tx_part)
        # print('tx_part',tx_part.shape)
        # tx_part[:, 1] = 100 - tx_part[:, 1]
        tx_part[:,1] = 100 - tx_part[:, 1]
        tx_part = tx_part.T
        axs[2].plot(tx_part[1,:], '-+', label=task_list[task_idx] + ' channel ' + channel_idx[idx])

    axs[2].grid(linestyle='--')
    axs[2].set_ylabel('TX Parts')
    axs[2].set(ylim=(0,100))
    axs[2].set_xlabel('Time (s)')
    axs[2].legend()
    
    # Save the combined plot
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def compute_avg_rtt(log_file):
    data = read_jsonl(log_file)

    # Prepare data for plotting
    channel_rtts = {}
    rtts = {}
    tx_parts = {}
    outage_rates = {}

    for tasks in data:
        for task, vals in tasks.items():
            if task not in channel_rtts:
                channel_rtts[task] = []
            channel_rtts[task].append(np.array(vals['channel_rtts']) * 1000)

            if task not in rtts:
                rtts[task] = []
            rtts[task].append(np.array(vals['rtt']) * 1000)

            if task not in tx_parts:
                tx_parts[task] = []
            tx_parts[task].append(np.array(vals['tx_parts']))
            
            # if task not in outage_rates:
            #     outage_rates[task] = []
            # outage_rates[task].append(np.array(vals['outage_rates']))
            
    # avg_rtt = 0
    # for task_idx, (task, rtt) in enumerate(rtts.items()):
    #     rtt = np.array(rtt)
    #     avg_rtt += np.sum(rtt)
        
    # avg_rtt /= len(rtts) * len(rtt)
    
    ## Calculate avg within 25th percentile and 75th percentile
    avg_rtt = 0
    for task_idx, (task, rtt) in enumerate(rtts.items()):
        rtt = np.array(rtt)
        rtt = np.sort(rtt)
        avg_rtt += np.sum(rtt[int(len(rtt) * 0.25):int(len(rtt) * 0.75)])        
    avg_rtt /= len(rtts) * len(rtt) * 0.5
    return avg_rtt

def txtRead(fileName):
    file = open(fileName, "r")
    lines = file.readlines()
    rttlist = []
    packetIndexList = []
    for idxLine,line in enumerate(lines):
        if idxLine > 2:
            lineList = line.split(" ")
            if len(lineList) < 2:
                break
            rttlist.append(float(lineList[1]))
            packetIndexList.append(int(lineList[0]))
    file.close()
    duration = 20
    rttSeclist = []
    step = round(packetIndexList[-1]/duration)
    for idx in range(duration):
        rttSeclist.append(np.mean(rttlist[idx*step:idx*step+step]))
    return rttSeclist


def main():
    pathName = "./"    
    file_name = "Adaptive-16_cross_2x8x2x16M_149_gap1_16.jsonl"
    digitList = re.findall(r'\d+', file_name)
    txtName = f"NoAda/output{digitList[-1]}.txt"
    fulfilename = pathName + file_name
    fultxtName = pathName + txtName
    avg_rtt = compute_avg_rtt(fulfilename)
    # print(file_name, avg_rtt)
    rttseclist = txtRead(fultxtName)
    result_plot_rttseclist(fulfilename, pathName+file_name.split('.')[0] + '.png',rttseclist)
    
    # result_plot(fulfilename, pathName+file_name.split('.')[0] + '.png')
    
    # fileList = os.listdir(pathName)
    # # print(fileList)
    # for file_name in fileList:
    #     if file_name.endswith(".jsonl"):
    #         digitList = re.findall(r'\d+', file_name)
    #         txtName = f"NoAda/output{digitList[-1]}.txt"
    #         fulfilename = pathName + file_name
    #         avg_rtt = compute_avg_rtt(fulfilename)
    #         fultxtName = pathName + txtName
    #         # print(file_name, avg_rtt)
    #         # result_plot(fulfilename, pathName+file_name.split('.')[0] + '.png')
    #         rttseclist = txtRead(fultxtName)
    #         result_plot_rttseclist(fulfilename, pathName+file_name.split('.')[0] + '.png',rttseclist)
            # break


# result_plot('if-750-single.jsonl', 'if-750-single.png')

# result_plot('reference.jsonl', 'reference.png')

# result_plot('low_interference3.jsonl', 'low.png')

if __name__ == "__main__":
    main()