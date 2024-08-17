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
import read_txt as rt

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
            
            if task not in outage_rates:
                outage_rates[task] = []
            outage_rates[task].append(np.array(vals['outage_rate']))
            
            

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
    
    # Save the combined plot
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()



def result_plot_rttseclist(log_file, save_path,rttseclist):
    data = read_jsonl(log_file)
    channel_rtts = {}
    rtts = {}
    tx_parts = {}
    outage_rates = {}

    for tasks in data:
        for task, vals in tasks.items():
            print(task,vals)
            if task not in channel_rtts:
                channel_rtts[task] = []
            channel_rtts[task].append(np.array(vals['channel_rtts']) * 1000)

            if task not in rtts:
                rtts[task] = []
            rtts[task].append(np.array(vals['rtt']) * 1000)

            if task not in tx_parts:
                tx_parts[task] = []
            tx_parts[task].append(np.array(vals['tx_parts']))
            
            if task not in outage_rates:
                outage_rates[task] = []
            outage_rates[task].append(np.array(vals['outage_rate']))
            
            

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
        print(tasks)
        # break
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
            
            if task not in outage_rates:
                outage_rates[task] = []
            outage_rates[task].append(np.array(vals['outage_rate']))
            
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

def txtRead_port(fileName):
    file = open(fileName, "r")
    lines = file.readlines()
    rttlist = []
    packetIndexList = []
    port = lines[1].split("@")[0][-4:]
    print(port)
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
    return port,rttSeclist

def txtReadrttlist_port(fileName):
    file = open(fileName, "r")
    lines = file.readlines()
    rttlist = []
    packetIndexList = []
    port = lines[1].split("@")[0][-4:]
    # print(port)
    for idxLine,line in enumerate(lines):
        if idxLine > 2:
            lineList = line.split(" ")
            if len(lineList) < 2:
                break
            rttlist.append(float(lineList[1]))
            packetIndexList.append(int(lineList[0]))
    file.close()
    return port,rttlist


def result_plot_rttsecdict(log_file, save_path,rttsecdict):
    data = read_jsonl(log_file)
    channel_rtts = {}
    rtts = {}
    tx_parts = {}
    outage_rates = {}
    port_list = []

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
            
            if task not in outage_rates:
                outage_rates[task] = []
            outage_rates[task].append(np.array(vals['outage_rate']))

            if task not in  port_list:
                port_list.append(task)
    # print(port_list)
    # task_list
    task_list = [x.split("@")[0] for x in port_list]
    channel_idx = ['2.4GHz', '5GHz']
    color_list = ['r','b','y','g','k','c','m','w']
    # print(channel_rtts[port_list[0]])

    # Create subplots
    fig, axs = plt.subplots(3, 1, figsize=(20, 20))

    # Plot channel RTTs
    for task_idx, (task, c_rtts) in enumerate(channel_rtts.items()):
        c_rtts = np.array(c_rtts).T
        for idx, rtt in enumerate(c_rtts):
            IdxTimertt1 = range(0,len(rtt)*2,2)
            axs[0].plot(IdxTimertt1,rtt, '-+',  label=task + ' channel ' + channel_idx[idx])
    
    axs[0].set_yscale('custom', threshold=40)
    axs[0].grid(linestyle='--')
    axs[0].set_ylabel('Channel RTT (ms)')
    axs[0].set_xlabel('Time (s)')
    axs[0].legend(loc = "upper center",bbox_to_anchor=(0.5, 1.1),
          ncol=4, fancybox=True, shadow=True)


    
    targetRtt = 22
    # Plot RTTs
    for idx,port in enumerate(task_list):
        print("port",port)
        index = task_list.index(port)
        temprttseclist = rttsecdict[port]
        IdxTimeSecrtt = range(len(temprttseclist))
        temprttseclist = np.array(temprttseclist)*1000
        axs[1].plot(IdxTimeSecrtt,temprttseclist, color = color_list[index])
        axs[1].plot(IdxTimeSecrtt,np.mean(temprttseclist)*np.ones(len(IdxTimeSecrtt)),color = color_list[index], label=port+'average RTT %.2f'%np.mean(temprttseclist))
    a = int(len(temprttseclist))
    
    for task_idx, (task, rtt) in enumerate(rtts.items()):
        rtt = np.array(rtt)
        b = len(rtt)
        TimerttList = range(a,int(b*2+a),2) #time (s)
        axs[1].plot(TimerttList,rtt, '-+',color=color_list[task_idx], label=task_list[task_idx]+"avg RTT: %.2f"%np.mean(rtt[5:]))
    IdxAll = list(IdxTimeSecrtt)+list(TimerttList)
    axs[1].plot(IdxAll,targetRtt*np.ones(len(IdxAll)), label='Target RTT (22ms)')
    axs[1].set_yscale('custom', threshold=40)
    axs[1].grid(linestyle='--')
    # axs[1].set_xlim(0, 25)
    axs[1].set_ylabel('RTT (ms)')
    axs[1].set_xlabel('Time (s)')
    axs[1].legend(loc = "upper center",bbox_to_anchor=(0.5, 1.1),
          ncol=4, fancybox=True, shadow=True)

    
    # # Plot TX Parts
    for task_idx, (task, tx_part) in enumerate(tx_parts.items()):
        tx_part = np.array(tx_part) * 100
        tx_part[:,1] = 100 - tx_part[:, 1]
        tx_part = tx_part.T
        # print(task_idx)
        # axs[2].plot(tx_part[1,:], '-+')
        axs[2].plot(tx_part[1,:], '-+',color=color_list[task_idx], label=task_list[task_idx])

    axs[2].grid(linestyle='--')
    axs[2].set_ylabel('TX Parts')
    axs[2].set(ylim=(0,100))
    axs[2].set_xlabel('Time (s)')
    axs[2].legend()
    
    # Save the combined plot
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def taskNum(log_file):
    data = read_jsonl(log_file)
    port_list = []

    for tasks in data:
        for task, vals in tasks.items():
            if task not in  port_list:
                port_list.append(task)
    # print(port_list)
    # task_list
    return len(port_list)

