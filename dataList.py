# -*- coding: utf-8 -*-

import os # On importe le module os qui dispose de variables et de fonctions utiles pour dialoguer avec le systeme d'exploitation       
from typing import List

class dataList:
    
    """Classe pour gerer des listes de donnees provenant de fichiers type .init, .xml, .txt, eventuellement .csv
        Permet de creer des 'dataList' definies par :
            - leur nom (le nom du fichier) : 'name'
            - l'extention du fichier : 'ext'
            - la localisation du fichier : 'loc'
            - une liste de chaine de caracteres (le contenu du fichier) : 'data'
            - une copie du contenu initial (liste de chaine de caracteres) : '_copy'
            - et c'est tout pour l'instant
        Attention : mauvaise gestion des lignes commentees par paquet
    """
    
    def __init__(self, name="dataList.ini", loc="", liste=False):
        """Constructeur de notre classe"""
  
        self.name = str(name)
        self.loc = str(loc)
        
        index=len(self.name)-1
        found=False
        while index >= 0 and not found:
            if self.name[index]=='.':
                found=True
            else: 
                index -= 1
        if found:
            self.ext = self.name[index:]
        else:
            print("init : Erreur dans l'initialisation de l'attribut 'ext' (extention du fichier)")
        
        if not liste :
            os.chdir(self.loc)
            file = open(self.name, "r")
            fileContent = file.read()
            file.close()
            self.data = fileContent.split("\n")
            self._copy = fileContent.split("\n")
        elif type(liste)==list:
            self.data=liste
            self._copy=liste.copy()
        else : 
            print("The attribute liste must be a list")

    def _get_copy(self):
        """Methode pour acceder en lecture a l'attribut 'copy'"""
        return self._copy
    copy = property(_get_copy)

    def readFile(self, name='currentName', loc='currentLoc'):
        """Methode pour lire le contenu d'un fichier et redefinir l'attribut 'data' avec le contenu du fichier 
            (par defaut sur le fichier definit par les attributs de l'objet)"""
        if name=='currentName':
            name=self.name
        if loc=='currentLoc':
            loc=self.loc
        try:
            os.chdir(loc)
            file = open(name, "r")
            fileContent = file.read()
            file.close()
        except:
            print("readFile : Erreur dans la lecture du fichier (verifier la localisation, le nom, si le fichier n'est pas verouille)")
        else:
            self.data = fileContent.split("\n")
       
    def writeFile(self, name='currentName', loc='currentLoc'):
        """Methode pour ecrire le contenu de l'attribut 'data' sur un fichier 
            (par defaut sur le fichier definit par les attributs de l'objet)"""
        if name=='currentName':
            name=self.name
        if loc=='currentLoc':
            loc=self.loc
        try:
            content="\n".join(self.data)
            os.chdir(loc)
            file=open(name, "w")
            file.write(content)
            file.close()
        except:
            print("writeFile : Erreur dans l'ecriture du fichier (verifier la localisation, le nom, si le fichier n'est pas verouille)")
        
    def reinitFile(self):
        """Methode pour reinitialiser le contenu du fichier avec le contenu de la propriete '-copy'"""
        try:
            content="\n".join(self._copy)
            os.chdir(self.loc)
            file=open(self.name, "w")
            file.write(content)
            file.close()
        except:
            print("reinitFile : Erreur dans l'ecriture du fichier (verifier la localisation, le nom, si le fichier n'est pas verouille)")
    
    def reinitData(self):
        """Methode pour reinitialiser le contenu de l'attribut 'data' avec le contenu de la propriete '-copy'"""
        while len(self.data) > 0 : self.data.pop()
        for i in range(0, len(self._copy)):
            self.data.append(self._copy[i])

    def isComment(self, index):
        """Methode pour savoir si une ligne est commentee ou non, definie pour les fichiers .ini, .xml et .dat (OPL)
            Input : index de la ligne (element de la liste 'data')
            Ouput : True ou False
        """
        output = False
        if self.ext == '.xml':
            if '<!--' in self.data[index]:
                output=True;     
        elif self.ext == '.ini':
            i=0
            firstChar = ' '
            while i < len(self.data[index]) and firstChar == ' ':
                firstChar = self.data[index][i]
                i += 1
            if firstChar == ';' or firstChar == '#':
                output = True
        elif self.ext == '.dat':
            i=0
            firstChar = ' '
            while i < len(self.data[index]) and firstChar == ' ':
                firstChar = self.data[index][i]
                i += 1
            if firstChar == '/' :
                output = True
        elif self.ext == '.log':
            output = False
        else :
            print("isComment : Nom de l'extention inconnu, ou non pris en charge par la fonction, Ouput=False par defaut")
        return output

    def findParam(self,param,start=0, ignoreComments=True, warning=True, reverseSearch=False):
        """Methode pour trouver un parametre dans l'attribut 'data'
            Input : le nom du parametre, le numero de ligne a partir duquel chercher le parametre (optionnel, utile si ce parametre apparait plusieurs fois), 
                    si l'on souhaite ignorer les lignes commentees ou non (initialise a 'True', pour les fichiers .ini, .xml, .dat)
            Ouput : [le numero de la ligne qui contient le parametre, la ligne complete qui contient le parametre]
        """
        output = [-1,'notFound']
        i=start
        if(reverseSearch):
            if (i==0):
                i=len(self.data)-1
            if (ignoreComments):
                while (i >= 0 and not (str(param) in self.data[i] and not (self.isComment(i) and ignoreComments))):
                    i -= 1
                if i>=0:
                    output = [i,self.data[i]]  
            else:
                while (i >= 0 and not (str(param) in self.data[i])):
                    i -= 1
                if i>=0:
                    output = [i,self.data[i]]           
        else:
            if (ignoreComments):
                while (i < len(self.data) and not (str(param) in self.data[i] and not (self.isComment(i) and ignoreComments))):
                    i += 1
                if i<len(self.data):
                    output = [i,self.data[i]]  
            else:
                while (i < len(self.data) and not (str(param) in self.data[i])):
                    i += 1
                if i<len(self.data):
                    output = [i,self.data[i]]  
        
        if output == [-1,'notFound'] and warning:
            print ("findParam : Parametre introuvable, ouput par defaut : [-1,'notFound']")
        return output            
    

    #Cherche la valeur d'un parametre dans une liste de chaines de caractere (construite pour les fichiers Persee, pas robuste)
    def findParamValue(self,param,start=0, ignoreComments=True, reverseSearch=False, warning=False):
        """Methode pour trouver la valeur d'un parametre dans l'attribut 'data', definie pour les fichiers .ini, .xml, .csv (HIST et PLAN de Persee) et .dat (OPL)
            Input : le nom du parametre, le numero de ligne a partir duquel chercher le parametre (optionnel, utile si ce parametre apparait plusieurs fois), 
                    si l'on souhaite ignorer les lignes commentees ou non (initialise a 'True', pour les fichiers .ini, .xml)
            Ouput : la valeur du parametre
        """
        line=self.findParam(param, start, ignoreComments, warning, reverseSearch)[1]
        output='notFound'
        
        if line !='notFound':  
            if self.ext == '.xml':
                index1=line.index('>')
                index2=line.index('</')
                output=line[index1+1:index2]
            elif self.ext == '.ini':
                index=line.index('=')
                output=line[-(len(line)-index-1):]
            elif self.ext == '.dat':
                if 'SheetRead' in line or 'SheetWrite' in line:
                    index1=line.index('!')+1
                    index2=line.index(')')-2
                    output=line[index1:index2]
                elif 'SheetConnection' in line:
                    index1=line.index('(')+2
                    index2=line.index(')')-2
                    output=line[index1:index2]
                else :
                    index=line.index('=')
                    output=line[-(len(line)-index-1):] 
            elif self.ext == '.csv':
                index=len(line)-1
                found=False
                while index > 0 and not found:
                    if line[index]==';':
                        found=True
                    else: 
                        index -= 1
                output=line[-(len(line)-index-1):] 
            else :
                print("findParamValue : Nom de l'extention inconnu, ou non pris en charge par la fonction, ouput='notFound' par defaut")
        
        elif warning:
            print ("findParamValue : Parametre ou valeur introuvable, ouput par defaut :'notFound'")
         
        output = self.cleanStr(output, full=True)    
                
        return output

    def changeParamValue(self, param, new, start=0, ignoreComments=True):
        """Methode pour changer la valeur d'un parametre dans l'attribut 'data', definie pour les fichiers .ini, .xml, .dat
            Input : le nom du parametre, le numero de ligne a partir duquel chercher le parametre (optionnel, utile si ce parametre apparait plusieurs fois), 
                    si l'on souhaite ignorer les lignes commentees ou non (initialise a 'True', pour les fichiers .ini, .xml)
            Ouput : 
        """
        line=self.findParam(param, start, ignoreComments)
        output=False
        
        if line[1] !='notFound':
            output=True
            if self.ext == '.xml':
                
                index1=line[1].index('>')
                index2=line[1].index('</')
                self.data[line[0]]=line[1][:index1+1]+str(new)+line[1][-(len(line[1])-index2):]
                #print("Ligne numero " + str(line[0]) + ", nouveau contenu : "+ str(self.data[line[0]]))
            
            elif self.ext == '.dat':
                
                if 'SheetRead' in line[1] or 'SheetWrite' in line[1]:
                    index1=line[1].index('!')+1
                    index2=line[1].index(')')-1
                    self.data[line[0]]=line[1][:index1]+str(new)+line[1][index2:]
                elif 'SheetConnection' in line[1]:
                    index1=line[1].index('(')+2
                    index2=line[1].index(')')-1
                    self.data[line[0]]=line[1][:index1]+str(new)+line[1][index2:]
                else :
                    index=line[1].index('=')
                    self.data[line[0]]=line[1][:index+1]+str(new)

                #print("Ligne numero " + str(line[0]) + ", nouveau contenu : "+ str(self.data[line[0]]))
                
            elif self.ext == '.ini':
                
                index=line[1].index('=')
                self.data[line[0]]=line[1][:index+1]+str(new) 
                #print("Ligne numero " + str(line[0]) + ", nouveau contenu : "+ str(self.data[line[0]]))
                  
            else :
                output=False
                print("changeParamValue : Nom de l'extention inconnu, ou non pris en charge par la fonction")
                
        return output
    
    def commentParam(self, param, start=0, warning=False):
        """Methode pour commenter une ligne contenant le parametre donne, definie pour les fichiers .ini, .xml, .dat
            Input : le nom du parametre, le numero de ligne a partir duquel chercher le parametre (optionnel, utile si ce parametre apparait plusieurs fois), 
            Ouput : 
        """
        line=self.findParam(param, start, True)
        output=False
        if line[1] !='notFound':
            output=True
            if self.ext == '.xml':
                
                self.data[line[0]]='<!--'+self.data[line[0]]+'-->'
                print("Ligne numero " + str(line[0]) + ", commentee.")
            
            elif self.ext == '.dat':
                
                self.data[line[0]]='//'+self.data[line[0]]
                print("Ligne numero " + str(line[0]) + ", commentee.")
                
            elif self.ext == '.ini':
                
                self.data[line[0]]='#'+self.data[line[0]]
                print("Ligne numero " + str(line[0]) + ", commentee.")        

            else :
                output=False
                print("commentParam : Nom de l'extention inconnu, ou non pris en charge par la fonction")

        else : 
            if warning:
                print("Parametre introuvable, ou ligne deja commentee.")	
        return output
 
    def clean(self, full=False, breakXml = False, ignoreComments=False):
        """Methode pour 'nettoyer' l'attribut 'data': supprime les blancs et les lignes commentees, definie pour les fichiers .ini, .xml, .dat (OPL)
            Input : possibilite de 'casser' l'architecture xml en supprimant les espaces en debut de ligne (initialise a 'False')
            Ouput : la liste nettoyee
        """
        if self.ext == '.xml' or self.ext == '.ini' or self.ext == '.dat':
            i=0
            while i < len(self.data) :
                if (self.isComment(i) and ignoreComments) or self.data[i]=='' :
                    del self.data[i]
                else:
                    i += 1  
        else:
            i=0
            while i < len(self.data) :
                if self.data[i]=='' :
                    del self.data[i]
                else:
                    i += 1  
            
        if self.ext != '.xml':  
            i=0
            while i < len(self.data):
                self.data[i] = self.cleanStr(self.data[i], left=True, right=True, full=full)
                i += 1        
        if self.ext == '.xml' and breakXml:
            i=0
            while i < len(self.data):
                self.data[i] = self.cleanStr(self.data[i], left=True, right=True, full=full)
                i += 1
        else:
            i=0
            while i < len(self.data):
                self.data[i] = self.cleanStr(self.data[i], right=True)
                i += 1
                
    
    def fill(self,T):
        """Methode pour 'remplir' l'attribut 'data' de ligne vides (creer pour pouvoir entsuite l'inserer dans un dataFrame de la librairie Panda)
            Input : taille de l'attribut 'data' a atteindre
            Ouput : 
        """
        while len(self.data) < T:
            self.data.append('')

    
    #Renvoie une liste avec les valeurs de la liste originale "nettoyee" au prealable (construite pour les fichiers Persee, pas robuste)
    def valueList(self):
        """Methode pour obtenir une version de l'attribut 'data' ne contenant que les valeurs, definie pour les fichiers .ini, .xml, .csv (HIST et PLAN de Persee)
            Input : si l'on souhaite ignorer les lignes commentees ou non (initialise a 'True', pour les fichiers .ini, .xml)
            Ouput : version de l'attribut 'data' ne contenant que les valeurs (liste de chaine de caracteres)
        """
        output=[]  
        
        if self.ext == '.ini':
             for i in range(0,len(self.data)):                   
                    line=self.data[i]
                    if '=' in line:
                        index=line.index('=')
                        value=line[-(len(line)-index-1):]

                        try:
                            #value=float(value)
                            output.append(value)
                        except:
                            output.append(value)
                    else:
                        output.append('')               
    
        elif self.ext == '.xml': 
            for i in range(0,len(self.data)):
                line=self.data[i]
                if '</' in line:
                    index1=line.index('>')
                    index2=line.index('</')
                    value=line[index1+1:index2]
                    value=self.cleanStr(value, full=True)
                    try:
                        #value=float(value)
                        output.append(value)
                    except:
                        output.append(value)
                else:
                    output.append('')

        elif self.ext == '.csv':
            for i in range(0,len(self.data)):
                line=self.data[i]
                value=''
                if ';' in line:
                    j=len(line)-1
                    while j > 0 and line[j] != ' ' and line[j] != ';':
                        value=line[j]+value
                        j=j-1         
                    value=self.cleanStr(value, full=True)
                    try:
                        #value=float(value)
                        output.append(value)
                    except:
                        output.append(value)
                else:
                    output.append('')
        
        return output 

        
    #Renvoie une liste avec les valeurs de la liste originale "nettoyee" au prealable (construite pour les fichiers Persee, pas robuste)
    def noValueList(self, ignoreComments=True):
        """Methode pour obtenir une version de l'attribut 'data' sans les valeurs, definie pour les fichiers .ini, .xml, .csv (HIST et PLAN Persee)
            Input : si l'on souhaite ignorer les lignes commentees ou non (initialise a 'True', pour les fichiers .ini, .xml)
            Ouput : version de l'attribut 'data' ne contenant que les valeurs (liste de chaine de caracteres)
        """
        output=[]  
        
        if self.ext == '.ini':
             for i in range(0,len(self.data)):                   
                    line=self.data[i]
                    if '=' in line:
                        index=line.index('=')
                        value=line[-(len(line)-index-1):]
                        
                        line=line.replace(value,'')
  
                    output.append(line)            
    
        elif self.ext == '.xml': 
            for i in range(0,len(self.data)):
                line=self.data[i]
                if '</' in line:
                    index1=line.index('>')
                    index2=line.index('</')
                    value=line[index1+1:index2]
                    
                    line=line.replace(value,'')
  
                output.append(line) 

        elif self.ext == '.csv':
            for i in range(0,len(self.data)):
                line=self.data[i]
                value=''
                if ';' in line:
                    j=len(line)-1
                    while j > 0 and line[j] != ' ' and line[j] != ';':
                        value=line[j]+value
                        j=j-1         
                    
                    line=line.replace(value,'')
  
                    output.append(line) 
        
        return output 


    def cleanStr(self, string, left=False, right=False, full = False):
        """Methode pour supprimer les espaces au debut et a la fin d'une chaine de caracteres
            Input : une chaine de caracteres, un booleen si l'on veut supprimer les espaces du debut, 
            un booleen si l'on veut supprimer les espaces de la fin et un booleen si on veut supprimer tous les espaces (tout est initialise a 'False')
            Ouput : une chaine de caracteres 'nettoyee'
        """
        leftClean= not left
        rightClean= not right
        if full:
            string=string.replace(' ','')
            if self.ext == '.xml':
                string=string.replace('\t','')
        while not (leftClean and rightClean) :
            if (string[0] != ' ' and self.ext != '.xml') or (self.ext == '.xml' and string[0] != ' ' and string[0:1] != '\t'):
                leftClean = True
            else:
                if string[0:1] == '\t':
                    string=string[2:]
                else:
                    string=string[1:]
            if (string[len(string)-1] != ' ' and self.ext != '.xml') or (self.ext == '.xml' and string[len(string)-1] != ' ' and string[len(string)-2:len(string)] != '\t'):
                rightClean = True
            else:
                if string[len(string)-2:len(string)] == '\t':
                    string=string[:len(string)-2]
                else:
                    string=string[:len(string)-1]
        return string
    
    #Renvoie la liste des parametres du .ini que Persee interpretera comme variable de dimensionnement a optimiser (symbolise par une valeur negative)
    def findParamDim(self,start=0, ignoreComments=True, reverseSearch=False):
        """Methode pour trouver la liste des parametres du .ini que Persee interpretra comme des variables d'optimisation du dimensionnement (dont la valeur est initialisee a un chiffre negatif)
            ATENTION : exclue les parametres "InitSOC" et "FinalSOC" et les valeurs <1
            Input : le numero de ligne a partir duquel chercher le parametre (optionnel), 
                    si l'on souhaite ignorer les lignes commentees ou non (initialise a 'True')
            Ouput : la liste des parametres
        """
        if self.ext != ".ini" :
            print("The file must be a .ini file.")
            raise ValueError
        
        else :
            paramDim=[]
    
            line=""
            while line !='notFound':

                lineIndex=self.findParam("=-",start,ignoreComments,reverseSearch)
                line=lineIndex[1]
                index=lineIndex[0]
                value=self.findParamValue("=-",start,ignoreComments,reverseSearch)
               
                if line !='notFound' and not "InitSOC" in line and not "FinalSOC" in line and "-0." not in value:
                
                    i=line.index('=')       
                    output=line[:-(len(line)-i)]    
                    paramDim.append(output)
                    
                start=index+1
        
        return paramDim
    
    #Renvoie la liste des parametres du .ini que Persee interpretera comme variable de dimensionnement a optimiser (symbolise par une valeur negative)
    def findParamDimOpt(self,paramDim : List[str]):
        """Methode qui renvoie la liste des valeurs des parametres de dimensionnement optimises presentes dans le .PLAN
            Input : la liste des parametres de dimensionnement optimises
            Ouput : la liste des  valeurs de ces parametres
        """
        paramDimPrim=paramDim.copy()
        #On garde le nom de l'element uniquement
        for i in range(0,len(paramDimPrim)) :
            if "." in paramDimPrim[i]:
                index=paramDimPrim[i].index(".")
                paramDimPrim[i]=paramDimPrim[i][:index]

        #On va chercher la valeur dans le PLAN
        paramDimValues=[]
        possibleName=["Component Optimal Weight","Installed Optimal Size","Installed Size","Storage Optimal Capacity"]
        
        for param in paramDimPrim:
            for name in possibleName:
                value=self.findParamValue(param+" ; "+name,warning=False, ignoreComments=False)
                if value !='notFound' :
                    paramDimValues.append(value)
                    break
        
        if len(paramDim) != len(paramDimValues):
            print("SOME VALUES WERE NOT FOUND")
        
        return paramDimValues
                
                
    #Renvoie la liste des parametres du .ini que Persee interpretera comme variable de dimensionnement a optimiser (symbolise par une valeur negative)
    def changeAllParamValues(self, param, new, start=0, ignoreComments=True):
        """Methode pour changer la valeur de tous les parametres dans l'attribut 'data', definie pour les fichiers .ini, .xml, .dat
            Input : le nom du parametre, le numero de ligne a partir duquel chercher le parametre (optionnel, utile si ce parametre apparait plusieurs fois), 
                    si l'on souhaite ignorer les lignes commentees ou non (initialise a 'True', pour les fichiers .ini, .xml)
            Ouput : 
        """
    
        line=""
        found=False
        while line !='notFound':

            lineIndex=self.findParam(param,start,ignoreComments,warning = not found)
            line=lineIndex[1]
            index=lineIndex[0]
           
            if line !='notFound':
                self.changeParamValue(param,new,start)
                found=True
                
            start=index+1
        
