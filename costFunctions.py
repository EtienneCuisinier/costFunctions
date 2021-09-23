import time
import os
import shutil
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

#dedicated modules
from representativePeriods import representativePeriods
from dataList import dataList
from runPerseeBatch import runPerseeBatch

mpl.rcParams['figure.dpi'] = 120
plt.style.use('seaborn-whitegrid')

class costFunctions:
        
    def __init__(self,loc, nameDataOrignal, nameData364Days, nameConfig, nameSettings, namePLAN, nameFbsfLog, nameSortie, storageID, lossesID, efficiencyID, initSocID, finalSocID, capacityID, powerID, costID, week=False, day=False, nbPeriods=-1):
        """Author: Etienne Cuisinier (etienne.cuisinier@cea.fr)"""
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        periodSets=[]

        ##################### 1.0) Cutting the data series into 13 periods of 4 weeks ('month') or customized
        dfData=pd.read_csv(loc+nameData364Days,sep=';')
        col=dfData.columns
        dateTime=dfData[col[0]]
        dfData=dfData.reindex(columns=list(dfData.columns[1:]))
        col=dfData.columns
        
        listPeriods=[]
        if nbPeriods<0:
            nbPeriods=13
        if len(dateTime)/24/nbPeriods % 1 > 0:
            print("ERROR: the number of days in the data serie must be a multiple of nbPeriods ")
        else:    
            for period in range(nbPeriods): 
                temp=[]
                index=period*int(len(dateTime)/nbPeriods)

                for k in range(int(len(dateTime)/nbPeriods)):
                    temp.append([])
                    for j in range(len(dfData.iloc[period])):
                        temp[k].append(dfData.iloc[k+index][j])
                        
                listPeriods.append(temp) 
            self.listPeriods=listPeriods
            periodSets.append(listPeriods)
            
        ##################### 1.1) Cutting the data series into 52 periods of 1 week (optional, adds one set of periods)
        if week:              
            listWeeks=[]
            nbWeeks=52
            for period in range(nbWeeks): 
                temp=[]
                index=period*int(len(dateTime)/nbWeeks)
            
                for k in range(int(len(dateTime)/nbWeeks)):
                    temp.append([])
                    for j in range(len(dfData.iloc[period])):
                        temp[k].append(dfData.iloc[k+index][j])
                        
                listWeeks.append(temp)  
            self.listWeeks=listWeeks
            periodSets.append(listWeeks)

        ##################### 1.2) Cutting the data series into 364 periods of 1 day (optional, adds one set of periods)
        if day:                
            listDays=[]
            nbDays=364
            for period in range(nbDays): 
                temp=[]
                index=period*int(len(dateTime)/nbDays)
            
                for k in range(int(len(dateTime)/nbDays)):
                    temp.append([])
                    for j in range(len(dfData.iloc[period])):
                        temp[k].append(dfData.iloc[k+index][j])
                        
                listDays.append(temp) 
            self.listDays=listDays
            periodSets.append(listDays)

        #Files locations and Persee files
        self.loc=loc
        self.nameDataOrignal=nameDataOrignal
        self.nameData364Days=nameData364Days
        self.nameConfig=nameConfig
        self.nameSettings=nameSettings
        self.namePLAN=namePLAN
        self.nameFbsfLog=nameFbsfLog
        self.nameSortie=nameSortie
        
        #Technical parameters names
        self.storageID=storageID
        self.lossesID=lossesID
        self.efficiencyID=efficiencyID
        self.initSocID=initSocID
        self.finalSocID=finalSocID
        self.capacityID=capacityID
        self.powerID=powerID
        self.costID=costID       
        
        #Data series splitted into periods
        self.periodSets=periodSets
        self.nbPeriods=nbPeriods
        self.sizePeriods=len(dateTime)/nbPeriods

    def computeRp(self, dt=1, nRP=1, sRP=1, nBins=40, imposedPeriod=[], imposePeak=[], binMethod=1, timeLimitRp=60, gap=0.0001, threads=8, weightsOnDataSets=[]):
          
        allPeriodsRp=[]
        
        ##################### 2) Building representative period(s) for each period
        for periodSet in range(len(self.periodSets)):
            current=[]
            for period in range(len(self.periodSets[periodSet])):     
                #Formating
                data=[]
                for j in range(len(self.periodSets[periodSet][0][0])):
                    data.append([])
                    for k in range( len(self.periodSets[periodSet][period])):
                        value=self.periodSets[periodSet][period][k][j]
                        data[j].append(value)
                
                print("Computing representative period",str(period),"of periods of length",str(len(self.periodSets[periodSet][0])))
                
                if len(self.periodSets[periodSet][0])==24: 
                    rp=representativePeriods(data, dt, 1, 1, nBins, timeLimit=timeLimitRp, gap=gap, threads=threads, imposedPeriod=imposedPeriod, imposePeak=imposePeak, binMethod=binMethod)  
                else:
                    rp=representativePeriods(data, dt, nRP, sRP, nBins, timeLimit=timeLimitRp, gap=gap, threads=threads, imposedPeriod=imposedPeriod, imposePeak=imposePeak, binMethod=binMethod, weightsOnDataSets=weightsOnDataSets)  
                current.append(rp)
                
            allPeriodsRp.append(current)
        
        self.allPeriodsRp=allPeriodsRp
        self.dt=dt
        self.nRP=nRP
        self.sRP=sRP
        
    def defineStorageLevelDeltas(self, dt=1, nbPoints=20, maxStorageDeltaPerPeriod=1):

        ##################### 3) Definition of the discretization of the cost functions computation
        
        settings=dataList(self.nameSettings,self.loc)
        sizeSto=float(settings.findParamValue(self.storageID+self.capacityID,ignoreComments=True))
        powerSto=float(settings.findParamValue(self.storageID+self.powerID,ignoreComments=True))
        efficiencySto=float(settings.findParamValue(self.storageID+self.efficiencyID,ignoreComments=True))
        
        if powerSto <= 0:
            print("ERROR: the maximum power of the storage must be > 0 !")
        else:
            granularity=1/nbPoints
            maxSto=min(maxStorageDeltaPerPeriod*sizeSto,powerSto*dt*len(self.listPeriods[0])*efficiencySto)
            deltas=[]
            steps=[]
            for periodSet in range(len(self.allPeriodsRp)):
                deltas.append([])
                for j in range(int(8760/self.allPeriodsRp[periodSet][0].nbPdt)):
                    deltas[periodSet].append([])
                    for i in range(-nbPoints,nbPoints+1):   
                        deltas[periodSet][j].append(i*granularity*maxSto*self.allPeriodsRp[periodSet][0].nbPdt/self.sizePeriods)
                steps.append(deltas[periodSet][0][1]-deltas[periodSet][0][0])
        
        self.dt=dt        
        self.steps=steps 	  
        self.sizeSto=sizeSto
        self.deltas=deltas

    def computeCf(self, nameBatch, storageID, lossesID, initSocID, finalSocID, gap='1.e-3', timeLimit='600', initSOC=0.01, converterState=False, converterID='', absInitialStateID=''):
        self.cFmethod="basic"
        
        allPeriodsFunctions=[]
        allPeriodsFunctionsOff=[]
            
        ##################### 4) Computation of cost functions
        for periodSet in range(len(self.allPeriodsRp)):
            print("------------> set of periods of length:",str(len(self.periodSets[periodSet][0])))

            timeStart=time.perf_counter()
                
            #reading Persee data file
            dataPersee=np.genfromtxt(self.loc+self.nameDataOrignal, delimiter=';', dtype=str)
            dataPersee[0].tolist()
            
            #modification of the Persee configuration file
            configuration=dataList(self.nameConfig,self.loc)
            configuration.changeParamValue('futursize', str(len(self.allPeriodsRp[periodSet][0].rpList[0][0]))) 
            configuration.changeParamValue('pastsize', '24') 
            configuration.changeParamValue('timeshift', '24') 
            configuration.changeParamValue('CycleStop', '1') 
            configuration.commentParam('<TimeStepFile>') 
            configuration.commentParam('<ComputationFuturSize>') 
            
            #modification of the Persee settings file
            settings=dataList(self.nameSettings,self.loc)
            settings.changeParamValue('Cplex.Gap', gap) 
            settings.changeParamValue('Cplex.TimeLimit', timeLimit) 
            settings.changeParamValue(storageID+lossesID, '0.') #losses are already considered when in the MILP model using the cost functions
            
            costs=[]
            costsOff=[]

            if converterState:
                settings.changeParamValue(converterID+absInitialStateID, '1')
            
            for period in range(len(self.allPeriodsRp[periodSet])):
            
                print("-------> period ",period)
                
                #writing Persee files for the cost functions computation
                for rp in range(self.allPeriodsRp[periodSet][period].nRP):
                    
                    currentRp=self.allPeriodsRp[periodSet][period]
                    name='\\'+self.nameDataOrignal+'_'+str(self.allPeriodsRp[periodSet][period].nbPdt)+'_period'+str(period)+'_rp'+str(rp)+'.csv'
                
                    writeRp(dataPersee,currentRp,self.listPeriods,self.dt,self.loc+'//representativePeriods',name,noRp=rp)
                                    
                #computation of the operational cost for each storage delta
                originalPoints=[]
                originalPointsOff=[]
                    
                for point in range(len(self.deltas[periodSet][period])-1,-1,-1):
                    
                    ratio=self.allPeriodsRp[periodSet][period].sRPh / self.allPeriodsRp[periodSet][period].nbPdt #ratio to extrapolate the cost of the original period from the cost of the representative period
                    
                    if self.deltas[periodSet][period][point] >= 0:
                        settings.changeParamValue(storageID+initSocID, str(initSOC)) #the default initial state of charge can be set positive to avoid side effects (10% by default)
                        settings.changeParamValue(storageID+finalSocID, str(self.deltas[periodSet][period][point]*ratio/self.sizeSto + initSOC)) 
                    else: 
                        settings.changeParamValue(storageID+initSocID, str(-self.deltas[periodSet][period][point]*ratio/self.sizeSto + initSOC))
                        settings.changeParamValue(storageID+finalSocID, str(initSOC))
             
                    #computations are done for each representative period of the current period, costs are then weighted
                    weightedCosts=[]
                    weightedCostsOff=[]
                    ignoredPointWeights=[] #if one of the representative period yield an unfeasible problem, its weight is recorded to further ajust the final cost 

                    for rp in range(self.allPeriodsRp[periodSet][period].nRP):
                        name='representativePeriods/'+self.nameDataOrignal[1:]+'_'+str(self.allPeriodsRp[periodSet][period].nbPdt)+'_period'+str(period)+'_rp'+str(rp)+'.csv'
                        configuration.changeParamValue(self.nameDataOrignal[1:], './'+name)
            
                        #writing Persee files
                        settings.writeFile()
                        configuration.writeFile()
            
                        #running Persee
                        timeSimulation=runPerseeBatch(self.loc,nameBatch,self.nameFbsfLog)
                    
                        #looking for unfeasible problem
                        if timeSimulation==-2: 
                            ignoredPointWeights.append(self.allPeriodsRp[periodSet][period].optWeightsCompact[rp])
            
                        else: 
                            #reading results
                            resultsFile=dataList(self.namePLAN,self.loc)
                            originalCost=float(resultsFile.findParamValue(self.costID,ignoreComments=False)) 
                            
                            cost=originalCost*self.allPeriodsRp[periodSet][period].optWeightsCompact[rp]
                            
                            #if the initial state of the converter has an important side effect on the operational cost 
                            #both initial state cases are computed to build two cost functions (and so that the cost to change the state is accounted only once)
                            if converterState:
                               
                                #the other starting point is computed, if the obtained cost is inferior, both results are weighted
                                settings.changeParamValue(converterID+absInitialStateID, '0')
                                settings.writeFile()
                                
                                #running Persee
                                # print("relaunch with new initial state")
                                timeSimulation=runPerseeBatch(self.loc,nameBatch,self.nameFbsfLog)

                                #back to the original state
                                settings.changeParamValue(converterID+absInitialStateID, '1')
                                settings.writeFile()
                                
                                #ignoring unfeasible problem
                                if timeSimulation != -2: 
                                    resultsFile=dataList(self.namePLAN,self.loc)
                                    originalCostOff=float(resultsFile.findParamValue(self.costID,ignoreComments=False)) 
                                    
                                    #results are weighted so that the cost to change the state is accounted only once
                                    totalWeight=sum(self.allPeriodsRp[periodSet][period].optWeightsCompact)
                                    if originalCostOff < originalCost:
                                        cost=(originalCost + originalCostOff*(1/ratio-1))*self.allPeriodsRp[periodSet][period].optWeightsCompact[rp]/totalWeight
                                        costOff=originalCostOff*self.allPeriodsRp[periodSet][period].optWeightsCompact[rp]
                                    else:
                                        cost=originalCost*self.allPeriodsRp[periodSet][period].optWeightsCompact[rp]
                                        costOff=(originalCostOff + originalCost*(1/ratio-1))*self.allPeriodsRp[periodSet][period].optWeightsCompact[rp]/totalWeight   
                            
                            weightedCosts.append(cost)
                            if converterState:
                                weightedCostsOff.append(costOff)
                            #     print("representative period "+str(rp)+" done, ON state, cost = "+str(cost)+", with weight = "+str(self.allPeriodsRp[periodSet][period].optWeightsCompact[rp]))
                            #     print("representative period "+str(rp)+" done, OFF state, cost = "+str(costOff)+", with weight = "+str(self.allPeriodsRp[periodSet][period].optWeightsCompact[rp]))
                            # else:
                            #     print("representative period "+str(rp)+" done, cost = "+str(cost)+", with weight = "+str(self.allPeriodsRp[periodSet][period].optWeightsCompact[rp]))

                    #summing weighted costs, ajustement made if some costs were ignored due to computation failures
                    if (len(ignoredPointWeights)==0 or (len(ignoredPointWeights)>0 and len(ignoredPointWeights)<self.allPeriodsRp[periodSet][period].nRP)):
                        coefAdjustWeights=(1/ratio)/(1/ratio - sum(ignoredPointWeights))
                        
                        sumCosts=sum(weightedCosts)*coefAdjustWeights
                        originalPoints.append([self.deltas[periodSet][period][point],sumCosts])
                        
                        sumCostsOff=sum(weightedCostsOff)*coefAdjustWeights
                        originalPointsOff.append([self.deltas[periodSet][period][point],sumCostsOff])

                        if converterState:
                            print("delta = ",self.deltas[periodSet][period][point], " done, corresponding cost (converter ON) = ", str(sumCosts))
                            print("delta = ",self.deltas[periodSet][period][point], " done, corresponding cost (converter OFF) = ", str(sumCostsOff))
                        else:
                            print("delta = ",self.deltas[periodSet][period][point], " done, corresponding cost = ", str(sumCosts))

                    else:
                        print("Computations failed for this point, point ignored")
                    
                    if sumCosts==0 and sumCostsOff==0: #stopping computations if costs are null
                        break
                        
                originalPoints.reverse()
                originalPointsOff.reverse()
                costs.append(originalPoints)
                costsOff.append(originalPointsOff)
            
            allPeriodsFunctions.append(costs)        
            allPeriodsFunctionsOff.append(costsOff)    

        #restoring Persee files     
        settings.reinitData()
        settings.writeFile()
        configuration.reinitData()
        configuration.writeFile()

        self.allPeriodsFunctions=allPeriodsFunctions
        self.allPeriodsFunctionsOff=allPeriodsFunctionsOff

        self.configuration=configuration
        self.converterState=converterState
        
        timeTot=time.perf_counter() - timeStart
        print("Total computation time: ",timeTot," seconds")
        
    def extrapolateCf(self,absTolerance=5):
        timeStart=time.perf_counter()
        
        output=extrapolateCfOneConverterState(self.allPeriodsFunctions,self.periodSets,self.configuration,absTolerance=absTolerance)
            
        self.allPeriodsWeightedFunctions=output[0]
        self.allNbDaysInPeriod=output[1]
        
        if self.converterState:
            output=extrapolateCfOneConverterState(self.allPeriodsFunctionsOff,self.periodSets,self.configuration,absTolerance=absTolerance)
                
            self.allPeriodsWeightedFunctionsOff=output[0]
                 
        timeTot=time.perf_counter() - timeStart
        print("Costs extrapolation, total computation time: ",timeTot," seconds")
                
    def writeCf(self,ref=''):
        
        if self.converterState:                      
            writeCfOneConverterState(self.allPeriodsFunctions,self.allPeriodsWeightedFunctions,self.periodSets,self.allNbDaysInPeriod,self.storageID,self.loc,'\SeasonalCostsOn\\')
            writeCfOneConverterState(self.allPeriodsFunctions,self.allPeriodsWeightedFunctions,self.periodSets,self.allNbDaysInPeriod,self.storageID,self.loc,'\SeasonalCosts\\')
            writeCfOneConverterState(self.allPeriodsFunctionsOff,self.allPeriodsWeightedFunctionsOff,self.periodSets,self.allNbDaysInPeriod,self.storageID,self.loc,'\SeasonalCostsOff\\')
            if ref !='':
                writeCfOneConverterState(self.allPeriodsFunctions,self.allPeriodsWeightedFunctions,self.periodSets,self.allNbDaysInPeriod,self.storageID,self.loc,'\\'+ref+'_On\\')
                writeCfOneConverterState(self.allPeriodsFunctionsOff,self.allPeriodsWeightedFunctionsOff,self.periodSets,self.allNbDaysInPeriod,self.storageID,self.loc,'\\'+ref+'_Off\\')
                
        else:
            writeCfOneConverterState(self.allPeriodsFunctions,self.allPeriodsWeightedFunctions,self.periodSets,self.allNbDaysInPeriod,self.storageID,self.loc,'\SeasonalCosts\\')
            if ref !='':
                writeCfOneConverterState(self.allPeriodsFunctions,self.allPeriodsWeightedFunctions,self.periodSets,self.allNbDaysInPeriod,self.storageID,self.loc,'\\'+ref+'\\')

    def showRp(self, rebuildMethod='basic',periodSet=0, period=-1):
        
        if period >= 0 and period < len(self.allPeriodsRp[periodSet]):
            print("period=",period)
            self.allPeriodsRp[periodSet][period].showRp()
            self.allPeriodsRp[periodSet][period].showDcRp()
            # self.allPeriodsRp[periodSet][period].rebuildData(rebuildMethod)
            # self.allPeriodsRp[periodSet][period].showRebuiltData()
            
        else:
            for period in range(len(self.listPeriods)):
                print("period=",period)
                self.allPeriodsRp[periodSet][period].showRp()
                self.allPeriodsRp[periodSet][period].showDcRp()
                # self.allPeriodsRp[periodSet][period].rebuildData(rebuildMethod)
                # self.allPeriodsRp[periodSet][period].showRebuiltData()

    def readCf(self, ref, nbPeriodSets=1):
        
        if self.converterState:                      
            output=readCfOneConverterState(self.nbPeriods,self.sizePeriods,self.loc,'\\'+ref+'_On\\',nbPeriodSets)
            self.allPeriodsFunctions=output[0]
            self.allPeriodsWeightedFunctions=output[1]
            output=readCfOneConverterState(self.nbPeriods,self.sizePeriods,self.loc,'\\'+ref+'_Off\\',nbPeriodSets)
            self.allPeriodsFunctionsOff=output[0]
            self.allPeriodsWeightedFunctionsOff=output[1]
        else:                      
            output=readCfOneConverterState(self.nbPeriods,self.sizePeriods,self.loc,'\\'+ref+'\\',nbPeriodSets)
            self.allPeriodsFunctions=output[0]
            self.allPeriodsWeightedFunctions=output[1]
            
        
    def showCf(self, absTimeStep=-1, period=0, points='original', periodSet=0, converterState='on'):
        def scatter(pt,label=''):
            pt=pt.T
            pt=pt.tolist()
            plt.scatter(pt[0],pt[1],label=label)
            
        if absTimeStep>0:
            if converterState=='on':
                pt=np.array(self.allPeriodsWeightedFunctions[periodSet][period][absTimeStep])
                scatter(pt) 
                plt.title('Extrapolated cost function (set of periods of length '+str(len(self.periodSets[periodSet][0]))+'), period '+str(period)+' with absolute time step = '+str(absTimeStep))
            elif converterState=='off':
                pt=np.array(self.allPeriodsWeightedFunctionsOff[periodSet][period][absTimeStep])
                scatter(pt)
                plt.title('Extrapolated cost function (set of periods of length '+str(len(self.periodSets[periodSet][0]))+'), period '+str(period)+' with absolute time step = '+str(absTimeStep))

        else:
            if converterState=='on':
                pt=np.array(self.allPeriodsFunctions[periodSet][period])
                scatter(pt) 
                plt.title('Original cost function (set of periods of length '+str(len(self.periodSets[periodSet][0]))+'), period '+str(period))
            elif converterState=='off':
                pt=np.array(self.allPeriodsFunctionsOff[periodSet][period])
                scatter(pt) 
                plt.title('Original cost function (set of periods of length '+str(len(self.periodSets[periodSet][0]))+'), period '+str(period))
            elif converterState=='both':
                pt=np.array(self.allPeriodsFunctions[periodSet][period])
                ptOff=np.array(self.allPeriodsFunctionsOff[periodSet][period])
                scatter(pt,label="ON")
                scatter(pt,label="OFF")
                plt.title('Original cost function (set of periods of length '+str(len(self.periodSets[periodSet][0]))+'), period '+str(period))
                plt.legend(title='Converter initial state:')

        plt.xlabel('Storage delta')
        plt.ylabel('Cost')

