import json
import string
import sys
import glob
import os
import itertools
import math
import operator
from datetime import datetime


DEBUG = 0



class parameters:
    # -------------------------------------------------------------------------------------------------------------------------
    # GLOBAL DICTIONARIES: these are used to store command line arguments values or user input values (so that the behavior is consistent between User interactive mode and CLI mode)

    PATHFORAPPLICATIONCONFIGDATA='./'
    CONFIGFILE = 'resource-analysis.json'
    ERRORFILE = 'resource-analysis-errors.json'
    APPLICATIONCONFIG_DICTIONARY={}
    MODE_OF_OPT_OPS = 0
    paramsdict={}
    paramslist=[]

    # -------------------------------------------------------------------------------------------------------------------------
    # FORMULAS FOR DISTANCE CALCULATION FROM TARGET
    # -------------------------------------------------------------------------------------------------------------------------

    # , 'abs(currentvalue-average)',  '(currentvalue-minimum)**4']
    #metricformulas = ['(currentvalue-average)**2']
    # -------------------------------------------------------------------------------------------------------------------------
    NO_OPTIMIZATION = 0
    OPTIMIZE_BY_CALC = 1
    OPTIMIZE_BY_FILE = 2



    def __init__(self):
        now = datetime.now()  # current date and time
        date_time = now.strftime("%d/%m/%Y %H:%M:%S")
        #date_time = now.strftime("%d/%m/%Y")
        self.paramsdict["TIMESTAMP"] = date_time
        TMPJSON=[]
        self.DSTSITES = []
        screenrows, screencolumns = os.popen('stty size', 'r').read().split()
        self.ScreenWitdh = int(screencolumns)
        self.ColorsList =(menu.OKBLUE,menu.OKCYAN,menu.OKGREEN,menu.WARNING,menu.FAIL,menu.White,menu.Yellow,menu.Magenta,menu.Grey) 

        #try:

        with open(self.PATHFORAPPLICATIONCONFIGDATA+self.CONFIGFILE,'r') as ConfigFile:
            TMPJSON = json.load(ConfigFile)
        self.APPLICATIONCONFIG_DICTIONARY=dict(TMPJSON)
        self.PATHFOROPENSTACKFILES=self.APPLICATIONCONFIG_DICTIONARY["Files"]["PathForOpenstackFiles"]
        self.PATHFOROUTPUTREPORTS=self.APPLICATIONCONFIG_DICTIONARY["Files"]["PathForOutputReports"]
        self.FILETYPES=tuple(self.APPLICATIONCONFIG_DICTIONARY["Files"]["FileTypes"])
        self.paramsdict = self.APPLICATIONCONFIG_DICTIONARY["Application_Parameters"]
        self.paramslist=list(self.APPLICATIONCONFIG_DICTIONARY["Application_Visible_Parameters"])
        self.OUTPUTFILENAME=self.PATHFOROUTPUTREPORTS+'/capacity-forecast.results'
        self.MYGLOBALFILE = open(self.OUTPUTFILENAME, 'w')
        self.metricformulas=self.APPLICATIONCONFIG_DICTIONARY["RackOptimizationInputParameters"]["MetricFormulasForRackOptimization"]
        #except:
        #    print(" CRITICAL! : object class PARAMETERS, __init__ did not find the application configuration file {:}".format(self.PATHFORAPPLICATIONCONFIG))
        #    exit(-1)
        with open(self.PATHFORAPPLICATIONCONFIGDATA+self.ERRORFILE,'r') as ConfigFile:
            TMPJSON = json.load(ConfigFile)
        self.ERROR_DICTIONARY=dict(TMPJSON)

    def set(self, key, value):
        self.paramsdict[key] = value
        return value

    def get(self, key):
        return self.paramsdict[key]

    def is_silentmode(self):
        return self.paramsdict["SILENTMODE"]
    # -----------------------------------
    # PRINT to tty or FILE
    def myprint(self, value):
        if type(value) != str:
                print(str(value))
        else:
                print(value)

    def get_param_value(self, name):
        return self.paramsdict[name]

    def get_azoptimization_mode(self):
    # NO_OPTIMIZATION = 0
    # OPTIMIZE_BY_CALC = 1
    # OPTIMIZE_BY_FILE = 2
        if len(self.paramsdict["HW_OPTIMIZATION_MODE"]) == 0:
            MODE_OF_OPT_OPS = self.NO_OPTIMIZATION
        else:
            if self.paramsdict["HW_OPTIMIZATION_MODE"].find('OPTIMIZE') > -1:
                MODE_OF_OPT_OPS = self.OPTIMIZE_BY_CALC
            else:
                MODE_OF_OPT_OPS = self.OPTIMIZE_BY_FILE
        return MODE_OF_OPT_OPS

    def show_cli_command(self):
        MyLine = menu.OKGREEN+'{0:_^'+str(self.ScreenWitdh)+'}'
        self.myprint(MyLine.format('LIST OF PARAMETER ARGUMENTS'))
        self.myprint(json.dumps(self.paramsdict,indent=40))
        # PRINT CLI COMMAND AND PARAMETERS USED
        CMD = "python3 resource-analysis.py"
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
        self.myprint(CMD4)
        return True

        # this function is used to fetch - for a suffix - the list of files to use 
    def GetListOfFilesFromSuffixMatch(self,suffissotouse):
            # ----------------------------------------------
            # TRUE if site  == mgmt site
        def IsItAMgmtSite(suffix):
                if len(suffix)==14 or suffix[14:]=='ber800' or suffix[14:]=='stg810':
                    return True
                else:
                    return False
            # ----------------------------------------------

        cleanlist=[]
        ListOfFiles=os.listdir(self.PATHFOROPENSTACKFILES)

        files_txt = [i for i in ListOfFiles if i.endswith('.json') and (i.find(suffissotouse)>-1 and (self.paramsdict["SKIPMGMTSITE"]==False or IsItAMgmtSite(i)==False))]
        for Filename in files_txt:
            for FileType in self.FILETYPES:
                PositionInFilename=Filename.find(FileType)
                if PositionInFilename>-1:
                    value = Filename[PositionInFilename+len(FileType)+1:Filename.find('.json')]
                    condition3= self.paramsdict["SKIPMGMTSITE"]==False or IsItAMgmtSite(value)==False
                    if condition3:
                        cleanlist.append(value)
        cleandict=dict.fromkeys(cleanlist)
        cleanlist=[]
        cleanlist=list(cleandict)
        if len(cleanlist)==0:
            print("ERROR : no Openstack JSONs files found in folder... exiting")
            exit(-1)
        return(cleanlist)




