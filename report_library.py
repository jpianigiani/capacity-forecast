# Author Jacopo Pianigiani jacopopianigiani@juniper.net
# Written in 2022

import json
import string
import sys
import glob
import os
import math
import re
import operator
from datetime import datetime
import traceback
from aop_logger import aop_logger

#from aop_logger import aop_logger



# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------
#                           CLASS :     PARAMETERS
# -------------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------------
class parameters:
    # 
    # -------------------------------------------------------------------------------------------------------------------------
    # GLOBAL DICTIONARIES: these are used to store command line arguments values or user input values (so that the behavior is consistent between User interactive mode and CLI mode)

    PATHFORAPPLICATIONCONFIGDATA='./'
    APPLICATION = 'resource-analysis'

    APPLICATIONCONFIG_DICTIONARY={}
    MODE_OF_OPT_OPS = 0
    paramsdict={}
    paramslist=[]
    ERROR_REPORT=[]    
    ERROR_DATA=[]
    
    # -------------------------------------------------------------------------------------------------------------------------
    # FORMULAS FOR DISTANCE CALCULATION FROM TARGET
    # -------------------------------------------------------------------------------------------------------------------------

    # , 'abs(currentvalue-average)',  '(currentvalue-minimum)**4']
    #metricformulas = ['(currentvalue-average)**2']
    # -------------------------------------------------------------------------------------------------------------------------
    NO_OPTIMIZATION = 0
    OPTIMIZE_BY_CALC = 1
    OPTIMIZE_BY_FILE = 2

    def __init__(self, myApplicationName=APPLICATION):
        modulename="aop_logger"
        if modulename not in sys.modules:
            self.AOP_LOGGER_ENABLED=False
        else:
            self.AOP_LOGGER_ENABLED=True
        self.myApplicationName=myApplicationName
        CONFIGFILENAME=myApplicationName+".json"
        print("opening config file : ",CONFIGFILENAME)
        ERRORFILENAME=myApplicationName+"-errors.json"
        self.SYSLOGFILE=myApplicationName+".log"
        now = datetime.now()  # current date and time
        date_time = now.strftime("%d/%m/%Y %H:%M:%S")
        #date_time = now.strftime("%d/%m/%Y")
        self.paramsdict["TIMESTAMP"] = date_time
        TMPJSON=[]
        self.DSTSITES = []
        screenrows, screencolumns = os.popen('stty size', 'r').read().split()
        self.ScreenWitdh = int(screencolumns)
        self.ColorsList =(menu.OKBLUE,menu.OKCYAN,menu.OKGREEN,menu.WARNING,menu.FAIL,menu.White,menu.Yellow,menu.Magenta,menu.Grey) 
        self.ERROR_REPORT=[]
        
        #-------------------------------------------------------------------------------------------------------------------
        try:

            with open(self.PATHFORAPPLICATIONCONFIGDATA+CONFIGFILENAME,'r') as ConfigFile:
                try:
                    TMPJSON = json.load(ConfigFile)
                except:
                    traceback.print_exc(limit=None, file=None, chain=True)
                    print(" CRITICAL! : object class PARAMETERS, __init__ found JSON syntax error in  {:}".format(self.PATHFORAPPLICATIONCONFIGDATA+CONFIGFILENAME))
                    exit(-1)
            self.APPLICATIONCONFIG_DICTIONARY=dict(TMPJSON)
        #-------------------------------------------------------------------------------------------------------------------
            self.PATHFOROUTPUTREPORTS=self.APPLICATIONCONFIG_DICTIONARY["Files"]["PathForOutputReports"]
        #-------------------------------------------------------------------------------------------------------------------
            self.paramsdict = self.APPLICATIONCONFIG_DICTIONARY["Application_Parameters"]
            self.paramslist=list(self.APPLICATIONCONFIG_DICTIONARY["User_CLI_Visible_Parameters"])
        #-------------------------------------------------------------------------------------------------------------------
        
        except:
            traceback.print_exc(limit=None, file=None, chain=True)
            #-------------------------------------------------------------------------------------------------------------------
            print("#-------------------------------------------------------------------------------------------------------------------")
            print(" CRITICAL! : object class PARAMETERS, __init__ did not find the application configuration file {:}".format(self.PATHFORAPPLICATIONCONFIGDATA+CONFIGFILENAME))
            print("\t Files {:} and  {:} must be , from thedirectory as python main executable, as follows: {:}".format(CONFIGFILENAME, ERRORFILENAME,self.PATHFORAPPLICATIONCONFIGDATA))
            print("#-------------------------------------------------------------------------------------------------------------------")
            exit(-1)
        #-------------------------------------------------------------------------------------------------------------------
        try:
            with open(self.PATHFORAPPLICATIONCONFIGDATA+ERRORFILENAME,'r') as ConfigFile:
                self.ERROR_DICTIONARY = json.load(ConfigFile)
        except:
            traceback.print_exc(limit=None, file=None, chain=True)
            print("#-------------------------------------------------------------------------------------------------------------------")
            print(" CRITICAL! : object class PARAMETERS, __init__ did not find the application configuration file {:}".format(self.PATHFORAPPLICATIONCONFIGDATA+CONFIGFILENAME))
            print("\t Files {:} and  {:} must be , from the directory as python main executable, as follows: {:}".format(CONFIGFILENAME, ERRORFILENAME,self.PATHFORAPPLICATIONCONFIGDATA))
            print("#-------------------------------------------------------------------------------------------------------------------")
            exit(-1)
         
        self.DEBUG=self.APPLICATIONCONFIG_DICTIONARY["Application_Parameters"]["DEBUG"]
        #-------------------------------------------------------------------------------------------------------------------
        try:
            if self.AOP_LOGGER_ENABLED:
                mysyslog=aop_logger(3,self.SYSLOGFILE)
                myloghandler=mysyslog.syslog_handler(
                        address= (self.APPLICATIONCONFIG_DICTIONARY["syslog"]["Target"],
                        self.APPLICATIONCONFIG_DICTIONARY["syslog"]["Port"]))
                self.logger=mysyslog.logger
        except NameError as Err:
            print("AOP-LOGGER disabled")

        #-------------------------------------------------------------------------------------------------------------------
    def get_logger(self):
        return self.logger



    def get_configdata_dictionary(self):
        return self.APPLICATIONCONFIG_DICTIONARY

    def set(self, key, value):
        self.paramsdict[key] = value
        return value

    def get(self, key):
        return self.paramsdict[key]

    def is_silentmode(self):
        return self.paramsdict["SILENTMODE"]
    # -----------------------------------
    def get_param_value(self, name):
        return self.paramsdict[name]
    # -----------------------------------

    # -----------------------------------
    def show_cli_command(self):
        MyLine = menu.OKGREEN+'{0:_^'+str(self.ScreenWitdh)+'}'
        print(MyLine.format('LIST OF PARAMETER ARGUMENTS'))
        print(json.dumps(self.paramsdict,indent=40))
        # PRINT CLI COMMAND AND PARAMETERS USED
        CMD = "python3 <appname>.py"
        for x in self.paramsdict:
            if x in self.paramslist:
                if type(x) == list:
                    l = len(x)
                    CMD += "{}=".format(x)
                    for x2 in x:
                        CMD += "{}".format(x2)
                        if x2 != x[l]:
                            CMD += ","
                else:
                    CMD += " {}={} ".format(x, self.paramsdict[x])

        CMD2 = CMD.replace("[", "")
        CMD3 = CMD2.replace("]", "")
        CMD4 = CMD3.replace(", ", ",")
        print(CMD4)
        return True
        
    def SuffixToShortDate(self,suffix):
        retval =suffix[6:8]+"-"+suffix[4:6]+"-"+suffix[0:4]
        return retval

    def SuffixToYYMMDDDateValue(self,suffix):
        retval =int(suffix[0:4]+suffix[4:6]+suffix[6:8])
        return retval
