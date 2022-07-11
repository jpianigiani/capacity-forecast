# Author Jacopo Pianigiani jacopopianigiani@juniper.net
# Written in 2022

import json
import string
import sys
import glob
import os
import itertools
from itertools import chain
import math
import operator
from   datetime import datetime
import time
from operator import itemgetter, attrgetter
from mycapacitymodule import *

#--------------------------------------------------------------------------------------------------------------
#------------------------- ############# VM REPORT ############# ----------------------------------------------
#--------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
class vm_report(report):
    def __init__(self,params):
        super().__init__(params)
        #self.ReportType=super().ReportType_VM
        self.ReportType=super().get_reporttype()
        self.ReportTotalUsage=[]
        self.color=menu.OKGREEN
        # VM REPORT is used as the source (for the capacity-status.py, also for the destination) to create the complete report (LIST of LISTS, one list per VM) of VMs in that site; these are the report keys
        self.REPORT_KEYS= super().get_keys()
        self.REPORT_SORTINGKEYS= super().get_sorting_keys()




    # -----------------------------------------------------------------------
    # Transforms dict array into REPORT array 2d - VM level - one line = 1 list = 1 VM 
    # -----------------------------------------------------------------------
    def produce_vm_report(self,pars,dictarray_object):


        SUFFISSO=pars.paramsdict["SOURCE_SITE_SUFFIX"]
     
        TEMP_RES=[]
        minidict={}
        NEW_SERVICE_ARRAY=[]
        CopyOfServiceArray= pars.paramsdict["SERVICE"]
        #print("DEBUG 1\n\n")
        #print("SERVICE=",pars.paramsdict["SERVICE"])
        #print("INITIALSERVICEVALUE=",pars.paramsdict["INITIALSERVICEVALUE"])

        #print("-----------------------------------")
        # PARSE PARAMETER=SERVICE AND RETRIEVE RELEVANT OS PROJECT NAMES
        for PROGETTO in dictarray_object.SERVERDICT:

            str_PROGETTO=str(PROGETTO)
            Condition1=str_PROGETTO in pars.paramsdict["SERVICE"] 
            Condition2 ="ALL" in pars.paramsdict["SERVICE"]
            Condition3 = pars.paramsdict["ANYSERVICE"]==True
            for ServiceName in CopyOfServiceArray:
                Condition4=True
                if len(ServiceName)>0:
                    if ServiceName[len(ServiceName)-1]==pars.APPLICATIONCONFIG_DICTIONARY["DefaultValues"]["ServiceNameWildCard"]:
                        Condition4=str_PROGETTO.find(ServiceName[0:len(ServiceName)-1])>-1 
                    else:
                        Condition4=str_PROGETTO==ServiceName 
                else:
                    Condition4=False

            if Condition1 or Condition2 or Condition3 or Condition4:
                NEW_SERVICE_ARRAY.append(str_PROGETTO)
        pars.paramsdict["SERVICE"]=NEW_SERVICE_ARRAY
        #print("produce_vm_report: parsing the following services: ",NEW_SERVICE_ARRAY)
        if len(NEW_SERVICE_ARRAY)==0:
            pars.cast_error("00202","")

        for item in [ x for x in dictarray_object.HYPERVISOR_LIST if x["State"] == "up"]:
            nodo = str(item["Hypervisor Hostname"])
            nomecorto = str(item["Hypervisor Hostname"].split('.')[0])
            site_name = str(item["Hypervisor Hostname"].split('.')[1])
            TEMP_RES=[]

            for PROGETTO in dictarray_object.SERVERDICT:
                str_PROGETTO=str(PROGETTO)
                
                if str_PROGETTO in NEW_SERVICE_ARRAY:

                    for VM in [ x for x in dictarray_object.SERVERDICT[PROGETTO] if x["Host"] == item["Hypervisor Hostname"]]:
                        TMP_RES=self.addemptyrecord()
                        AGGS = dictarray_object.cmpt_to_agglist(nodo)
                        AZNAME = str(AGGS[0])
                        HOSTAGGNAME =AGGS[1:]
                        suffissobreve=str(SUFFISSO[0:14])
                        VMNAME=str(VM["Name"])
                        # NEW UPDATE METHOD BY KEY
                        #self.VMPERPROJECT[PROGETTO].append(VMNAME)
                        self.UpdateLastRecordValueByKey( "TimeStamp",SUFFISSO[0:14])
                        self.UpdateLastRecordValueByKey( "Site",site_name)
                        self.UpdateLastRecordValueByKey( "Rack",nomecorto[21:23])
                        self.UpdateLastRecordValueByKey( "HypervisorHostname",nodo)
                        self.UpdateLastRecordValueByKey( "vCPUsAvailPerHV",item["vCPUs"])
                        self.UpdateLastRecordValueByKey( "vCPUsUsedPerHV",item["vCPUs Used"])
                        self.UpdateLastRecordValueByKey( "MemoryMBperHV",item["Memory MB"])
                        self.UpdateLastRecordValueByKey( "MemoryMBUsedperHV",item["Memory MB Used"])
                        self.UpdateLastRecordValueByKey( "AZ",AZNAME)
                        self.UpdateLastRecordValueByKey( "HostAggr",HOSTAGGNAME)
                        self.UpdateLastRecordValueByKey( "Project",str_PROGETTO)
                        self.UpdateLastRecordValueByKey( "VMname",str(VM["Name"]))

                        str_VMFLAVORID=str(VM["Flavor ID"])
                        self.UpdateLastRecordValueByKey( "Lineup",self.split_vnfname(VM["Name"],"Lineup"))
                        self.UpdateLastRecordValueByKey( "vnfname",self.split_vnfname(VM["Name"],"vnfname"))
                        self.UpdateLastRecordValueByKey( "vnfcname",self.split_vnfname(VM["Name"],"vnfcname"))

                        FOUNDFLAVOR=False
                        Warning=''
                        for y in dictarray_object.FLAVOR_LIST:
                            str_FLAVOR=str(y["ID"])
                            str_VMFLAVORNAME=str(y["Name"])
    #------------------------------------------------------------------------
                            # NEW PARSE FLAVORS IMPLEMENTATION
                            try:
                                minidict=dictarray_object.parse_flavor_properties(pars,y)
                            except:
                                print("ERROR 99a:")
                                traceback.print_exc(limit=None, file=None, chain=True)
                                print(y)

    
                            if str_FLAVOR == str_VMFLAVORID:
                                if len(str_VMFLAVORID)==0:
                                    self.UpdateLastRecordValueByKey( "Flavor","!! MISSING FLAVOR ID")
                                    ErrString="VMName: "+str(VM["Name"])+" ;  no Flavor ID associated to VM"
                                    pars.cast_error("00100",ErrString)
                                else:
                                    if len(str_VMFLAVORNAME)==0:
                                        self.UpdateLastRecordValueByKey( "Flavor","<no name> FlavorID="+str_VMFLAVORID)
                                        self.UpdateLastRecordValueByKey( "Warning","MissingFlavorNameOnly")
                                        Warning+="MissingFlavorNameOnly; "
                                    else:

                                        #print(json.dumps(minidict,indent=22))
                                        try:
                                            if "vnf_type" in minidict.keys():
                                                str_FLAVORHOSTAGGR=minidict["vnf_type"]
                                            else:
                                                str_FLAVORHOSTAGGR='None'
                                            if "hw:cpu_policy" in minidict.keys():
                                                hwpolicy=minidict["hw:cpu_policy"].upper()
                                                dictarray_object.site_based_flavor_properties_parser(pars, minidict, site_name,str(VM["Name"]),hwpolicy)
                                            else:
                                                dictarray_object.site_based_flavor_properties_parser(pars, minidict, site_name,str(VM["Name"]),"")

                                            if "hw:emulator_threads_policy" in minidict.keys():
                                                if str_PROGETTO.find("NIMS_Core")>-1 and minidict["hw:emulator_threads_policy"].upper()!="SHARE":
                                                        Warning= "VM {:} Flavor without HW:emulator_thread_policy set".format(str(VM["Name"]))
                                                        pars.cast_error("00105",Warning)
                                        except:
                                            print("ERROR 99: produce_vm_report")
                                            traceback.print_exc(limit=None, file=None, chain=True)
                                            #print(site_name)
                                            exit(-1)
                                        # END OF NEW PARSE FLAVORS IMPLEMENTATION
                #------------------------------------------------------------------------
                                        self.UpdateLastRecordValueByKey( "Flavor",str_VMFLAVORNAME)


                                self.UpdateLastRecordValueByKey( "vCPUsUSedPerVM",y["VCPUs"])
                                self.UpdateLastRecordValueByKey( "RAMusedMBperVM",y["RAM"])
                                self.UpdateLastRecordValueByKey( "CephPerVMGB",y["Disk"])
                                self.UpdateLastRecordValueByKey( "TargetHostAggr",str_FLAVORHOSTAGGR)
                                TEMP_RES=[]
                                FOUNDFLAVOR=True
                                break

                        if FOUNDFLAVOR==False:	
                            Warning += "ERROR: FlavorID not present"
                            self.UpdateLastRecordValueByKey( "Flavor",str(VM["Flavor Name"]+ " n/a"))
                            self.UpdateLastRecordValueByKey( "vCPUsUSedPerVM","n/a")
                            self.UpdateLastRecordValueByKey( "RAMusedMBperVM","n/a")
                            self.UpdateLastRecordValueByKey( "CephPerVMGB","n/a")
                            self.UpdateLastRecordValueByKey( "Warning","ERROR: FlavorID not present")
                            ErrString="VMName: "+str(VM["Name"])+" with FlavorName:>"+str(VM["Flavor Name"])+"< :FlavorID not present"
                            pars.cast_error("00103",ErrString)
                            TEMP_RES=[]





    # VM REPORT ONLY
    def calculate_report_total_usage(self, pars):
        totvcpuused = 0
        totramused = 0
        retval = []

        Item1 = "vCPUsUSedPerVM"
        Item2 = "RAMusedMBperVM"
        errorSign =False
        for x in self.Report:
            try:
                totvcpuused += x[self.get_keys().index(Item1)]
                totramused += x[self.get_keys().index(Item2)]
                errmsg=""
            except:
                totvcpuused=-1
                totramused=-1
                errmsg = "ERROR IN FLAVORS!!"
                errorSign =True

        self.ReportTotalUsage=[]
        if errorSign==False:
            retval.append("TOTAL # OF VCPUs USED :")
            retval.append(totvcpuused)
            retval.append("TOTAL RAM USED :")
            retval.append(self.mem_show_as_gb(totramused,True))
            retval.append("TOTAL # OF VMs :")
            retval.append(len(self.Report))
        else:
            retval.append(errmsg)
        self.ReportTotalUsage=retval
        return retval

