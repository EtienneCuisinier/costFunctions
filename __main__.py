import os

os.chdir(os.path.dirname(os.path.realpath(__file__)))
from dataList import dataList
from costFunctions import costFunctions

def test_costFunctions():
    
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    os.chdir("../")
    loc=os.getcwd()
    
    #Persee files
    nameDataOrignal='\dataSeries.csv' 
    nameData364Days='\dataSeries364.csv'
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
    nBins=40 
    imposedPeriod=[]
    imposePeak=[]
    binMethod=1 
    timeLimitRp=30 
    gapRp=0.00001 
    threads=8 
    seriesToConsider=[0]
    
    #Cost functions computation parameters
    nbPoints=2  
    maxStorageDeltaPerPeriod=1 
    
    costID='UnDiscounted Net OPEX ;'
    initSOC=0.1 
    gap='1.e-4' 
    timeLimit='600' 
    converterState=True
    reference='test'
        
    #Building cost functions
    cf=costFunctions(loc, nameDataOrignal, nameData364Days, config, settings, namePLAN, nameFbsfLog, nameSortie, storageID, lossesID, efficiencyID, initSocID, finalSocID, capacityID, powerID, costID=costID, nbPeriods=-1)
    
    cf.computeRp(dt, nRP, sRP, nBins, imposedPeriod, imposePeak, binMethod, timeLimitRp, gapRp, threads, seriesToConsider)
    
    cf.defineStorageLevelDeltas(dt, nbPoints, maxStorageDeltaPerPeriod)
    
    cf.computeCf(nameBatch, storageID, lossesID, initSocID, finalSocID, gap, timeLimit, initSOC, converterState, converterID, absInitialStateID)    
    
    cf.extrapolateCf()
    
    cf.writeCf(reference)
    
    cf.showCf()


if __name__ == '__main__':
    test_costFunctions()






