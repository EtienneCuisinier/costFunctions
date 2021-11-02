import os

os.chdir(os.path.dirname(os.path.realpath(__file__)))
from costFunctions import costFunctions

def test_costFunctions():
    
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    os.chdir("../")
    loc=os.getcwd()
    
    reference='test'

    #Persee files
    nameData='\dataSeries.csv' 
    nameConfig="config.xml" 
    nameSettings="settings.ini" 
    nameDesc="desc.xml" 
    
    namePLAN="results_PLAN.csv" 
    nameFbsfLog="FbsfFramework.log" 
    nameSortie="perseeProject.csv" 
    nameBatch="run_batch.bat"
     
    #Persee storage parameters
    storageID='LTS' 
    lossesID='.KLoss' 
    efficiencyID='.Eta' 
    initSocID='.InitSOC' 
    finalSocID='.FinalSOC' 
    capacityID='.MaxEsto' 
    powerID='.MaxFlow' 
    
    #Persee converter parameters
    addStartUpCostsID='.AddStartUpCost' 
    addFixedCostsID='.AddFixedCost' 
    startUpCostsID='.StartUpCost' 
    fixedCostsID='.FixedCost' 
    absInitialStateID='.AbsInitialState' 
    stateID='.State' 
    converterID='IFP' 
    
    #Representative periods computation parameters
    dt=1 
    nRP=2
    sRP=2  
    seriesToConsider=['Thermal_Load','Thermal_Solar']
    weights=[2,1]
    imposedPeriod=[]
    imposePeak=[]
    nBins=40 
    binMethod=1 
    timeLimitRp=30 
    gapRp=0.00001 
    threadsRp=8 

    #Cost functions computation parameters
    nbTimeStepsForComputations=8736 #size of the data serie used to compute the cost functions (hours)
    periodSizes=[672,168] #sizes of the periods used to compute the cost functions (hours), multiple sizes can be chosen
    periodSizes=672
    nbPoints=2 #number of points over which the action of storing/releasing energy is evaluated
    maxStorageDeltaPerPeriod=[1,0.5] #maximum percentage of the storage capacity that can be stored/released over a period
    maxStorageDeltaPerPeriod=1

    costID='UnDiscounted Net OPEX ;'
    initSOC=0.1 #initial state of charge of the storage when computing representative periods, an empty storage can lead to side effects
    gap='1.e-4' 
    timeLimit='600' 
    converterState=True #whether to compute the cost functions for both initial states of the converter or not
        
    #Building cost functions
    cf=costFunctions(periodSizes, seriesToConsider,
                     loc, nameData, nameConfig, nameSettings, namePLAN, nameFbsfLog, nameSortie, 
                     storageID, lossesID, efficiencyID, initSocID, finalSocID, capacityID, powerID, costID, 
                     nbTimeStepsForComputations, dt, converterState)

    cf.computeRp(nRP, sRP, weights, imposedPeriods, imposePeak, gapRp, timeLimitRp, threadsRp, nBins, binMethod)

    cf.defineStorageLevelDeltas(nbPoints, maxStorageDeltaPerPeriod)

    cf.computeCf(nameBatch, gap, timeLimit, initSOC, converterID, absInitialStateID)    

    cf.extrapolateCf()

    cf.writeCf(reference)

    cf.showCf(periodSet=0, period=5, absTimeStep=10)

    cf.showRp(periodSet=0, period=6)




if __name__ == '__main__':
    test_costFunctions()