#--------------------------------------------------------------------------------------------------------------
#------------------------- ############# MENU REPORT ############# --------------------------------------------
#--------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
class menu_report(report):

    def __init__(self,params):
        super().__init__(params)
        self.ReportType=super().get_reporttype()
        self.ReportTotalUsage=[]
        self.name="MENU"
        self.color=menu.OKCYAN

        self.REPORT_KEYS= super().get_keys()
        self.REPORT_SORTINGKEYS= super().get_sorting_keys()
        #self.MENU_REPORT_KEYS= self.REPORTFIELDGROUP["MENU_Report_Keys"]
        #self.MENU_REPORT_SORTINGKEYS = self.REPORTFIELDGROUP["MENU_Report_Sorting_Keys"]
        screenrows, screencolumns = os.popen('stty size', 'r').read().split()
        self.ScreenWitdh=int(screencolumns)
        self.SVCNOTTOSHOW =  params.APPLICATIONCONFIG_DICTIONARY["DefaultValues"]["ServicesToSkip"]
        #("service", "admin", "tempest", "c_rally", "DeleteMe", "Kashif")

    

    def CreatePerSiteProjectReport(self, params):
            
            cleanlist = []
            cleanlist=params.Get_Clean_Openstack_FilesList()
            
            index = 0
            newlist = []

            ProgNumIndex =self.get_keys().index("Item")
            SiteIndex =self.get_keys().index("Site")
            SiteTypeIndex =self.get_keys().index("Site")
            DateIndex = self.get_keys().index("Date")
            SuffixIndex =self.get_keys().index("Suffix")
            ProjectsIndex =self.get_keys().index("Projects")
            self.ClearData()

            for FileName in cleanlist:
                if len(FileName) == 20:
                # NOTE: STG810 does not show stg810 in the suffix as the cc-jumphost hostname is configured wrongly.
                    sitename = FileName[14:]
                    date = FileName[:14]
                else:
                    sitename = "stg810"
                    date = FileName[:14]
                

                ShortDate = self.tstoshortdate(FileName)
                self.addemptyrecord()
                self.UpdateLastRecordValueByKey("Item",index)
                self.UpdateLastRecordValueByKey("Site",sitename)
                self.UpdateLastRecordValueByKey("SiteType",params.SiteType(sitename))

                self.UpdateLastRecordValueByKey("Date",ShortDate)
                self.UpdateLastRecordValueByKey("Suffix",FileName)  
                ListOfProjPerSuffix=[]
                for Item in self.load_svcs_by_prefix(params,FileName):
                    ListOfProjPerSuffix.append("{:} ({:})".format(Item[0],Item[1]))
                self.UpdateLastRecordValueByKey("Projects",ListOfProjPerSuffix) 
            index = 0 
            self.Report.sort(key=lambda x: (x[DateIndex],x[SiteTypeIndex],x[SiteIndex]), reverse=True)
            

            #self.sort_report(self.get_sorting_keys())
            for Rec in self.Report:
                Rec[ProgNumIndex]=index
                index+=1



    #--------------------------------------------------------------------
    # GET LIST OF FILES TO USE IN MENU
    #--------------------------------------------------------------------
    def ShowProjectsPerSiteandGetInput(self, params, prompt):

        self.CreatePerSiteProjectReport(params)
        ReportKeys =self.get_keys()
        ProgNumIndex =ReportKeys.index("Item")
        SiteIndex =ReportKeys.index("Site")
        SiteTypeIndex =ReportKeys.index("SiteType")

        DateIndex = ReportKeys.index("Date")
        SuffixIndex =ReportKeys.index("Suffix")
        ProjectsIndex =ReportKeys.index("Projects")
        EachProjectLength = ListItemLen =self.FIELDLISTS["Projects"]
    # PREPARE THE LIST OF ITEMS
        for Record in self.Report :
            counter = Record[ProgNumIndex]
            sitename = Record[SiteIndex]
            shortdate = Record[DateIndex]
            filesuffix = Record[SuffixIndex]
            ListOfProjectsPerSite =  Record[ProjectsIndex]
            PerSiteHeader = "  {:2d} - {:6s} - {:10s} - ".format(counter, sitename, shortdate)
            line = ""
            linelen = 0
            self.PerSiteWidth = len(PerSiteHeader)
            for ProjectInThisSite in ListOfProjectsPerSite:
                ProjectName="{0:"+str(EachProjectLength)+"}"
                item = ProjectName.format(ProjectInThisSite[0:EachProjectLength])
                linelen += len(item)
                line += item
                remaining_space=self.ScreenWitdh - linelen
                
                prjspersite="\n{0:"+str(self.PerSiteWidth+1)+"s}"
                if linelen > self.ScreenWitdh-self.PerSiteWidth-EachProjectLength:
                    line += prjspersite.format(" ")
                    linelen = 0
            string2 = "{:s}".format(line)

            stringa3 = "{:s} {:s}".format(PerSiteHeader, string2)

            TMPREC = []
            TMPREC.append(stringa3)

        return self.print_menu(params,prompt)

 # ------- GET LIST OF PROJECT EXISTING IN SRC SITE ---------------
    def GetListOfProjectsInSite(self, params, parname):

        os.system("clear")
        stringalinea1 = '{0:_^'+str(self.ScreenWitdh)+'}'
        params.print(stringalinea1.format( " SERVICES AVAILABLE IN SITE "+params.paramsdict[parname]))
        results = []
        for Item in self.load_svcs_by_prefix(params,params.paramsdict[parname]):
            TMPREC=[]
            TMPREC.append(0)
            TMPREC.append(Item[0])
            TMPREC.append(Item[1])
            results.append(TMPREC)

        sortedres = sorted(results, key=lambda x: x[0], reverse=False)

        index = 0        
        for Item in sortedres:
            Item[0]=index
            params.print("\n\t{:} --- {:30s} --- ({:4d})".format(index, Item[1],Item[2]))
            index+=1
        #print(sortedres)
        src=""
        ListOfEntries=[]
        while len(src)==0 or len(ListOfEntries)==0: 
            src = str(input("\n\tEnter source SERVICES separated by <,> or ALL or string to match Service Name:"))
            TempListOfEntries= src.split(",")
            ListOfEntries=[]
            for i in TempListOfEntries:
                if i.strip() != '':
                    ListOfEntries.append(i)
            print(ListOfEntries)

        res = []
        ServiceNames=[i[1] for i in sortedres]
        print(ServiceNames)
        for EntryItem in ListOfEntries:
            if EntryItem in ["all", "ALL"]:
                res = [i for i in ServiceNames]
                params.paramsdict["ANYSERVICE"]=True
            elif EntryItem.isdigit():
                Value=int(EntryItem)
                res.append(sortedres[Value][1])                
            else:
                for ServiceName in ServiceNames:
                    if EntryItem[len(EntryItem)-1]==params.APPLICATIONCONFIG_DICTIONARY["DefaultValues"]["ServiceNameWildCard"]:
                        CriteriaToMeet=ServiceName.find(EntryItem[0:len(EntryItem)-1])>-1
                    else:
                        CriteriaToMeet=ServiceName==EntryItem
                    if CriteriaToMeet:
                        res.append(ServiceName)

            print(res)
            if len(res)==0:
                params.cast_error("00202","")
        return res
    # ----------------------------------------------------------
    # - ----- PARSE ARGS AND DEFINE LEVEL OF USER INTERACTIVITY -------
    # this function defines which user inputs to request in user interactive mode based on command line arguments provided
    #

    def split_cli_args(self,input,output):
        # ----------------------------------------------------------
        # PARSE ARGUMENTS PASSED TO COMMAND
        # ----------------------------------------------------------

        Counter=0
        l=0
        try:
            # First all command line arguments are parsed into a  dict (based on their type)
            for Word in input:
                if Counter>0:
                    if Word.find("=")==-1:
                        key=output.paramslist[l]
                        value=Word
                        l+=1
                    else:
                        key=Word.split("=")[0]
                        val=Word.split("=")[1]
                        if type(output.paramsdict[key]) is bool:
                            output.paramsdict[key]=val.upper()=='TRUE'
                            #print(MyPARAMSDICT.paramsdict[key])
                        elif type(output.paramsdict[key]) is list:
                            mylist=val.split(",")
                            for y in mylist:
                                output.paramsdict[key].append(y)
                        else:
                            output.paramsdict[key]=val
                Counter+=1
        except: 
            print("ERROR - split_cli_args - The following command line parameter is not correct : {:s}".format(Word))
            exit(-1)
        l+=1
        print(json.dumps(output.paramsdict,indent=22))



    def parse_args(self,input,output, src_da, dst_da):
        # ----------------------------------------------
        self.split_cli_args(input,output)
        #SOURCE SITE(S)
        # If SOURCE_SITE_SUFFIX CLI argument is not present, the User Interface fetching the input is shown and user input is returned to the parameters dict
        parname = "SOURCE_SITE_SUFFIX"
        Parname_Of_Sitelist="SRCSITESLIST"
        MyPrompt="Source site"
        output.paramsdict[Parname_Of_Sitelist]=[]

        if len(output.paramsdict[parname])==0:
            MySiteSuffixValue=self.ShowProjectsPerSiteandGetInput( output,MyPrompt)
            output.paramsdict[parname]=MySiteSuffixValue
            output.paramsdict[Parname_Of_Sitelist].append(MySiteSuffixValue)
        else:
            myvaluetosearchfiles=output.paramsdict[parname]
            MyList=output.GetListOfFilesFromSuffixMatch(myvaluetosearchfiles)
            for SiteFileSuffix in MyList:
                output.paramsdict[Parname_Of_Sitelist].append(SiteFileSuffix)
            output.paramsdict[parname]=output.paramsdict[Parname_Of_Sitelist][0]            

        # in order for the services in each site:suffix to be shown, the array of dicts with all the json must be loaded first
        src_da.load_jsons_into_dictarrays(output,parname)


        if output.paramsdict["JUSTSOURCE"]==False:
            # DESTINATION SITES
            parname = "DESTINATION_SITE_SUFFIX"
            Parname_Of_Sitelist="DESTSITESLIST"
            MyPrompt="Destination site"

            output.paramsdict[Parname_Of_Sitelist]=[]        
            if len(output.paramsdict[parname])==0:
                MySiteSuffixValue=self.ShowProjectsPerSiteandGetInput(output, MyPrompt)
                output.paramsdict[parname]=MySiteSuffixValue
                output.paramsdict[Parname_Of_Sitelist].append(MySiteSuffixValue)
            else:
                myvaluetosearchfiles=output.paramsdict[parname]
                for SiteFileSuffix in output.GetListOfFilesFromSuffixMatch(myvaluetosearchfiles):
                    output.paramsdict[Parname_Of_Sitelist].append(SiteFileSuffix)
                output.paramsdict[parname]=output.paramsdict[Parname_Of_Sitelist][0]
                # in order for the services in each site:suffix to be shown, the array of dicts with all the json must be loaded first   
            dst_da.load_jsons_into_dictarrays(output,parname)

        # so that the name(s) of the Services can be either assigned or user selected
        if len(output.paramsdict["SERVICE"])==0:
            parname = "SOURCE_SITE_SUFFIX"
            src_da.load_jsons_into_dictarrays(output,parname)
            if output.paramsdict["ANYSERVICE"]==False:
                output.paramsdict["SERVICE"]=self.GetListOfProjectsInSite(output,parname )
        
        output.paramsdict["INITIALSERVICEVALUE"]=output.paramsdict["SERVICE"]

        print("------------------ LIST OF PARAMETER ARGUMENTS ---------------------------")	
        print(json.dumps(output.paramsdict,indent=30))

        return 1
        # MERGE WITH 
   

    def load_svcs_by_prefix(self, params, SUFFISSO):
    # --------------------------------------------------------------
    # Load site data files and finds the list of projects (and total vCPUs for each) in each site:suffix
            COUNT=0
            RESULT=[]
            TMPRES=[]
            try:
                    ITEM="server_dict"
                    FILENAME = params.PATHFOROPENSTACKFILES + "/"+ "openstack_" + ITEM + "_" + SUFFISSO +  ".json"
                    with open(FILENAME, 'r') as file1:
                                LOCALSERVERDICT= json.load(file1)
                    ITEM="flavor_list"
                    FILENAME = params.PATHFOROPENSTACKFILES + "/"+ "openstack_" + ITEM + "_" + SUFFISSO +  ".json"
                    with open(FILENAME, 'r') as file1:
                            #print("DEBUG load_svcs_by_prefix .. loading {:s} ".format(FILENAME))
                            FLAVOR_LIST= json.load(file1)
                    for PROGETTO in LOCALSERVERDICT:
                                    found=False
                                    for z in self.SVCNOTTOSHOW:
                                            if str(PROGETTO).find(z)>-1:
                                                    found=True
                                                    break
                                    if found==False:
                                            str_PROGETTO=str(PROGETTO)
                                            VCPU_PER_PRJ=0
                                            for VM in LOCALSERVERDICT[PROGETTO]:
                                                            FOUNDFLAVOR=False
                                                            str_VMFLAVORID=VM["Flavor ID"]
                                                            for y in FLAVOR_LIST:
                                                                    str_FLAVOR=str(y["ID"])
                                                                    if str_FLAVOR == str_VMFLAVORID:
                                                                            VCPU_PER_PRJ+=y["VCPUs"]

                                            TMPRES=[]
                                            TMPRES.append(str(PROGETTO))
                                            TMPRES.append(VCPU_PER_PRJ)
                                            RESULT.append(TMPRES)

                                            #RESULT.append(str(PROGETTO)+"("+str(VCPU_PER_PRJ)+")")

            except (IOError, EOFError) as e:
                    print("load_svcs_by_prefix ERROR 08 START")
                    print(" opening JSON File {:s} -> does not exist".format(FILENAME))
                    exit(-1)
            return sorted(RESULT)



    # PRINTS THE USER INTERACTIVE MENU PREPARED IN get_fileslist()
    def print_menu(self, params, prompt):
        FormatString_AllSpaces = '{0: ^'+str(self.ScreenWitdh)+'}'
        FormatString_AllDots = '{0:.^'+str(self.ScreenWitdh)+'}'
        rowindex = 0
        goon = True
        pagestarts = []
        pageends=[]
        pageitems = []
        DateIndex = self.get_keys().index("Date")
        PreviousDate=self.Report[0][DateIndex]
        pagestarts.append(0)
        # SETS STARTING AND ENDING RECORD IN REPORT BY TIMESTAMP DATE - one page per date
        for RecordNum in range(len(self.Report )):
            CurrentDate=self.Report[RecordNum][DateIndex]
            if CurrentDate!=PreviousDate:
                pageends.append(RecordNum)
                pagestarts.append(RecordNum)
                PreviousDate=CurrentDate
        pageends.append(len(self.Report))

        currentpage = 0
        index = 0
        while goon:
            index= index  % len(pagestarts)
            os.system("clear")
            print(menu.FAIL + FormatString_AllSpaces.format(''))
            print(menu.FAIL + FormatString_AllSpaces.format(' CAPACITY FORECAST '))
            print(menu.FAIL + FormatString_AllSpaces.format(''))
            print(menu.Yellow)
            print(FormatString_AllSpaces.format(' Page '+str(index)+' '))

            self.print_report_line(params,self.get_keys(),False)
            for rowindex in range(pagestarts[index], pageends[index]):
                print(FormatString_AllDots.format(''))
                self.print_report_line(params,self.Report[rowindex], True)

            print(FormatString_AllSpaces.format(''))
            RetvalIndex= self.get_keys().index("Suffix")
            PAGEBACK = ['-', '_', 'b', 'B']
            try:
                print(
                    "\nTo change page:\n\t\t\t-Previous Page : -,_,b,B; \n\t\t\t-Next page: any other  letter or <CR>; \n\t\t\t-Exit: type END :")
                userinput = input(
                    "\n\t\t\t--------- Enter {:s} suffix: ".format(prompt))
                ISNUMBER = userinput.isdigit()               
                ISNULL = len(userinput) == 0
                ISQUIT = userinput.upper().find("END")>-1
                if ISNULL:
                    goon=True

                if ISQUIT:
                    goon = False
                    print("\n\t\t\t\t ......... EXITING .........\n\n")
                    exit(-1)

                if ISNUMBER:
                    src = int(userinput)
                    if src >= pagestarts[index] and src <= pageends[index]:
                        print(
                            "\t\t\t\t ......... INPUT ACCEPTED {:d}.........\n\n".format(src))
                        retval = self.Report[src][RetvalIndex]
                        print(
                            "\t\t\t\t\t ---------- USER INPUT=>{:s}<--".format(retval))
                        goon = False
                        return retval
                    else:
                        print(
                            "\n\t\t\t\t ......... Please enter a number between {:d} and {:d} \n\n".format(pagestarts[index], pageends[index]-1))
                        time.sleep(1.0)
                else:
                    if userinput in PAGEBACK:
                        value = -1
                        DisplayString="PREVIOUS"
                    else:
                        value = 1
                        DisplayString="NEXT"

                    print("\t\t\t\t\t\t.....{:s} PAGE...".format(DisplayString))
                    index += value
                    goon = True


            except (ValueError) as e:
                goon = False
                print("\t\t\t\t ......... EXITING .........\n\n")
                exit(-1)
            except (NameError) as e:
                print("\t\t\t\t\t\t.....NEXT PAGE...")
                index += 1
                index = index % len(pagestarts)
                goon = True