# --------------------EXTRACTS SITENAME FROM SUFFISSO note : STG810 specific parsing
    def parse_suffisso(self, suffisso):
        if len(suffisso) == 20:
            # NOTE: STG810 does not show stg810 in the suffix as the cc-jumphost hostname is configured wrongly
            return suffisso[14:]
        else:
            return "stg810"

class dictarray:
    DICT_ARRAY = []
    AGGREGATE_LIST = []
    HYPERVISOR_LIST = []
    SERVERDICT = {}
    FLAVOR_LIST = []
    VOLUME_LIST = []

    def __init__(self):
        self.DICT_ARRAY = []
        self.AGGREGATE_LIST = []
        self.HYPERVISOR_LIST = []
        self.SERVERDICT = {}
        self.FLAVOR_LIST = []
        self.VOLUME_LIST = []


    # --------------------------------------------------------------
    # This function loads the json files into the relevant ARRAY of list or dict
    # -----------------------------------------
    def load_jsons_into_dictarrays(self, pars, paramname):
        # --------------------------------------------------------------
        # Load site data files
        COUNT = 0
        self.DICT_ARRAY = []
        for ITEM in pars.FILETYPES:
            value = pars.paramsdict[paramname]
            FILENAME = pars.PATHFOROPENSTACKFILES + "/" + "openstack_" + ITEM + "_" + value + ".json"

            try:
                with open(FILENAME, 'r') as file1:
                    TMPJSON = json.load(file1)
                    self.DICT_ARRAY.append(TMPJSON)
                    # if  DEBUG>1:
                    #print("load_jsons_into_dictarrays:  Loading  dict in array from {} for {} which is {} items long and {}\n".format(pars[paramname], FILENAME, len(TMPJSON),type(TMPJSON)))
                COUNT += 1

            except (IOError, EOFError) as e:
                print("ERROR - file {:s} does not exist".format(FILENAME))
                exit(-1)

        self.AGGREGATE_LIST = self.DICT_ARRAY[0]
        self.HYPERVISOR_LIST = self.DICT_ARRAY[1]
        self.SERVERDICT = dict(self.DICT_ARRAY[2])
        self.FLAVOR_LIST = self.DICT_ARRAY[3]
        self.VOLUME_LIST = self.DICT_ARRAY[4]

        return COUNT

    # ------- GET LIST OF PROJECT EXISTING IN SRC SITE ---------------
    def GetListOfProjectsInSite(self, pars, menu):
        results = []

        for PROGETTO in self.SERVERDICT:
            str_PROGETTO = str(PROGETTO)
            results.append(str_PROGETTO)
        index = 0
        sortedres = sorted(results, key=lambda x: x[0], reverse=False)
        os.system("clear")
        stringalinea1 = '{0:_^'+str(menu.ScreenWitdh)+'}'
        pars.myprint(stringalinea1.format(
            " SERVICES AVAILABLE IN SITE "+pars.paramsdict["SOURCE_SITE_SUFFIX"]))
        for ServiceName in sortedres:
            print("- {:2d} --- {:20s}".format(index, ServiceName))
            index += 1
        src=""
        
        while len(src)==0: 
            src = str(input("Enter source SERVICES separated by <space>:"))
        res = []
        if src.upper().find("ALL")>-1:
            res = [i for i in sortedres]
        else:
            lista = [int(i) for i in src.split(' ') if i.isdigit()]
            for x in lista:
                res.append(sortedres[x])
        print(res)
        return res


    def get_vms_by_computenode(self,node):
        retval=[]
        for x in self.SERVERDICT:
            #print(json.dump(x,indent=22))
            for VM in [y for y in self.SERVERDICT[x] if y["Host"] == node]:
                vmtoadd= VM["Name"]
                retval.append(vmtoadd)
        #print("get_vm_by_computenode {:}".format(retval))
        return retval

