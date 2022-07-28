# Author Jacopo Pianigiani jacopopianigiani@juniper.net
# Written in 2022

from curses import ERR
import json
import string
import sys
import glob
import os
import itertools
import math
import re
import operator
from datetime import datetime
import traceback

from aop_logger import aop_logger


DEBUG = 0

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
    CONFIGFILE = 'resource-analysis.json'
    ERRORFILE = 'resource-analysis-errors.json'
    SYSLOGFILE = 'resource-analysis.log'

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

    def __init__(self):
        modulename="aop_logger"
        if modulename not in sys.modules:
            self.AOP_LOGGER_ENABLED=False
        else:
            self.AOP_LOGGER_ENABLED=True

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

            with open(self.PATHFORAPPLICATIONCONFIGDATA+self.CONFIGFILE,'r') as ConfigFile:
                try:
                    TMPJSON = json.load(ConfigFile)
                except:
                    traceback.print_exc(limit=None, file=None, chain=True)
                    print(" CRITICAL! : object class PARAMETERS, __init__ found JSON syntax error in  {:}".format(self.PATHFORAPPLICATIONCONFIGDATA+self.CONFIGFILE))
                    exit(-1)
            self.APPLICATIONCONFIG_DICTIONARY=dict(TMPJSON)
        #-------------------------------------------------------------------------------------------------------------------
            self.PATHFOROPENSTACKFILES=self.APPLICATIONCONFIG_DICTIONARY["Files"]["PathForOpenstackFiles"]
            self.PATHFOROUTPUTREPORTS=self.APPLICATIONCONFIG_DICTIONARY["Files"]["PathForOutputReports"]
        #-------------------------------------------------------------------------------------------------------------------

        #-------------------------------------------------------------------------------------------------------------------
            self.FILETYPES=tuple(self.APPLICATIONCONFIG_DICTIONARY["Files"]["FileTypes"])
            self.EXTENDEDFILETYPES=tuple(self.APPLICATIONCONFIG_DICTIONARY["Files"]["ExtendedFileTypes"])
            self.EXTENDEDFILETYPES_OPTIONAL=tuple(self.APPLICATIONCONFIG_DICTIONARY["Files"]["ExtendedFileTypes_Optional"])
        #-------------------------------------------------------------------------------------------------------------------

            self.paramsdict = self.APPLICATIONCONFIG_DICTIONARY["Application_Parameters"]
            self.paramslist=list(self.APPLICATIONCONFIG_DICTIONARY["User_CLI_Visible_Parameters"])
            self.metricformulas=self.APPLICATIONCONFIG_DICTIONARY["RackOptimizationInputParameters"]["MetricFormulasForRackOptimization"]
        #-------------------------------------------------------------------------------------------------------------------
        
        except:
            traceback.print_exc(limit=None, file=None, chain=True)
            #-------------------------------------------------------------------------------------------------------------------
            print("#-------------------------------------------------------------------------------------------------------------------")
            print(" CRITICAL! : object class PARAMETERS, __init__ did not find the application configuration file {:}".format(self.PATHFORAPPLICATIONCONFIGDATA+self.CONFIGFILE))
            print("\t Files {:} and  {:} must be , from thedirectory as python main executable, as follows: {:}".format(self.CONFIGFILE, self.ERRORFILE,self.PATHFORAPPLICATIONCONFIGDATA))
            print("#-------------------------------------------------------------------------------------------------------------------")
            exit(-1)
        #-------------------------------------------------------------------------------------------------------------------
        try:
            with open(self.PATHFORAPPLICATIONCONFIGDATA+self.ERRORFILE,'r') as ConfigFile:
                self.ERROR_DICTIONARY = json.load(ConfigFile)
        except:
            traceback.print_exc(limit=None, file=None, chain=True)
            print("#-------------------------------------------------------------------------------------------------------------------")
            print(" CRITICAL! : object class PARAMETERS, __init__ did not find the application configuration file {:}".format(self.PATHFORAPPLICATIONCONFIGDATA+self.CONFIGFILE))
            print("\t Files {:} and  {:} must be , from the directory as python main executable, as follows: {:}".format(self.CONFIGFILE, self.ERRORFILE,self.PATHFORAPPLICATIONCONFIGDATA))
            print("#-------------------------------------------------------------------------------------------------------------------")
            exit(-1)
         
        self.DEBUG=self.APPLICATIONCONFIG_DICTIONARY["Application_Parameters"]["DEBUG"]
        #-------------------------------------------------------------------------------------------------------------------
        if self.AOP_LOGGER_ENABLED:
            mysyslog=aop_logger(3,self.SYSLOGFILE)
            myloghandler=mysyslog.syslog_handler(
                    address= (self.APPLICATIONCONFIG_DICTIONARY["syslog"]["Target"],
                    self.APPLICATIONCONFIG_DICTIONARY["syslog"]["Port"]))
            self.logger=mysyslog.logger
        #-------------------------------------------------------------------------------------------------------------------



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
    # -----------------------------------
    def show_cli_command(self):
        MyLine = menu.OKGREEN+'{0:_^'+str(self.ScreenWitdh)+'}'
        print(MyLine.format('LIST OF PARAMETER ARGUMENTS'))
        print(json.dumps(self.paramsdict,indent=40))
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

    def IsItAMgmtSite(self,suffix):
            Sitename=self.parse_suffisso(suffix)
            if Sitename in self.APPLICATIONCONFIG_DICTIONARY["SitesCategories"]["LiveMgmtSites"]:
                Retval=True
            if Sitename in self.APPLICATIONCONFIG_DICTIONARY["SitesCategories"]["LabMgmtSites"]:
                Retval= True
            else:
                Retval =False
            return Retval

    def SiteType(self, sitename):
        Categs= self.APPLICATIONCONFIG_DICTIONARY["SitesCategories"]["Categories"]
        for Item in Categs:
            if sitename in self.APPLICATIONCONFIG_DICTIONARY["SitesCategories"][Item]:
                return Item
            
        return "??"

    # ----------------------------------------------
    def IsItWhatSite(self,category,suffix):
            Sitename=self.parse_suffisso(suffix)
            if category not in self.APPLICATIONCONFIG_DICTIONARY["SitesCategories"]["Categories"]:
                ErrString= "Category passed to IsItWhatSite is not in application config data list :"+category
                self.cast_error("00011",ErrString)

            if Sitename in self.APPLICATIONCONFIG_DICTIONARY["SitesCategories"][category]:
                Retval=True
            if Sitename in self.APPLICATIONCONFIG_DICTIONARY["SitesCategories"][category]:
                Retval= True
            else:
                Retval =False
            return Retval

    def set_service_to_initialvalue(self):
        self.paramsdict["SERVICE"]=self.paramsdict["INITIALSERVICEVALUE"]

    # ----------------------------------------------
    def Parse_Filtered_OS_FileList_BySuffixOrCommandMatch(self,CleanListOfJSONFiles, SuffixParameter):
            
            InternalReport=[]
            Retval=[]

            ParamsList=SuffixParameter.split(",")
            SiteCmdList= self.APPLICATIONCONFIG_DICTIONARY["SitesCategories"]["SiteCommands"]
            SiteCmdMap=self.APPLICATIONCONFIG_DICTIONARY["SitesCategories"]["SiteCommandMap"]
            TimeCmdList= self.APPLICATIONCONFIG_DICTIONARY["SitesCategories"]["TimeCommands"]

            MySiteList=[]
            SiteCommandsList=[]
            TimeCommandsList=[]

            SiteCommandsList  = list(filter(len, SiteCommandsList))