#--------------------------------------------------------------------------------------------------------------
#------------------------- ############# HW REPORT ############# ----------------------------------------------
#--------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------    
class hw_report(report):
    def __init__(self,params):
        super().__init__(params)

        self.ReportType=super().get_reporttype()
        self.ReportTotalUsage=[]
        self.color=menu.Yellow

        self.REPORT_KEYS= super().get_keys()
        self.REPORT_SORTINGKEYS= super().get_sorting_keys()
        #self.HW_REPORT_KEYS= self.REPORTFIELDGROUP["HW_Report_Keys"]
        #self.HW_REPORT_SORTINGKEYS = self.REPORTFIELDGROUP["HW_Report_Sorting_Keys"]


    # ---------------------------------------------------------------------------------------------------
    # Produces a report (list of lists); one row per hardware compute based on the global ARRAY of (list,dict) passed as parameter. 
    # ---------------------------------------------------------------------------------------------------
    def produce_hw_report(self,SUFFISSO, pars, dictarray_object ):
            self.Report=[]
            TEMP_RES=[]
            for item in [ x for x in dictarray_object.HYPERVISOR_LIST if x["State"] == "up"]:
                nodo = str(item["Hypervisor Hostname"])
                nomecorto = str(item["Hypervisor Hostname"].split('.')[0])
                site_name = str(item["Hypervisor Hostname"].split('.')[1])
                TEMP_RES=[]
                TEMP_RES=self.addemptyrecord()
                timestamp = SUFFISSO[0:14]
                rack = nomecorto[21:23]

                self.UpdateLastRecordValueByKey( "TimeStamp",timestamp)
                self.UpdateLastRecordValueByKey( "Site",site_name)
                self.UpdateLastRecordValueByKey( "Rack",rack)
                self.UpdateLastRecordValueByKey( "HypervisorHostname",nodo)
                self.UpdateLastRecordValueByKey( "vCPUsAvailPerHV",item["vCPUs"])
                self.UpdateLastRecordValueByKey( "MemoryMBperHV",item["Memory MB"])             
                  
                AGGS =dictarray_object.cmpt_to_agglist(nodo)
                self.UpdateLastRecordValueByKey( "AZ",AGGS[0])               
                self.UpdateLastRecordValueByKey( "HostAggr",AGGS[1:]) 

                # WIPE_DESTSITE Parameter implementation
                if pars.paramsdict["WIPE_DESTSITE"]==True and SUFFISSO==pars.paramsdict["DESTINATION_SITE_SUFFIX"]:
                    self.UpdateLastRecordValueByKey( "vCPUsUsedPerHV",0)
                    self.UpdateLastRecordValueByKey( "MemoryMBUsedperHV",0)
                    self.UpdateLastRecordValueByKey( "PctUsageOfCmpt",0)

                    EmptyVMList=[]
                    self.UpdateLastRecordValueByKey( "ExistingVMs",EmptyVMList) 
                else:
                    self.UpdateLastRecordValueByKey( "vCPUsUsedPerHV",item["vCPUs Used"])
                    self.UpdateLastRecordValueByKey( "MemoryMBUsedperHV",item["Memory MB Used"])  
                    #self.UpdateLastRecordValueByKey( "ExistingVMs",WHATTODO??)               
                    self.UpdateLastRecordValueByKey( "ExistingVMs",dictarray_object.get_vms_by_computenode(nodo)) 
                    self.UpdateLastRecordValueByKey( "PctUsageOfCmpt",self.calc_max_percentage(item["vCPUs Used"],item["vCPUs"],item["Memory MB Used"],item["Memory MB"]))
                EmptyVMList=[]
                self.UpdateLastRecordValueByKey( "NewVMs",EmptyVMList) 

    def Calculate_UsageSymmetry_ofLoadPerCompute(self): 
        LoadValuesPerCompute=self.get_column_by_key("vCPUsUsedPerHV")
        CapacityValuesPerCompute=self.get_column_by_key("vCPUsAvailPerHV")
        total=0
        NOfEntries = len (LoadValuesPerCompute)
        totalLoad = 0
        totalCapacity=0
        average=0.0
        deviationLoad=0
        deviationCapacity=0
        for item in range(NOfEntries):
            totalLoad+=LoadValuesPerCompute[item]
            totalCapacity+=CapacityValuesPerCompute[item]
        averageLoad=float(totalLoad/NOfEntries)
        averageCapacity=float(totalCapacity/NOfEntries)
        for item in range(NOfEntries):
            deviationLoad+=(LoadValuesPerCompute[item]-averageLoad)**2
            deviationCapacity+=(CapacityValuesPerCompute[item]-averageCapacity)**2
        deviationLoad= math.sqrt(deviationLoad/NOfEntries)
        deviationCapacity=math.sqrt(deviationCapacity/NOfEntries)
        
        return ("Avg. vCPU used per cmp:",averageLoad,
                "Avg. vCPU avail per cmp:",averageCapacity,
                "Avg. Deviation of vCPU used per cmp:",deviationLoad,
                "Avg. Deviation of vCPU avail per cmp:",deviationCapacity)
 # -----------------------------------------------------------------------------------------------------
    #
    #----------------------        AUTOOPTIMIZE RACKS TO AZ ALLOCATION      -------------------------------
    #
    #------------------------------------------------------------------------------------------------------
    def Hardware_Layout_Optimization_ByRackAndAZ(self, pars, MyRackReport,  metric_formula): #sort_formula,
        #self = class = Report. Reporttype=HW

    # CALCULATE THE DISTANCE FOR A VECTOR OF 5 RACKCOMBOS -- NEEDS TO BE PARAMETRIZABLE
        def Calculate_UsageSymmetry_ofLoadPerAZ(loadvector,CurrentMetricFormula): 
            
            total=0
            NOfEntries = len (loadvector)
            maximum=0
            minimum=math.inf
            metric=0
            total = 0
            average=0.0
            for item in loadvector:
                total+=item
                if item>maximum:
                    maximum=item
                if item<maximum:
                    maximum=item
            average=float(total/NOfEntries)

            for item in loadvector:
                currentvalue=item
                #print(CurrentMetricFormula, item)
                metric += eval(CurrentMetricFormula)
            return metric

    #------------------------------------------------------------------------------------------------------------------------------------------------------------
        #if no optimization, HW_REPORT returned as is
        if pars.get_azoptimization_mode()==pars.NO_OPTIMIZATION:
            #print(" ### DEBUG - no AZ realign parameter passed to select input file for Rack to AZ realignment")
            return self
        if len(self.Report)==0:
            print("ERROR in optimize_HW_OPTIMIZATION_MODEment_in_HWReport : length of HW report = 0 entries ")
            exit(-1)
        #print(self[0])

        SUFFISSO = pars.paramsdict["DESTINATION_SITE_SUFFIX"]
        stringalinea1 = '{0:_^'+str(pars.ScreenWitdh)+'}'

        #Initialize and produce RACK REPORT . Initialize report for optimixzation results
        print (stringalinea1.format(menu.Yellow+SUFFISSO+"  initial layout "+str(SUFFISSO)))
        MyRackReport.Report=[]
        MyRackReport.Rack_Opt_Memory={ "rackslayout":[],"azcpus":[],"sigma2":math.inf, "metric_formula":''}
        MyRackReport.Rack_Opt_Memory["metric_formula"]=metric_formula
        MyRackReport.produce_rack_report(pars,self)
        MyRackReport.sort_report(MyRackReport.get_sorting_keys())
        MyRackReport.print_report(pars)
        
 
        # Calculate metric (current) for current layout
        LoadValuesPerRack=MyRackReport.get_column_by_key(MyRackReport.RackReportKeyForOptimizationMetric)

        CurrentMetricValue = Calculate_UsageSymmetry_ofLoadPerAZ(LoadValuesPerRack,metric_formula)
        MyRackReport.Rack_Opt_Memory["sigma2"]=CurrentMetricValue
        print("\tCurrent Metric Value: {:.2f}".format(CurrentMetricValue))
        print (stringalinea1.format(menu.Yellow))
        racks=MyRackReport.get_column_by_key("Rack")

        UsageLoadForCurrentRackToAZPerm=[]
        returnarray=[]

        NumberOfAZs = len(racks)/MyRackReport.RacksPerAZ
        if NumberOfAZs-math.floor(NumberOfAZs)>0:
            print(" ERROR -- optimize_HW_OPTIMIZATION_MODEment_in_HWReport : Number of racks is {:d} vs RacksPerAZ is {:d}".format(len(racks,MyRackReport.RacksPerAZ)))
            exit(-1)
        #UsageLoadForCurrentRackToAZPerm = list of per AZ total of VCPUs: passed as param to Calculate_UsageSymmetry_ofLoadPerAZ func to calculate sigma2
        #for x in range(len(racks)/MyRackReport.RacksPerAZ):


        conta=0
        matches=0
        total=1
        sumofrackvalues=0

        # Calculate total # of items of iterator to go through
        for i in range(1,len(racks) + 1):
            total = total*i
        
        #Init line
        print (stringalinea1.format("\n"+menu.FAIL+ pars.parse_suffisso(SUFFISSO)+menu.Yellow+" -->  brute force scan on rack pairs to optimize AZ resource distribution, based on metric : "+metric_formula+menu.Yellow+" "))

        sys.stdout.write('\t|')
        sys.stdout.flush()
        colors=[menu.WARNING, menu.FAIL]

        # SCan through all permutations of racks
        for TEMP in list(itertools.permutations(racks)) :
            changecol=False
            c=''
            if conta % (total/20) ==0:
                c+=" {:.0%} |".format(conta/total)
                sys.stdout.write(c)
                sys.stdout.flush()


            UsageLoadForCurrentRackToAZPerm=[0]*math.floor(NumberOfAZs)
            # for every permutation, calculate UsageLoadForCurrentRackToAZPerm 
            for index in range(0,len(TEMP),MyRackReport.RacksPerAZ):
                UsageLoadForCurrentRackToAZPermindex=int(index/MyRackReport.RacksPerAZ)
                TotalLoadPerAZ=0
                for Counter in range(MyRackReport.RacksPerAZ):
                    rackvalue=TEMP[index+Counter]
                    valueindex=racks.index(rackvalue)
                    TotalLoadPerAZ+=LoadValuesPerRack[valueindex]
                UsageLoadForCurrentRackToAZPerm[UsageLoadForCurrentRackToAZPermindex]= TotalLoadPerAZ
            #print("index={} UsageLoadForCurrentRackToAZPermindex={} TEMP={} UsageLoadForCurrentRackToAZPerm={} ".format(index,UsageLoadForCurrentRackToAZPermindex,TEMP,UsageLoadForCurrentRackToAZPerm))
            SIGMA2=Calculate_UsageSymmetry_ofLoadPerAZ(UsageLoadForCurrentRackToAZPerm, metric_formula)
            #print("TEMP={}  SIGMA2={}".format(TEMP,SIGMA2))
            #condition1 = SIGMA2<Rack_Opt_Memory["sigma2"]
            if SIGMA2<=MyRackReport.Rack_Opt_Memory["sigma2"]:
                    #changecol= condition1 != condition1
                    #print("UsageLoadForCurrentRackToAZPerm={}   NEW LOWER SIGMA:{}".format(UsageLoadForCurrentRackToAZPerm,Rack_Opt_Memory["sigma2"]))
                matches+=1
                MyRackReport.Rack_Opt_Memory["sigma2"]=SIGMA2
                MyRackReport.Rack_Opt_Memory["rackslayout"]=[]
                MyRackReport.Rack_Opt_Memory["azcpus"]=[]
                for ww in TEMP:
                    MyRackReport.Rack_Opt_Memory["rackslayout"].append(ww)
                for ww in UsageLoadForCurrentRackToAZPerm:
                    MyRackReport.Rack_Opt_Memory["azcpus"].append(ww)

            conta+=1

        try:

            print(stringalinea1.format("\n"+menu.Yellow+ " OPTIMIZATION RESULTS "+menu.Yellow))
            print("\nOPTIMIZATION OF RACKS DISTRIBUTION TO AZ: FINAL RACK LAYOUT:\n")
            print("\tTOTAL MATCHING LAYOUTS ="+str(matches))
            print("\tOPTIMIZED RACK LAYOUT:")
            print(MyRackReport.Rack_Opt_Memory["rackslayout"])
            print("\tDISTRIBUTION OF VCPUS:")
            print(MyRackReport.Rack_Opt_Memory["azcpus"])
            MyRackReport.OUTPUTDICT[pars.parse_suffisso(SUFFISSO)]=MyRackReport.Rack_Opt_Memory
            MyRackReport.writeoptimizedrackstofile(pars)
            print("\n\t\tREALIGNING RACKS TO AZ IN ACCORDANCE TO RACK-TO-AZ NEW MAP\n \t\tRACK TO AZ MAP={} METRIC={} SIGMA={}".format(MyRackReport.Rack_Opt_Memory["rackslayout"],metric_formula,MyRackReport.Rack_Opt_Memory["sigma2"]))
            print (stringalinea1.format(menu.Yellow))

            returnarray.append(MyRackReport.Rack_Opt_Memory["rackslayout"])
            retval=self.after_opt_realign_racks_to_optimizedAZdistro_inHWReport(MyRackReport)
        except :
            print(sys.exc_info())
            print("ERROR in optimize_HW_OPTIMIZATION_MODEment_in_HWReport : Exiting")
            exit(-1)
        return returnarray
    # UPDATE HW_REPORT WITH NEW VALUES OF RACKS , BASED on NEW AZ TO RACK MAPPING 
    
    def after_opt_realign_racks_to_optimizedAZdistro_inHWReport(self,RackReport):
        racktoazmap=RackReport.Rack_Opt_Memory["rackslayout"]
        #print(" DEBUG after_opt_realign_racks_to_optimizedAZdistro_inHWReport: new Rack to AZ map is: ")
        #print(racktoazmap)
        for item in self.Report:
            rack_key_inhwreport=self.get_keys().index("Rack")
            azkey_inhwreport=self.get_keys().index("AZ")
            AZPreviousValueinHWreport=item[azkey_inhwreport]
            RackValueinHwReport=item[rack_key_inhwreport]
            #try:
            indexrackinmap=racktoazmap.index(RackValueinHwReport)
            NewAZValueForThisRack=int(indexrackinmap/RackReport.RacksPerAZ)+1
            NewAZNameForThisRack="DT_NIMS_AZ"+str(NewAZValueForThisRack)
            #print("DEBUG after_opt_realign_racks_to_optimizedAZdistro_inHWReport - change {:} from {:} to {:}".format(RackValueinHwReport,AZPreviousValueinHWreport,NewAZNameForThisRack))
            item[azkey_inhwreport]=NewAZNameForThisRack
        return True
            #except:
            #    print("ERROR in class: rack_report- def after_opt_realign_racks_to_optimizedAZdistro_inHWReport")
            #    exit(-1)


