from docplex.mp.model import Model
import matplotlib.pyplot as plt
plt.style.use('seaborn-whitegrid')

class representativePeriods:
    
    """ Author: Etienne Cuisinier (etienne.cuisinier@cea.fr)
        A class to build representative periods and cumpute related indicators. 
        The method used was proposed by Poncelet K. & al. in "Selecting Representative Days for Capturing the Implications of Integrating Intermittent Renewables in Generation Expansion Planning Problems" (2017) (DOI: 10.1109/TPWRS.2016.2596803)
        For now, the extended model is not included in the code.
        The class is composed of the following attributes:
            
            Initialization mandatory parameters: 
            - a list of the original data sets (lists) to compress (must have the same length, the length must be a multiple of 24/dt): data
            - the number of representative periods to build: nRP
            - the size of the representative periods to build (expressed as a number of days): sRP
            
            Initialization optional parameters: 

            - the time step size (in hours): dt
            - weigths on the input data sets: all sets are normalised when accounting for errors on duration curves or when rebuilding the whole data set. Weights can be attributed.
            - optional representative period imposed by the user (a list of period numbers): imposedPeriods
            - optional peak representative periods for each data sets, defined for representative days only (for instance, [0,-1,1] means: [no period imposed,impose the period with lowest value, imposed the period with highest value]): imposePeak
            - the gap tolerance (maximum objective difference between the optimal solution and the obtained solution, 0.1% by default): gap
            - the solving time limit (1 minute by default): timeLimit
            - the number of bins to consider (methodological parameter, 40 by default): nBins 
            - the bin construction method (1 by default): binMethod (changes the step definition)
            - the rebuild method: rebuildMethod ('basic' by default, or 'squared' or 'durationCurve')

            Internal parameters and ouputs:
            - the number of data sets: nbSets
            - the number of time steps: nbPdt
            - the number of optional representative periods: nORP
            - the size of the representative periods to build in hours: sRPh
            - the bins: bins
            - the parameters L (see Poncelet K. & al.): paramL
            - the parameters AA (see Poncelet K. & al.): paramAA
            - an mathematical programming model (mp model from docplex): mdl
            - the optimised objective: objective
            - the optimal weights (for each optional representative period) : optWeights
            - the optimal weights, compact version (only for selected periods): optWeightsCompact
            - the optimal weights per time step: optWeightsDt
            - the selected periods (1 if selected, 0 otherwise): optSelPeriods
            - the selected periods, number of selected periods: optSelPeriodsCompact
            - the optimised selected periods per time step: optSelPeriodsDt
            - the optimised error on data (see Poncelet K. & al., "error_c,b"): optError
            - the optimised total error (see Poncelet K. & al.): optErrorTot
            - the rebuilt data sets from selected representative periods: rebuiltData
            - the linking matrix (attribution of one representative period to each original period): lMatrix
            - the indexes of representative periods used to rebuild data sets (per optional representative period): rpUse
            - the indexes of representative periods used to rebuild data sets (per time step): rpUseHourly
            - the error on the rebuilt data: errorRebuiltData
            - the peak periods: peaks
            - the representative periods (merged in a single list, for each data set): rp
            - the representative periods (one list per period, for each data set): rpList
            
    """
    
 
    
    def __init__(self, data, nRP, sRP, dt=1, 
                 weightsOnDataSets=[], imposedPeriods=[], imposePeak=[], 
                 gap=0.01, timeLimit=300, threads=8, 
                 nBins=40,binMethod=1,rebuildMethod='basic'):
                
        try: data[0][0]
        except: data=[data]     
        
        #normalising data sets
        maxi=[]
        for i in range(len(data)):
            maxi.append(max(data[i]))
            if maxi[i] > 0:
                data[i]=[data[i][j]/maxi[i] for j in range(len(data[i]))]
        
        #building parameters
        try:
            nbSets=len(data)
            nbPdt=len(data[0])
            nORP=int(nbPdt/24*dt - sRP + 1)
            sRPh=int(sRP*24/dt)
            bins=[]
            paramL=[]
            paramAA=[]
            peaks=[]
            
            setORP=set(range(nORP))
            setBins=set(range(nBins))
            totWeight=nbPdt / sRPh
        
            #parametres pour construire le probleme d'optimisation
            for i in range(nbSets):
                bins.append(buildBins(data[i],nBins,binMethod))
                paramL.append(buildL(data[i],nBins, sRPh,binMethod))
                paramAA.append(buildAA(data[i],nBins,sRPh,dt,binMethod))
            
            #recherche du pic sur chaque serie si l'option est activee
            for i in range(len(imposePeak)):
                if imposePeak[i] == 1:
                    peaks.append(int( data[i].index(max(data[i])) / sRPh ))
                elif imposePeak[i] == -1:
                    peaks.append(int( data[i].index(min(data[i])) / sRPh ))
                else:
                    peaks.append(-1)
            
        except:
            print('ERROR when building parameters')
        
        #model MILP
        mdl = Model(name='representPeriods')
        mdl.parameters.mip.tolerances.mipgap=gap            
        mdl.set_time_limit(float(timeLimit))  
        if threads > 0:
            mdl.context.cplex_parameters.threads = threads

        #variables
        try:
           selected=mdl.binary_var_dict(setORP, name="u")
           weights=mdl.continuous_var_dict(setORP, lb=0, name="w")
        
           error=[]
           for n in range(nbSets):
               error.append(mdl.continuous_var_dict(setBins,lb=0))
        except:
            print('Error when defining variables')

        #constraints
        try:
            mdl.add_constraint( mdl.sum_vars(selected[i] for i in setORP) == nRP )
            mdl.add_constraint( mdl.sum_vars(weights[i] for i in setORP) == totWeight )
            
            if sRP > 1: #on ajoute cette contrainte pour eviter que 2 periodes selectionnees ne se chevauchent
                for i in setORP:
                    if i < nORP-sRP-1:
                        mdl.add_constraint( mdl.sum_vars(selected[ii] for ii in range(i,i+sRP)) <= 1 )
                    else:  
                        mdl.add_constraint( mdl.sum_vars(selected[ii] for ii in range(i,nORP)) <= 1 )


            for n in range(nbSets):
                for i in setBins:
                    mdl.add_constraint( mdl.abs(paramL[n][i] - mdl.sum(weights[j]*paramAA[n][j][i]/totWeight for j in setORP)) == error[n][i] )
                
            for j in setORP:
                mdl.add_constraint( weights[j] <= selected[j]*totWeight)
      
            for i in range(len(imposedPeriods)):
                mdl.add_constraint( selected[imposedPeriods[i]] == 1 )
            
            if len(imposePeak)>0:
                for n in range(len(peaks)):
                    if (peaks[n]>0):
                        mdl.add_constraint( selected[peaks[n]] == 1 )
                
            #objective 
            totalError = 0
            i=0
            for n in range (nbSets):
                if weightsOnDataSets==[]:
                    totalError += mdl.sum_vars(error[n][i] for i in setBins)  
                else:
                    totalError += mdl.sum_vars(error[n][i] for i in setBins)*weightsOnDataSets[i]
                    i+=1
             
            mdl.minimize(totalError)
        except:
            print('Error when defining constraints or objective')
       
        mdl.print_information()
    
    
        try:
            mdl.solve()
        except:
            print('Error when solving problem')
        else:
            #de-normalising data sets
            for i in range(len(data)):
                data[i]=[data[i][j]*maxi[i] for j in range(len(data[i]))]
            
            
            print (mdl.solve_details) 
        
            #gather results
            optSelPeriods = [selected[i].solution_value for i in setORP]
            optSelPeriodsCompact = [i for i in setORP if selected[i].solution_value == 1]

            optWeightsCompact = [weights[w].solution_value for w in setORP]
            
            
            while len(optWeightsCompact) > nRP: 
                optWeightsCompact.remove(min(optWeightsCompact)) #pour supprimer les valeurs negligeables
            
            optWeights = [weights[w].solution_value for w in setORP]
            optError = []
            optErrorTot = []
            
            for n in range(nbSets):
                optError.append([])
                for i in setBins:
                    optError[n].append(error[n][i].solution_value)
            
                optErrorTot.append( sum (error[n][i].solution_value for i in setBins) )
    
            print('Selected periods: '+str(optSelPeriodsCompact))
            print('Respective weights: '+str(optWeightsCompact))
            print('Total error on duration curve(s) '+str(optErrorTot))
            
            optWeightsDt=list()
            optSelPeriodsDt=list()
            i=0
            while i < nORP:
                if optSelPeriods[i]==1:
                    for k in range(sRPh):
                        optWeightsDt.append(optWeights[i])
                        optSelPeriodsDt.append(optSelPeriods[i])
                    i += sRP
                else:
                    for j in range(int(24/dt)):
                        optWeightsDt.append(0)
                        optSelPeriodsDt.append(0)
                    i += 1
    
            rp=[[]]
            rpList=[[[]]]
            for n in range(nbSets):
                if n > 0:
                    rp.append([])
                    rpList.append([[]])
                
                #building rp from optSelPeriodsDt
                for i in range(len(optSelPeriodsDt)):
                    if optSelPeriodsDt[i]==1:
                        rp[n].append(data[n][i])
                       
                #building rpList from rp
                period=0
                for i in range( len(rp[n])):
                    if int(i/(sRPh/dt)) > period:
                        period += 1
                        rpList[n].append([])
                    rpList[n][period].append(rp[n][i])
                    
            #filtering obtained weights (close to zero values given by the optimizer are excluded) 
            count=nRP
            optWeightsTemp=[]
            for i in range(len(optWeights)): 
                if optWeights[i] > 0:
                    if count > 0:
                        optWeightsTemp.append(optWeights[i])
                        count -= 1
                    else:
                        mini=min(optWeightsTemp)
                        if optWeights[i] > mini:
                            optWeightsTemp[optWeightsTemp.index(mini)]=optWeights[i]
                            optWeights[optWeights.index(mini)]=0
                        else:
                            optWeights[i]=0
            
            
            self.data=data
            self.dt=dt
            self.nRP=nRP
            self.sRP=sRP
            self.nBins=nBins
            self.timeLimit=timeLimit
            self.gap=gap
            self.imposedPeriods=imposedPeriods
            self.imposePeak=imposePeak
            self.binMethod=binMethod

            self.nbPdt=nbPdt
            self.nbSets=nbSets
            self.mdl=mdl
            self.nORP=nORP
            self.sRPh=sRPh
            self.bins=bins
            self.paramL=paramL
            self.paramAA=paramAA
            self.objective=mdl.objective_value
            self.optSelPeriods=optSelPeriods
            self.optSelPeriodsCompact=optSelPeriodsCompact
            self.optSelPeriodsDt=optSelPeriodsDt

            self.optWeights=optWeights
            self.optWeightsCompact=optWeightsCompact
            self.optWeightsDt=optWeightsDt
            self.optError = optError
            self.optErrorTot = optErrorTot
            self.peaks = peaks
            self.rp = rp
            self.rpList = rpList
            
            self.rebuiltData=None
            self.lMatrix=None
            self.rpUse=None
            self.rpUseHourly=None
            self.errorRebuiltData=None
            
            self.weightsOnDataSets=weightsOnDataSets
    
            
    def showDcRp (self,save=False,name=''):
    
        for i in range(self.nbSets):
            if self.weightsOnDataSets==[] or self.weightsOnDataSets[i]>0:
                print ('Showing duration curves for data['+str(i)+']')
                
                print ('Compare duration curve of original data with (approximated) duration curve of selected representative periods (weighted)')
        
                dcRp=buildDc(self.data[i], self.optWeightsDt)
                dcData=buildDc(self.data[i])
                
                plt.plot(dcData, label="dc original")
                plt.plot(dcRp, label="dc representative periods")
                plt.xlabel('Time')
                plt.ylabel('Unit')
                plt.legend()
                plt.show()
                
                if save:
                    plt.savefig('dcRpCurve-'+str(i)+'_'+name)
                
    def showRp (self):

        for i in range(self.nbSets):
            if self.weightsOnDataSets==[] or self.weightsOnDataSets[i]>0 :
                print ('Showing representative period(s) for data['+str(i)+']')
                    
                for j in range(len(self.rpList[i])):
    
                    plt.plot(self.rpList[i][j])
                    plt.xlabel('Time')
                    plt.ylabel('Unit')
                    plt.title("representative period "+str(j)+" with weight = "+str(round(self.optWeightsCompact[j],2)))
                    plt.show()
                    
                plt.plot(self.data[i])
                plt.xlabel('Time')
                plt.ylabel('Unit')
                plt.title("Original data")
                plt.show()
            
    def showDcRebuiltData (self,save=False, name=''):
    
        for i in range(self.nbSets):
            if self.weightsOnDataSets==[] or self.weightsOnDataSets[i]>0:
                print ('Showing duration curves for data['+str(i)+']')
                
                print ('Compare duration curve of original data with (approximated) duration curve of rebuilt data')
                
                dcRebuilt=buildDc(self.rebuiltData[i])
                dcOriginal=buildDc(self.data[i])
                
                plt.plot(dcOriginal, label="data original")
                plt.plot(dcRebuilt, label="rebuilt data")
                plt.xlabel('Time')
                plt.ylabel('Units')
                plt.legend()
                plt.show()
                
                if save:
                    plt.savefig('dcRpCurve-'+str(i)+'_'+name)
    
    def showRebuiltData (self,save=False, name=''):
    
        for i in range(self.nbSets):
            if self.weightsOnDataSets==[] or self.weightsOnDataSets[i]>0:
                print ('For data['+str(i)+']')
                
                print ('Compare duration curve of original data with duration curve of rebuilt data')
                
                plt.plot(self.data[i], label="data original")
                plt.plot(self.rebuiltData[i], label="rebuilt data")
                plt.xlabel('Time')
                plt.ylabel('Units')
                plt.legend()
                plt.show()
                
                if save:
                    plt.savefig('dcRpCurve-'+str(i)+'_'+name)
    
    def rebuildData (self, rebuildMethod='basic',timeshift=24):
        
        #build the linking matrix, reconstitute the data with representative periods
        rebuiltData=[[]]
        lMatrix=[]
        lList=[]
        rpUse=[]
        rpUseHourly=[]
        errorRebuiltData=[]
        
        #normalising data sets
        maxi=[]
        dataNorm=[self.data[i].copy() for i in range(len(self.data))]
        for i in range(len(dataNorm)):
            maxi.append(max(dataNorm[i]))
            dataNorm[i]=[dataNorm[i][j]/maxi[i] for j in range(len(dataNorm[i]))]
    
        for n in range(self.nbSets):
            if n > 0:
                rebuiltData.append([])
            
        for i in range(self.nbPdt):
            lMatrix.append(list())
            lList.append(-1)
            for j in range(self.nRP*self.sRPh):
                lMatrix[i].append(0)
    
        #count the usage of each representative period: per period and per time step
        for i in range(self.nORP):
            rpUse.append(0)
    
        for i in range(self.nbPdt):
            rpUseHourly.append(0)
         
        for i in range(int(self.nbPdt/self.sRPh)): #for each period, we select the best representative period to associate
    
            errorBest=-1;
            previousK=-1
            countCompact=-1
            countCompactPrevious=-1
            
            #list of selected representative periods (to be updated)
            bestRp=[[]]
            for n in range(self.nbSets):
                if n > 0:
                    bestRp.append([])
                for j in range(self.sRPh):
                    bestRp[n].append(-1)
                    
            #checking each optional representative period
            for k in range(self.nORP):
                if (self.optWeights[k]>0):
                    error=[]
                    errorTot=0
                    countCompact=countCompact+1
                    #computing the error for each data set
                    
                    weightIndex=0
                    for n in range(self.nbSets):
                        error.append(0)

                        #error metric to minimize
                        if rebuildMethod=='basic':
               
                            for l in range(self.sRPh):
                                error[n] = error[n] + abs(dataNorm[n][int(i*self.sRPh+l)] - dataNorm[n][int(k*24/self.dt+l)])
                        
                        elif rebuildMethod=='squares':
                            for l in range(self.sRPh):
                                error[n] = error[n] + (1+abs(dataNorm[n][int(i*self.sRPh+l)] - dataNorm[n][int(k*24/self.dt+l)]))*(1+abs(dataNorm[n][int(i*self.sRPh+l)] - dataNorm[n][int(k*24/self.dt+l)]))
                        
                        elif rebuildMethod=='durationCurve':
                            dcRp=list()
                            dcOriginal=list()
                            
                            for l in range(self.sRPh):
                                dcRp.append(dataNorm[n][int(k*24/self.dt+l)])
                                dcOriginal.append(dataNorm[n][i*self.sRPh+l])
    
                            dcRp.sort(reverse=True)
                            dcOriginal.sort(reverse=True)
    
                            for l in range(self.sRPh):
                                error[n] = error[n] + abs(dcRp[l] - dcOriginal[l])
                        
                        #accounting for the error on the current data set in the total error (with possible attributed weights)
                        if self.weightsOnDataSets==[]:
                            errorTot = errorTot + error[n]
                        else:
                            errorTot = errorTot + error[n]*self.weightsOnDataSets[weightIndex]
                            weightIndex += 1

                    #update best candidate
                    if (errorBest < 0 or errorTot < errorBest):
                        errorBest = errorTot
                        
                        #note representative period usage (per representative period)
                        rpUse[k]+=1
                        if(previousK>-1):
                            rpUse[previousK]=rpUse[previousK]-1
                         
                        
                        for m in range(self.sRPh):
                            for n in range(self.nbSets):
                                bestRp[n][m] = self.data[n][int(k*24/self.dt+m)]
    
                            #note representative period usage (per hour)
                            rpUseHourly[int(k*24/self.dt+m)]+=1
                            if(previousK>-1):
                                rpUseHourly[int(previousK*24/self.dt+m)]-=1
                                      
                            #update matrix
                            lMatrix[i*self.sRPh+m][countCompact*self.sRPh+m] = 1
                            if(countCompactPrevious > -1):
                                lMatrix[i*self.sRPh+m][countCompactPrevious*self.sRPh+m] = 0
                        
                            #update list
                            lList[i*self.sRPh+m] = k
                        
                        previousK=k
                        countCompactPrevious=countCompact
                                
            #update our rebuilt data with representative periods
            errorRebuiltData.append(errorBest)
            for n in range(self.nbSets):
                for m in range(self.sRPh):
                    rebuiltData[n].append(bestRp[n][m])
                    
            
            #build the representative periods file for Persee
            visualisationList=[]
            perseeList=lList.copy()
            #removing the '-1' which correspond to the left values if the size of representative periods is not a multiple of 365
            perseeList = [value for value in perseeList if value != -1]

            uniqueList=list(dict.fromkeys(perseeList))
            
            for j in range(len(perseeList)):
                for i in range(len(uniqueList)):
                    if perseeList[j] == uniqueList[i]:
                        break
                perseeList[j] = i*self.sRPh+j%self.sRPh
                if i not in visualisationList: 
                    visualisationList.append(i)
                    
            #timeshifting to match with Pegase rolling horizon
            perseeList+=perseeList[0:timeshift]
            del perseeList[0:timeshift]
            perseeList=perseeList[len(perseeList)-1:len(perseeList)]+perseeList
            del perseeList[len(perseeList)-1:len(perseeList)]
            
            self.rebuiltData=rebuiltData
            self.lMatrix=lMatrix
            self.rpUse=rpUse
            self.rpUseHourly=rpUseHourly
            self.errorRebuiltData=errorRebuiltData
            self.lList=lList
            self.perseeList=perseeList
            self.visualisationList=visualisationList
            

