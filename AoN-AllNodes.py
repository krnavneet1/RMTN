# -*- coding: utf-8 -*-
"""
Created on Mon Dec 16 06:18:29 2019

@author: NaVnEeT
"""

import pandas as pd
import networkx as nx
import os
import re

def ShortestPath(graph,source,destination):
    '''Generate shortest path node list and length for a given source and destination'''
    Path=nx.dijkstra_path(graph,source,destination,UserInput)
    PathLength=nx.dijkstra_path_length(graph,source,destination,UserInput)
    return(Path,PathLength)

def RunAoN(var1,UserInput,UserInput1,Demand,xls,fol,incrmnt):
    '''Run All or nathing traffic assignment'''
#Reading from excel-workbook(edge-list) and creating the network
    WaterWayUID=pd.read_excel(xls,'Water')
    RoadUID=pd.read_excel(xls,'Road')
    RailUID=pd.read_excel(xls,'Rail')
    ODUID=pd.read_excel(xls,'OD')
    TerminalUID=pd.read_excel(xls,'Terminal')
    Road_ODUID=pd.concat([RoadUID,ODUID])
    
#Creating Graph(NWK means network)
    
    WaterWayNWK=nx.from_pandas_edgelist(WaterWayUID,'Node-A','Node-B',[UserInput])
    RoadNWK=nx.from_pandas_edgelist(Road_ODUID,'Node-A','Node-B',[UserInput])
    RailNWK=nx.from_pandas_edgelist(RailUID,'Node-A','Node-B',[UserInput])
    TerminalNWK=nx.from_pandas_edgelist(TerminalUID,'Node-A','Node-B',[UserInput])
    Network_lst=[WaterWayNWK,RoadNWK,RailNWK,TerminalNWK]
    SynchoromodalNWK=nx.compose_all(Network_lst)
    
    if UserInput1=='road':
        network=RoadNWK
    elif UserInput1=='rail':
        network=RailNWK
    elif UserInput1=='water':
        network=WaterWayNWK
    elif UserInput1=='synchromodal':
        network=SynchoromodalNWK
    else:
        print('Wrong network name')

    AoN=Demand.copy()
    for source,target,demand in Demand.itertuples(index=False):
        DummyGraph=network.copy()
        Path,length=ShortestPath(DummyGraph,source,target)
        AoN.loc[(AoN['source']==source) & (AoN['target']==target),'Intiallength']=length
        AoN.loc[(AoN['source']==source) & (AoN['target']==target),'IntialCost']=length*demand
        try:
            for nodes in Path[1:len(Path)-1]:
                DummyGraph1=network.copy()
                DummyGraph1.remove_node(nodes)
                newpath,newlength=ShortestPath(DummyGraph1,source,target)
                AoN.loc[(AoN['source']==source) & (AoN['target']==target),nodes+"-length"]=newlength
                AoN.loc[(AoN['source']==source) & (AoN['target']==target),nodes+"-Cost"]=newlength*demand
        except nx.NetworkXNoPath:
            print("Removal of",nodes,"disconnect the",source,"and",target)
    for header in list(AoN):
        if str('Intial') not in str(header) and str('Cost') in str(header):
            AoN[header]=AoN[header].fillna(AoN['IntialCost'])
        elif str('Intial') not in str(header) and str('path') in str(header):
            AoN[header]=AoN[header].fillna(0)
    report_path = 'AoNAllNodeOutput_'+UserInput1
    if var1=='default':
        if not os.path.exists(os.path.join(report_path,var1)):
            os.makedirs(os.path.join(report_path,var1))
        outName='AoNAllNode'+'_'+UserInput+'.xlsx'
        writer=pd.ExcelWriter(os.path.join(report_path,var1,outName), engine='xlsxwriter')
        AoN.to_excel(writer,UserInput)
        writer.save()
    else:
        if not os.path.exists(os.path.join(report_path,var1,fol)):
            os.makedirs(os.path.join(report_path,var1,fol))
        outName='AoNAllNode'+'_'+UserInput+incrmnt
        writer=pd.ExcelWriter(os.path.join(report_path,var1,fol,outName), engine='xlsxwriter')
        AoN.to_excel(writer,UserInput)
        writer.save()
        

cwd = os.getcwd()
var1=input('Select "default" for running with default parameter otherwise "decrement" : ')
var1=var1.lower()
UserInput=input('Select weight(Time, Distance or Travelcost) for links: ')
UserInput=UserInput.title()
UserInput1=input('Select from network(water,rail,road or synchromodal): ')
UserInput1=UserInput1.lower()

#Make a group of interdependent nodes which are related to each other
xls2=pd.ExcelFile('list.xlsx')

#read demand matrix
xls3=pd.ExcelFile('Demand.xlsx')
Demand=pd.read_excel(xls3,'Demand')

if str(var1)==str('default'):
    path=cwd+'\\LinkList\\default\\'
    xls=pd.ExcelFile(path+'MatrixCost_default.xlsx')
    RunAoN(var1,UserInput,UserInput1,Demand,xls,None,None)
else:
    path=cwd+'\\LinkList\\time\\'
    folders=os.listdir(path)
    for f in folders:
        xlpath=path+'\\'+f
        xlses=os.listdir(xlpath)
        for xl in xlses:
            xls=pd.ExcelFile(xlpath+'\\'+xl)
            incrmnt=re.split('_',xl)
            RunAoN(var1,UserInput,UserInput1,Demand,xls,f,incrmnt[1])