# --------------------EXTRACTS SITENAME FROM SUFFISSO note : STG810 specific parsing
    def parse_suffisso(self, suffisso):
        if len(suffisso) == 20:
            # NOTE: STG810 does not show stg810 in the suffix as the cc-jumphost hostname is configured wrongly
            sitename= suffisso[14:]
            retval=sitename.lower()
        else:
            sitename= "stg810"
            retval=sitename.lower()
        return retval
    
    def cast_error(self,ErrorCode, AddlData):
        NEWRECORD=[]
        a = str(self.__class__)
        #traceback.print_exc(limit=None, file=None, chain=True)
        #ErrorObjectClass= a.replace("'",'').replace("<",'').replace(">","").replace("class ","")

        ErrorInfo=self.ERROR_DICTIONARY[ErrorCode]
        #print(json.dumps(ErrorInfo,indent=30))
        ErrorObjectClass=ErrorInfo["Class"]
        SrcSuffix=self.get_param_value("SOURCE_SITE_SUFFIX")
        SiteName= self.parse_suffisso(SrcSuffix)
        if ErrorInfo["Level"]in self.APPLICATIONCONFIG_DICTIONARY["syslog"]["ErrorsToReport"]:
            NEWRECORD.append(SrcSuffix[0:8])
            NEWRECORD.append(SiteName)
            NEWRECORD.append(ErrorInfo["Level"])
            NEWRECORD.append(ErrorObjectClass)
            NEWRECORD.append(ErrorCode)
            NEWRECORD.append(ErrorInfo["Synopsis"])
            NEWRECORD.append(AddlData)
            #NEWRECORD.append(ErrorInfo)

            try:
                if self.AOP_LOGGER_ENABLED:
                    syslogstring="Timestamp: {:9s} Site: {:12s} ErrCode: {:5s} Class:{:30s} Synopsis:{:60s}: {:120s}".format(SrcSuffix[0:8],
                                SiteName,ErrorCode,ErrorObjectClass,ErrorInfo["Synopsis"],AddlData)
                    if ErrorInfo["Level"]=="CRITICAL":
                        self.logger.critical(syslogstring)
                    elif ErrorInfo["Level"]=="ERROR":
                        self.logger.error(syslogstring)
                    elif ErrorInfo["Level"]=="WARNING":
                        self.logger.warning(syslogstring)
            except NameError as Err:
                pass
            self.ERROR_REPORT.append(NEWRECORD)
        
        

        actions = ErrorInfo["AfterErrorExecution"]
        for Item in actions:
            print("cast_error")
            print(ErrorCode)
            print(NEWRECORD)
            print(AddlData)
            print(Item)
            eval(Item)


# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------
#                           CLASS :     REPORT
# -------------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------------
class report():

    Report = []
    ReportTotalUsage = []
    GenericDict={}


    def __init__(self,params):
        #super().__init__()
        self.Report = []
        self.ReportType=self.get_reporttype()
        self.State=''
        self.KEYS_KEYNAME="_KEYS"
        self.SORTINGKEYS_KEYNAME="_SORTING_KEYS"
        self.color=menu.Yellow
        self.ReportTotalUsage = []
        self.PARAMS = params
        self.name=str(self.__class__).replace("'",'').replace("<",'').replace(">","").replace("class ","") + hex(id(self))

        self.ReportsNamesAndData = params.APPLICATIONCONFIG_DICTIONARY["ReportsSettings"]
        self.FIELDLENGTHS= params.APPLICATIONCONFIG_DICTIONARY["FieldLenghts"]
        self.FIELDLISTS= params.APPLICATIONCONFIG_DICTIONARY["FieldLists"]
        #print(json.dumps(self.APPLICATIONCONFIG_DICTIONARY,indent=22))
        self.FIELDTRANSFORMS=params.APPLICATIONCONFIG_DICTIONARY["FieldTransforms"]
        self.FILESSTRUCTURE =params.APPLICATIONCONFIG_DICTIONARY["Files"]

        self.REPORTFIELDGROUP =params.APPLICATIONCONFIG_DICTIONARY["Reports_Keys"]

        self.GenericDict={}

        self.FIELDTRANSFORMSATTRIBUTES=params.APPLICATIONCONFIG_DICTIONARY["FieldTransformsAttributes"]
        self.myRegexDict= {}
        self.myMessageRegexDict={}
        for Item in self.FIELDTRANSFORMSATTRIBUTES["split_string"].keys():
            value = self.FIELDTRANSFORMSATTRIBUTES["split_string"][Item]
            #print("DEBUG", Item, value)
            self.myRegexDict[Item]=re.compile(value)
        if "message_parser" in self.FIELDTRANSFORMSATTRIBUTES.keys():
            #print(json.dumps(self.FIELDTRANSFORMSATTRIBUTES["message_parser"],indent=4))
            for Item in self.FIELDTRANSFORMSATTRIBUTES["message_parser"].keys():
                value = self.FIELDTRANSFORMSATTRIBUTES["message_parser"][Item]
                #print("message_parser init:DEBUG", Item, value)
                try:
                    self.myMessageRegexDict[Item]=re.compile(value)       
                except:
                    print("ERROR IN compiling regex: ")
                    print("Item:",Item, " Value:",value)


    def get_reporttype(self):
        MyClass= str(self.__class__).replace("<","").replace(">","").replace("'","")
        retval=MyClass.split(".")[1].upper()
        return retval

    def ClearData(self):      
        self.Report = []
        self.State=''
        self.ReportTotalUsage = []

    def set_name(self,myname):
        self.name=myname
        self.ReportFile = open(self.FILESSTRUCTURE["PathForOutputReports"]+"/"+self.name, 'w')


    def set_state(self,mystatus):
        self.State=mystatus
        self.write_line_to_file(mystatus)


    def write_line_to_file(self,line):
        try:
            self.ReportFile.write(line+"\n")
        except:
            self.PARAMS.cast_error("00005","line:"+line)


    def get_keys(self):
        try:
            return self.REPORTFIELDGROUP[self.ReportType+self.KEYS_KEYNAME]
        except:
            self.PARAMS.cast_error( "00007","get_keys :{:}".format(self.ReportType+self.KEYS_KEYNAME))

    def get_sorting_keys(self):
        try:
            return self.REPORTFIELDGROUP[self.ReportType+self.SORTINGKEYS_KEYNAME]
        except:
            self.PARAMS.cast_error( "00006","get_sorting_keys: :{:}".format(self.ReportType+self.SORTINGKEYS_KEYNAME))



    


    def UpdateLastRecordValueByKey(self, mykey, value):

        if mykey is None:
            print("UpdateLastRecordValueByKey : error : key is null") 
            exit(-1)
        record= self.Report[len(self.Report)-1]
        if mykey in self.FIELDLISTS.keys():
            for x in value:
                record[self.get_keys().index(mykey)].append(x)
        else:
            record[self.get_keys().index(mykey)]=value


    def FindRecordByKeyValue(self, mykey, value):
        MyFieldIndex=self.get_keys().index(mykey)
        for x in self.Report:
            if x[MyFieldIndex]==value:
                return x  
        return []        


    def AppendRecordToReport(self, newrecord):
        self.Report.append(newrecord)

    def length(self):
        return len(self.Report)

    def keys_length(self):
        return len(self.get_keys())

    def get_fieldlength(self,key):
        if key in self.FIELDLENGTHS:
            return self.FIELDLENGTHS[key]
        else:
            return self.FIELDLENGTHS["default"]

    def addemptyrecord(self):
        myrecord=[]
        for mykey in self.get_keys():
            if mykey in self.FIELDLISTS.keys():
                value=[]
            else:
                value=""
            myrecord.append(value)
        self.Report.append(myrecord)
        return self.Report[len(self.Report)-1]

    def get_column_by_key(self,mykey):
        Index=self.get_keys().index(mykey)
        retval=[row[Index] for row in self.Report]
        return retval




