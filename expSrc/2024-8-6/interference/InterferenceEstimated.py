import matplotlib.pyplot as plt
import numpy as np
import os
import seaborn as sns
import pandas as pd
import time
import json
import scale

from matplotlib import rcParams
rcParams['font.family'] ='sans-serif'
# rcParams['font.sans-serif'] = ['Arial']
rcParams['font.size'] = 16
def delLastLine(fileName):
    with open(fileName, 'r') as f:
        lines = f.readlines()
    if "@" in lines[-1]:
        print('filename is ', fileName)
        with open(fileName, 'w') as f:
            f.writelines(lines[:-1])
        
def txtRead(fileName):
    file = open(fileName, "r")
    lines = file.readlines()
    rttlist = []
    for idxLine,line in enumerate(lines):
        if idxLine > 2:
            lineList = line.split(" ")
            if len(lineList) < 2:
                break
            rttlist.append(float(lineList[1]))
    file.close()
    return rttlist

def rttArrayDictPlot_cdf(fileName,taskrtt,index=0):
    print(fileName)
    targetRtt = 22
    plt.figure(figsize=(10, 6))   
    plt.axvline(x=targetRtt, color='r', linestyle='--', label='Target RTT')
    for port,rttlist in taskrtt.items():
        rttlist = np.array(rttlist) * 1000 # convert to ms.
        rttlist = rttlist[index:]
        rttstd = np.std(rttlist)
        rttAverage = np.mean(rttlist)
        sns.ecdfplot(rttlist, label=port+" (avg RTT: %.2f ms)" % rttAverage + " (std: %.2f ms)" % rttstd)       
    plt.title(fileName.split("/")[-1] ,fontsize=24)
    plt.xlabel("RTT (ms)", fontsize=16)
    plt.ylabel("CDF",fontsize=16)
    plt.grid()
    plt.legend(fontsize=12)
    plt.savefig(fileName.split(".txt")[0] + f"_{index}_interEst.png") 
    plt.show()
        

def outlier_removal(data, thresh=100):
    for idx,data_point in enumerate(data):
        if data_point > thresh:
            data[idx] = np.mean(data[:idx])
    return data


def main():
    inerferenceFile = "./5G_16M.txt"
    Taskfile = "../../../dpScript/2024-8-6/rtt/output1.txt"
    # Taskfile = "../../../dpScript/2024-8-6/output9.txt"
    print(inerferenceFile)
    rttDict = {}
    delLastLine(inerferenceFile)
    delLastLine(Taskfile)
    interRttlist = txtRead(inerferenceFile)
    taskRttlist = txtRead(Taskfile)
    rttDict["interference"] = interRttlist
    rttDict["task"] = taskRttlist
    rttArrayDictPlot_cdf(Taskfile,rttDict,index=0)


if __name__ == "__main__":
    main()