class report(parameters):
    # GENERAL - Length of Each KEY in SOURCE REPORT

    # GENERAL - Function applied during printing of report on each field to transform output

    ReportType_VM = "VM"
    ReportType_HW = "HW"
    ReportType_RACK = "RACK"
    ReportType_TOTALRESULTS = "TOTALRESULTS"
    ReportType_MENU = "MENU"
    ReportType_REPORTTOTALUSAGE = "MENU"
    ReportTypesList = (ReportType_VM, ReportType_HW, ReportType_RACK,
                       ReportType_TOTALRESULTS, ReportType_MENU,ReportType_REPORTTOTALUSAGE)

    ReportKeysVariables = ["VM_REPORT_KEYS",
                            "HW_REPORT_KEYS","RACK_REPORT_KEYS",
                            "TOTALRESULTS_REPORT_KEYS","MENU_REPORT_KEYS",
                            "HWREPORTTOTALUSAGE_KEYS"]
    ReportSortingKeysVariables =[
        "VM_REPORT_SORTINGKEYS",
        "HW_REPORT_SORTINGKEYS",
        "RACK_REPORT_SORTINGKEYS",
        "TOTALRESULTS_REPORT_SORTINGKEYS",
        "MENU_REPORT_SORTINGKEYS",
        "HWREPORTTOTALUSAGE_SORTINGKEYS"]
    Report = []
    ReportTotalUsage = []


    def __init__(self):
        super().__init__()
        self.Report = []
        self.ReportType=0
        self.State=''
        self.ReportTotalUsage = []
        self.name=str(self.__class__).replace("'",'').replace("<",'').replace(">","").replace("class ","") + hex(id(self))
        self.FIELDLENGTHS= self.APPLICATIONCONFIG_DICTIONARY["FieldLenghts"]
        self.FIELDLISTS= self.APPLICATIONCONFIG_DICTIONARY["FieldLists"]
        #print(json.dumps(self.APPLICATIONCONFIG_DICTIONARY,indent=22))
        self.FIELDLISTSITEMSLENGTH= self.APPLICATIONCONFIG_DICTIONARY["FieldListsItemsLength"]

        self.FIELDTRANSFORMS=self.APPLICATIONCONFIG_DICTIONARY["FieldTransforms"]
        self.REPORTFIELDGROUP =self.APPLICATIONCONFIG_DICTIONARY["Reports_Keys"]
        self.RACKOPTPARAMETERS =self.APPLICATIONCONFIG_DICTIONARY["RackOptimizationInputParameters"]

    def ClearData(self):      
        self.Report = []
        self.State=''
        self.ReportTotalUsage = []

    def set_name(self,myname):
        self.name=myname
        self.ReportFile = open(self.APPLICATIONCONFIG_DICTIONARY["Files"]["PathForOutputReports"]+"/"+self.name, 'w')


    def set_state(self,mystatus):
        self.State=mystatus
        self.write_line_to_file(mystatus)


    def write_line_to_file(self,line):
        try:
            self.ReportFile.write(line+"\n")
        except:
            print("ERROR : {} write_line_to_file - name for object {} is empty".format(self.__class__,self.name))
            exit(-1)

    def get_sorting_keys(self):
        try:
            return eval("self."+self.ReportSortingKeysVariables[self.ReportTypesList.index(self.ReportType)])
        except:
            print("__ ERROR __ get_sorting_keys__ reporttype = {} List of vars = {}".format(
                self.ReportType, self.ReportSortingKeysVariables))

    def get_keys(self):
        #try:
            index1=self.ReportTypesList.index(self.ReportType)
            stringa2=""
            stringa2="self."+self.ReportKeysVariables[index1]
            return eval(stringa2)
        #except:
        #    print("STRING passed to eval from get_keys(): >{:}< ".format(stringa2))
        #    print("__ ERROR __ get_keys__ reporttype = {:} List of vars = {}".format(
        #        self.ReportType, self.ReportKeys))
        #    print(self.ReportTypesList)
        #    print(self.ReportType)
        #    exit(-1)

    def UpdateLastRecordValueByKey(self, mykey, value):
        record= self.Report[len(self.Report)-1]
        if mykey in self.FIELDLISTS:
            for x in value:
                record[self.get_keys().index(mykey)].append(x)
        else:
            record[self.get_keys().index(mykey)]=value

    def FindRecordByKeyValue(self, mykey, value):
        MyFieldIndex=self.get_keys().index(mykey)
        for x in self.Report:
            if x[MyFieldIndex]==value:
                return x           
        #print("ERROR Class report,FindRecordByKeyValue : record with value {:} not found in field with key {:} ".format(mykey,value))
        return []

    def appendnewrecord(self, newrecord):
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
            if mykey in self.FIELDLISTS:
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


    # Associates  VM to HOSTS
    # ----------------------------------
    def cmpt_to_agglist(self, mynodo, agglist):
        appartenenza_nodo = []
        for item in agglist:
            if mynodo in item["hosts"]:
                appartenenza_nodo.append(str(item["name"]))
        if DEBUG >= 3:
            print(
                "--- DEBUG --- for nodo={:s} agglist={:s}".format(mynodo, appartenenza_nodo))
        return appartenenza_nodo