#---------------------------------------------------
#   Receives a Report Record, produces as return value a 2D Array containing one record per Line to be printed with wrapping of text beyond FieldLength
#---------------------------------------------------
    def LineWrapper(self, record):
        var_Keys=self.get_keys()
        Lines=[[]]
        MaxRows=1024
        Lines=[['' for j in range(len(var_Keys) )] for i in range(MaxRows)]
        if record is None:
            print("DEBUG: LineWrapper : record is NONE")
            exit(-1)
        MaxRows=0
        try: #CHANGETHIS
            myunwrappedline=''
            for ReportKeyItem in var_Keys:
                RecordEntryIndex =var_Keys.index(ReportKeyItem)
                var_FieldLen = self.get_fieldlength(ReportKeyItem)
                var_RecordEntry= record[RecordEntryIndex]
                if var_RecordEntry is None:
                    print("DEBUG LineWrapper: Field {:} is none \nfor record: ".format(ReportKeyItem,record))
                    exit(-1)  
                if type(var_RecordEntry)== list:
                    var_Entry=""
                    for ListItem in var_RecordEntry:
                        var_Entry+=ListItem
                else:
                    var_Entry=var_RecordEntry
                var_RecordEntryLen = len(var_Entry)
                
                stringa1="{:"+str( var_FieldLen  )+"s} |"
                myunwrappedline+=stringa1.format(var_Entry)  

                RowsValue = math.ceil(var_RecordEntryLen/var_FieldLen)
                if RowsValue>MaxRows:
                    MaxRows=RowsValue
                if RowsValue==0:
                    #print("DEBUG LineWrapper: Field {:} has Rowsvalue={:} \nfor record: ".format(ReportKeyItem,RowsValue,record))
                    RowsValue=1
                    Lines[0][RecordEntryIndex]=""
                    #exit(-1)    
                else:
                    for NofLinesPerRecEntry in range(RowsValue):
                        stringa_start = NofLinesPerRecEntry*var_FieldLen
                        if (var_RecordEntryLen> stringa_start+ var_FieldLen  ):
                            stringa_end = (1+NofLinesPerRecEntry)*var_FieldLen
                        else:
                            stringa_end =  var_RecordEntryLen
                        try:
                            newItem=var_Entry[stringa_start:stringa_end]
                        except:
                            print("DEBUG: Error in LineWrapper : ReportKeyItem : {:}, Var_Entry={:}".format(ReportKeyItem,var_Entry))
                            exit(-1)
                        Lines[NofLinesPerRecEntry][RecordEntryIndex]=newItem
                    

            retval=[]
            for i in range(MaxRows):
                myline=''
                for j in range(len(var_Keys)):
                    length=self.get_fieldlength(var_Keys[j])
                    stringa1="{:"+str( length  )+"s} |"
                    myline+=stringa1.format(Lines[i][j])  

                retval.append(myline)

            return retval,myunwrappedline


        except:
            traceback.print_exc(limit=None, file=None, chain=True)
            print("Record:", record)
            print("ReportKeyItem=",ReportKeyItem)
            self.PARAMS.cast_error("00009","Record:"+str(record))
            exit(-1)


