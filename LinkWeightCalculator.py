                                                                                                     # -*- coding: utf-8 -*-
"""
Created on Wed Apr 25 11:51:30 2018

@author: NaVnEeT

This code will calculate and update the link weight of the synchromodal transport network (road, rail, water, terminal).
The default value of different paramenter are taken from BasGoed model except for capacity.
More detail about these value can be found in following two master thesis:
    1. http://resolver.tudelft.nl/uuid:ed5af468-4555-4018-8463-43165db2775f
    2. http://resolver.tudelft.nl/uuid:808c664b-dd20-478f-8b4a-130ea99d0a60

INPUT: An excel named matrix having 4 sheets Water, Road, Rail, Terminal and OD. 
       Each sheet has list of links with corresponding distance (in meters) 

OUTPUT: A folder named as LinkList containing three sub-folders:-
        1. Default - Caontains an excel with default link weight
        2. Time - Contains folder for each modality and combination of modality. Each folder contains excel with updated travel time per link and updated general cost of traveling per link.
                    The amount of decrement is added in the name of excel, for example 'MatrixCost_0.3.xlsx' represent a drement of 30%
        3. Capacity - Contains folder for each modality and combination of modality. Each folder contains excel with updated capacity per link.
                    The amount of decrement is added in the name of excel, for example 'MatrixCost_0.3.xlsx' represent a drement of 30%
                    
Note1: The decremnt percentage in link weight can be updated by changing the value in line 260 and 263
"""

import pandas as pd
import os
import numpy as np

xls=pd.ExcelFile('Matrix.xlsx')
water=pd.read_excel(xls,'Water')
road=pd.read_excel(xls,'Road')
rail=pd.read_excel(xls,'Rail')
Translink=pd.read_excel(xls,'Terminal')                      
AccEgrLink=pd.read_excel(xls,'OD')

"Default value from BasGoed"
DistCostWater,DistCostRoad,DistCostRail=[0.004,0.038,0.004]
TimeCostWater,TimeCostRoad,TimeCostRail=[0.13,3.98,1.0]
paramA,paramB=[26.285,0.146]
AvgSpeedWater,AvgSpeedRoad,AvgSpeedRail,AvgSpeedOD=[15,60,90,30]
CapacityRoad,CapacityODP,CapacityRail,CapacityWater=[4600.0,4600.0,4400.0,6000.0]
"Default values for BPR function"
alpha=0.15
'''Where BetaRDW is for roadways and waterways and BetaRl is for railways'''
BetaRDW,BetaRl=[4.0,8.0]
       
def GeoLinkCost(DistCost,TimeCost,Dist,AvgSpeed):
    "Calculate geographical link cost for each type of moalities"
    CostGeoLink=DistCost*Dist+TimeCost*(Dist/AvgSpeed)
    return(CostGeoLink)
    
def TransLinkCost(DistCost,TimeCost,Dist,AvgSpeed,paraA,paraB,NoOfContainers,modality):
    "Calculate the transhipment link(terminal to geonode) cost"
    if str(modality)==str('road'):
        TranshipmentCost=(paraA*(NoOfContainers**-paraB))+(1.5*DistCost*Dist)+TimeCost*((1.5*Dist)/AvgSpeed)
    else:
        TranshipmentCost=paraA*(NoOfContainers**-paraB)
    return(TranshipmentCost)

def AccEgrLinkCost(DistCost,TimeCost,Dist,AvgSpeed,LinkHandlingCost):
    "calculate access/egress link cost for each link"
    AccEgrCost=(1.5*DistCost*Dist)+TimeCost*((1.5*Dist)/AvgSpeed)+LinkHandlingCost
    return(AccEgrCost)

def WaterCost(water,alpha,Beta,Capacity,AvgSpeedWater):
    '''Calculate and update link weight for water network'''
    watertemp=water.copy()
    WCost=[]
    Wtime=[]
    watertemp['Distance']=watertemp['Distance']/1000
    watertemp['alpha']=alpha
    watertemp['Beta']=Beta
    watertemp['Capacity']=Capacity
    for distances in watertemp['Distance']:
        Wcost=GeoLinkCost(DistCostWater,TimeCostWater,distances,AvgSpeedWater)
        Wtm=distances/AvgSpeedWater
        WCost.append(Wcost)
        Wtime.append(Wtm)
    watertemp['Time']=Wtime
    watertemp['Travelcost']=WCost
    return(watertemp)

def RoadCost(road,alpha,Beta,Capacity,AvgSpeedRoad):
    '''Calculate and update link weight for road network'''
    roadtemp=road.copy()
    RCost=[]
    Rtime=[]
    roadtemp['Distance']=roadtemp['Distance']/1000
    roadtemp['alpha']=alpha
    roadtemp['Beta']=Beta
    roadtemp['Capacity']=Capacity
    for distances in roadtemp['Distance']:
        Rcost=GeoLinkCost(DistCostRoad,TimeCostRoad,distances,AvgSpeedRoad)
        Rtm=distances/AvgSpeedRoad
        RCost.append(Rcost)
        Rtime.append(Rtm)
    roadtemp['Time']=Rtime
    roadtemp['Travelcost']=RCost
    return(roadtemp)

