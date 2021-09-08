import os       

class dataList:
    
    """Author: Etienne Cuisinier (etienne.cuisinier@cea.fr)
		Class to deal with lists of data from Persee files: .init, .xml, .txt, .csv
        The object 'dataList' is defined by:
            - the file name: 'name'
            - the file extension: 'ext'
            - the file location: 'loc'
            - the file content, a list of strings: 'data'
            - a copy of the initial content: '_copy'
        Note: nundles of commented lines are not managed 
    """
    
    def __init__(self, name="dataList.ini", loc="",initList=False):
  
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
            print("ERROR: file extension not found")
        
        if not initList:
            os.chdir(self.loc)
            file = open(self.name, "r")
            fileContent = file.read()
            file.close()
            self.data = fileContent.split("\n")
            self._copy = fileContent.split("\n")
        elif type(initList)==list:
            self.data=initList
            self._copy=initList.copy()
        else: 
            print("ERROR: the attribute initList must be a list")

    def _get_copy(self):
        return self._copy
    copy = property(_get_copy)

    def readFile(self, name='currentName', loc='currentLoc'):
        """Reads a file content and redefine the attribute 'data' with the file content"""
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
            print("ERROR when reading the file")
        else:
            self.data = fileContent.split("\n")
       
    def writeFile(self, name='currentName', loc='currentLoc'):
        """Write the 'data' attribute content on a file"""
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
            print("ERROR when writing the file")
        

    def reinitData(self):
        """Reinitialize the content of the 'data' attribute with its initial content"""
        while len(self.data) > 0: self.data.pop()
        for i in range(0, len(self._copy)):
            self.data.append(self._copy[i])

    def isComment(self, index):
        """ Input: line index
            Ouput: if the line is commented or not
        """
        output = False
        if self.ext == '.xml' or self.ext == '.oplproject':
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
            if firstChar == '/':
                output = True
        elif self.ext == '.log':
            output = False
        else:
            print("ERROR (isComment)")
        return output

    def findParam(self,param,start=0, ignoreComments=True, warning=True):        
        """Input: the parameter name, the line number from which searching starts (optionnal), if commented lines should be ignored,
                    if a warning should be given if the parameter is not found, 
            Ouput: [the line number, the line that includes the parameter]
        """
        
        output = [-1,'notFound']
        i=start     
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
            print ("Parameter cannot be found, ouput : [-1,'notFound']")
        return output            
    
    def findParamValue(self,param,start=0, ignoreComments=True, warning=False):
        """Input: the parameter name, the line number from which searching starts (optionnal), if commented lines should be ignored,
                    if a warning should be given if the parameter is not found, 
            Ouput: the parameter value (string)
        """
        
        line=self.findParam(param, start, ignoreComments, warning)[1]
        output='notFound'
        
        if line !='notFound':  
            if self.ext == '.xml':
                index1=line.index('>')
                index2=line.index('</')
                output=line[index1+1:index2]
            elif self.ext == '.ini':
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
            else:
                print("ERROR (findParamValue)")
        
        elif warning:
            print ("Parameter or its value cannot be found")
         
        output = self.cleanStr(output, full=True)    
                
        return output

    def changeParamValue(self, param, new, start=0, ignoreComments=True):
        """Input: the parameter name, its new value, the line number from which searching starts (optionnal), if commented lines should be ignored,
                    if a warning should be given if the parameter is not found, 
        """
        line=self.findParam(param, start, ignoreComments)
       
        if line[1] !='notFound':
            if self.ext == '.xml':
                
                index1=line[1].index('>')
                index2=line[1].index('</')
                self.data[line[0]]=line[1][:index1+1]+str(new)+line[1][-(len(line[1])-index2):]
                #print("Line number " + str(line[0]) + ", nouveau contenu: "+ str(self.data[line[0]]))
                
            elif self.ext == '.ini':
                
                index=line[1].index('=')
                self.data[line[0]]=line[1][:index+1]+str(new) 
                #print("Line number " + str(line[0]) + ", nouveau contenu: "+ str(self.data[line[0]]))
                    
            else:
                print("ERROR, file extension unkown")
    
    def commentParam(self, param, start=0, warning=False):
        """Input: the parameter name to comment, the line number from which searching starts (optionnal), if commented lines should be ignored,
                    if a warning should be given if the parameter is not found, 
        """
        line=self.findParam(param, start, True)
       
        if line[1] !='notFound':
            if self.ext == '.xml':
                
                self.data[line[0]]='<!--'+self.data[line[0]]+'-->'
                print("Line number " + str(line[0]) + ", commented.")
            
            elif self.ext == '.dat':
                
                self.data[line[0]]='//'+self.data[line[0]]
                print("Line number " + str(line[0]) + ", commented.")
                
            elif self.ext == '.ini':
                
                self.data[line[0]]='#'+self.data[line[0]]
                print("Line number " + str(line[0]) + ", commented.")        

            else:
                print("ERROR: file extension unkown")

        else: 
            if warning:
                print("Cannot find parameter, or line already commented")	   
 
    def clean(self, full=False, breakXml = False, ignoreComments=False):
        """Delete blanks and commented lines in the attribute 'data'
            Input: delete blanks within a line or only extremities, option to break the xml architecture, option to ignore commented lines
        """
        if self.ext == '.xml' or self.ext == '.ini' or self.ext == '.dat':
            i=0
            while i < len(self.data):
                if (self.isComment(i) and ignoreComments) or self.data[i]=='':
                    del self.data[i]
                else:
                    i += 1  
        else:
            i=0
            while i < len(self.data):
                if self.data[i]=='':
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
   

    def cleanStr(self, string, left=False, right=False, full=False):
        """Deletes blanks in a string
            Input: a string, option to delete blanks at the beginning of the string, at the end of the string, or all blanks 
            Ouput: a cleaned string
        """
        leftClean= not left
        rightClean= not right
        if full:
            string=string.replace(' ','')
            if self.ext == '.xml':
                string=string.replace('\t','')
        while not (leftClean and rightClean):
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
    

                
    def changeAllParamValues(self, param, new, start=0, ignoreComments=True):
        """Input: the parameter name, its new value, the line number from which searching starts (optionnal), if commented lines should be ignored,
                    if a warning should be given if the parameter is not found, 
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
        