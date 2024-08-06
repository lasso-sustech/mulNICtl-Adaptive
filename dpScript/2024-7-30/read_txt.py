import matplotlib.pyplot as plt
import numpy as np
import os
import seaborn as sns
import pandas as pd
import time

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
        

def txtRead_multiChannel(fileName):
    from collections import Counter
    file = open(fileName, "r")
    lines = file.readlines()
    rttlist = []
    packetIdx = []
    for idxLine,line in enumerate(lines):
        if idxLine > 1:
            lineList = line.split(" ")
            if len(lineList) < 2:
                break
            packetIdx.append(int(lineList[0]))
            rttlist.append(float(lineList[2]))
    file.close()
    IdxList = list(set(packetIdx))
    IdxList.sort(key=packetIdx.index)
    IdxList.pop()
    # print("IdxList: ",IdxList.type)
    # print("IdxList: ",IdxList)

    Channel1Num = Counter(rttlist)[0]
    Channel2Num = Counter(rttlist)[1]
    print("Channel1Num: ",Channel1Num)
    print("Channel2Num: ",Channel2Num)
    
    data = np.loadtxt(fileName, skiprows=2)
    datachannel1 = np.empty((Channel1Num,2)) #2.4G
    datachannel2 = np.empty((Channel2Num,2)) #5G
    # print("datachannel1 shape: ",datachannel1.shape)
    # print("data shape: ",data.shape)
    # print("data :", data[-1,:],data[0,:])
    data1Idx = 0
    data2Idx = 0
    for idxrow in range(Channel1Num + Channel2Num - 1): 
        if data[idxrow,2] == 0:
            datachannel1[data1Idx,:] = data[idxrow,:2]
            data1Idx += 1
        elif data[idxrow,2] == 1:
            # print(data2Idx) 
            datachannel2[data2Idx,:] = data[idxrow,:2]
            data2Idx += 1
    
    ## max data
    rttArray = np.empty((len(IdxList),2),dtype=float)
    for idxrow,item in enumerate(IdxList):
        # print(item)
        rttArray[idxrow,0] = item
        if item in datachannel1[:,0]:
            a = np.where(datachannel1[:,0]==item)[0][0]
            if item in datachannel2[:,0]:
                b = np.where(datachannel2[:,0]==item)[0][0]
                rttArray[idxrow,1] = np.max((datachannel1[a,1],datachannel2[b,1]))
            else:
                rttArray[idxrow,1] = datachannel1[a,1]     
        else:
            if item in datachannel2[:,0]:
                b = np.where(datachannel2[:,0]==item)[0][0]
                rttArray[idxrow,1] = datachannel2[b,1]
    print("rttArray shape: ",rttArray.shape)
    print("rttArray :", rttArray[-1,:],rttArray[0,:])
    return rttArray    
     
