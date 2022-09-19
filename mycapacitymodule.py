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
from  report_library import *



class parameters_specific(parameters):

    def __init__(self,MyApplicationName):
        super().__init__(MyApplicationName)
        self.PATHFOROPENSTACKFILES=super().get_configdata_dictionary()["Files"]["PathForOpenstackFiles"]
        #-------------------------------------------------------------------------------------------------------------------
        self.FILETYPES=tuple(super().get_configdata_dictionary()["Files"]["FileTypes"])
        self.EXTENDEDFILETYPES=tuple(super().get_configdata_dictionary()["Files"]["ExtendedFileTypes"])
        self.EXTENDEDFILETYPES_OPTIONAL=tuple(super().get_configdata_dictionary()["Files"]["ExtendedFileTypes_Optional"])
        #-------------------------------------------------------------------------------------------------------------------


    def IsItAMgmtSite(self,suffix):
            Sitename=self.parse_suffisso(suffix)
            if Sitename in super().get_configdata_dictionary()["SitesCategories"]["LiveMgmtSites"]:
                Retval=True
            if Sitename in super().get_configdata_dictionary()["SitesCategories"]["LabMgmtSites"]:
                Retval= True
            else:
                Retval =False
            return Retval

    def SiteType(self, sitename):
        Categs= super().get_configdata_dictionary()["SitesCategories"]["Categories"]
        for Item in Categs:
            if sitename in super().get_configdata_dictionary()["SitesCategories"][Item]:
                return Item
            
        return "??"

    # ----------------------------------------------
    def IsItWhatSite(self,category,suffix):
            Sitename=self.parse_suffisso(suffix)
            if category not in self.APPLICATIONCONFIG_DICTIONARY["SitesCategories"]["Categories"]:
                ErrString= "Category passed to IsItWhatSite is not in application config data list :"+category
                self.cast_error("00011",ErrString)

            if Sitename in super().get_configdata_dictionary()["SitesCategories"][category]:
                Retval=True
            if Sitename in super().get_configdata_dictionary()["SitesCategories"][category]:
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
            SiteCmdList= super().get_configdata_dictionary()["SitesCategories"]["SiteCommands"]
            SiteCmdMap=super().get_configdata_dictionary()["SitesCategories"]["SiteCommandMap"]
            TimeCmdList= super().get_configdata_dictionary()["SitesCategories"]["TimeCommands"]

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
                        MyAddlSitesList=super().get_configdata_dictionary()["SitesCategories"][SubItem]
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
            if flavorrecord is None:
                print("ERROR: Flavor record is none")
                exit(-1)
            
            if "Properties" in flavorrecord.keys():
                
                if len(flavorrecord["Properties"])==0:
                    retval=pars.APPLICATIONCONFIG_DICTIONARY["DefaultValues"]["DefaultFlavorProperties"]
                    ErrString="flavor {:} has properties, but empty: applying default values;using EXT as HostAgg, VM CPU UNPINNED".format(flavorrecord["Name"])
                    pars.cast_error("00102",ErrString)
                    return retval
                else:
                    StringReplace =pars.APPLICATIONCONFIG_DICTIONARY["DefaultValues"]["DefaultFlavorProperties_StringReplace"]
                    #print("DEBUGGER00 keys are:",StringReplace.keys())
                    for key in StringReplace.keys():
                        temp = flavorrecord["Properties"].replace(' ','').replace("'","").upper()
                        MyFlavorPropertiesDict=temp.replace(key,StringReplace[key])
                        #print("DEBUGGER000 - MyFlavorPropertiesDict=",MyFlavorPropertiesDict)
                        #MyFlavorPropertiesDict = flavorrecord["Properties"].replace(key,StringReplace[key]).upper()
            else:    
                ErrString="flavor {:}: missing properties:  applying default values;using EXT as HostAgg, VM CPU UNPINNED".format(flavorrecord["Name"] )
                pars.cast_error("00102",ErrString)
                retval=pars.APPLICATIONCONFIGDICTIONARY["DefaulValue"]["DefaultFlavorProperties"]
                return retval

            if MyFlavorPropertiesDict is  None:
                ErrString="dictarrays: parse_flavor_properties: {}".format(flavorrecord["Name"])
                pars.cast_error("00102",ErrString)
                retval=pars.APPLICATIONCONFIGDICTIONARY["DefaulValue"]["DefaultFlavorProperties"]
                return retval

            else:
                lista1 = MyFlavorPropertiesDict.split(',')
                #print("DEBUGGER0: myflavorpropertiesdict={:}\n\tDEBUGGER0 lista1={:}".format(json.dumps(MyFlavorPropertiesDict,indent=22),lista1))
                if lista1 is None:
                    print("DEBUGGER1: ERROR: lista0 is none")
                    lista1=[]
                    exit(-1)

                mykeys=[]
                myvalues=[]

                for x in lista1:
                    if x is not None:
                        mypropertyentry=x.split("=")
                        #print("\t\tDEBUGGER2: myarray={:}".format(mypropertyentry))
                        key=x.split("=")[0]
                        value=x.split("=")[1]
                        #print("\t\tDEBUGGER2: x={:} key={:} value={:}".format(x,key,value))
                        if key is not None:
                            mykeys.append(str(key))
                # WARNING - REPLACEMENT OF DTNIMS WITH DT_NIMS since Flavors metadata have Placement zone MISPELLED
                        if value is not None:
                            adjustedvalue=value.upper().replace("DTNIMS","DT_NIMS")
                            myvalues.append(adjustedvalue)
                        minidict={}
                        minidict.fromkeys(mykeys)

                        for x in myvalues:
                            index=myvalues.index(x)
                            minidict[mykeys[index]]=x

                    else:
                        print("\t\tDEBUGGER2: x is None")
                return minidict




