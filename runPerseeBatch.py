import os
import subprocess
import time
os.chdir(os.path.dirname(os.path.realpath(__file__)))
from dataList import dataList

def runPerseeBatch(loc:str, bat:str, nameFbsfLog="FbsfFramework.log") -> int:
    """Author: Etienne Cuisinier (etienne.cuisinier@cea.fr)
	Runs Persee and returns the computation time (sec)"""
    
    t0Simu=time.perf_counter()
    os.chdir(loc)
    #running Persee
    try:
        subprocess.check_output("call "+bat,shell=True,stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        print("ERROR when running Persee")

    timeSimu = time.perf_counter() - t0Simu
       
    logFile=dataList(nameFbsfLog,loc)
    if (logFile.findParam("Best Feasible (TimeLimit Reached)", warning=False)[1]!='notFound'):
        print("TIME LIMIT REACHED at some steps")
        timeSimu=-1
    if (logFile.findParam("Resultat optim :  \"Unknown\"", warning=False)[1]!='notFound'):
        print("NO SOLUTION at some steps")
        timeSimu=-2
    
    return timeSimu