def txtRead_multiChannel_port(fileName):
    from collections import Counter
    file = open(fileName, "r")
    lines = file.readlines()
    rttlist = []
    packetIdx = []
    port = lines[1].split("@")[0][-4:]
    print(port)
    for idxLine,line in enumerate(lines):
        if idxLine > 1:
            lineList = line.split(" ")
            if len(lineList) < 2:
                break
            packetIdx.append(int(lineList[0]))
            rttlist.append(float(lineList[2]))
    file.close()
    IdxList = list(set(packetIdx))
    IdxList.sort(key=packetIdx.index)
    IdxList.pop()
    # print("IdxList: ",IdxList.type)
    # print("IdxList: ",IdxList)

    Channel1Num = Counter(rttlist)[0]
    Channel2Num = Counter(rttlist)[1]
    print("Channel1Num: ",Channel1Num)
    print("Channel2Num: ",Channel2Num)
    
    data = np.loadtxt(fileName, skiprows=2)
    datachannel1 = np.empty((Channel1Num,2)) #2.4G
    datachannel2 = np.empty((Channel2Num,2)) #5G
    # print("datachannel1 shape: ",datachannel1.shape)
    # print("data shape: ",data.shape)
    # print("data :", data[-1,:],data[0,:])
    data1Idx = 0
    data2Idx = 0
    for idxrow in range(Channel1Num + Channel2Num - 1): 
        if data[idxrow,2] == 0:
            datachannel1[data1Idx,:] = data[idxrow,:2]
            data1Idx += 1
        elif data[idxrow,2] == 1:
            # print(data2Idx) 
            datachannel2[data2Idx,:] = data[idxrow,:2]
            data2Idx += 1
    
    ## max data
    rttArray = np.empty((len(IdxList),1),dtype=float)
    for idxrow,item in enumerate(IdxList):
        # print(item)
        rttArray[idxrow,0] = item
        if item in datachannel1[:,0]:
            a = np.where(datachannel1[:,0]==item)[0][0]
            if item in datachannel2[:,0]:
                b = np.where(datachannel2[:,0]==item)[0][0]
                rttArray[idxrow,0] = np.max((datachannel1[a,1],datachannel2[b,1]))
            else:
                rttArray[idxrow,0] = datachannel1[a,1]     
        else:
            if item in datachannel2[:,0]:
                b = np.where(datachannel2[:,0]==item)[0][0]
                rttArray[idxrow,0] = datachannel2[b,1]
    print("rttArray shape: ",rttArray.shape)
    print("rttArray :", rttArray[-1,:],rttArray[0,:])
    return port,rttArray    

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

#画自适应的rtt cdf曲线
def rttArraySinglePlot_cdf(fileName,rttArray,index=0):
    targetRtt = 22
    plt.figure(figsize=(10, 6))   
    rttlist = rttArray[index:,1] * 1000 # convert to ms.
    print("rttlist shape: ",rttlist.shape)
    rttstd = np.std(rttlist)
    print("rttstd: ",rttstd)
    rttAverage = np.mean(rttlist)
    snsplot = sns.ecdfplot(rttlist)       
    plt.axvline(x=targetRtt, color='r', linestyle='--', label='Target RTT')
    plt.title(fileName.split("/")[-1] + ": rttstd: %.2f" % rttstd, fontsize=24)
    plt.xlabel("RTT (ms)", fontsize=16)
    plt.ylabel("CDF",fontsize=16)
    plt.grid()
    plt.legend([" (avg RTT: %.2f ms)" % rttAverage, "Target RTT: %.2f ms" % targetRtt], loc='upper right', fontsize=12)
    plt.savefig("./"+fileName.split(".")[1] + f"_{index}_cdf.png")     
    # plt.savefig("./"+fileName.split(".")[1] + "10s_cdf.png")     

def rttArrayDictPlot_cdf(fileName,taskrtt,index=0):
    # print(fileName)
    color_list = ['r','b','y','g','k','c','m','w']
    targetRtt = 22
    plt.figure(figsize=(10, 6))   
    plt.axvline(x=targetRtt, color='r', linestyle='--', label='Target RTT')
    for idx, (port,rttlist) in enumerate(taskrtt.items()):
        rttlist = np.array(rttlist) * 1000 # convert to ms.
        rttlist = rttlist[index:]
        rttstd = np.std(rttlist)
        rttAverage = np.mean(rttlist)
        sns.ecdfplot(rttlist, color = color_list[idx],label=port+" (avg RTT: %.2f ms)" % rttAverage + " (std: %.2f ms)" % rttstd)       
        
    plt.title(fileName.split("/")[-1] ,fontsize=24)
    plt.xlabel("RTT (ms)", fontsize=16)
    plt.ylabel("CDF",fontsize=16)
    plt.grid()
    plt.legend(fontsize=12)
    plt.savefig(fileName.split(".txt")[0] + f"_{index}_cdf.png") 
    plt.show()
        