#---------------------------------------------------
#   Receives a Report Record, produces as return value a 2D Array containing one record per Line to be printed with wrapping of text beyond FieldLength
#---------------------------------------------------
    def LineWrapper(self, record):
        var_Keys=self.get_keys()
        Lines=[[]]
        MaxRows=8
        Lines=[['' for j in range(len(var_Keys) )] for i in range(MaxRows)]
        MaxRows=0

        for ReportKeyItem in var_Keys:
            RecordEntryIndex =var_Keys.index(ReportKeyItem)
            var_FieldLen = self.get_fieldlength(ReportKeyItem)
            var_RecordEntry= record[RecordEntryIndex]  
            if type(var_RecordEntry)== list:
                var_Entry=""
                for ListItem in var_RecordEntry:
                    var_Entry+=ListItem
            else:
                var_Entry=var_RecordEntry
            var_RecordEntryLen = len(var_Entry)
            RowsValue = math.ceil(var_RecordEntryLen/var_FieldLen)
            if RowsValue>MaxRows:
                MaxRows=RowsValue

            for NofLinesPerRecEntry in range(RowsValue):
                stringa_start = NofLinesPerRecEntry*var_FieldLen
                if (var_RecordEntryLen> stringa_start+ var_FieldLen  ):
                    stringa_end = (1+NofLinesPerRecEntry)*var_FieldLen
                else:
                    stringa_end =  var_RecordEntryLen
                newItem=var_Entry[stringa_start:stringa_end]
                Lines[NofLinesPerRecEntry][RecordEntryIndex]=newItem

        retval=[]
        for i in range(MaxRows):
            myline=''
            for j in range(len(var_Keys)):
                length=self.get_fieldlength(var_Keys[j])
                stringa1="{:"+str( length  )+"s} |"
                myline+=stringa1.format(Lines[i][j])    
            retval.append(myline)

        return retval


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
                    ListItemLen =self.FIELDLISTSITEMSLENGTH[self.FIELDLISTS.index(columnname)]
                    FormatString_ListItemField ="{:"+str( ListItemLen)+"s}"
                    NewRecordListEntry=[]
                    for RecordEntry in initialvalue:
                        try:
                            value = FormatString_ListItemField.format(str(RecordEntry))
                            TransformedValue = eval(transform)
                            #print("Record_ApplyTransforms DEBUG >{:}< >{:}<".format(TransformedValue,columnname))
                            #NewRecordListEntry.append(FormatString_SingleValue.format(TransformedValue))
                            NewRecordListEntry.append(TransformedValue)

                        except:
                            print("Record_ApplyTransforms: ERROR 05 in applying transform\n")
                            print("Record_ApplyTransforms: item RecordEntry={:},transform={:}".format(RecordEntry,transform) )
                            exit(-1)
                    NewRecord.append(NewRecordListEntry)
                    
                else:
                    value = str(initialvalue)
                    NewRecord.append(FormatString_SingleValue.format(eval(transform)))

            except:
                print("Record_ApplyTransforms: ERROR 04 START - neither list nor else\n")
                print("transform=",transform)
                print("record:\n")
                print(record)
                eval(transform)
                print("Record_ApplyTransforms: ERROR 04 - END")
                exit(-1)

        return NewRecord