#--------------------------------------------------------------------------------------------------------------
#------------------------- ############# RACK REPORT ############# --------------------------------------------
#--------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
class rack_report(report):
    # REPORT USED TO STORE COMPUTED DATA DURING AZ OPTIMIZATION
    

    RacksPerAZ = 2

    def __init__(self,params):
        super().__init__(params)
        #self.ReportType=super().ReportType_RACK
        self.ReportType=super().get_reporttype()

        self.Report=[]
        self.ReportTotalUsage=[]
        self.color=menu.OKBLUE

        self.REPORT_KEYS= super().get_keys()
        self.REPORT_SORTINGKEYS= super().get_sorting_keys()
        #self.RACK_REPORT_KEYS= self.REPORTFIELDGROUP["RACK_Report_keys"]
        #self.RACK_REPORT_SORTINGKEYS = self.REPORTFIELDGROUP["RACK_Report_Sorting_Keys"]

        self.RacksPerAZ=self.RACKOPTPARAMETERS["RacksPerAZ"]
        self.Rack_Opt_Memory={}
        self.OUTPUTDICT={}
        Rack_Opt_Memory={ "rackslayout":[],"azcpus":[],"sigma2":math.inf, "metric_formula":''}
        screenrows, screencolumns = os.popen('stty size', 'r').read().split()
        self.ScreenWitdh=int(screencolumns)
        self.RackReportKeyForOptimizationMetric=self.RACKOPTPARAMETERS["KeyForCalculatingRackOptimization"]

    def produce_rack_report(self, pars, hwreportbox):
        stringalinea1 = '{0:_^'+str(pars.ScreenWitdh)+'}'

    # PARSE VALUES OF RACK, AZ and VCPUS from HW report
        MyHwKeys=hwreportbox.get_keys()
        MyRackKeys=self.get_keys()
        vcpuavail_hwindex=MyHwKeys.index("vCPUsAvailPerHV")
        cmpt_hwindex=MyHwKeys.index("HypervisorHostname")
        ramavail_hwindex=MyHwKeys.index("MemoryMBperHV")
        vcpuused_hwindex=MyHwKeys.index("vCPUsUsedPerHV")
        ramused_hwindex=MyHwKeys.index("MemoryMBUsedperHV")
        rack_hwindex=MyHwKeys.index("Rack")
        az_hwindex=MyHwKeys.index("AZ")
        site_hwindex= MyHwKeys.index("Site")

        nofcmpts_Rackindex=MyRackKeys.index("NOfComputes")
        vcpuavail_Rackindex=MyRackKeys.index("VCPUsAvailPerRack")
        ramavail_Rackindex=MyRackKeys.index("RAMperRack")
        vcpuused_Rackindex=MyRackKeys.index("VCPUsUsedPerRack")
        ramused_Rackindex=MyRackKeys.index("RAMUsedperRack")
        rack_Rackindex=MyRackKeys.index("Rack")
        az_Rackindex=MyRackKeys.index("AZ")
        PctUsage_Rackindex=MyRackKeys.index("PctUsageOfRk")

        self.Report=[]
        conta=0
        for myRecord in hwreportbox.Report:
            RackValueFromHWReport = myRecord[rack_hwindex]
            SiteValueFromHWReport = myRecord[site_hwindex]
            RackFound=False
            MyRackRecord=self.FindRecordByKeyValue("Rack",RackValueFromHWReport)
            
            conta+=1

            if len(MyRackRecord)==0 :
                self.addemptyrecord()
                self.UpdateLastRecordValueByKey("Site",SiteValueFromHWReport)
                self.UpdateLastRecordValueByKey("Rack",RackValueFromHWReport)
                self.UpdateLastRecordValueByKey("AZ",myRecord[az_hwindex])
                self.UpdateLastRecordValueByKey("VCPUsAvailPerRack",myRecord[vcpuavail_hwindex])                
                self.UpdateLastRecordValueByKey("RAMperRack",myRecord[ramavail_hwindex])                
                self.UpdateLastRecordValueByKey("VCPUsUsedPerRack",myRecord[vcpuused_hwindex])                
                self.UpdateLastRecordValueByKey("RAMUsedperRack",myRecord[ramused_hwindex])
                self.UpdateLastRecordValueByKey("NOfComputes",1)
                self.UpdateLastRecordValueByKey("PctUsageOfRk",0)


            else:
                MyRackRecord[vcpuavail_Rackindex]+=myRecord[vcpuavail_hwindex]
                MyRackRecord[ramavail_Rackindex]+=myRecord[ramavail_hwindex]
                MyRackRecord[vcpuused_Rackindex]+=myRecord[vcpuused_hwindex]
                MyRackRecord[ramused_Rackindex]+=myRecord[ramused_hwindex]
                MyRackRecord[nofcmpts_Rackindex]+=1
            

        for MyRackRecord in self.Report:
                #print(MyRackRecord)
                #print(PctUsage_Rackindex,myRackRecord[vcpuused_Rackindex],myRackRecord[vcpuavail_Rackindex],myRackRecord[ramused_Rackindex],myRackRecord[ramavail_Rackindex],self.calc_max_percentage(myRackRecord[vcpuused_Rackindex],myRackRecord[vcpuavail_Rackindex],myRackRecord[ramused_Rackindex],myRackRecord[ramavail_Rackindex]))
                Num1 = MyRackRecord[vcpuused_Rackindex] 
                Den1 = MyRackRecord[vcpuavail_Rackindex]
                Num2 = MyRackRecord[ramused_Rackindex]
                Den2 = MyRackRecord[ramavail_Rackindex]
                MyValue = self.calc_max_percentage(Num1,Den1, Num2,Den2)
                #print("MyValue={:}".format(MyValue))
                MyRackRecord[PctUsage_Rackindex]=MyValue
        #print(self.Report)




    # FUNCTIONS TO EVALUATE SORTING KEY AND METRIC FOR RACKCOMBOS or LOADVECTOR respectively
    # the following variables are usable for computing the value of sorting key
    # ----      
    # maximum  = MAX # of VCPUs in the ARRAY of inputlist rack combos
    # minimum     = MIN # of VCPUs in the ARRAY of inputlist of rack combos
    # total   == TOTAL # of VCPUs  across all rack combos records
    # NOfEntries   =TOTAL # of rackcombos records in input list
    # average    =AVG # of VCPUs across all rack combos records
    # currentvalue = Value of VPUs for each rack combo record
    # ------
    # RESORTING ARRAY OF RACK COMBOS BASED ON 'string formula'
    

   

    #--------------------------------------- PROCEDURE TO REALIGN AZ based on EXTERNALLY PROVIDED JSON FILE    -----------------------------
    def realignAZinhwreport(self,pars,dst_report):
        if len(pars.paramsdict["HW_OPTIMIZATION_MODE"])==0:
            #print(" ### DEBUG - no AZ realign parameter passed to select input file for Rack to AZ realignment")
            return dst_report
        try:
            FILENAME=pars.PATHFOROUTPUTREPORTS+'/HW_OPTIMIZATION_MODE_targetracklayout_'+pars.paramsdict["HW_OPTIMIZATION_MODE"]+".json"
            with open(FILENAME,'r') as file1:
                HW_OPTIMIZATION_MODE=json.load(file1)
                print( json.dumps(HW_OPTIMIZATION_MODE, indent=22))
        except (IOError,EOFError) as e:
            print(" ERROR - file {:s} not found for Rack to AZ realignment".format(pars.paramsdict["HW_OPTIMIZATION_MODE"]))
            exit(1)

        sitename = pars.parse_suffisso(pars.paramsdict["DESTINATION_SITE_SUFFIX"])
        try:
            NEWAZMAP=dict(HW_OPTIMIZATION_MODE[sitename])
            #print("DEBUG HW_OPTIMIZATION_MODE2:",json.dumps(NEWAZMAP,indent=22))
        except (KeyError) as e:
            print(" --- ERROR : in file {:s} for AZ realignment, the site {:s} has no data for AZ realignment: Rack to AZ mapping is therefore unchanged!".format(MyPARAMSDICT.paramsdict["HW_OPTIMIZATION_MODE"],sitename))
            return(dst_report)
        newracktoazmap={}
        for i in range(len(HW_OPTIMIZATION_MODE[sitename]["rackslayout"])):
            racknum=HW_OPTIMIZATION_MODE[sitename]["rackslayout"][i]
            aznum=int(i/2)+1
            azname = "DT_NIMS_AZ"+str(aznum)
            newracktoazmap[racknum]=azname
        #print(json.dumps(newracktoazmap,indent=22))

        for ITEM in dst_report.Report:
            AZINREP=ITEM[dst_report.get_keys().index("AZ")]
            RACKINREP=int(ITEM[dst_report.get_keys().index("Rack")])
            ITEM[dst_report.get_keys().index("AZ")]= newracktoazmap[str(RACKINREP)]

        return HW_OPTIMIZATION_MODE[sitename]["rackslayout"]
            #print("DEBUG3 - ", newracktoazmap[str(RACKINREP)])
    #        for NEWITEM in NEWAZMAP:
    #            if RACKINREP in NEWAZMAP.get(NEWITEM):
    #                ITEM[HW_REPORT_KEYS.index("AZ")]=str(NEWITEM)
                                # print(" ---- REPORT RACK={:d} NEWRACKS={} ----- >{:b}--- REPLACE: {:s} with {:s} ?".format(RACKINREP,NEWAZMAP.get(NEWITEM),int(RACKINREP) in NEWAZMAP.get(AZINREP), AZINREP,NEWITEM))


    # --------------------------- WRITE OPTIMIZED RACK LAYOUT TO FILE
    def writeoptimizedrackstofile(self, pars):
        FILENAME=pars.PATHFOROUTPUTREPORTS+'/'+'HW_OPTIMIZATION_MODE_targetracklayout_'+'OUTPUT'+'.json'
        memorydict=self.OUTPUTDICT
        suffix=pars.paramsdict["DESTINATION_SITE_SUFFIX"]
        if len(memorydict)==0:
            print("WARNING writeoptimizedrackstofile: no data in optimized rack layout dict: skipping appending data to {} ".format(FILENAME))
            return False
        sitename=pars.parse_suffisso(suffix)
        print(json.dumps(memorydict,indent=22))
        with open(FILENAME,'w') as file1:
            json.dump(memorydict,file1)
            file1.close
        return True