def rttArrayDictPlot_cdf_ada(fileName,taskrtt,index=0,part = 0.45):
    #NoAda and Ada
    # print(fileName)
    color_list = ['r','b','y','g','k','c','m','w']
    targetRtt = 22
    plt.figure(figsize=(10, 6))   
    plt.axvline(x=targetRtt, color='r', linestyle='--', label='Target RTT')
    for idx, (port,rttlist) in enumerate(taskrtt.items()):
        print("PORT:    ",port)
        TotalLen = len(rttlist)
        NoadaRttList = rttlist[:int(TotalLen*part)]
        AdaRttList = rttlist[-int(TotalLen*part):]
        NoadaRttList = np.array(NoadaRttList) * 1000 # convert to ms.
        AdaRttList = np.array(AdaRttList) * 1000 # convert to ms.
        # rttlist = rttlist[index:]
        Noadarttstd = np.std(NoadaRttList)
        Adarttstd = np.std(AdaRttList)
        NoadarttAverage = np.mean(NoadaRttList)
        AdarttAverage = np.mean(AdaRttList)
        Gain = (NoadarttAverage-AdarttAverage)/NoadarttAverage
        print("Gain: ", Gain)
        print('color :', color_list[idx])
        sns.ecdfplot(NoadaRttList, linestyle = "--",label=port+" (Single avg RTT: %.2f ms)" % NoadarttAverage + " (std: %.2f ms)" % Noadarttstd)
        sns.ecdfplot(AdaRttList, color = color_list[idx],label=port+" (Double: %.2f ms)" % AdarttAverage + " (std: %.2f ms)" % Adarttstd + " (Gain: %.3f )"% Gain) 
    ax = plt.gca()
    colorIdx = 0
    for idx in range(1,len(ax.lines),2):
        ax.lines[idx].set_color(color_list[colorIdx])
        ax.lines[idx+1].set_color(color_list[colorIdx])
        colorIdx += 1  
    plt.title(fileName.split("/")[-1] ,fontsize=24)
    plt.xlabel("RTT (ms)", fontsize=16)
    plt.ylabel("CDF",fontsize=16)
    plt.xlim([0, 80])
    plt.grid()
    plt.legend(fontsize=12)
    plt.savefig(fileName.split(".txt")[0] + f"_{index}_cdf.png") 
    # plt.show()

#画自适应的rtt曲线
def rttArraySinglePlot_time(fileName,rttArray):
    plt.figure(figsize=(10, 6))
    # rttArray= txtRead_multiChannel(fileName)
    rttlist = rttArray[:,1] * 1000 # convert to ms.
    print("rttlist shape: ",rttlist.shape)
    rttAverage = np.mean(rttlist)
    plt.plot(rttlist)
    plt.title(fileName.split("/")[-1], fontsize=24)
    plt.xlabel("PacketIndex", fontsize=16)
    plt.ylabel("RTT (ms)",fontsize=16)
    plt.legend([" (avg RTT: %.2f ms)" % rttAverage], loc='upper right', fontsize=12)
    plt.savefig("./"+fileName.split(".")[1] + "_time.png") 
    plt.show()
        
def rttPlot(scenario):
    path_files = os.listdir("./"+scenario)
    loop = round(len(path_files)/5)
    print(loop)
    for idx_loop in range(loop):
        fileList = ["output"+str(i)+".txt" for i in range(idx_loop*5, (idx_loop+1)*5)]
        througputList = ["50Mbps","40Mbps","30Mbps","20Mbps","10Mbps"]
        lengendList = []
        duration = 10 #sum is 10s
        plt.figure(figsize=(10, 6))
        df = pd.DataFrame()
        for idx,fileName in enumerate(fileList):
            file = "./"+scenario + "/" + fileName
            rttlist = txtRead(file)
            rttlist = np.array(rttlist) * 1000 # convert to ms.
            # rttlist = outlier_removal(rttlist,50)
            # print("max RTT: ",max(rttlist))
            rttAverage = np.mean(rttlist)
            lengendList.append([througputList[idx] + " (avg RTT: %.2f ms)" % rttAverage])
            idxtime = np.arange(0, duration, duration/len(rttlist))
            # print(lengendList[idx])
            # df[througputList[idx]] = rttlist
            snsplot = sns.ecdfplot(rttlist)
        #     plt.plot(idxtime, rttlist)
        # plt.title(scenario, fontsize=24)
        # plt.xlabel("time", fontsize=16)
        # plt.ylabel("RTT (ms)",fontsize=16)
        # plt.legend(lengendList, loc='upper right', fontsize=12)
        # plt.savefig(scenario + str(idx_loop+1) + ".png")
        
        # plt.figure(figsize=(10, 6))
        
        plt.title(scenario, fontsize=24)
        plt.xlabel("RTT (ms)", fontsize=16)
        plt.ylabel("CDF",fontsize=16)
        plt.grid()
        plt.legend(lengendList, loc='upper right', fontsize=12)
        plt.savefig("./"+fileName.split(".")[1] + "_cdf.png")