#---------------------------------------------------
#   Receives a Report Record, produces as return value a 2D Array containing one record per Line to be printed with wrapping of text beyond FieldLength
#---------------------------------------------------
    def LineWrapper_V2(self, record):


        if record is None:
            print("DEBUG: LineWrapper : record is NONE")
            exit(-1)
        
        
        #try: #CHANGETHIS

        if "REPORT_MULTILINE_KEYS" in self.REPORTFIELDGROUP.keys():
            ListOfMultilineKeys=self.REPORTFIELDGROUP["REPORT_MULTILINE_KEYS"].keys()
            self.MultiLineFlag=True
        else:
            ListOfMultilineKeys=["1"]
            self.MultiLineFlag=False
        

        Lines=[[]]
        MaxRows=1024

        myunwrappedline=''
        retval=[]
        RowIncrement=0
        for MultiLineRowIndexString in ListOfMultilineKeys:
            var_TotalKeys=self.get_keys()
            MaxRows=1024
            Lines=[['' for j in range(len(var_TotalKeys) )] for i in range(MaxRows*len(ListOfMultilineKeys))] 
            if self.MultiLineFlag:
                var_LineKeys=self.REPORTFIELDGROUP["REPORT_MULTILINE_KEYS"][MultiLineRowIndexString]
            else:
                var_LineKeys=self.get_keys()

            MultiLineRowIndex=int(MultiLineRowIndexString)
            #print("DEBUG - v2 - ",MultiLineRowIndex, "....",var_Keys)
            MaxRows=0
            for ReportKeyItem in var_LineKeys:

                RecordEntryIndex =var_TotalKeys.index(ReportKeyItem)
                TableEntryIndex=var_LineKeys.index(ReportKeyItem)

                var_FieldLen = self.get_fieldlength(ReportKeyItem)
                var_RecordEntry= record[RecordEntryIndex]

                if var_RecordEntry is None:
                    print("DEBUG LineWrapper: Field {:} is none \nfor record: ".format(ReportKeyItem,record))
                    exit(-1)  
                if type(var_RecordEntry)== list:
                    var_Entry=""
                    for ListItem in var_RecordEntry:
                        var_Entry+=ListItem
                else:
                    var_Entry=var_RecordEntry
                var_RecordEntryLen = len(var_Entry)
                
                stringa1="{:"+str( var_FieldLen  )+"s} |"
                myunwrappedline+=stringa1.format(var_Entry)  

                RowsValue = math.ceil(var_RecordEntryLen/var_FieldLen)
                if RowsValue>MaxRows:
                    MaxRows=RowsValue

                if RowsValue==0:
                    #print("DEBUG LineWrapper: Field {:} has Rowsvalue={:} \nfor record: ".format(ReportKeyItem,RowsValue,record))
                    RowsValue=1
                    Lines[0][TableEntryIndex]=""
                    #exit(-1)    
                else:
                    for NofLinesPerRecEntry in range(RowsValue):
                        stringa_start = NofLinesPerRecEntry*var_FieldLen
                        if (var_RecordEntryLen> stringa_start+ var_FieldLen  ):
                            stringa_end = (1+NofLinesPerRecEntry)*var_FieldLen
                        else:
                            stringa_end =  var_RecordEntryLen
                        try:
                            newItem=var_Entry[stringa_start:stringa_end]
                        except:
                            print("DEBUG: Error in LineWrapper : ReportKeyItem : {:}, Var_Entry={:}".format(ReportKeyItem,var_Entry))
                            exit(-1)
                        Lines[NofLinesPerRecEntry][TableEntryIndex]=newItem
                    
                if MultiLineRowIndex==1 and False :
                    print("DEBUG - Linewrapperv2 - \nReportKeyIem:",ReportKeyItem, " in var_Linekeys:",var_LineKeys,"\nRecordEntryIndex :",RecordEntryIndex, " TableEntryIndex:",TableEntryIndex)
                    print("var_RecordEntry:",var_RecordEntry)
                    print("Lines:\n",Lines)

            LineLenTotal=0
            for i in range(MaxRows):
                myline=''
                for j in range(len(var_LineKeys)):
                    length=self.get_fieldlength(var_LineKeys[j])
                    stringa1="{:"+str( length  )+"s} |"
                    stringa2=stringa1.format(Lines[i][j])
                    myline+=stringa2  
                    LineLenTotal=len(stringa2) 

            
                retval.append(myline)
            string1="_"*LineLenTotal
            retval.append(string1)
        return retval,myunwrappedline

            
        #except:
        #    traceback.print_exc(limit=None, file=None, chain=True)
        #    print("Record:", record)
        #    print("ReportKeyItem=",ReportKeyItem)
        #    self.PARAMS.cast_error("00009","Record:"+str(record))
        #    exit(-1)