def writeRp(dataPersee, rP, periods, dt, locDataPersee, name, noRp=-1):
    
    #write representative periods files for Persee
    dataRp=np.array(dataPersee[0:4].tolist())
    dataRp=dataRp.T
    dataRp=dataRp.tolist()
    
    if (noRp >= 0) :
        for k in range (0,len(rP.rpList[0][0])):
            dataRp[0].append(int((k+1)*60*60/dt))
    else : 
        for k in range (0,len(rP.rp[0])):
            dataRp[0].append(int((k+1)*60*60/dt))
    
    for n in range (0,len((periods[0][0]))):
        if (noRp >= 0) :
            dataRp[n+1].extend(rP.rpList[n][noRp])
        else : 
            dataRp[n+1].extend(rP.rp[n])

    #suppressing empty columns
    i=0
    while len(dataRp[len(dataRp)-1]) < 5 and len(dataRp)>0 : 
        i+=1
        del dataRp[len(dataRp)-1]

    dataRp=np.array(dataRp)
    dataRp=dataRp.T
    dataRp=dataRp.tolist()
    
    df = pd.DataFrame(dataRp)
    
    if not os.path.isdir(locDataPersee):
        os.mkdir(locDataPersee)
    
    df.to_csv(path_or_buf=locDataPersee+name,sep=';',decimal='.',header=False, index=False)   
    