def outlier_removal(data, thresh=100):
    for idx,data_point in enumerate(data):
        if data_point > thresh:
            data[idx] = np.mean(data[:idx])
    return data

#画单空口的rtt cdf曲线
def rttSinglePlot_cdf(fileName):
    targetRtt = 22
    plt.figure(figsize=(10, 6))
    duration = 20 #sum is 10s
    rttlist = txtRead(fileName)
    rttlist = np.array(rttlist) * 1000 # convert to ms.
    print("rttlist shape: ",rttlist.shape)
    # rttlist = outlier_removal(rttlist,50)
    # print("max RTT: ",max(rttlist))
    rttAverage = np.mean(rttlist)
    idxtime = np.arange(0, duration, duration/len(rttlist))
    # print(lengendList[idx])
    # df[througputList[idx]] = rttlist
    snsplot = sns.ecdfplot(rttlist)      
    plt.axvline(x=targetRtt, color='r', linestyle='--', label='Target RTT') 
    plt.title(fileName.split("/")[-1], fontsize=24)
    plt.xlabel("RTT (ms)", fontsize=16)
    plt.ylabel("CDF",fontsize=16)
    plt.grid()
    plt.legend([" (avg RTT: %.2f ms)" % rttAverage], loc='upper right', fontsize=12)
    plt.savefig("./"+fileName.split(".")[1] + "_cdf.png")

#画单空口的rtt曲线
def rttSinglePlot_time(fileName):
    plt.figure(figsize=(10, 6))
    duration = 20 #sum is 10s
    rttlist = txtRead(fileName)
    rttlist = np.array(rttlist) * 1000 # convert to ms.
    # rttlist = outlier_removal(rttlist,50)
    # print("max RTT: ",max(rttlist))
    rttAverage = np.mean(rttlist)
    # idxtime = np.arange(0, duration, duration/len(rttlist))
    plt.plot(rttlist)
    plt.title(fileName.split("/")[-1], fontsize=24)
    plt.xlabel("PacketIndex", fontsize=16)
    plt.ylabel("RTT (ms)",fontsize=16)
    plt.legend([" (avg RTT: %.2f ms)" % rttAverage], loc='upper right', fontsize=12)
    plt.savefig("./"+fileName.split(".")[1] + "_time.png")
def main():
    
    # filePath = "./"
    # path_files = os.listdir(filePath)
    # for file_name in path_files:
    #     if file_name.endswith(".txt"):
    #         fileName = filePath + file_name
    #         delLastLine(fileName)
    #         rttArray= txtRead_multiChannel(fileName)
    #         rttArraySinglePlot_cdf(fileName,rttArray)
    #         rttArraySinglePlot_cdf(fileName,rttArray,1000)
    #         rttArraySinglePlot_time(fileName,rttArray)
    filePath = "./experiment2/"
    path_files = os.listdir(filePath)
    txtIndex = 18
    taskNum = 4
    taskList = []
    taskRttlist = {}
    for idxstream in range(txtIndex,txtIndex+taskNum):
        taskList.append(f"output{idxstream}.txt")
    for txtName in taskList:
        temptxtName = filePath + txtName
        if os.path.exists(temptxtName):
            delLastLine(temptxtName)
            port,temprttArray = txtRead_multiChannel_port(temptxtName)
            taskRttlist[port] = temprttArray
    print("filename:", temptxtName.split('.txt')[0])
    rttArrayDictPlot_cdf_ada(temptxtName,taskRttlist,part=0.45)

       



if __name__ == "__main__":
    main()