#--------------------------------------------------------------------------------------------------------------
#------------------------- ############# SITE REPORT ############# --------------------------------------------
#--------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
class site_report(report):
    def __init__(self,params):
        super().__init__(params)
        self.ReportType=super().get_reporttype()
        self.ReportTotalUsage=[]
        self.Report=[]
        self.color=menu.FAIL

        self.REPORT_KEYS= super().get_keys()
        self.REPORT_SORTINGKEYS= super().get_sorting_keys()
        #self.SITE_REPORT_KEYS= self.REPORTFIELDGROUP["SITE_Report_Keys"]
        #self.SITE_REPORT_SORTINGKEYS = self.REPORTFIELDGROUP["SITE_Report_Sorting_Keys"]


#   PRODUCE PER SITE PER PROJECT USAGE SUMMARY REPORT , called SITE REPORT
    def produce_site_report(self,pars,  SRC_VM_REPORTBOX, SRC_HW_REPORTBOX):
        self.ClearData()
        Sitename=pars.parse_suffisso( pars.paramsdict["SOURCE_SITE_SUFFIX"])
        SRCVMReportKeys= SRC_VM_REPORTBOX.get_keys()
        SrcvCPUsUSedPerVMIndex =SRCVMReportKeys.index("vCPUsUSedPerVM")
        SrcRAMusedMBperVMIndex = SRCVMReportKeys.index("RAMusedMBperVM")
        SrcProjectperVMIndex = SRCVMReportKeys.index("Project")
        SrcVMNameIndex = SRCVMReportKeys.index("VMname")

        SRCHWReportKeys=SRC_HW_REPORTBOX.get_keys()
        SRC_VCPUsPerCmpIndex=SRCHWReportKeys.index("vCPUsAvailPerHV")
        SRC_RAMPerCmpIndex=SRCHWReportKeys.index("MemoryMBperHV")
        SRC_VCPUsUsedPerCmpIndex=SRCHWReportKeys.index("vCPUsUsedPerHV")
        SRC_RAMUsedPerCmpIndex=SRCHWReportKeys.index("MemoryMBUsedperHV")

        TotalVMs=0
        TotalVCPUUsed=0
        TotalRAMUsed=0
        TotalVCPUAvail=0
        TotalRAMAVail=0
        ProjectsInSite=[]
        VMsPerProjectInSite=[]
        VCPUPerProjectInSite=[]
        RAMPerProjectInSite=[]
        PctUsage=[]
        VCPUInSite=[]
        RAMInSite=[]
        VCPUAvailPerSite=0
        RAMAvailPerSite=0
        VCPUUsedPerSite=0
        RAMUsedPerSite=0
        CountOfLineupsPerSite=0
       # "SITE_Report_Keys": ["Site","Project",
       # "NOfVMs","VCPUsUsed", "VCPUsAvail","RAMUsed" ,"RAMAvail","PctUsageOfCmpt"  ],

        for srccompute in SRC_HW_REPORTBOX.Report:
            VCPUAvailPerSite+=srccompute[SRC_VCPUsPerCmpIndex]
            RAMAvailPerSite+=srccompute[SRC_RAMPerCmpIndex]
            VCPUUsedPerSite+=srccompute[SRC_VCPUsUsedPerCmpIndex]
            RAMUsedPerSite+=srccompute[SRC_RAMUsedPerCmpIndex]

        for srcvm in SRC_VM_REPORTBOX.Report:
            CurrentVMProject =srcvm[SrcProjectperVMIndex] 
            CurrentVMVCPUs=srcvm[SrcvCPUsUSedPerVMIndex]
            CurrentVMRAM=srcvm[SrcRAMusedMBperVMIndex]

            #print(CurrentVMLineup)
            if CurrentVMProject not in ProjectsInSite:
                ProjectsInSite.append(CurrentVMProject)
                VMsPerProjectInSite.append(0)
                VCPUPerProjectInSite.append(0)
                RAMPerProjectInSite.append(0)
                VCPUInSite.append(VCPUAvailPerSite)
                RAMInSite.append(RAMAvailPerSite)
                PctUsage.append(0)
            else:
                IndexToUpdate=ProjectsInSite.index(CurrentVMProject)
                VMsPerProjectInSite[IndexToUpdate]+=1
                try:
                    if type(CurrentVMVCPUs)!=int or  type(CurrentVMRAM)!=int:
                        CurrentVMVCPUs=0
                        CurrentVMRAM=0
                    VCPUPerProjectInSite[IndexToUpdate]+=int(CurrentVMVCPUs)
                    RAMPerProjectInSite[IndexToUpdate]+=int(CurrentVMRAM)

                except:
                    CurrentVMVCPUs=0
                    CurrentVMRAM=0
                    Errstring="produce_site_report : VM {:} has no associated flavor. Setting VCPU=0 and RAM=0".format(srcvm[SRCVMReportKeys.index("VMname")])
                    print(Errstring)
                    pars.cast_error("00100", Errstring) 
                TotalVMs+=1
                TotalVCPUUsed+=CurrentVMVCPUs
                TotalRAMUsed+=CurrentVMRAM
                PctUsage[IndexToUpdate]=self.calc_max_percentage( VCPUPerProjectInSite[IndexToUpdate],VCPUAvailPerSite, RAMPerProjectInSite[IndexToUpdate],RAMAvailPerSite)



        ProjectsInSite.append("TOTAL PER SITE")
        VMsPerProjectInSite.append(TotalVMs)
        VCPUPerProjectInSite.append(VCPUUsedPerSite)
        RAMPerProjectInSite.append(RAMUsedPerSite)
        VCPUInSite.append(VCPUAvailPerSite)
        RAMInSite.append(RAMAvailPerSite)
        PctUsage.append(self.calc_max_percentage( VCPUUsedPerSite,VCPUAvailPerSite, RAMUsedPerSite,RAMAvailPerSite))

        for Counter in range(len(ProjectsInSite)):
            MyRec=self.addemptyrecord()
            self.UpdateLastRecordValueByKey("Site",Sitename)
            self.UpdateLastRecordValueByKey("Project",ProjectsInSite[Counter])
            self.UpdateLastRecordValueByKey("NOfVMs",VMsPerProjectInSite[Counter])
            self.UpdateLastRecordValueByKey("VCPUsUsed",VCPUPerProjectInSite[Counter])
            self.UpdateLastRecordValueByKey("VCPUsAvail",VCPUInSite[Counter])
            self.UpdateLastRecordValueByKey("RAMUsed",RAMPerProjectInSite[Counter])
            self.UpdateLastRecordValueByKey("RAMAvail",RAMInSite[Counter])
            self.UpdateLastRecordValueByKey("PctUsage",PctUsage[Counter])
            #self.UpdateLastRecordValueByKey("Lineup","")




