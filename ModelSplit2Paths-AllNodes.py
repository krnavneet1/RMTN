# -*- coding: utf-8 -*-
"""
Created on Wed Dec 25 14:12:54 2019
Mode split with AoN traffic assignment for synchromodal transport network consisting 
of three modes-Rail,water and Road. The output xlsx files has system cost when 
a node is removed.

Four user input is required to run this.
@author: NaVnEeT
"""

import pandas as pd
import networkx as nx
import math as m
import os
import re
import logging as lg


def ShortestPath(graph,source,destination):
    '''Generate shortest path node list and length for a given source and destination'''
    Path=nx.dijkstra_path(graph,source,destination,UserInput)
    PathLength=nx.dijkstra_path_length(graph,source,destination,UserInput)
    return(Path,PathLength)

def RunMS2P(var1,UserInput,UserInput1,InterDepPair,Demand,xls,fol,incrmnt,Beta):
    '''Run model split traffic assignment analysis for interdependent pair removal'''
    WaterWay=pd.read_excel(xls,'Water')
    Road=pd.read_excel(xls,'Road')
    Rail=pd.read_excel(xls,'Rail')
    OD=pd.read_excel(xls,'OD')
    Terminal=pd.read_excel(xls,'Terminal')
    Road_OD=pd.concat([Road,OD])
    
    #Creating Graph(NWK means network)
    
    WaterWayNWK=nx.from_pandas_edgelist(WaterWay,'Node-A','Node-B',[UserInput])
    RoadNWK=nx.from_pandas_edgelist(Road_OD,'Node-A','Node-B',[UserInput])
    RailNWK=nx.from_pandas_edgelist(Rail,'Node-A','Node-B',[UserInput])
    TerminalNWK=nx.from_pandas_edgelist(Terminal,'Node-A','Node-B',[UserInput])
    Network_lst=[WaterWayNWK,RoadNWK,RailNWK,TerminalNWK]
    SynchoromodalNWK=nx.compose_all(Network_lst)

    if UserInput1=='road':
        network=RoadNWK
    elif UserInput1=='rail':
        network=RailNWK
    elif UserInput1=='water':
        network=WaterWayNWK
    else:
        network=SynchoromodalNWK
    print('Calculating...')    
        
    headers=[]
    orglen=['IntialPath1length','IntialPath2length','IntialDemandSplitP1','IntialDemandSplitP2','IntialCost']
    headers=orglen
    header=pd.DataFrame(columns=headers)
    header=header.fillna(0)
    modesplit=pd.concat([Demand,header],axis=1)
    beta=Beta
    for source,target,demand in Demand.itertuples(index=False):
        DummyGraph=network.copy()
        FirstPath,FPlength=ShortestPath(DummyGraph,source,target)
        DummyGraph.remove_nodes_from(FirstPath[1:len(FirstPath)-1])
        try:
            SecondPath,SPlength=ShortestPath(DummyGraph,source,target)
            d1=(m.exp(-beta*(FPlength)))/float(m.exp(-beta*(FPlength))+m.exp(-beta*(SPlength)))
            d2=(m.exp(-beta*(SPlength)))/float(m.exp(-beta*(FPlength))+m.exp(-beta*(SPlength)))
            intialcost=(FPlength*d1*demand)+(SPlength*d2*demand)
            modesplit.loc[(modesplit['source']==source) & (modesplit['target']==target),'IntialPath1length']=FPlength
            modesplit.loc[(modesplit['source']==source) & (modesplit['target']==target),'IntialPath2length']=SPlength
            modesplit.loc[(modesplit['source']==source) & (modesplit['target']==target),'IntialDemandSplitP1']=d1
            modesplit.loc[(modesplit['source']==source) & (modesplit['target']==target),'IntialDemandSplitP2']=d2
            modesplit.loc[(modesplit['source']==source) & (modesplit['target']==target),'IntialCost']=intialcost
            nodes=list(set(FirstPath[1:len(FirstPath)-1]).union(set(SecondPath[1:len(SecondPath)-1])))
            for node in nodes:
                DummyGraph1=network.copy()
                DummyGraph1.remove_node(node)
                try:
                    NewPath1,NWlength1=ShortestPath(DummyGraph1,source,target)
                except nx.NetworkXNoPath:
                    lg.info("Removal of %s disconnect the %s and %s",node,source,target)
                    modesplit.loc[(modesplit['source']==source) & (modesplit['target']==target),node+"-Cost"]=intialcost
                DummyGraph1.remove_nodes_from(NewPath1[1:len(NewPath1)-1])
                try:
                    NewPath2,NWlength2=ShortestPath(DummyGraph1,source,target)
                except nx.NetworkXNoPath:
                    lg.info("No second path after Removal of %s disconnect the %s and %s",node,source,target)
                    modesplit.loc[(modesplit['source']==source) & (modesplit['target']==target),node+"-Cost"]=intialcost
                d1=(m.exp(-beta*(NWlength1)))/float(m.exp(-beta*(NWlength1))+m.exp(-beta*(NWlength2)))
                d2=(m.exp(-beta*(NWlength2)))/float(m.exp(-beta*(NWlength1))+m.exp(-beta*(NWlength2)))
                cost=(NWlength1*d1*demand)+(NWlength2*d2*demand)
                modesplit.loc[(modesplit['source']==source) & (modesplit['target']==target),node+"-path1length"]=NWlength1
                modesplit.loc[(modesplit['source']==source) & (modesplit['target']==target),node+"-path2length"]=NWlength2
                modesplit.loc[(modesplit['source']==source) & (modesplit['target']==target),node+"-DSP1"]=d1
                modesplit.loc[(modesplit['source']==source) & (modesplit['target']==target),node+"-DSP2"]=d2
                modesplit.loc[(modesplit['source']==source) & (modesplit['target']==target),node+"-Cost"]=cost
        except nx.NetworkXNoPath:
            lg.info("No second disjoint path between %s and %s",source,target)
    modesplit=modesplit.fillna(0)
    report_path = 'MS2POutput-AllNodes_'+UserInput1+str(beta)
    if var1=='default':
        if not os.path.exists(os.path.join(report_path,var1)):
            os.makedirs(os.path.join(report_path,var1))
        outName='MS2PAllNodes'+'_'+UserInput+'.xlsx'
        writer=pd.ExcelWriter(os.path.join(report_path,var1,outName), engine='xlsxwriter')
        modesplit.to_excel(writer,UserInput)
        writer.save()
    else:
        if not os.path.exists(os.path.join(report_path,var1,fol)):
            os.makedirs(os.path.join(report_path,var1,fol))
        outName='MS2PAllNodes'+'_'+UserInput+incrmnt
        writer=pd.ExcelWriter(os.path.join(report_path,var1,fol,outName), engine='xlsxwriter')
        modesplit.to_excel(writer,UserInput)
        writer.save()       