def main():
            
    pathName = './'
    fileList = os.listdir(pathName)
    # print(fileList)
    for file_name in fileList:
        if file_name.endswith(".jsonl"):
            ## jsonl file
            if file_name.split(".")[0]+".png"in fileList:
                print(file_name.split(".")[0]+".png")
                continue
            else:
                fulfilename = pathName+ file_name
                digitList = re.findall(r'\d+', file_name)
                streamNum  = taskNum(fulfilename)
                print(streamNum)
                taskList = []
                for idxstream in range(streamNum):
                    taskList.append(f"output{int(digitList[-1])+idxstream}.txt")
                    # print(taskList)
                taskRtt = {}
                for txtName in taskList:
                    temptxtName = pathName + "NoAda/" + txtName
                    if os.path.exists(temptxtName):
                        port,temprttseclist = txtRead_port(temptxtName)
                        taskRtt[port] = temprttseclist
                
                # avg_rtt = compute_avg_rtt(fulfilename)
                print(fulfilename)
                result_plot_rttsecdict(fulfilename, pathName+file_name.split('.')[0] + '.png',taskRtt)
                
            
            fulfilename = pathName+ file_name
            digitList = re.findall(r'\d+', file_name)
            streamNum  = taskNum(fulfilename)
            taskList = []
            for idxstream in range(streamNum):
                taskList.append(f"output{int(digitList[-1])+idxstream}.txt")
            taskRttlist = {}
            for txtName in taskList:
                temptxtName = pathName + "NoAda/" + txtName
                if os.path.exists(temptxtName):
                    port,temprttlist = txtReadrttlist_port(temptxtName)
                    taskRttlist[port] = temprttlist
            # print("filename:", temptxtName.split('.txt')[0])
            rt.rttArrayDictPlot_cdf(temptxtName,taskRttlist)
            
            for txtName in taskList:
                temptxtName = pathName + "Ada/" + txtName
                if os.path.exists(temptxtName):
                    port,temprttlist = txtReadrttlist_port(temptxtName)
                    taskRttlist[port] = temprttlist
            print("filename:", temptxtName.split('.txt')[0])
            rt.rttArrayDictPlot_cdf(temptxtName,taskRttlist)
            rt.rttArrayDictPlot_cdf(temptxtName,taskRttlist,index=1000)
    #        
            # break
    # filePath = "./Ada/"
    # path_files = os.listdir(filePath)
    # for file_name in path_files:
    #     if file_name.endswith(".txt"):
    #         if file_name.split(".")[0]+"_time.png" in path_files:
    #             print(file_name.split(".")[0]+".png")
    #             continue
    #         else:
    #             fileName = filePath + file_name
    #             rt.delLastLine(fileName)
    #             rttArray= rt.txtRead_multiChannel(fileName)
    #             rt.rttArraySinglePlot_cdf(fileName,rttArray)
    #             rt.rttArraySinglePlot_cdf(fileName,rttArray,1000)
    #             rt.rttArraySinglePlot_time(fileName,rttArray)
    
    # filePath = "./NoAda/"
    # path_files = os.listdir(filePath)
    # # print(path_files)
    # for file_name in path_files:
    #     if file_name.endswith(".txt"):
    #         # print(file_name.split(".")[0]+"_time.png")
    #         # break
    #         if file_name.split(".")[0]+"_time.png"in path_files:
    #             print(file_name.split(".")[0]+".png")
    #             continue
    #         else:
    #             fileName = filePath + file_name
    #             rt.delLastLine(fileName)
    #             rt.rttSinglePlot_cdf(fileName)
    #             rt.rttSinglePlot_time(fileName)
if __name__ == "__main__":
    main()