def extrapolateCfOneConverterState(allPeriodsFunctions,periodSets,configuration,absTolerance=5):
    timeShift=float(configuration.findParamValue('<timeshift>',ignoreComments=True))

    ##################### 5) extrapolation of the cost fonctions for each weighted combination of two periods: building the 'mixed curves'
    
    allPeriodsWeightedFunctions=[]
    allNbDaysInPeriod=[]
		
    for periodSet in range(len(allPeriodsFunctions)):
        allWeightedFunctions=[]
        nbDaysInPeriod=int(len(periodSets[periodSet][0])/timeShift)
        allNbDaysInPeriod.append(nbDaysInPeriod)

        for period in range(len(allPeriodsFunctions[periodSet])):
            #building weighted functions
            weightedFunctions=[]
            for h in range(nbDaysInPeriod):
                weightedFunctions.append([])

            #the weighting if done between the current period and the next one
            nextPeriod=period+1
            if period+1 >= len(allPeriodsFunctions[periodSet]):
                nextPeriod=0
            
            #defining the lower and the upper function (it is assumed that function curves do not cross)
            sumCostsCurrentPeriod=0
            for point in range(len(allPeriodsFunctions[periodSet][period])):
                sumCostsCurrentPeriod+=allPeriodsFunctions[periodSet][period][point][1]
            sumCostsNextPeriod=0
            for point in range(len(allPeriodsFunctions[periodSet][nextPeriod])):
                sumCostsNextPeriod+=allPeriodsFunctions[periodSet][nextPeriod][point][1]
            
            if sumCostsCurrentPeriod > sumCostsNextPeriod:
                curveUp=np.array(allPeriodsFunctions[periodSet][period])
                curveDown=np.array(allPeriodsFunctions[periodSet][nextPeriod])
                currentUp=True
            else:              
                curveUp=np.array(allPeriodsFunctions[periodSet][nextPeriod])
                curveDown=np.array(allPeriodsFunctions[periodSet][period])
                currentUp=False
                
            #formating
            curveUp=curveUp.T
            curveUp=curveUp.tolist()
            curveDown=curveDown.T
            curveDown=curveDown.tolist()
                        
            #if one curve if longer than the other on the left, this part is called the 'head', the rest is called the 'core'
            #similarly, if one curve if longer than the other on the right, this part is called the 'tail'
            head=False
            if abs(curveUp[0][0]) > abs(curveDown[0][0]):
                curveHead=curveUp
                curveTail=curveDown
                head=True
            elif abs(curveUp[0][0]) < abs(curveDown[0][0]):
                curveHead=curveDown
                curveTail=curveUp
                head=True
            else: 
                curveHead=curveUp
                curveTail=curveDown
            
            j=0
            if (head):
                head=[[],[]]
                while curveTail[0][0] != curveHead[0][j] and j < len(curveHead[0]):
                    head[0].append(curveHead[0][j])
                    head[1].append(curveHead[1][j])
                    j+=1
                    if j == len(curveHead[0])-1: print('ERROR when building the head of a cost function')
                    #now, j is the first point of the curve with a head that is in the core
                
            #building the core of each curve
            mini=max(min(curveHead[0]), min(curveTail[0])) #minimum value excluding the head
            maxi=min(max(curveHead[0]), max(curveTail[0])) #maximum value excluding the tail
            
            step=curveHead[0][1]-curveHead[0][0]
				
            nbCorePoints=int((maxi-mini)/step)+1
    
            for i in range (j, j+nbCorePoints):
                #numerical approximations can lead to two points with strictly different x values but that can be considered as equal: hence a tolerance is considered 
                if round(curveHead[0][i],absTolerance) == round(curveTail[0][i-j],absTolerance): 
                    for h in range(nbDaysInPeriod):
                        #definition of the coefficient between the two functions
                        if currentUp:
                            coefHead=1-h/nbDaysInPeriod
                            coefTail=h/nbDaysInPeriod
                        else:
                            coefHead=h/nbDaysInPeriod
                            coefTail=1-h/nbDaysInPeriod
                            
                        balance=curveHead[1][i]*coefHead+curveTail[1][i-j]*coefTail
                        weightedFunctions[h].append([curveHead[0][i],balance])
                       
                else:
                    print('ERROR when building the core of an extrapolated cost function')
                    break
                    break
                    break 
                #now, is the last point of the curve with a head that is in the core
    
            #if one curve if longer than the other on the left, this part is called the 'head', the rest is called the 'core'
            #similarly, if one curve if longer than the other on the right, this part is called the 'tail'
            tail=False
            if abs(curveTail[0][len(curveTail[0])-1]) > abs(curveHead[0][len(curveHead[0])-1]):
                tail=True  
            if (tail):
                tail=[[],[]]
                for k in range (i-j+1, len(curveTail[0])):
                    tail[0].append(curveTail[0][k])
                    tail[1].append(curveTail[1][k])
                   
            else: k=len(curveTail[0])-1 #correcting the value of k if there is no tail
            #now, k is the last point of the curve with a tail
    
            #building the edges of each curve (the head and the tail)
            #j=first point of the curve with the head that is in the core
            #i=last point of the curve with the head
            #k=last point of curve with the tail
            
            #original slopes are kept, the step on the x-axis is reduced
            
            #head   
            slopes=[] #defining the slopes of the head
           
            for l in range(j):
                slope=(curveHead[1][l+1]-curveHead[1][l])/step
                slopes.append(slope)
            slopes.reverse()
            
            #adding the point for each curve
            for h in range(nbDaysInPeriod):     
                currentHead=[[weightedFunctions[h][0][0]],[weightedFunctions[h][0][1]]]
                  
                #coefficient definition
                if currentUp:
                    coefHead=1-h/nbDaysInPeriod
                    coefTail=h/nbDaysInPeriod
                else:
                    coefHead=h/nbDaysInPeriod
                    coefTail=1-h/nbDaysInPeriod
                for l in range(j):
                    currentHead[0].append(currentHead[0][l]-step*coefHead)
                    currentHead[1].append(currentHead[1][l]-step*coefHead*slopes[l]) 
                
                #formating and adding the head to the core
                del currentHead[0][0]
                del currentHead[1][0]
                currentHead[0].reverse()
                currentHead[1].reverse()
                currentHead=np.array(currentHead)
                currentHead=currentHead.T
                currentHead=currentHead.tolist()
                weightedFunctions[h]=currentHead+weightedFunctions[h]    
                                                    
            #tail
            slopes=[] #defining the slopes of the tail
                            
            for l in range (i-j,k):
                slope=(curveTail[1][l+1]-curveTail[1][l])/step
                slopes.append(slope)
                
            #adding the point for each curve
            for h in range(nbDaysInPeriod):                   
                currentTail=[[weightedFunctions[h][len(weightedFunctions[h])-1][0]],[weightedFunctions[h][len(weightedFunctions[h])-1][1]]]

                #coefficient definition
                if currentUp:
                    coefHead=h/nbDaysInPeriod
                    coefTail=1-h/nbDaysInPeriod
                else:
                    coefHead=1-h/nbDaysInPeriod
                    coefTail=h/nbDaysInPeriod
                for l in range(k-(i-j)):
                    currentTail[0].append(currentTail[0][l]+step*coefTail)
                    currentTail[1].append(currentTail[1][l]+step*coefTail*slopes[l]) 

                #formating and adding the head to the core
                del currentTail[0][0]
                del currentTail[1][0]
                currentTail=np.array(currentTail)
                currentTail=currentTail.T
                currentTail=currentTail.tolist()
                weightedFunctions[h]=weightedFunctions[h]+currentTail 
                                
            allWeightedFunctions.append(weightedFunctions)

            print('cost function extrapolations, period '+str(period)+' done')
            
        allPeriodsWeightedFunctions.append(allWeightedFunctions)
        
            
    return [allPeriodsWeightedFunctions,allNbDaysInPeriod]

