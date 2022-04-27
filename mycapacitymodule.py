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

    PATHFORAPPLICATIONCONFIG='./resource-analysis.json'
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

        with open(self.PATHFORAPPLICATIONCONFIG,'r') as ConfigFile:
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
        if self.get("OUTPUTTOFILE"):
            if type(value) == list:
                temp = ''
                self.MYGLOBALFILE.write(temp.join(str(value)))
                self.MYGLOBALFILE.write('\n')
            else:
                self.MYGLOBALFILE.write(value)
                self.MYGLOBALFILE.write('\n')
        else:
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
    def get_src_prj(self, pars, menu):
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
        for x in sortedres:
            print("- {:2d} --- {:20s}".format(index, x))
            index += 1

        src = str(input("Enter source SERVICES separated by <space>:"))
        print(src)
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

    # ---------------------------------
    # Print a report ARRAY (list of lists), line by line
    def print_report(self, pars):
        
        MyLine = '{0:_^'+str(pars.ScreenWitdh)+'}'
        a = str(self.__class__)
        b= a.replace("'",'').replace("<",'').replace(">","").replace("class ","")
        if b.find("vm_report")>-1:
            color=menu.OKGREEN
        else:
            color=menu.Yellow

        pars.myprint(MyLine.format(self.name))
        self.write_line_to_file(MyLine.format(self.name)+"\n")
        pars.myprint(MyLine.format(self.State))
        self.write_line_to_file(MyLine.format(self.State)+"\n")

        def print_keys_on_top_of_report(self):
            var_Keys=self.get_keys()
            HeaderLines=[]
            MaxRows=0
            ColLengths=[]

            for ReportKeyItem in var_Keys:

                var_FieldLen = self.get_fieldlength(ReportKeyItem)
                var_KeyLen = len(ReportKeyItem)                
                #print("field = {:s} KeyLen={:d} FieldLen={:d}".format(ReportKeyItem, var_KeyLen,var_FieldLen))
                NewKeyLine=[]
                ColLengths.append(math.ceil(var_KeyLen/var_FieldLen))


                if math.ceil(var_KeyLen/var_FieldLen)>MaxRows:
                    MaxRows=math.ceil(var_KeyLen/var_FieldLen)
                for NofLinesPerKey in range(0,math.ceil(var_KeyLen/var_FieldLen)):
                    stringa_start = NofLinesPerKey*var_FieldLen
                    if (var_KeyLen> stringa_start+ var_FieldLen  ):
                        stringa_end = (1+NofLinesPerKey)*var_FieldLen
                    else:
                        stringa_end =  var_KeyLen
                    newItem=ReportKeyItem[stringa_start:stringa_end]
                    #"{:"+str(var_FieldLen)+"s}".format()
                    NewKeyLine.append(newItem)
                    #print(newItem)
                
                HeaderLines.append(NewKeyLine)
            NewHeaders=[['' for i in range(MaxRows)] for j in range(len(var_Keys) )]
            for i in range(len(HeaderLines)):
                for j in range(len(HeaderLines[i])):
                    NewHeaders[i][j]=HeaderLines[i][j]

            for i in range(MaxRows):
                myline=''
                for j in range(len(var_Keys)):
                    length=self.get_fieldlength(var_Keys[j])
                    stringa1="{:"+str( length  )+"s} |"
                    myline+=stringa1.format(NewHeaders[j][i])      
                pars.myprint(stringa1.format(color+myline))
                self.write_line_to_file(stringa1.format(color+myline))
            
        # --------------------------------------------------------------------------------------------------------
        # PRINT_REPORT - def procedure
        # --------------------------------------------------------------------------------------------------------
        if self.length() == 0:
            print("ERROR - print_report  - report array {} has 0 records".format(self))
            print("-- print_report : ")
            print(json.dumps(pars.paramsdict ,indent=22))
            print("-- print_report")
            exit(-1)
        if pars.is_silentmode() == False:
            pars.myprint(color)
        
        print_keys_on_top_of_report(self)
        
        reportkeys=self.get_keys()

        for record in self.Report:
            myline = ''
            myformat = ''

            currentrecord={}
            for row_itemnumber in range(self.keys_length()):
                # Fetches each item in the report row into initialvalue and gets what type it is, and what's the length of the output record (FIELDLENGTH)

                if row_itemnumber < len(record):
                    initialvalue = record[row_itemnumber]
                    mytype = type(initialvalue)
                    key=reportkeys[row_itemnumber]
                    currentrecord[key]=record[row_itemnumber]
                    newelement = row_itemnumber
                else:
                    initialvalue = '!!'
                    mytype = string
                    newelement = row_itemnumber

                columnname = self.get_keys()[newelement]
                length = self.FIELDLENGTHS[columnname]
                stringa1="{:"+str( length)+"s} |"
                stringa2="{:"+str( length)+"s}"
                try:
                    transform = self.FIELDTRANSFORMS[columnname]
                except:
                    transform = 'value'
                try:
                    if mytype == list:
                        tmpline = ''
                        tmpval=''
                            #tmpline=" ".join(map(eval(transform),initialvalue))
                        for x in initialvalue:
                            value = str(x)
                            tmpval += eval(transform)
                        tmpline += stringa2.format(tmpval)
                        myline += stringa1.format(tmpline)
                    else:
                        value = str(initialvalue)
                        myline += stringa1.format(eval(transform)[0:length])
                            #myline += eval(transform) + " | "
                except:
                    myline += stringa2.format("?? |")
                    print(transform)
                    eval(transform)

            
            pars.myprint("{:s}".format(myline))
            self.write_line_to_file("{:s}".format(myline))

        if len(self.ReportTotalUsage)>0:
            myline=self.ReportTotalUsage
            pars.myprint(myline)
            self.write_line_to_file("{:}".format(myline))
            
        return -1

    # SORT SOURCE REPORT IN ACCORDANCE TO SORTING KEYS
    def sort_report(self, sortkeys):
        #try:
            reportkeys = self.get_keys()
            mykeys = []
            myfunc = ''
            for m in sortkeys:
                #print("DEBUG SORT REPORT self= :m=",self, m)
                # GET THE INDEX OF EACH ITEM IN SORTINGKEYs
                val = reportkeys.index(m)

                mykeys.append('x['+str(val)+']')
            myfunc = ",".join(mykeys)
            # print(myfunc)
            # print(reportkeys)
            # print(len(reportkeys))

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
            return 0
    

    def show_as_percentage(self,numerator, denominator, len):
            value_num=int(numerator)
            value_den=int(denominator)
            myvalue= int(100*value_num/value_den)
            returnval = "{:>3s}".format(str(myvalue)+"%")
            return returnval.rjust(len)

    # REMOVES DT_NIMS from AZ/hostaggs
    def shorten_hostaggs(self, x):
        value= x.replace("DT_NIMS_", "")
        return value[0]

    def shorten_az(self, x):
        value= x.replace("DT_NIMS_", "")
        return value