cwd = os.getcwd()

var1=input('Select "default" for running with default parameter otherwise "incerement" : ')  
var1=var1.lower()
Beta=input('Modal split parameter:')
Beta=float(Beta)
UserInput=input('Select weight(Time, Distance or Travelcost) for links: ')
UserInput=UserInput.title()
UserInput1=input('Select from network(water,rail,road or synchromodal): ')
UserInput1=UserInput1.lower()

xls2=pd.ExcelFile('list.xlsx')
xls3=pd.ExcelFile('Demand.xlsx')
Demand=pd.read_excel(xls3,'Demand')
Interdependent=pd.read_excel(xls2,'InterdependNode')
ODpair=pd.read_excel(xls2,'OD')

#Make a group of interdependent nodes which are related to each other
InterdepPair=[]
for index,row in Interdependent.iterrows():
    Interdeps=[]
    nam,ID=row['Interdep'].split("_")  
    for index,row in Interdependent.iterrows():
        nams,IDs=row['Interdep'].split("_")
        if IDs==ID:
            Interdeps.append(row['Interdep'])
    InterdepPair.append(Interdeps)
removeduplicates = set(tuple(x) for x in InterdepPair)
InterDepPair = [ list(x) for x in removeduplicates ] 


if str(var1)==str('default'):
    path=cwd+'\\LinkList\\default\\'
    xls=pd.ExcelFile(path+'MatrixCost_default.xlsx')
    lg.basicConfig(filename='MS2PAllNodes.log',level=lg.INFO)
    RunMS2P(var1,UserInput,UserInput1,InterDepPair,Demand,xls,None,None,Beta)
    lg.shutdown()

else:
    path=cwd+'\\LinkList\\time\\'
    folders=os.listdir(path)
    for f in folders:
        xlpath=path+'\\'+f
        xlses=os.listdir(xlpath)
        for xl in xlses:
            xls=pd.ExcelFile(xlpath+'\\'+xl)
            incrmnt=re.split('_',xl)
            lg.basicConfig(filename='MS2PAllNodes.log',level=lg.INFO)
            RunMS2P(var1,UserInput,UserInput1,InterDepPair,Demand,xls,f,incrmnt[1],Beta)
            lg.shutdown()