def writeCfOneConverterState(allPeriodsFunctions,allPeriodsWeightedFunctions,periodSets,allNbDaysInPeriod,storageID,loc,folder):
    if not os.path.isdir(folder[1:]):
        os.mkdir(loc+folder)
        
    ##################### 6) writing cost functions for each period
    for periodSet in range( len(allPeriodsFunctions)):
        
        #original cost functions
        for period in range(len(allPeriodsFunctions[periodSet])):
            originalPoints=allPeriodsFunctions[periodSet][period]
            print('costs for period ' + str(period))    
            pt=np.array(originalPoints)
            pt=pt.T
            pt=pt.tolist()
            plt.title('Original points')     
            plt.scatter(pt[0],pt[1])
            
            header=[storageID+'.deltaSetPoint',storageID+'.costSetPoint'] 
            name='SeasonalStorage_file_'+str(len(periodSets[periodSet][0]))+'_'+str(period+1)+'.csv' 
            df=pd.DataFrame(np.array(originalPoints), columns=header)
            df.to_csv(path_or_buf=loc+folder+name,sep=';',decimal='.',header=True, index=False) 
            
            # plt.show()
        #plt.savefig('cost.png', dpi=1200)
        plt.show()     
           
		#extrapolated cost functions
        for period in range(len(allPeriodsFunctions[periodSet])):
            #on considere le mois courant et le prochain
            nextPeriod=period+1
            if period+1 >= len(allPeriodsFunctions[periodSet]):
                nextPeriod=0
            #coefs=range(5)
            #coefs=range(23,28)
            for coef in range(allNbDaysInPeriod[periodSet]):
                points=allPeriodsWeightedFunctions[periodSet][period][coef]
                #formating
                pt=np.array(points)
                pt=pt.T
                pt=pt.tolist()
                plt.title('Weighted points')     
                plt.scatter(pt[0],pt[1])
    
                header=[storageID+'.deltaSetPoint',storageID+'.costSetPoint'] 
                name='SeasonalStorage_file_'+str(len(periodSets[periodSet][0]))+'_'+str(period)+'-'+str(allNbDaysInPeriod[periodSet]-coef)+'_'+str(nextPeriod)+'-'+str(coef)+'.csv' 
                                    
                df=pd.DataFrame(np.array(points), columns=header)
                df.to_csv(path_or_buf=loc+folder+name,sep=';',decimal='.',header=True, index=False) 
                                        
            print('writting costs, month '+str(period)+' done')
            #plt.savefig('cost.png', dpi=1200)
        plt.show()

    #plt.savefig('cost.png', dpi=1200)
    #plt.show()