class menu(parameters):
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

    def __init__(self):

        screenrows, screencolumns = os.popen('stty size', 'r').read().split()
        self.ScreenWitdh = int(screencolumns)

        # GLOBAL USER INTERFACE SETTINGS AND PARAMETERS
        self.UILIST = []
        self.SitesPerPageToShow = 18
        self.PerSiteWidth = 20
        self.WidthOfEachProjectName = 30
        self.RemainingWidthForProjectsinSite = 61
        # screencolumns=120

    def printline(self):
        stringalinea1 = '{0:_^'+str(self.ScreenWitdh)+'}'
        report.myprint(stringalinea1)

    # PRINTS THE USER INTERACTIVE MENU PREPARED IN get_fileslist()
    def print_menu(self, sortedlist, prompt):
        # PRINT LIST OF ITEMS BY PAGE
        stringalinea1 = '{0:-^'+str(self.ScreenWitdh)+'}'
        stringalinea2 = '{0:.^'+str(self.ScreenWitdh)+'}'
        rowindex = 0
        goon = True
        pagestarts = []
        pageitems = []

        for pagenum in range(0, 1+int(len(self.UILIST)/self.SitesPerPageToShow), 1):
            pagestarts.append(pagenum*self.SitesPerPageToShow)
            pageitems.append(min((+1)*self.SitesPerPageToShow,
                             len(self.UILIST)-pagenum*self.SitesPerPageToShow))

        currentpage = 0
        index = 0
        while goon:
            os.system("clear")
            print(menu.FAIL + stringalinea1.format(''))
            print(menu.FAIL + stringalinea1.format(' CAPACITY FORECAST '))
            print(menu.FAIL + stringalinea1.format(''))

            # print("\n")
            data = self.UILIST[0][0][20:31]

            print(stringalinea1.format(' Page '+str(index)+' '))
            for rowindex in range(pagestarts[index], pagestarts[index]+pageitems[index]):
                newdata = self.UILIST[rowindex][0][20:31]
                if newdata != data:
                    data = newdata
                    print(stringalinea2.format(''))
                print(menu.Yellow+"{:s}".format(self.UILIST[rowindex][0]))

            print(stringalinea1.format(''))
            PAGEBACK = ['-', '_', 'b', 'B']
            try:
                print(
                    "\n\t\t\t--------- Previous Page : -,_,b; next page: any other  letter; <Enter> to exit :")
                userinput = input(
                    "\n\t\t\t--------- Enter {:s} suffix: ".format(prompt))
                ISNUMBER = userinput.isdigit()
                ISALPHA = userinput.isalpha()
                ISNULL = len(userinput) == 0
                if ISNUMBER and ISNULL == False:
                    src = int(userinput)
                if ISNUMBER == False and ISNULL == False or ISALPHA:
                    src = -1
                    if userinput in PAGEBACK:
                        value = -1
                    else:
                        value = 1

                if ISNULL:
                    src = -99

                if src >= 0 and src < pagestarts[index]+pageitems[index]:
                    print(
                        "\t\t\t\t ......... INPUT ACCEPTED {:d}.........\n\n".format(src))
                    retval = sortedlist[src][3]
                    print(
                        "\t\t\t\t\t ---------- USER INPUT=>{:s}<--".format(retval))
                    goon = False
                    return retval
                elif src == -1:
                    if value == 1:
                        print("\t\t\t\t\t\t.....NEXT PAGE...")
                    else:
                        print("\t\t\t\t\t\t.....PREVIOUS PAGE...")

                    index += value
                    index = index % len(pagestarts)
                    goon = True
                    os.system('sleep 0.2')
                elif src == -99:
                    goon = False
                    print("\t\t\t\t ......... EXITING2 .........\n\n")
                    exit(-1)
            except (ValueError) as e:
                goon = False
                print("\t\t\t\t ......... EXITING .........\n\n")
                exit(-1)
            except (NameError) as e:
                print("\t\t\t\t\t\t.....NEXT PAGE...")
                index += 1
                index = index % len(pagestarts)
                goon = True