#--------------------------------------------------------------------------------------------------------------
#------------------------- ############# TOTALRESULTS REPORT ############# ------------------------------------
#--------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
class totalresults_report(report):

    def __init__(self,params):
        super().__init__(params)
        self.ReportType=super().get_reporttype()
        self.REPORT_KEYS= super().get_keys()
        self.REPORT_SORTINGKEYS= super().get_sorting_keys()
        #self.TOTALRESULTS_REPORT_KEYS= self.REPORTFIELDGROUP["TOTALRESULTS_Report_keys"]
        #self.TOTALRESULTS_REPORT_SORTINGKEYS = self.REPORTFIELDGROUP["TOTALRESULTS_Report_Sorting_Keys"]
        self.ReportTotalUsage=[]
        self.Report=[]
        self.color=menu.OKGREEN

    
    # ----------------------------------------------------------------------------------------------------------------------------------------
    # PRODUCE TOTAL REPORT
    # ----------------------------------------------------------------------------------------------------------------------------------------
    def check_capacity_and_produce_Total_Report(self, pars,  SRC_REPORTBOX, DST_REPORTBOX, metric_formula, myoptimizedrackrecord):

        def hostaggr_match(pars, hostaggr1, hostaggrlist2):
            if pars.paramsdict["IGNOREHOSTAGS"] == True:
                return True
            stringa1 = hostaggr1.upper()
            stringa2 = stringa1.replace("DTNIMS", "DT_NIMS")
            for x in hostaggrlist2:
                x.upper().replace("DTNIMS", "DT_NIMS")
            retval = stringa2 in hostaggrlist2
            return retval


        destsitename = pars.parse_suffisso(pars.paramsdict["DESTINATION_SITE_SUFFIX"])
        MODE_OF_OPT_OPS = pars.get_azoptimization_mode()
        
        # Now check if instantiation fits in the newly adjusted report

        vmfits = False
        capacity_fit = []
        srcvm = []
        VMNAME = ''
        HOSTAGGRSET = []
        HOSTAGGRLIST = []

        # SORT VMs TO BE 'INSTANTIATED' by Project, VNF, VNFC
        SourceReportSortKeys = ["Project", "AZ", "vnfname", "vnfcname"]
        SRC_REPORTBOX.sort_report(SourceReportSortKeys)

        SrcvCPUsUSedPerVMIndex = SRC_REPORTBOX.get_keys().index("vCPUsUSedPerVM")
        SrcRAMusedMBperVMIndex = SRC_REPORTBOX.get_keys().index("RAMusedMBperVM")
        SrcAZIndex = SRC_REPORTBOX.get_keys().index("AZ")
        SrcVMnameIndex = SRC_REPORTBOX.get_keys().index("VMname")
        SrcHostAggrIndex = SRC_REPORTBOX.get_keys().index("HostAggr")
        SrcTargetHostAggrIndex = SRC_REPORTBOX.get_keys().index("TargetHostAggr")

        DstvCPUsUsedPerHVIndex = DST_REPORTBOX.get_keys().index("vCPUsUsedPerHV")
        DstMemoryMBUsedperHVIndex = DST_REPORTBOX.get_keys().index("MemoryMBUsedperHV")
        DstvCPUAvailIndex = DST_REPORTBOX.get_keys().index("vCPUsAvailPerHV")
        DstMemoryMBperHVIndex = DST_REPORTBOX.get_keys().index("MemoryMBperHV")
        DstAZIndex = DST_REPORTBOX.get_keys().index("AZ")
        DstHostAggrIndex = DST_REPORTBOX.get_keys().index("HostAggr")
        DstNewVMsIndex = DST_REPORTBOX.get_keys().index("NewVMs")
        DstPctUsageIndex = DST_REPORTBOX.get_keys().index("PctUsageOfCmpt")

        # CLEAR NEW VMs on DST REPORT
        for dstcmp in DST_REPORTBOX.Report:
            dstcmp[DstNewVMsIndex] = []

        # GO THROUGH ALL VMs in SOURCE REPORT ONE BY ONE....

        for srcvm in SRC_REPORTBOX.Report:
            VM_VCPUS = srcvm[SrcvCPUsUSedPerVMIndex]
            VM_RAM = srcvm[SrcRAMusedMBperVMIndex]
            VM_AZ = srcvm[SrcAZIndex]
            VM_VMNAME = srcvm[SrcVMnameIndex]
            VM_HOSTAGGRSET = set(srcvm[SrcHostAggrIndex])
            VM_HOSTAGGRLIST = list(HOSTAGGRSET)
            VM_HOSTAGGR = srcvm[SrcTargetHostAggrIndex]
            #print("DEBUG {:}............ ".format(srcvm))
            # SORT COMPUTES BY LEAST USED VCPU
            #if pars.paramsdict["BESTVMDISTRO"]:
            #    mykeys="vCPUsUsedPerHV"
            #    DST_REPORTBOX.sort_report(mykeys)
                #for i in range (1):
                #    print(" DEBUG 1 - check_capacity_and_produce_Total_Report- sorted ")
                #    print(DST_REPORTBOX.Report[i])
            for dstcmp in DST_REPORTBOX.Report:
                hwcpu_total = dstcmp[DstvCPUAvailIndex]
                hwram_total = dstcmp[DstMemoryMBperHVIndex]
                hwcpu_used = dstcmp[DstvCPUsUsedPerHVIndex]
                hwram_used = dstcmp[DstMemoryMBUsedperHVIndex]
                dstcmp[DstPctUsageIndex]=int(100*(hwcpu_used/hwcpu_total))
            #sorted(DST_REPORTBOX.Report,key=lambda x: x[DstPctUsageIndex], reverse=False)
            sorted(DST_REPORTBOX.Report, key=itemgetter(DstAZIndex,DstPctUsageIndex))

            vmfits = False
            result = []

            for dstcmp in [x for x in DST_REPORTBOX.Report if hostaggr_match(pars, VM_HOSTAGGR, x[DstHostAggrIndex]) and VM_AZ in x[DstAZIndex]]:
                #print("2 - check_capacity_and_produce_Total_Report ")
                #print("{:}............ ".format(dstcmp))

                hwcpu_total = dstcmp[DstvCPUAvailIndex]
                hwram_total = dstcmp[DstMemoryMBperHVIndex]
                hwcpu_used = dstcmp[DstvCPUsUsedPerHVIndex]
                hwram_used = dstcmp[DstMemoryMBUsedperHVIndex]
                if VM_VCPUS < hwcpu_total-hwcpu_used and VM_RAM < hwram_total-hwram_used:
                    try:
                        dstcmp[DstvCPUsUsedPerHVIndex] += VM_VCPUS
                        dstcmp[DstMemoryMBUsedperHVIndex] += VM_RAM
                        #dstcmp.append("{:24s} {:>2d} {:>5s} {:s}".format(VMNAME,VCPUS,dst.mem_show_as_gb(RAM,True),HOSTAGGR[8]))
                        dstcmp[DstNewVMsIndex].append(" {:>10s} ".format(
                            DST_REPORTBOX.split_vnfname(VM_VMNAME, "vnfname-vnfcname")))

                        vmfits = True
   
                        break
                    except:
                        print("DSTCMP Record:\n{:}".format(dstcmp))
                        print("DSTCMP DstNewVMsIndex:\n{:}".format(
                            DstNewVMsIndex))
        
        # CALCULATES THE % OF VCPU USED OVER TOTAL
        CumulativeVCPUUsed=0
        CumulativeVCPUAvail=0       
        for x in DST_REPORTBOX.Report:
                hwcpu_total = dstcmp[DstvCPUAvailIndex]
                hwram_total = dstcmp[DstMemoryMBperHVIndex]
                hwcpu_used = dstcmp[DstvCPUsUsedPerHVIndex]
                hwram_used = dstcmp[DstMemoryMBUsedperHVIndex]
                CumulativeVCPUUsed+=hwcpu_used
                CumulativeVCPUAvail+=hwcpu_total
        OverallVCPULoad = "{:d}%".format(int( 100*float (CumulativeVCPUUsed/CumulativeVCPUAvail)))

        # APPEND RESULTS TO TOTAL_REPORT OBJECT
        TotalRepoKeys=self.get_keys()
        MyRecord=self.addemptyrecord()
        MyRecord[TotalRepoKeys.index("Capacity-fits")]=vmfits
        MyRecord[TotalRepoKeys.index("SourceSuffix")]=pars.paramsdict["SOURCE_SITE_SUFFIX"]
        MyRecord[TotalRepoKeys.index("DestinationSuffix")]=pars.paramsdict["DESTINATION_SITE_SUFFIX"]
        MyRecord[TotalRepoKeys.index("Service")]=pars.paramsdict["SERVICE"]
        MyRecord[TotalRepoKeys.index("vCPU_Load_after")]=OverallVCPULoad

        if vmfits == False:
            #result.append(vmfits)
            Description = "VM: {:s} on AZ {:s} and HostAgg {:s} did not have sufficient capacity".format(
                VM_VMNAME, VM_AZ, VM_HOSTAGGR)
        else:
            Description = "SUCCESS : all source VM instantiated into destination"

        MyRecord[TotalRepoKeys.index("Outcome")]=Description

        return result