def RailCost(rail,alpha,Beta,Capacity,AvgSpeedRail):
    '''Calculate and update link weight for rail network'''
    railtemp=rail.copy()
    RaCost=[]
    Ratime=[]
    railtemp['Distance']=railtemp['Distance']/1000
    railtemp['alpha']=alpha
    railtemp['Beta']=Beta
    railtemp['Capacity']=Capacity
    for distances in railtemp['Distance']:
        Racost=GeoLinkCost(DistCostRail,TimeCostRail,distances,AvgSpeedRail)
        Ratm=distances/AvgSpeedRail
        Ratime.append(Ratm)
        RaCost.append(Racost)
    railtemp['Time']=Ratime
    railtemp['Travelcost']=RaCost
    return(railtemp)

def TerminalCost(Translink,alpha,Beta,AvgSpeedOD,AvgSpeedRail,AvgSpeedWater):
    '''Calculate and update link weight for terminals'''
    Translinktemp=Translink.copy()
    TranslinkCost=[]
    TranslinkTime=[]
    Translinktemp['Distance']=Translinktemp['Distance']/1000
    for row in range(len(Translinktemp)):
        if Translinktemp['Node-B'][row][0]=='R' or Translinktemp['Node-A'][row][0]=='R':
            Tcost=TransLinkCost(DistCostRoad,TimeCostRoad,Translinktemp['Distance'][row],AvgSpeedOD,paramA,paramB,Translinktemp['Capacity'][row],'road')
            Ttm=(1.5*Translinktemp['Distance'][row])/AvgSpeedOD
        elif Translinktemp['Node-B'][row][0]=='S' or Translinktemp['Node-A'][row][0]=='S':
            Tcost=TransLinkCost(0,0,0,0,paramA,paramB,Translinktemp['Capacity'][row],'rail')
            Ttm=Translinktemp['Distance'][row]/AvgSpeedRail
        else:
            Tcost=TransLinkCost(0,0,0,0,paramA,paramB,Translinktemp['Capacity'][row],'water')
            Ttm=Translinktemp['Distance'][row]/AvgSpeedWater
        TranslinkTime.append(Ttm)
        TranslinkCost.append(Tcost)
    Translinktemp['Time']=TranslinkTime
    Translinktemp['Travelcost']=TranslinkCost
    Translinktemp['alpha']=alpha
    Translinktemp['Beta']=Beta
    return(Translinktemp)

def ODlinkCost(AccEgrLink,alpha,Beta,Capacity,AvgSpeedOD):
    '''Calculate and update link weight for OD links'''
    AccEgrLinktemp=AccEgrLink.copy()
    ODCost=[]
    ODTime=[]
    AccEgrLinktemp['Distance']=AccEgrLinktemp['Distance']/1000
    AccEgrLinktemp['alpha']=alpha
    AccEgrLinktemp['Beta']=Beta
    AccEgrLinktemp['Capacity']=Capacity
    for distances in AccEgrLinktemp['Distance']:
        AEcost=AccEgrLinkCost(DistCostRoad,TimeCostRoad,distances,AvgSpeedOD,1)
        ODtm=(1.5*distances)/AvgSpeedOD
        ODCost.append(AEcost)
        ODTime.append(ODtm)
    AccEgrLinktemp['Time']=ODTime
    AccEgrLinktemp['Travelcost']=ODCost
    return(AccEgrLinktemp)

def MatrixCostOutput(watercost,roadcost,railcost,terminalcost,odcosts,increment,incrementtype,networks):
    '''Create output as excel'''
    report_path='LinkList'
    if len(networks)==1:
        if not os.path.exists(os.path.join(report_path, incrementtype,networks[0])):
            os.makedirs(os.path.join(report_path, incrementtype,networks[0]))
        outName='MatrixCost_'+str(increment)+'.xlsx' 
        writer=pd.ExcelWriter(os.path.join(report_path,incrementtype,networks[0],outName), engine='xlsxwriter')
        watercost.to_excel(writer,'Water')
        roadcost.to_excel(writer,'Road')
        railcost.to_excel(writer,'Rail')
        terminalcost.to_excel(writer,'Terminal')
        odcosts.to_excel(writer,'OD')    
        writer.save()
    elif len(networks)>1:
        folderName=networks[0]+networks[1]
        if not os.path.exists(os.path.join(report_path, incrementtype,folderName)):
            os.makedirs(os.path.join(report_path, incrementtype,folderName))
        outName='MatrixCost_'+str(increment)+'.xlsx' 
        writer=pd.ExcelWriter(os.path.join(report_path,incrementtype,folderName,outName), engine='xlsxwriter')
        watercost.to_excel(writer,'Water')
        roadcost.to_excel(writer,'Road')
        railcost.to_excel(writer,'Rail')
        terminalcost.to_excel(writer,'Terminal')
        odcosts.to_excel(writer,'OD')    
        writer.save()
    else:
        FolderName='default'
        if not os.path.exists(os.path.join(report_path,FolderName)):
            os.makedirs(os.path.join(report_path,FolderName))
        outName='MatrixCost_default.xlsx' 
        writer=pd.ExcelWriter(os.path.join(report_path,FolderName,outName), engine='xlsxwriter')
        watercost.to_excel(writer,'Water')
        roadcost.to_excel(writer,'Road')
        railcost.to_excel(writer,'Rail')
        terminalcost.to_excel(writer,'Terminal')
        odcosts.to_excel(writer,'OD')    
        writer.save()
        
        
        
    