#---------------------------------------------------
#   Receives a Report Record, produces a 1D record[] after applying Transforms to each entry in accordance to .json file of application configuration
#---------------------------------------------------
    def Record_ApplyTransforms(self,record):
        reportkeys=self.get_keys()
        NewRecord=[]
        currentrecord={}

        for row_itemnumber in range(self.keys_length()):
            # Fetches each item in the report row into initialvalue and gets what type it is, and what's the length of the output record (FIELDLENGTH)
            initialvalue = record[row_itemnumber]
            mytype = type(initialvalue)
            key=reportkeys[row_itemnumber]
            currentrecord[key]=record[row_itemnumber]
            columnname = reportkeys[row_itemnumber]
            length = self.FIELDLENGTHS[columnname]
            FormatString_SingleValue="{:"+str( length)+"s}"
            try:
                transform = self.FIELDTRANSFORMS[columnname]
            except:
                transform = 'value'
            try:
                if mytype == list:
                    if columnname not in self.FIELDLISTS:
                        print("ERROR 04 - ApplyTransforms")
                        print("Record_ApplyTransforms: ERROR 04 START - \nMost likely FIELD is a list but it is not present in the application config JSON in the FIELDSLIST, so it is not classified neither list nor else\n")
                        print("transform=",transform)
                        print("column:",columnname)
                        print("currentrecord[key]:",currentrecord[key])
                        
                        exit(-1)
                    ListItemLen =self.FIELDLISTS[columnname]
                    FormatString_ListItemField ="{:"+str( ListItemLen)+"s}"
                    NewRecordListEntry=[]
                    for RecordEntry in initialvalue:
                        try:
                            value = FormatString_ListItemField.format(str(RecordEntry))
                            TransformedValue = eval(transform)
                            NewRecordListEntry.append(TransformedValue)

                        except:
                            traceback.print_exc(limit=None, file=None, chain=True)

                            ErrString="ApplyTransforms: item RecordEntry={:},transform={:}".format(RecordEntry,transform)
                            self.PARAMS.cast_error("00010",ErrString)
                    NewRecord.append(NewRecordListEntry)
                    
                else:
                    value = str(initialvalue)
                    NewRecord.append(FormatString_SingleValue.format(eval(transform)))

            except:
                #traceback.print_exc(limit=None, file=None, chain=True)
                print("######################################")
                print("Record_ApplyTransforms: ERROR 04 START - \nMost likely FIELD is a list but it is not present in the application config JSON in the FIELDSLIST, so it is not classified neither list nor else\n")
                print("transform function =",transform)
                print("column:",columnname)
                print("Field to apply is: {:} of type {:} and value {:} of type {;}".format(key,mytype,value,type))
                print("Record: {:} , current field index {:}\n".format(record,row_itemnumber))
                #print("Result of applying transform ")
                #eval(transform)
                print("Record_ApplyTransforms: ERROR 04 - END")
                print("######################################")

                exit(-1)

        return NewRecord


  # ---------------------------------
    # Print  report Keys header - using Text Wrapping
    # ---------------------------------   
    def print_report_line(self, pars,record, applytransforms):
            color=self.color
            NewRecord=[]
            NewLines=[[]]
            if applytransforms:
                NewRecord=self.Record_ApplyTransforms(record)
            else:
                NewRecord=record
            NewLines,UnWrappedline=self.LineWrapper_V2(NewRecord)

            print_on_screen=self.ReportType not in pars.APPLICATIONCONFIG_DICTIONARY["ReportsSettings"]["ReportTypesNotToBePrintedOnScreen"]
            wrap_line_on_file=pars.APPLICATIONCONFIG_DICTIONARY["ReportsSettings"]["WrapLinesWhenWritingToFiles"]

            for myline in NewLines:
                    if print_on_screen:
                        print("{:}".format(color+myline))
                        print
                    if wrap_line_on_file:
                        self.write_line_to_file("{:s}".format(myline))
            if wrap_line_on_file==False:
                self.write_line_to_file("{:s}".format(UnWrappedline))

    # ---------------------------------
    # Print a report ARRAY (list of lists), line by line  - Includes Text Wrapping
    # ---------------------------------
    def print_report(self, pars):
        # REPORT HEADER
        color=self.color
        MyLine = color+'{0:_^'+str(pars.ScreenWitdh)+'}'
        print(MyLine.format(self.name))
        self.write_line_to_file(MyLine.format(self.name)+"\n")
        print(MyLine.format(self.State))
        self.write_line_to_file(MyLine.format(self.State)+"\n")

        #PRINT KEYS HEADER
        self.print_report_line(pars,self.get_keys(), False)

        # PRINT THE REPORT LINE BY LINE
        NewRecord=[]
        reportkeys=self.get_keys()
        for record in self.Report:
            self.print_report_line(pars,record,True)

        return -1

    # ---------------------------------
    # SORT SOURCE REPORT IN ACCORDANCE TO SORTING KEYS
    # ---------------------------------
    def sort_report(self, sortkeys):
        #try:
            reportkeys = self.get_keys()
            mykeys = []
            myfunc = ''
            for m in sortkeys:
                val = reportkeys.index(m)
                mykeys.append('x['+str(val)+']')
            myfunc = ",".join(mykeys)


            self.Report.sort(key=lambda x: eval(myfunc))
        #except:
        #    print("SORT_REPORT: \nSorting Keys = {:} \nReport Keys = {:}\n".format(
        #        sortkeys, reportkeys))
        #    return -1

    


    def split_string(self, inputstring, resulttype,join=[],joiner='-'):
        Result= self.myRegexDict[resulttype].match(inputstring)
        if Result:
            #print(vmname,resulttype,Result, "-".join (Result.groups()))
            if len(join)==0:
                return joiner.join (Result.groups())
            else:
                resstring=""
                for groupid in join:
                    resstring=joiner.join(Result.groups(groupid))
                return resstring 
        else:
            #print("split_string : parsed ", inputstring," to find ", resulttype," but REGEX did not find result")
            try:
                print()
                retval = "?"*self.FIELDLENGTHS[resulttype]

                #print("DEBUG Split_string retval:",retval)
                return retval
                
            except:
                print("-------------------  APPLICATION ERROR: --------------------------")
                print("split_string : FIELDLENGTHS does not have field ",resulttype)
                print("-------------------------------------------------------------------")
                exit(-1)
            


    # CONVERTS FILE SUFFIX TO SHORT DATE
    def tstoshortdate(self, x):
        return x[0:4]+"-"+x[4:6]+"-"+x[6:8]

    def colorvnfname(self,x):
        raise NotImplementedError("Must override parent")

    # Transforms value to MB/GB string format
    def mem_show_as_gb(self, value, convert):
        try:
            if convert:
                retval = int(int(value)/1024)
            else:
                retval = int(value)
            returnval = "{:>6s}".format(str(retval)+" GB")
            return returnval
        except:
            return "??"
    
    def show_as_percentage(self,myvalue , len,multiplier=1):