#--------------------------------------------------------------------------------------------------------------
#------------------------- ############# ERROR REPORT ############# -------------------------------------------
#--------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
class error_report(report):
    def __init__(self,params):
        super().__init__(params)
        self.ReportType=super().get_reporttype()
        self.ReportTotalUsage=[]
        self.color=menu.White

        self.REPORT_KEYS= super().get_keys()
        self.REPORT_SORTINGKEYS= super().get_sorting_keys()
        #self.ERROR_REPORT_KEYS= self.REPORTFIELDGROUP["ERROR_Report_Keys"]
        #self.ERROR_REPORT_SORTINGKEYS = self.REPORTFIELDGROUP["ERROR_Report_Sorting_Keys"]
        self.Report=[]
    
    def produce_error_report(self,pars):
        self.Report=pars.ERROR_REPORT

#--------------------------------------------------------------------------------------------------------------
#------------------------- ############# SERVICE GRAPH ############# ----------------------------------------------
#--------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------- 
class servicegraph_report(report):

    def __init__(self,params):
        super().__init__(params)
        self.ReportType=super().get_reporttype()

        self.Report=[]
        self.ReportTotalUsage=[]
        self.color=menu.OKBLUE

        self.REPORT_KEYS= super().get_keys()
        self.REPORT_SORTINGKEYS= super().get_sorting_keys()
        screenrows, screencolumns = os.popen('stty size', 'r').read().split()


    def crawl_dict(self, mydictbranch, KeysArray, MyType):
        MyBranch = mydictbranch
        for MyKey in KeysArray:
            if MyKey in MyBranch.keys():
                MyBranch=MyBranch[MyKey]
                MyCurrentType=type(MyBranch[MyKey])
            else:
                return type(MyType)() 
        return MyBranch

    def produce_servicegraphreport(self, params, dictarray_object):
        if params.get_param_value("SERVICEGRAPHENABLED")==False:
            print("ERROR: produce_servicegraphreport :Service Graph data load not enabled in CLI parameters")
            return -1
        if dictarray_object.SKIPSERVICEGRAPH:
            MyName=dictarray_object.__class__
            ErrString = "produce_servicegraphreport: {:} has no complete Dictarrays for Servicegraph".format(MyName)
            params.cast_error("00201",ErrString)
            return
        ReportKeys= self.get_keys()

        self.ClearData()
        VirtualPortIndex = ReportKeys.index("VirtualPort")
        
        for PROGETTO in [ Zed for Zed in dictarray_object.SERVERDICT if Zed in params.paramsdict["SERVICE"]]:
            print("-- produce_servicegraphreport for "+PROGETTO)
            for VMRecord in dictarray_object.SERVERDICT[PROGETTO]:
                VMName=VMRecord["Name"]
                VM_UUID= VMRecord["ID"]
                VMHost= VMRecord["Host"]
                VMFlavorId=VMRecord["Flavor ID"]

                for VirtualMachineInterface in dictarray_object.VIRTUALPORT_DICT["virtual-machine-interfaces"]:
                    CurrentVMIDict= VirtualMachineInterface["virtual-machine-interface"]
                    CurrentVMI_FQDN= CurrentVMIDict["fq_name"]
                    ProjectName =CurrentVMI_FQDN[1]
                    if ProjectName==PROGETTO:
                        self.addemptyrecord()
                        self.UpdateLastRecordValueByKey("VMname",VMName)
                        self.UpdateLastRecordValueByKey("vnfname",self.split_vnfname(VMName,"vnfname"))
                        self.UpdateLastRecordValueByKey("Project",CurrentVMI_FQDN[1])
                        self.UpdateLastRecordValueByKey("VirtualPort",CurrentVMIDict["name"])

                        if "virtual_machine_interface_disable_policy" in CurrentVMIDict.keys():
                            VMI_PacketModeAttr = CurrentVMIDict["virtual_machine_interface_disable_policy"]
                        else:
                            VMI_PacketModeAttr= False
                        self.UpdateLastRecordValueByKey("PacketMode",VMI_PacketModeAttr)

                        VMI_VirtualNetworkAttr = CurrentVMIDict["virtual_network_refs"][0]["uuid"]
                        VMI_MirrorTo=""
                        if "virtual_machine_interface_properties" in CurrentVMIDict.keys():
                            VMI_IntfPropertiesDict= CurrentVMIDict["virtual_machine_interface_properties"]
                            if "interface_mirror" in VMI_IntfPropertiesDict.keys():
                                if VMI_IntfPropertiesDict["interface_mirror"]:
                                    if "mirror_to" in VMI_IntfPropertiesDict["interface_mirror"].keys():
                                        VMI_MirrorTo=VMI_IntfPropertiesDict["interface_mirror"]["mirror_to"]["analyzer_name"]+" (" + VMI_IntfPropertiesDict["interface_mirror"]["mirror_to"]["analyzer_ip_address"]+")"
                                else:
                                        VMI_MirrorTo="Null"
                            else:
                                    VMI_MirrorTo="None"
                        self.UpdateLastRecordValueByKey("MirrorTo",VMI_MirrorTo)

                        if "virtual_machine_interface_allowed_address_pairs" in CurrentVMIDict.keys():
                            VMI_AAPDict = CurrentVMIDict["virtual_machine_interface_allowed_address_pairs"]
                            #print(json.dumps(VMI_AAPDict,indent=6))
                            if "allowed_address_pair" in VMI_AAPDict.keys():
                                VMI_AAPList = VMI_AAPDict["allowed_address_pair"]

                                TMPREC =[]
                                for x in VMI_AAPList:
                                    MyStr=x["address_mode"]+","+x["ip"]["ip_prefix"]+"/"+str(x["ip"]["ip_prefix_len"])+"; "
                                    TMPREC.append(MyStr)
                                self.UpdateLastRecordValueByKey("AAP",TMPREC)
                            else:
                                self.UpdateLastRecordValueByKey("AAP",[])

                        else:
                            self.UpdateLastRecordValueByKey("AAP",[])


                        if "security_group_refs" in CurrentVMIDict.keys():
                            VMI_SecGroupRefsList = CurrentVMIDict["security_group_refs"]
                            TMPREC =[]
                            for x in VMI_SecGroupRefsList:
                                TMPREC.append(x["to"][2]+";")
                                self.UpdateLastRecordValueByKey("SecGroups",TMPREC)
                            else:
                                self.UpdateLastRecordValueByKey("SecGroups",[])

                        else:
                            self.UpdateLastRecordValueByKey("SecGroups",[])

                        if "virtual_network_refs" in CurrentVMIDict.keys():
                            VMI_VNRefsList = CurrentVMIDict["virtual_network_refs"]
                            TMPREC =[]
                            VNUUID_List=[]
                            for x in VMI_VNRefsList:
                                #TMPREC.append(x["to"][1]+":"+x["to"][2])
                                VNUUID_List.append(x["uuid"])
                                TMPREC2=[]
                                for W in dictarray_object.get_VNs_and_subnets(x["uuid"]):
                                    NewSubnetData=W[1]+": v"+W[2]+" "+W[3]
                                    TMPREC2.append(NewSubnetData)
                                TMPREC.append(x["to"][2]+"("+W[0]+")")
                                self.UpdateLastRecordValueByKey("Network",TMPREC)
                                self.UpdateLastRecordValueByKey("Subnet",TMPREC2)

                            else:
                                self.UpdateLastRecordValueByKey("Network",[])

                        else:
                            self.UpdateLastRecordValueByKey("Network",[])



                        if "id_perms" in CurrentVMIDict.keys():
                            VMI_IDpermissions =CurrentVMIDict["id_perms"]
                            if "permissions" in VMI_IDpermissions:
                                VMI_permissions=VMI_IDpermissions["permissions"]
                                self.UpdateLastRecordValueByKey("Owner",VMI_permissions["owner"])
                            else:
                                self.UpdateLastRecordValueByKey("Owner","")
                        else:
                            self.UpdateLastRecordValueByKey("Owner","")






class hw_vcpu_report(report):
    def __init__(self,params):
        super().__init__(params)

        self.ReportType=super().get_reporttype()
        self.ReportTotalUsage=[]
        self.color=menu.Yellow

        self.REPORT_KEYS= super().get_keys()
        self.REPORT_SORTINGKEYS= super().get_sorting_keys()
        #self.HW_REPORT_KEYS= self.REPORTFIELDGROUP["HW_Report_Keys"]
        #self.HW_REPORT_SORTINGKEYS = self.REPORTFIELDGROUP["HW_Report_Sorting_Keys"]




    # ---------------------------------------------------------------------------------------------------
    # Produces a report (list of lists); one row per hardware compute based on the global ARRAY of (list,dict) passed as parameter. 
    # ---------------------------------------------------------------------------------------------------
    def produce_hw_vcpu_report(self,SUFFISSO, pars, dictarray_object ):


        def giveRange(numString:str):
            ListOfNumbers=numString.split("-")
            if(len(ListOfNumbers)==1):
                return [int(ListOfNumbers[0])]
            elif(len(ListOfNumbers)==2):
                return range(int(ListOfNumbers[0]),int(ListOfNumbers[1])+1)
            else:
                raise IndexError("giveRange - Too many values passed to parse range : ",numString)

        def unpackvcpus(mylist):
            rList=[]
            for numString in mylist:
                #print("DEBUG unpackvcpus numString=",numString)
                rList.extend(set(chain(*map(giveRange,numString.split(",")))))
            return rList

        def clean_dups(mylist):
            ListNoDupes = list()
            for Item in mylist:
                if Item not in ListNoDupes:
                    ListNoDupes.append(Item)
            return ListNoDupes