def NetworkParamUpdate(Typ,networks,incrementtype,increment):
    '''Calculate and update network link weights'''
    CapacityRD,CapacityOD,CapacityRl,CapacityWtr=[CapacityRoad,CapacityODP,CapacityRail,CapacityWater]
    if str(Typ) != str('default'):
        AvgSpeedWtr,AvgSpeedRd,AvgSpeedRl,AvgSpeedODlink=[AvgSpeedWater,AvgSpeedRoad,AvgSpeedRail,AvgSpeedOD]        
        if str(incrementtype) == str('time'):
            for i in networks:
                if str(i)==str('road'):
                    AvgSpeedRd= AvgSpeedRd*(1.0-increment)
                    AvgSpeedODlink= AvgSpeedODlink*(1.0-increment)
                elif str(i)==str('rail'):
                    AvgSpeedRl=AvgSpeedRl*(1.0-increment)
                else:
                    AvgSpeedWtr=AvgSpeedWtr*(1.0-increment)
            watercost=WaterCost(water,alpha,BetaRDW,CapacityWtr,AvgSpeedWtr)
            roadcost=RoadCost(road,alpha,BetaRDW,CapacityRD,AvgSpeedRd)
            railcost=RailCost(rail,alpha,BetaRl,CapacityRl,AvgSpeedRl)
            terminalcost=TerminalCost(Translink,alpha,BetaRDW,AvgSpeedODlink,AvgSpeedRl,AvgSpeedWtr)
            odcosts=ODlinkCost(AccEgrLink,alpha,BetaRDW,CapacityOD,AvgSpeedODlink)
            MatrixCostOutput(watercost,roadcost,railcost,terminalcost,odcosts,increment,incrementtype,networks)
                
        else:
            CapacityRD,CapacityOD,CapacityRl,CapacityWtr=[CapacityRoad,CapacityODP,CapacityRail,CapacityWater]
            for i in networks:
                if str(i)=='road':
                    CapacityRD= CapacityRD*(1.0-increment)
                    CapacityOD= CapacityOD*(1.0-increment)
                elif str(i)=='rail':
                    CapacityRl=CapacityRl*(1.0-increment)
                else:
                    CapacityWtr=CapacityWtr*(1.0-increment)
            watercost=WaterCost(water,alpha,BetaRDW,CapacityWtr,AvgSpeedWater)
            roadcost=RoadCost(road,alpha,BetaRDW,CapacityRD,AvgSpeedRoad)
            railcost=RailCost(rail,alpha,BetaRl,CapacityRl,AvgSpeedRail)
            terminalcost=TerminalCost(Translink,alpha,BetaRDW,AvgSpeedOD,AvgSpeedRail,AvgSpeedWater)
            odcosts=ODlinkCost(AccEgrLink,alpha,BetaRDW,CapacityOD,AvgSpeedOD)
            MatrixCostOutput(watercost,roadcost,railcost,terminalcost,odcosts,increment,incrementtype,networks)

    else:
        watercost=WaterCost(water,alpha,BetaRDW,CapacityWtr,AvgSpeedWater)
        roadcost=RoadCost(road,alpha,BetaRDW,CapacityRD,AvgSpeedRoad)
        railcost=RailCost(rail,alpha,BetaRl,CapacityRl,AvgSpeedRail)
        terminalcost=TerminalCost(Translink,alpha,BetaRDW,AvgSpeedOD,AvgSpeedRail,AvgSpeedWater)
        odcosts=ODlinkCost(AccEgrLink,alpha,BetaRDW,CapacityOD,AvgSpeedOD)
        MatrixCostOutput(watercost,roadcost,railcost,terminalcost,odcosts,increment,incrementtype,networks)
userInput=input('chose \'default\' for orginal link weight calculation or choose \'NetworkParam\' for network parameter update: ')
userInput=userInput.lower()
if str(userInput)==str('default'):
    NetworkParamUpdate(userInput,[],None,None)
else:
    userinput1=input('Parameter to be updated (time or capacity):')
    userinput1=userinput1.lower()
    layers=[['rail'],['road'],['water'],['rail','road'],['water','rail'],['water','road']]
    if str(userinput1)==str('time'):
        for layer in layers:
            for decrement in np.arange(0.3,0.9,0.1):
                NetworkParamUpdate(userInput,layer,userinput1,np.around(decrement,1))
    elif str(userinput1)==str('capacity'):
        decrements=[0.2,0.4,0.6,0.8,0.9]
        for layer in layers:
            for decrement in decrements:
                NetworkParamUpdate(userInput,layer,userinput1,decrement)
    else:
        print('Not an updatable parameter')