#    def show_as_percentage(self,numerator, denominator, len):
            #value_num=int(numerator)
            #value_den=int(denominator)
            #myvalue= int(100*value_num/value_den)
            returnval = "{:>3s}".format(str(myvalue*multiplier)+"%")
            return returnval.rjust(len)

    # REMOVES DT_NIMS from AZ/hostaggs
    def shorten_hostaggs(self, x):
        try:
            value= x.replace("DT_NIMS_", "")
            return value[0]
        except:
            #print("shorten_hostaggs : ERROR : value passed x is {:s}, result of replace is {:s}".format(x,value))
            return "?"

    def shorten_az(self, x):
        try:
            value= x.replace("DT_NIMS_", "")
            return value
        except:
            print("shorten_az : ERROR : value passed x is {:s}, result of replace is {:s}".format(x,value))
            return "?"         

    def shortenAAP(self, x):
        Retval= x.replace("active","A").replace("standby","S")
        return Retval
    
    def message_parser(self,msglist):
        print("-------report_library.py:message_parser------------")
        resultdict={}
        for msg in msglist:
            message= msg.lower().strip()
            startmessage=message
            
            for MyRegexKey in self.myMessageRegexDict.keys():
                MyRegex=self.myMessageRegexDict[MyRegexKey]
                #try:
                #Result=MyRegex.search(message)

                Result=MyRegex.findall(message)
                #Result2=MyRegex.search(message)
                if Result:
                    if MyRegexKey not in resultdict.keys():
                        resultdict[MyRegexKey]=[]
                    for x in Result :
                    #for x in Result.groups() :
                        #print("X=",x)
                        if x :
                            if len(x)>0 and x not in resultdict[MyRegexKey]:
                                #print(x,"--",type(x))
                                resultdict[MyRegexKey].append(x)
                    #print("\tResultdict:",resultdict[MyRegexKey])
                #print("\tRegexKey:{:20s} \tResult:{:} \tResult2:{:} ".format(MyRegexKey, Result, Result2))
                #except:
                #    print("\tmessage_parser : error on re.search for key={:}".format(MyRegexKey))
        print(json.dumps(resultdict,indent=10))

    
    def calc_max_percentage(self,num1, den1, num2, den2):
        retval= int(100*max(float (num1) / float (den1) , float (num2)/ float (den2)))
        return retval
# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------
#                           CLASS :     MENU
# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------
class menu:
 
    # -------------------------------------------------------------------------------------------------------------------------
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    White = '\033[97m'
    Yellow = '\033[93m'
    Magenta = '\033[95m'
    Grey = '\033[90m'
    Black = '\033[90m'
    Backg_Yellow= '\033[1;42m'
    Backg_Green= '\033[1;42m'
    Backg_Default='\033[1;0m'
    Default = '\033[99m'

    ColorsList =(OKBLUE,OKCYAN,OKGREEN,WARNING,FAIL,White,Yellow,Magenta,Grey)