def buildDc (data, weights=[]) :

    if len(weights)==0:
        #build duration curve
        dC=list()
        for i in range( len(data)):
            dC.append(data[i])
    else:
        #build duration curve of selected representative periods (approximated)
        dC=list()
        for i in range( min(len(data),len(weights))):
            if (weights[i]>0):
                for j in range(round(weights[i])):
                    dC.append(data[i])
    dC.sort(reverse=True)
    return dC

def buildBins (data, nBins, method=1) :

    nTS = len(data) #number of time steps
    dC = buildDc(data)
      
    if method == 1:
        #build bins method 1
        stepBins=(max(data)-min(data))/(nBins-1)
        bins=list()
        for i in range(nBins):
            bins.append(min(data)+stepBins*i)
     
    elif method == 2:
        #build bins method 2 (different step definition)
        stepBins=int(nTS/(nBins))
        bins=list()
        for i in range(nBins):
            bins.append(dC[nTS-1-i*stepBins])
    else:
        print("The argument method should be 1 or 2 (1 by default)")
    
    return bins

def buildL (data, nBins, sRPh, method=1) :
    
    bins = buildBins(data, nBins, method)
    nTS = len(data) #number of time steps
    parameterL=list() #percentage of time during wich data exceeds the value of bin i
    
    for i in range(nBins):
        counter=0
        
        for j in range(nTS):
            if data[j]>=bins[i]:
                counter=counter+1
        parameterL.append(counter/nTS)
    return parameterL

def buildAA (data, nBins, sRPh, dt, method=1) :
    
    bins = buildBins(data, nBins, method)
    nORP=int(len(data)/24*dt - sRPh/24*dt + 1) #number of optional representative periods, keeping a daily coherence
    parameterAA=list() #parameter A for all representative periods
    
    for i in range(nORP):
        parameterA=list() #percentage of time during wich the representative period exceeds the value of bin i
        
        for h in range(nBins):
            counter=0
            
            for j in range(sRPh):
                if data[int(i*24/dt+j)]>=bins[h]:   
                    counter=counter+1
            parameterA.append(counter/sRPh)
        parameterAA.append(parameterA)
    return parameterAA