#---------------------------------------------------
#   REturns Report color by report class
#---------------------------------------------------      
    def set_report_color(self):
        a = str(self.__class__)
        b= a.replace("'",'').replace("<",'').replace(">","").replace("class ","")
        if b.find("vm_report")>-1:
            color=menu.OKGREEN
        else:
            color=menu.Yellow
        return color
  # ---------------------------------
    # Print  report Keys header - using Text Wrapping
    # ---------------------------------   
    def print_keys_on_top_of_report(self,pars):
        color=self.set_report_color()
        var_Keys=self.get_keys()
        NewLines=self.LineWrapper(var_Keys)
        for myline in NewLines:
            pars.myprint("{:}".format(myline))
            pars.myprint
            self.write_line_to_file(color+myline)

    def print_report_line(self, pars,record):
        NewRecord=[]
        NewLines=[[]]
        NewRecord=self.Record_ApplyTransforms(record)
        NewLines=self.LineWrapper(NewRecord)

        for myline in NewLines:
                pars.myprint("{:}".format(myline))
                pars.myprint
                self.write_line_to_file("{:s}".format(myline))
        return True

    # ---------------------------------
    # Print a report ARRAY (list of lists), line by line  - Includes Text Wrapping
    # ---------------------------------
    def print_report(self, pars):
        # REPORT HEADER
        MyLine = '{0:_^'+str(pars.ScreenWitdh)+'}'
        color=self.set_report_color()
        pars.myprint(MyLine.format(self.name))
        self.write_line_to_file(MyLine.format(self.name)+"\n")
        pars.myprint(MyLine.format(self.State))
        self.write_line_to_file(MyLine.format(self.State)+"\n")

        #PRINT KEYS HEADER
        self.print_keys_on_top_of_report(pars)

        # PRINT THE REPORT LINE BY LINE
        NewRecord=[]
        reportkeys=self.get_keys()
        for record in self.Report:
            self.print_report_line(pars,record)

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

    # CLASS REPORT General
    def calculate_report_total_usage(self, pars):
        totvcpuavail = 0
        totvcpuused = 0
        retval = []
        if self.ReportType==self.ReportType_HW:
            Divisor = "vCPUsAvailPerHV"
            Dividend = "vCPUsUsedPerHV"

        for x in self.Report:
            totvcpuavail += x[self.get_keys().index(Divisor)]
            totvcpuused += x[self.get_keys().index(Dividend)]
        if totvcpuavail > 0:
            usage = totvcpuused / float(totvcpuavail)
        else:
            usage = 0
        
        self.ReportTotalUsage=[]
        if self.ReportType==self.ReportType_HW:
            retval.append("% OF VCPU USAGE :")
            retval.append(str(int(usage*100))+"%")

        retval.append("TOTAL # OF VCPUs USED :")
        retval.append(totvcpuused)
        retval.append("TOTAL # OF VCPUs AVAIL :")
        retval.append(totvcpuavail)
        retval.append("TOTAL # OF COMPUTES :")
        retval.append(len(self.Report))
        
        retval.append("COMPUTE LOAD SYMMETRY :")
        retval.append(self.Calculate_UsageSymmetry_ofLoadPerCompute()) 
        self.ReportTotalUsage=retval
        return retval

    

    def split_vnfname(self, vmname, resulttype):
        if len(vmname) < 23:
            return vmname
        if resulttype == 'vnf':
            return vmname[12:16]
        if resulttype == 'vnfc':
            return vmname[18:23]
        if resulttype == 'Lineup':
            return vmname[6:9]
        if resulttype == 'vnf-vnfc':
            return vmname[12:16]+"-"+vmname[18:23]

    # CONVERTS FILE SUFFIX TO SHORT DATE
    def tstoshortdate(self, x):
        return x[0:4]+"-"+x[4:6]+"-"+x[6:8]

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
    

    def show_as_percentage(self,numerator, denominator, len):
            value_num=int(numerator)
            value_den=int(denominator)
            myvalue= int(100*value_num/value_den)
            returnval = "{:>3s}".format(str(myvalue)+"%")
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
class menu():
    # -------------------------------------------------------------------------------------------------------------------------
    # -------------------------------------------------------------------------------------------------------------------------
    #                           CLASS :     MENU
    # -------------------------------------------------------------------------------------------------------------------------
    # -------------------------------------------------------------------------------------------------------------------------
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
    Default = '\033[99m'

    ColorsList =(OKBLUE,OKCYAN,OKGREEN,WARNING,FAIL,White,Yellow,Magenta,Grey)