# ------------------------------------------------------------------------------------
# PRODUCE_HW_VCPU_REPORT
# ------------------------------------------------------------------------------------
        if pars.paramsdict["HWNUMAAWARE"]==False:
            print("Numa aware HW report disabled")
            return
        self.Report=[]
        CountVMsWithoutFlavor=0
        VMswithoutFlavor=[]
        # Scan each compute from the OPENSTACK JSON List
        for compute in [ x for x in dictarray_object.HYPERVISOR_LIST if x["State"] == "up"]:
            nodo_longformat = str(compute["Hypervisor Hostname"])
            nodo=nodo_longformat.split(".")[0]
            
            nomecorto = str(compute["Hypervisor Hostname"].split('.')[0])
            site_name = str(compute["Hypervisor Hostname"].split('.')[1])
            timestamp = SUFFISSO[0:14]
            rack = nomecorto[21:23]
            if DEBUG==1:
                print("------------------------------------------------------------------------------------------------------------------------------------------")
                print("------------------------------------------------------------------------------------------------------------------------------------------")
                print("DEBUG1 INFO produce_hw_vcpu_report\n")
                print("DEBUG1 INFO Nodo=:{:} Nodo_longformat={:}".format(nodo,nodo_longformat))
                #print(dictarray_object.HYPERVISOR_VCPU.keys())

            # GET THE RECORD from VIRSH JSON for this compute
            numarecord =dictarray_object.HYPERVISOR_VCPU[nodo]
            if DEBUG==1:
                #print("DEBUG2 produce_hw_vcpu_report: Dictionary ")
                #print(json.dumps(numarecord, indent=22))
                #print("DEBUG2 end produce_hw_vcpu_report: Dictionary ")
                print("---------------------------------------------------------------------")
                print("DEBUG2: INFO -- numarecord['node'].keys():",numarecord["node"].keys())
            
            #For each NUMA in HYPERVISOR, parsing JSON VIRSH...
            for myNUMAidstring in numarecord["node"].keys():
                myNumaId=int(myNUMAidstring)
                myvCPUperNUMAlist=numarecord["node"][myNUMAidstring]["cpus"]

                print("---------------------------------------------------------------------")
                # Get the list of VCPU IDs available for this numa
                if DEBUG==1:
                    print("DEBUG3 : numa={:}  \n\tmyvCPUperNUMAlist:{:}".format(myNUMAidstring,myvCPUperNUMAlist))
                myvCPUperNUMAlist=unpackvcpus(clean_dups(myvCPUperNUMAlist))
                myvCPUperNUMAload=[0] * len(myvCPUperNUMAlist)
                myNofPinnedVMsperCPU=[0] * len(myvCPUperNUMAlist)

                myVMusesList=[]
                myvmcpus_onwrongNUMA=[]
                myinstances_withcpuonwrongNUMA=[]
                perNUMAvcpu_listofvms=[]
                myvCPUperNUMA_vms=[perNUMAvcpu_listofvms] * len(myvCPUperNUMAlist)
                myvCPUperNUMA_pinnedvms=[perNUMAvcpu_listofvms] * len(myvCPUperNUMAlist)
                #Create three empty list : list of CPUs used by Instance, 
                #list of CPUs that , on the instance, are associated to CPUs on Wrong numa
                # list of instance IDs (to be replaced with VM UUID) with associated CPU on wrong numa
                myRAMperNUMAavail=numarecord["node"][myNUMAidstring]["size"]
                myRAMperNUMAfree=numarecord["node"][myNUMAidstring]["free"]


                if "instances" not in numarecord.keys():
                    if DEBUG==1:
                        print("---------------------------------------------------------------------")
                        print("DEBUG4 : WARNING : missing 'instances' key in  ",nodo_longformat)
                        print("Numa ID:",myNumaId)
                        print(numarecord.keys())
                        print("---------------------------------------------------------------------")

                # Scan the instances in the virsh JSON file by ID
                for myInstance in numarecord["instances"].keys():
                    # if a compute is empty it wont have instances so this will be skipped
                    # If domuuid key is not in keys, then we cannot search Openstack VMs by UUID.
                    # Not sure there is any alternative to having domuuid
                    vm_numaused=numarecord["instances"][myInstance]["numa_nodeset"]
                    if "domuuid" in numarecord["instances"][myInstance].keys() and vm_numaused==myNUMAidstring:
                        VMUUID_virsh=numarecord["instances"][myInstance]["domuuid"]
                        
                        myVMusesList=[]
                        myVMusesList=sorted(unpackvcpus(clean_dups( numarecord["instances"][myInstance]["cpus"])))
                        UseVMUUID=True
                        if DEBUG==1:
                            print("---------------------------------------------------------------------")
                            print("DEBUG5: INFO instance {:} in numa {:} vs {:} uses vcpus {:} ".format(myInstance,vm_numaused,myNUMAidstring,myVMusesList))

                        for usedvcpu in myVMusesList:
                            if usedvcpu not in myvCPUperNUMAlist:
                                myvmcpus_onwrongNUMA.append(usedvcpu)
                                myinstances_withcpuonwrongNUMA.append(dictarray_object.get_vmname(VMUUID_virsh))

                        for PROGETTO in dictarray_object.SERVERDICT:
                            str_PROGETTO=str(PROGETTO)
                            #for VM in [ x for x in dictarray_object.SERVERDICT[PROGETTO] if x["Host"] == compute["Hypervisor Hostname"]]:
                            for VM in [ x for x in dictarray_object.SERVERDICT[PROGETTO] if x["Host"] == compute["Hypervisor Hostname"] and x["ID"]==VMUUID_virsh]:
                                AGGS = dictarray_object.cmpt_to_agglist(nodo)
                                VMNAME=str(VM["Name"])
                                VMUUID=str(VM["ID"])
                                VMFLAVORID=VM["Flavor ID"]
                                if DEBUG==1:
                                    print("DEBUG6: INFO Progetto={:} VMNAME={:} FLAVORID={:}".format(str_PROGETTO,VMNAME,VMFLAVORID))
                                VM_VCPUS=0
                                VM_IS_CPU_PINNED=False
                                for FLAVOR in [x for x in dictarray_object.FLAVOR_LIST if x["ID"]==VMFLAVORID]:
                                    VM_VCPUS=FLAVOR["VCPUs"]
                                    minidict= dictarray_object.parse_flavor_properties(pars,FLAVOR)
                                    if DEBUG==1:
                                        print("\tDEBUG7: parsing flavor {:}".format(FLAVOR["ID"]))
                                    if "hw:cpu_policy" in minidict.keys():
                                        if minidict["hw:cpu_policy"].upper()=="DEDICATED":
                                            VM_IS_CPU_PINNED=True
                                    
                                    if DEBUG==1:
                                        if VM_IS_CPU_PINNED:
                                            mycolor=menu.OKGREEN
                                        else:
                                            mycolor=menu.FAIL
                                        print(mycolor+"\tDEBUG7: INFO VM IS CPU PINNED={:} ".format(VM_IS_CPU_PINNED))

                                if VM_VCPUS==0:
                                    CountVMsWithoutFlavor+=1
                                    VMswithoutFlavor.append(VMNAME)
                                    AdditionalLoadIndexPerCPU=0
                                    VMVCPUS=len(numarecord["instances"][myInstance]["cpus"])

                                if  VM_VCPUS>0:
                                    if VM_IS_CPU_PINNED:
                                        if len(myVMusesList)!=VM_VCPUS:
                                            WarningString="VM:{:} on compute {:} has {:} cpus in flavor, but {:} cpus in virsh".format(VMNAME,compute,VM_VCPUS,len(myVMusesList),)
                                            pars.cast_error("00304",WarningString)
                                            #exit(-1)
                                        AdditionalLoadIndexPerCPU=1
                                    else:
                                        AdditionalLoadIndexPerCPU= round(float(VM_VCPUS)/float(len(myVMusesList)),2)
                                else:
                                    pass
                                    
                                if DEBUG==1:
                                    print("\tDEBUG8: Additional Load per vCPU={:} ".format(AdditionalLoadIndexPerCPU))
                                    print("\tDEBUG8: Numa {:} Load Before={:}".format(myNUMAidstring,myvCPUperNUMAload))
                                CrossNumaUsage=False
                                for vcpu in myVMusesList:
                                    if vcpu in myvCPUperNUMAlist:
                                        VCPU_per_numa_index=myvCPUperNUMAlist.index(vcpu)
                                        oldvalue=myvCPUperNUMAload[VCPU_per_numa_index]
                                        newvalue=oldvalue+AdditionalLoadIndexPerCPU
                                        myvCPUperNUMAload[VCPU_per_numa_index]=newvalue

                                        if VMNAME not in myvCPUperNUMA_vms[VCPU_per_numa_index]:
                                            myvCPUperNUMA_vms[VCPU_per_numa_index].append(VMNAME)
                                
                                        if VM_IS_CPU_PINNED:
                                            oldvalue=myNofPinnedVMsperCPU[VCPU_per_numa_index]
                                            myNofPinnedVMsperCPU[VCPU_per_numa_index]=oldvalue+1
                                            if VMNAME not in myvCPUperNUMA_pinnedvms[VCPU_per_numa_index]:
                                                myvCPUperNUMA_pinnedvms[VCPU_per_numa_index].append(VMNAME)

                                    else:
                                        CrossNumaUsage=True
                                if DEBUG==1:
                                    print("\tDEBUG8: Numa {:} Load After ={:}".format(myNUMAidstring,myvCPUperNUMAload))
                                    print("\tDEBUG8: Numa {:} Pinn After ={:}".format(myNUMAidstring,myNofPinnedVMsperCPU))

                                if CrossNumaUsage:
                                        print("---------------------------------------------------------------------")
                                        ErrString="ERROR instance {:} with VMName = {:} , IS_CPUPINNED={:}  uses :".format(myInstance,VMNAME,VM_IS_CPU_PINNED)
                                        ErrString+=("\tvcpu {:}  as per VMUsesList {:} ".format(vcpu,myVMusesList))
                                        ErrString+="\tnot existing in numa VCPUs for compute  {:}, numa  {:}, NUMA CPU list={:} ".format(nodo, myNUMAidstring,myvCPUperNUMAlist)
                                        if VM_IS_CPU_PINNED:
                                            pars.cast_error("00305", ErrString)
                                        else :
                                            pars.cast_error("00306", ErrString)
                                        print(ErrString)
                                    

                #SRC=input("Continue?")

                # For each VCPU in this NUMA
                TotalCPULoadPerNUMA=0
                cast_pinned_overlap=False

                for myVCPUindex in range(len(myvCPUperNUMAlist)):
                    TotalCPULoadPerNUMA+=round(myvCPUperNUMAload[myVCPUindex],2)
                    if myNofPinnedVMsperCPU[myVCPUindex]>1:
                        WarningString+="vCPU "+str(myVCPUID)+" used by "+str(len(myvCPUperNUMA_vms[myVCPUindex]))+" VMs"
                        ErrString=",".join(myvCPUperNUMA_vms[myVCPUindex]) +" using same vCPUs "+str(myVCPUID)+" on NUMA "+myNUMAidstring
                        pars.cast_error("00302",ErrString)

                for myVCPUindex in range(len(myvCPUperNUMAlist)):
                    myVCPUID=myvCPUperNUMAlist[myVCPUindex]
                    myVMsusingthisvCPU=myvCPUperNUMA_vms[myVCPUindex]

            #"HW_VCPU_REPORT_KEYS":["TimeStamp", "Site", "AZ", "Rack", "HypervisorHostname", "NUMA_id",
            # "vCPUsAvailPerNUMA","vCPUsUsedPerNUMA","vCPU_id", "NOfVMs","VM_names","Warning"],
                    self.addemptyrecord()
                    self.UpdateLastRecordValueByKey( "TimeStamp",timestamp)
                    self.UpdateLastRecordValueByKey( "Site",site_name)
                    AGGS =dictarray_object.cmpt_to_agglist(nodo_longformat)
                    self.UpdateLastRecordValueByKey( "AZ",AGGS[0])               
                    self.UpdateLastRecordValueByKey( "Rack",rack)
                    self.UpdateLastRecordValueByKey( "HypervisorHostname",nodo_longformat)
                    self.UpdateLastRecordValueByKey( "NUMA_id",myNUMAidstring)
                    self.UpdateLastRecordValueByKey( "vCPUsAvailPerNUMA",len(myvCPUperNUMAlist))
                    self.UpdateLastRecordValueByKey( "vCPUsUsedPerNUMA",round(TotalCPULoadPerNUMA,2))
                    self.UpdateLastRecordValueByKey( "vCPU_Load_after",myvCPUperNUMAload[myVCPUindex])

                    self.UpdateLastRecordValueByKey( "vCPU_id",myVCPUID)
                    self.UpdateLastRecordValueByKey( "NOfVMs",len(myVMsusingthisvCPU))
                    self.UpdateLastRecordValueByKey( "NofPinnedVMs",myNofPinnedVMsperCPU[myVCPUindex])

                    self.UpdateLastRecordValueByKey( "VM_names",myVMsusingthisvCPU) 
                    WarningString=""
                    if myNofPinnedVMsperCPU[myVCPUindex]>1:
                        WarningString="vcpu: {:} used by {:} CPU-pinned-VMs".format(myVCPUID,myNofPinnedVMsperCPU[myVCPUindex])
                        self.UpdateLastRecordValueByKey( "Warning",WarningString) 

                    #if myVCPUID in myvmcpus_onwrongNUMA:
                    #    WarningString+=",".join(myinstances_withcpuonwrongNUMA)+" using vCPUs on wrong numa"
                    #    pars.cast_error("00305",WarningString)
                
        #print("---------------------------------------------------------------------")
        #print("DEBUG produce_hw_vcpu_report: ")

        #self.print_report(pars)
        #exit(-1)
    
                        