def readCfOneConverterState(nbPeriods,sizePeriods,loc,folder,nbPeriodSets):

    allPeriodsFunctions=[]
    allPeriodsWeightedFunctions=[]
    for periodSet in range(nbPeriodSets):
        allPeriodsFunctions.append([])
        allPeriodsWeightedFunctions.append([])
        
        #original cost functions
        for period in range(nbPeriods):
            allPeriodsFunctions[periodSet].append([])
            name='\\SeasonalStorage_file_'+str(int(sizePeriods))+'_'+str(period+1)+'.csv' 
            df=pd.read_csv(loc+name,sep=";", decimal=".")

            points=np.array(df)
            allPeriodsFunctions[periodSet][period]=points.tolist()
            
            print('costs for period ' + str(period))    
            points=points.T
            points=points.tolist()
            plt.title('Original points')     
            plt.scatter(points[0],points[1])

        plt.show()     
                
		#extrapolated cost functions
        for period in range(nbPeriods):
            allPeriodsWeightedFunctions[periodSet].append([])
            nextPeriod=period+1
            if period+1 >= nbPeriods:
                nextPeriod=0
            for coef in range(int(sizePeriods/24)):
                allPeriodsWeightedFunctions[periodSet][period].append([])
                
                name='SeasonalStorage_file_'+str(int(sizePeriods))+'_'+str(period)+'-'+str(int(sizePeriods/24)-coef)+'_'+str(nextPeriod)+'-'+str(coef)+'.csv' 
                df=pd.read_csv(loc+folder+name,sep=";", decimal=".")

                points=np.array(df)
                allPeriodsWeightedFunctions[periodSet][period][coef]=points.tolist()
            print('reading costs, month '+str(period)+' done')

                 
        plt.show()
    
    return [allPeriodsFunctions,allPeriodsWeightedFunctions]
