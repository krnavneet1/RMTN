# -*- coding: utf-8 -*-
"""
Created on Mon Mar 19 20:57:14 2018

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

def RunAoN(var1,UserInput,UserInput1,InterDepPair,Demand,xls,fol,incrmnt):
    '''Reading from excel-workbook(edge-list) and creating the network'''
    WaterWayUID=pd.read_excel(xls,'Water')
    RoadUID=pd.read_excel(xls,'Road')
    RailUID=pd.read_excel(xls,'Rail')
    ODUID=pd.read_excel(xls,'OD')
    TerminalUID=pd.read_excel(xls,'Terminal')
#    WaterWayUID=WaterWay.drop(['NewNode-A','NewNode-B'],axis=1)
#    RoadUID=Road.drop(['NewNode-A','NewNode-B'],axis=1)
#    RailUID=Rail.drop(['NewNode-A','NewNode-B'],axis=1)
#    ODUID=OD.drop(['NewNode-A','NewNode-B'],axis=1)
#    TerminalUID=Terminal.drop(['NewNode-A','NewNode-B'],axis=1)
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

    print('Calculating...')    
          
    headers=[]
    for pair in InterDepPair:
        path1=pair[0]+"-"+pair[1]+"-path"
        headers.append(path1)
        costs=pair[0]+"-"+pair[1]+"-Cost"
        headers.append(costs)
    orglen=['IntialPath','IntialCost']
    headers=orglen+headers
    header=pd.DataFrame(columns=headers)
    header=header.fillna(0)
    AoN=pd.concat([Demand,header],axis=1)
    for source,target,demand in Demand.itertuples(index=False):
        DummyGraph=network.copy()
        Path,length=ShortestPath(DummyGraph,source,target)
        AoN.loc[(AoN['source']==source) & (AoN['target']==target),'IntialPath']=length
        AoN.loc[(AoN['source']==source) & (AoN['target']==target),'IntialCost']=length*demand
        try:
            for pairs in InterDepPair:
                DummyGraph1=network.copy()
                interdepinfra1=list(set(pairs).intersection(set(Path)))
                if len(interdepinfra1)>0:
                    DummyGraph1.remove_nodes_from(pairs)
                    newpath,newlength=ShortestPath(DummyGraph1,source,target)
                    AoN.loc[(AoN['source']==source) & (AoN['target']==target),pairs[0]+"-"+pairs[1]+"-path"]=newlength
                    AoN.loc[(AoN['source']==source) & (AoN['target']==target),pairs[0]+"-"+pairs[1]+"-Cost"]=newlength*demand
                else:
                    '''If there is no interdependent infra in the path the cost is considered is zero as the infra has no effect on intial cost'''
                    AoN.loc[(AoN['source']==source) & (AoN['target']==target),pairs[0]+"-"+pairs[1]+"-path"]=length
                    AoN.loc[(AoN['source']==source) & (AoN['target']==target),pairs[0]+"-"+pairs[1]+"-Cost"]=length*demand
        except nx.NetworkXNoPath:
            print("No second path between",source,"and",target,"for pairs",pairs[0],"and",pairs[1])
    #AoN=AoN.convert_objects(convert_numeric=True).fillna(0)
    report_path = 'AoNOutput_'+UserInput1
    if var1=='default':
        if not os.path.exists(os.path.join(report_path,var1)):
            os.makedirs(os.path.join(report_path,var1))
        outName='AllOrNothing'+'_'+UserInput+'.xlsx'
        writer=pd.ExcelWriter(os.path.join(report_path,var1,outName), engine='xlsxwriter')
        AoN.to_excel(writer,UserInput)
        writer.save()
    else:
        if not os.path.exists(os.path.join(report_path,var1,fol)):
            os.makedirs(os.path.join(report_path,var1,fol))
        outName='AllOrNothing'+'_'+UserInput+incrmnt
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
Interdependent=pd.read_excel(xls2,'InterdependNode')
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
#read demand matrix
xls3=pd.ExcelFile('Demand.xlsx')
Demand=pd.read_excel(xls3,'Demand')

if str(var1)==str('default'):
    path=cwd+'\\LinkList\\default\\'
    xls=pd.ExcelFile(path+'MatrixCost_default.xlsx')
    RunAoN(var1,UserInput,UserInput1,InterDepPair,Demand,xls,None,None)
else:
    path=cwd+'\\LinkList\\time\\'
    folders=os.listdir(path)
    for f in folders:
        xlpath=path+'\\'+f
        xlses=os.listdir(xlpath)
        for xl in xlses:
            xls=pd.ExcelFile(xlpath+'\\'+xl)
            incrmnt=re.split('_',xl)
            RunAoN(var1,UserInput,UserInput1,InterDepPair,Demand,xls,f,incrmnt[1])