#           exit(-1)
# 
            SuffixList=[]
            for Item in ParamsList:
                if Item in SiteCmdList:
                    SiteCommandsList.append(Item)
                    for SubItem in SiteCmdMap[Item]:
                        MyAddlSitesList=self.APPLICATIONCONFIG_DICTIONARY["SitesCategories"][SubItem]
                        MySiteList+=MyAddlSitesList
                elif Item in TimeCmdList:
                    TimeCommandsList.append(Item)
                else:
                    SuffixList.append(Item)   
            MySiteList= list(dict.fromkeys(MySiteList))


            # Exact or partial Match of one or more Suffixes separated by Comma - Return files
            RetVal2=[]
            CurrentDate=19000101
 
            for x in CleanListOfJSONFiles: 
                Sitename=self.parse_suffisso(x)
                ShortDate=self.SuffixToShortDate(x)
                YYYYMMDDDate= self.SuffixToYYMMDDDateValue(x)
                IsLiveManagement= self.IsItWhatSite("LiveMgmtSites",x)
                IsLabManagement= self.IsItWhatSite("LabMgmtSites",x)
                IsManagement=IsLiveManagement or IsLabManagement

                AppendRecord0=True
                AppendRecord1=True
                AppendRecord2=True

                for Suffix in SuffixList:
                    AppendRecord0= x.find(Suffix)>-1 and AppendRecord0

                #print(x, x in MySiteList, MySiteList)
                if Sitename in MySiteList or len(MySiteList)==0:
                    AppendRecord1=True
                else:
                    AppendRecord1=False

                if self.paramsdict["SKIPMGMTSITE"] and IsManagement:
                    AppendRecord2=False
                else:
                    AppendRecord2=True

                if AppendRecord0 and AppendRecord1 and AppendRecord2:
                    RetVal2.append(x)


            if len(RetVal2)==0:
                print("No file returned")
                ErrString= "Parse_Filtered_OS_FileList_BySuffixOrCommandMatch: "+SuffixParameter+" file selector returns Empty Openstack filelist"
                self.cast_error("00012",ErrString)

            SortedByDateList = sorted(RetVal2, key=lambda x:x[0], reverse=True)


            return SortedByDateList        


            #    and (i.find(suffissotouse)>-1 
            #    and (self.paramsdict["SKIPMGMTSITE"]==False or IsItAMgmtSite(i)==False))] 
            # TRUE if site  == mgmt site

    def Get_Clean_Openstack_FilesList(self):

        cleanlist=[]
        try:
            ListOfFiles=os.listdir(self.PATHFOROPENSTACKFILES)
        except:
                self.cast_error("00003",self.PATHFOROPENSTACKFILES)
        files_txt=[i for i in ListOfFiles if i.endswith('.json')]
        for Filename in files_txt:
            for FileType in self.FILETYPES:
                PositionInFilename=Filename.find(FileType)
                if PositionInFilename>-1:
                    value = Filename[PositionInFilename+len(FileType)+1:Filename.find('.json')]
                    cleanlist.append(value)
        cleandict=dict.fromkeys(cleanlist)
        cleanlist=[]
        cleanlist=list(cleandict)
        return cleanlist

        # this function is used to fetch - for a suffix - the list of files to use 
    def GetListOfFilesFromSuffixMatch(self,suffissotouse):
            # ----------------------------------------------
        cleanlist=[]
        cleanlist= self.Get_Clean_Openstack_FilesList()
        if len(cleanlist)==0:
            self.cast_error("00003","Array CleanList is empty: 0 records")
        retval=self.Parse_Filtered_OS_FileList_BySuffixOrCommandMatch( cleanlist, suffissotouse)
        return(retval)
    
    def cast_error(self,ErrorCode, AddlData):
        NEWRECORD=[]
        a = str(self.__class__)
        traceback.print_exc(limit=None, file=None, chain=True)
        ErrorObjectClass= a.replace("'",'').replace("<",'').replace(">","").replace("class ","")
        ErrorInfo=self.ERROR_DICTIONARY[ErrorCode]
        #print(json.dumps(ErrorInfo,indent=30))
        ErrorObjectClass=ErrorInfo["Class"]
        SrcSuffix=self.get_param_value("SOURCE_SITE_SUFFIX")
        SiteName= self.parse_suffisso(SrcSuffix)
        if ErrorInfo["Level"]=="CRITICAL":
            NEWRECORD.append(SrcSuffix[0:8])
            NEWRECORD.append(SiteName)
            NEWRECORD.append(ErrorInfo["Level"])
            NEWRECORD.append(ErrorObjectClass)
            NEWRECORD.append(ErrorCode)
            NEWRECORD.append(ErrorInfo["Synopsis"])
            NEWRECORD.append(AddlData)
            #NEWRECORD.append(ErrorInfo)

            if self.AOP_LOGGER_ENABLED:
                syslogstring="Timestamp: {:9s} Site: {:12s} ErrCode: {:5s} Class:{:30s} Synopsis:{:60s}: {:120s}".format(SrcSuffix[0:8],
                            SiteName,ErrorCode,ErrorObjectClass,ErrorInfo["Synopsis"],AddlData)
                if ErrorInfo["Level"]=="CRITICAL":
                    self.logger.critical(syslogstring)
                elif ErrorInfo["Level"]=="ERROR":
                    self.logger.error(syslogstring)
                elif ErrorInfo["Level"]=="WARNING":
                    self.logger.warning(syslogstring)

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
#                           CLASS :     DICTARRAY
# -------------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------------
class dictarray:
    DICT_ARRAY = []
    AGGREGATE_LIST = []
    HYPERVISOR_LIST = []
    SERVERDICT = {}
    FLAVOR_LIST = []
    VOLUME_LIST = []
    NETWORK_LIST = []
    SUBNET_LIST = []
    VIRTUALPORT_DICT= {}

    def __init__(self):
        DICT_ARRAY = []
        self.AGGREGATE_LIST = []
        self.HYPERVISOR_LIST = []
        self.SERVERDICT = {}
        self.FLAVOR_LIST = []
        self.VOLUME_LIST = []
        self.NETWORK_LIST = []
        self.SUBNET_LIST = []
        self.VIRTUALPORT_DICT= {}
        self.VMPERPROJECT={}
        self.SKIPSERVICEGRAPH=False
        self.HWNUMAAWARE=True

    # --------------------------------------------------------------
    # This function loads the json files into the relevant ARRAY of list or dict
    # -----------------------------------------
    def load_jsons_into_dictarrays(self, pars, paramname):
        # --------------------------------------------------------------
        # Load site data files
        COUNT = 0
        DICT_ARRAY = []
        for ITEM in pars.FILETYPES:
            value = pars.paramsdict[paramname]
            FILENAME = pars.PATHFOROPENSTACKFILES + "/" + "openstack_" + ITEM + "_" + value + ".json"

            try:
                with open(FILENAME, 'r') as file1:
                    TMPJSON = json.load(file1)
                    DICT_ARRAY.append(TMPJSON)
                    # if  pars.DEBUG>1:
                    #print("load_jsons_into_dictarrays:  Loading  dict in array from {} for {} which is {} items long and {}\n".format(pars[paramname], FILENAME, len(TMPJSON),type(TMPJSON)))
                COUNT += 1

            except (IOError, EOFError) as e:
                pars.cast_error("00004","file:"+FILENAME)


        self.AGGREGATE_LIST = DICT_ARRAY[0]
        self.HYPERVISOR_LIST = DICT_ARRAY[1]
        self.SERVERDICT = dict(DICT_ARRAY[2])
        self.FLAVOR_LIST = DICT_ARRAY[3]
        self.VOLUME_LIST = DICT_ARRAY[4]

        if pars.paramsdict["SERVICEGRAPHENABLED"]:
            DICT_ARRAY = []
            for ITEM in pars.EXTENDEDFILETYPES:
                value = pars.paramsdict[paramname]
                FILENAME = pars.PATHFOROPENSTACKFILES + "/" + "openstack_" + ITEM + "_" + value + ".json"

                try:
                    with open(FILENAME, 'r') as file1:
                        TMPJSON = json.load(file1)
                        DICT_ARRAY.append(TMPJSON)
                        if  pars.DEBUG>1:
                            print("load_jsons_into_dictarrays:  Loading  dict in array from {} for {} which is {} items long and {}\n".format(pars[paramname], FILENAME, len(TMPJSON),type(TMPJSON)))
                    COUNT += 1
                except (IOError, EOFError) as e:
                    self.SKIPSERVICEGRAPH=True
                    MyName=self.__class__
                    ErrString="{:} skipping ServiceGraphReport ".format(MyName)
                    print(ErrString)                   
                    pars.cast_error("00013","file:"+FILENAME)

            if self.SKIPSERVICEGRAPH==False:
                self.NETWORK_LIST = DICT_ARRAY[0]
                self.SUBNET_LIST = DICT_ARRAY[1]
                self.VIRTUALPORT_DICT = dict(DICT_ARRAY[2])
        
        if pars.paramsdict["HWNUMAAWARE"]:
            DICT_ARRAY = []
            for ITEM in pars.EXTENDEDFILETYPES_OPTIONAL:
                value = pars.paramsdict[paramname]
                FILENAME = pars.PATHFOROPENSTACKFILES + "/" + "openstack_" + ITEM + "_" + value + ".json"
                try:
                    with open(FILENAME, 'r') as file1:
                        TMPJSON = json.load(file1)
                        DICT_ARRAY.append(TMPJSON)
                        #if  pars.DEBUG>1:
                        #    print("load_jsons_into_dictarrays:  Loading  dict in array from {} for {} which is {} items long and {}\n".format(pars[paramname], FILENAME, len(TMPJSON),type(TMPJSON)))
                    COUNT += 1
                except (IOError, EOFError) as e:
                    self.HWNUMAAWARE=True
                    MyName=self.__class__
                    ErrString="{:} skipping Numa Aware HW report ".format(MyName)
                    print(ErrString)                   
                    pars.cast_error("00013","file:"+FILENAME)

            if self.HWNUMAAWARE==True:
                self.HYPERVISOR_VCPU = dict(DICT_ARRAY[0])
        

            return 0




    def get_vms_by_computenode(self,node):
        retval=[]
        for x in self.SERVERDICT:
            #print(json.dump(x,indent=22))
            for VM in [y for y in self.SERVERDICT[x] if y["Host"] == node]:
                vmtoadd= VM["Name"]
                retval.append(vmtoadd)
        #print("get_vm_by_computenode {:}".format(retval))
        return retval

    def get_VNs_and_subnets(self,VNUUID):
        Retval=[]
        for VN in [x for x in self.NETWORK_LIST if x["ID"]==VNUUID]:
            VNSubnetUUID=VN["Subnets"]
            VNStatus= VN["State"]
            for Subnet in [y for y in self.SUBNET_LIST if y["ID"]==VNSubnetUUID]:
                SubnetCIDR=Subnet["Subnet"]
                SubnetIPVersion=Subnet["IP Version"]
                SubnetAllocPool=Subnet["Allocation Pools"]
                SubnetName=Subnet["Name"]
                TMPREC=[]
                TMPREC.append(VNStatus)
                TMPREC.append(SubnetName)
                TMPREC.append(str(SubnetIPVersion))
                TMPREC.append(SubnetCIDR)
                TMPREC.append(SubnetAllocPool)
                Retval.append(TMPREC)
        return Retval

                
    # Associates  VM to HOSTS
    # ----------------------------------
    def cmpt_to_agglist(self, mynodo):
        appartenenza_nodo = []
        for item in self.AGGREGATE_LIST:
            if mynodo in item["hosts"]:
                appartenenza_nodo.append(str(item["name"]))
        if DEBUG >= 3:
            print(
                "--- DEBUG --- for nodo={:s} agglist={:s}".format(mynodo, appartenenza_nodo))
        return appartenenza_nodo


    def get_vmname(self,vmuuid):
        VMNAME=""
        for PROGETTO in self.SERVERDICT:
            str_PROGETTO=str(PROGETTO)

            for VM in [ x for x in self.SERVERDICT[PROGETTO] if  str(x["ID"])==vmuuid]:
                                VMNAME=str(VM["Name"])

        if VMNAME=="":
            print("Error in get_vmname: did not find VM in project: ", str_PROGETTO,"with UUID:",vmuuid)
            print("DEBUG : get_vmname")
            
            VMNAME="!!UNKNOWN!!"
        return VMNAME


               

    def parse_flavor_properties(self, pars,flavorrecord):
        # -----------------------------------------------------------------------
        # EXTRACTS FLAVOR PLACEMENT ZONE FROM FLAVOR PROPERTIES RECORD
        # -----------------------------------------------------------------------
            if "Properties" in flavorrecord.keys():
                MyFlavorPropertiesDict = flavorrecord["Properties"]
                if len(MyFlavorPropertiesDict)==0:
                    retval=pars.APPLICATIONCONFIG_DICTIONARY["DefaultValues"]["DefaultFlavorProperties"]
                    ErrString="flavor {:} has properties, but empty: applying default values;using EXT as HostAgg, VM CPU UNPINNED".format(flavorrecord["Name"])
                    pars.cast_error("00102",ErrString)
                    return retval

            else:    
                ErrString="flavor {:}: missing properties:  applying default values;using EXT as HostAgg, VM CPU UNPINNED".format(flavorrecord["Name"] )
                pars.cast_error("00102",ErrString)
                retval=pars.APPLICATIONCONFIGDICTIONARY["DefaulValue"]["DefaultFlavorProperties"]
                return retval
                
            lista1 = MyFlavorPropertiesDict.split(',')
            mykeys=[]
            myvalues=[]
            try:
                for x in lista1:
                    key=x.split("=")[0].strip()
                    val=x.split("=")[1].strip().replace("'", "")
                    mykeys.append(str(key))
                # WARNING - REPLACEMENT OF DTNIMS WITH DT_NIMS since Flavors metadata have Placement zone MISPELLED
                    myvalues.append(val.upper().replace("DTNIMS","DT_NIMS"))
                minidict={}
                minidict.fromkeys(mykeys)

                for x in myvalues:
                    index=myvalues.index(x)
                    minidict[mykeys[index]]=x
                return minidict

            except:
                traceback.print_exc(limit=None, file=None, chain=True)
                ErrString="dictarrays: parse_flavor_properties: {}".format(flavorrecord["Name"])
                pars.cast_error("00102",ErrString)
                retval={}
        
            return retval

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


        self.REPORTFIELDGROUP =params.APPLICATIONCONFIG_DICTIONARY["Reports_Keys"]
        self.RACKOPTPARAMETERS =params.APPLICATIONCONFIG_DICTIONARY["RackOptimizationInputParameters"]
        self.FILESSTRUCTURE =params.APPLICATIONCONFIG_DICTIONARY["Files"]
        self.GenericDict={}

        self.FIELDTRANSFORMSATTRIBUTES=params.APPLICATIONCONFIG_DICTIONARY["FieldTransformsAttributes"]
        self.myRegexDict= {}
        for Item in self.FIELDTRANSFORMSATTRIBUTES["split_vnfname"].keys():
            value = self.FIELDTRANSFORMSATTRIBUTES["split_vnfname"][Item]
            #print("DEBUG", Item, value)
            self.myRegexDict[Item]=re.compile(value)        

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
        if not mykey:
            print("UpdateLastRecordValueByKey : error : key is null") 
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



    
    def calc_max_percentage(self,num1, den1, num2, den2):

        retval= int(100*max(float (num1) / float (den1) , float (num2)/ float (den2)))

        return retval

#---------------------------------------------------
#   Receives a Report Record, produces as return value a 2D Array containing one record per Line to be printed with wrapping of text beyond FieldLength
#---------------------------------------------------
    def LineWrapper(self, record):
        var_Keys=self.get_keys()
        Lines=[[]]
        MaxRows=128
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
            NewLines,UnWrappedline=self.LineWrapper(NewRecord)

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

    # CLASS REPORT General
    def calculate_report_total_usage(self, pars):
        totvcpuavail = 0
        totvcpuused = 0
        retval = []
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
        Result= self.myRegexDict[resulttype].match(vmname)
        if Result:
            #print(vmname,resulttype,Result, "-".join (Result.groups()))
            return "-".join (Result.groups())
        else:
            #print(vmname,resulttype," not found")
            try:
                return "?"*self.FIELDLENGTHS[resulttype]
            except:
                print("split_vnfname : FIELDLENGTHS does not have field ",resulttype)
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
    Default = '\033[99m'

    ColorsList =(OKBLUE,OKCYAN,OKGREEN,WARNING,FAIL,White,Yellow,Magenta,Grey)





