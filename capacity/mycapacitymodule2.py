
#from asyncore import file_dispatcher
import json
import string
import sys
import glob
import os
import itertools
import math
import operator
from   datetime import datetime
from mycapacitymodule import *

class vm_report(report):

    def __init__(self):
        super().__init__()
        self.ReportType=super().ReportType_VM
        self.ReportTotalUsage=[]
        # VM REPORT is used as the source (for the capacity-status.py, also for the destination) to create the complete report (LIST of LISTS, one list per VM) of VMs in that site; these are the report keys
        self.VM_REPORT_KEYS = ("TimeStamp", "Site",  "Rack", "HypervisorHostname", "vCPUsAvailPerHV", "vCPUsUsedPerHV", "MemoryMBperHV",
                    "MemoryMBUsedperHV", "AZ", "HostAggr", "Project", "VMname", "Flavor", "vCPUsUSedPerVM", 
                    "RAMusedMBperVM", "CephPerVMGB","TargetHostAggr", "Lineup","vnfname", "vnfcname", "Warning")
        self.VM_REPORT_SORTINGKEYS = ["Project" , "AZ", "HypervisorHostname","vnfname", "vnfcname" , "Flavor"]



    # -----------------------------------------------------------------------
    # Transforms dict array into REPORT array 2d - VM level - one line = 1 list = 1 VM 
    # -----------------------------------------------------------------------
    def produce_vm_report(self,pars,dictarray_object):
        # -----------------------------------------------------------------------
        # EXTRACTS FLAVOR PLACEMENT ZONE FROM FLAVOR PROPERTIES RECORD
        # -----------------------------------------------------------------------
        def parse_flavor_properties(pars,flavorrecord,minidict):
            try:
                stringa1 = flavorrecord["Properties"]
            except KeyError as e:
                print("ERROR in parse_flavor_properties: flavor {} does not have properties to parse!! Using EXT as default Host Aggregate for this flavor")
                retval="DT_NIMS_EXT"
                return retval
            lista1 = stringa1.split(',')
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
                for x in  myvalues:
                    index=myvalues.index(x)
                    minidict[mykeys[index]]=x
                #print(json.dumps(minidict,indent=22))
                if "vnf_type" in minidict.keys():
                    retval=minidict["vnf_type"]
                else:
                    retval='None'
            except:
                if pars.is_silentmode()==False:
                    print("ERROR in parse_flavor_properties: {}".format(flavorrecord))
                retval='None'  
        
            return retval

    # -----------------------------------------------------------------------
    # Transforms dict array into REPORT array 2d - VM level - one line = 1 list = 1 VM 
    # -----------------------------------------------------------------------
        SUFFISSO=pars.paramsdict["SUFFISSOSRC"]

        #if pars.paramsdict["SILENTMODE"]==False:
        #    pars.myprint("REPORT KEYS \n {:s} \n".format( json.dumps(self.get_keys())))


        #FLAVOR_LIST=dictarray_object.DICT_ARRAY[3]
        #VOLUME_LIST=dictarray_object.DICT_ARRAY[4]

        TEMP_RES=[]
        minidict={}
        for item in [ x for x in dictarray_object.HYPERVISOR_LIST if x["State"] == "up"]:
                nodo = str(item["Hypervisor Hostname"])
                nomecorto = str(item["Hypervisor Hostname"].split('.')[0])
                site_name = str(item["Hypervisor Hostname"].split('.')[1])
                TEMP_RES=[]

                for PROGETTO in dictarray_object.SERVERDICT:

                    str_PROGETTO=str(PROGETTO)
                    if str_PROGETTO in pars.paramsdict["SERVICE"] or "ALL" in pars.paramsdict["SERVICE"]:
                        for VM in [ x for x in dictarray_object.SERVERDICT[PROGETTO] if x["Host"] == item["Hypervisor Hostname"]]:
                            TMP_RES=self.addemptyrecord()

                            AGGS = self.cmpt_to_agglist(nodo, dictarray_object.AGGREGATE_LIST)
                            AZNAME = str(AGGS[0])
                            HOSTAGGNAME =AGGS[1:]
                            suffissobreve=str(SUFFISSO[0:14])


                            # NEW UPDATE METHOD BY KEY
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
                            self.UpdateLastRecordValueByKey( "vnfname",self.split_vnfname(VM["Name"],"vnf"))
                            self.UpdateLastRecordValueByKey( "vnfcname",self.split_vnfname(VM["Name"],"vnfc"))
                            
                            FOUNDFLAVOR=False
                            Warning=''
                            for y in dictarray_object.FLAVOR_LIST:
                                str_FLAVOR=str(y["ID"])
                                str_VMFLAVORNAME=str(y["Name"])
                                str_FLAVORHOSTAGGR=parse_flavor_properties(pars,y,minidict)
                                if str_FLAVOR == str_VMFLAVORID:
                                    if len(str_VMFLAVORID)==0:
                                        #TEMP_RES.append("MISSINGVMFLAVORID")
                                        self.UpdateLastRecordValueByKey( "Flavor","!! MISSING FLAVOR ID")
                                    else:
                                        if len(str_VMFLAVORNAME)==0:
                                            #TEMP_RES.append("<no name> FlavorID="+str_VMFLAVORID)
                                            self.UpdateLastRecordValueByKey( "Flavor","<no name> FlavorID="+str_VMFLAVORID)
                                            self.UpdateLastRecordValueByKey( "Warning","MissingFlavorNameOnly")

                                            Warning+="MissingFlavorNameOnly; "
                                        else:
                                            #TEMP_RES.append(str_VMFLAVORNAME)	
                                            self.UpdateLastRecordValueByKey( "Flavor",str_VMFLAVORNAME)

                                    #TEMP_RES.append(y["VCPUs"])
                                    #TEMP_RES.append(y["RAM"])
                                    #TEMP_RES.append(y["Disk"])
                                    #TEMP_RES.append(str_FLAVORHOSTAGGR)

                                    self.UpdateLastRecordValueByKey( "vCPUsUSedPerVM",y["VCPUs"])
                                    self.UpdateLastRecordValueByKey( "RAMusedMBperVM",y["RAM"])
                                    self.UpdateLastRecordValueByKey( "CephPerVMGB",y["Disk"])
                                    self.UpdateLastRecordValueByKey( "TargetHostAggr",str_FLAVORHOSTAGGR)

                                    #TEMP_RES.append(self.split_vnfname(VM["Name"],"Lineup"))
                                    #TEMP_RES.append(self.split_vnfname(VM["Name"],"vnf"))
                                    #TEMP_RES.append(self.split_vnfname(VM["Name"],"vnfc"))

                                    #self.appendnewrecord(TEMP_RES)
                                    TEMP_RES=[]
                                    FOUNDFLAVOR=True
                                    break

                            if FOUNDFLAVOR==False:	
                                Warning += "ERROR: FlavorID not present"
                                #TEMP_RES.append(str(VM["Flavor Name"]+ " n/a"))
                                #TEMP_RES.append("n/a")
                                #TEMP_RES.append("n/a")
                                #TEMP_RES.append("n/a")
                                #TEMP_RES.append(Warning)

                                self.UpdateLastRecordValueByKey( "Flavor",str(VM["Flavor Name"]+ " n/a"))
                                self.UpdateLastRecordValueByKey( "vCPUsUSedPerVM","n/a")
                                self.UpdateLastRecordValueByKey( "RAMusedMBperVM","n/a")
                                self.UpdateLastRecordValueByKey( "CephPerVMGB","n/a")
                                self.UpdateLastRecordValueByKey( "Warning","ERROR: FlavorID not present")

                                #self.appendnewrecord(TEMP_RES)
                                TEMP_RES=[]
class menu_report(menu,report):

    def __init__(self):
        self.ReportType=super().ReportType_MENU
        self.ReportTotalUsage=[]
        self.MENU_REPORT_KEYS=("Item","Site","Date","Suffix","Projects")
        self.MENU_REPORT_SORTINGKEYS= ["Item"]
        screenrows, screencolumns = os.popen('stty size', 'r').read().split()
        self.ScreenWitdh=int(screencolumns)
        self.SVCNOTTOSHOW = ("service", "admin", "tempest", "c_rally", "DeleteMe", "Kashif")
        super().__init__()
    
    #--------------------------------------------------------------------
    # GET LIST OF FILES TO USE IN MENU
    #--------------------------------------------------------------------
    def get_fileslist(self, params, prompt):
        MenuReport= menu_report()
        if True:
            cleanlist = []
            sortedlist=[]
            files = os.listdir(params.PATH)
            files_txt = [i for i in files if i.endswith('.json')]
            for FileName in files_txt:
                for FileTypeName in params.FILETYPES:
                    p = FileName.find(FileTypeName)
                    if p > -1:
                        cleanlist.append(FileName[p+len(FileTypeName)+1:FileName.find('.json')])
            cleandict = dict.fromkeys(cleanlist)
            cleanlist = []
            cleanlist = list(cleandict)
            index = 0
            newlist = []
            for FileName in cleanlist:
                if len(FileName) == 20:
                # NOTE: STG810 does not show stg810 in the suffix as the cc-jumphost hostname is configured wrongly.
                    site = FileName[14:]
                    date = FileName[:14]
                    shortdate = MenuReport.tstoshortdate(FileName)
                else:
                    site = "stg810"
                    date = FileName[:14]
                shortdate = MenuReport.tstoshortdate(FileName)
                newrecord = []
                newrecord.append(index)
                newrecord.append(site)
                newrecord.append(date)
                newrecord.append(FileName)
                newrecord.append(self.load_svcs_by_prefix(params,FileName))
                newlist.append(newrecord)
        # SORT THE LIST OF SITE:DATE files (by suffixes)  by DATE+SITENAME
            index = 0
            sortedlist = sorted(newlist, key=lambda x: x[2]+x[1], reverse=True)
            MenuReport.Report = sorted(newlist, key=lambda x: x[2]+x[1], reverse=True)

        # PREPARE THE LIST OF ITEMS
            for Record in MenuReport.Report :
                Record[MenuReport.get_keys().index("Item")] = index
                counter = Record[MenuReport.get_keys().index("Item")]
                sitename = Record[MenuReport.get_keys().index("Site")]
                TimestampValue = Record[MenuReport.get_keys().index("Date")]
                shortdate = MenuReport.tstoshortdate(TimestampValue)
                filesuffix = Record[3]
                ListOfProjectsPerSite =  Record[MenuReport.get_keys().index("Projects")]
                PerSiteHeader = "  {:2d} - {:6s} - {:10s} - ".format(counter, sitename, shortdate)
                line = ""
                linelen = 0
                self.PerSiteWidth = len(PerSiteHeader)


                for ProjectInThisSite in ListOfProjectsPerSite:
                    ProjectName="{0:"+str(self.WidthOfEachProjectName)+"}"
                    item = ProjectName.format(ProjectInThisSite[0:self.WidthOfEachProjectName])
                    linelen += len(item)
                    line += item
                    remaining_space=self.ScreenWitdh - linelen
                    
                    prjspersite="\n{0:"+str(self.PerSiteWidth+1)+"s}"
                    if linelen > self.ScreenWitdh-self.PerSiteWidth-self.WidthOfEachProjectName:
                        line += prjspersite.format(" ")
                        linelen = 0
                string2 = "{:s}".format(line)

                stringa3 = "{:s} {:s}".format(PerSiteHeader, string2)

                TMPREC = []
                TMPREC.append(stringa3)
                self.UILIST.append(TMPREC)
                index += 1
        return self.print_menu(sortedlist,prompt)



    # ----------------------------------------------------------
    # - ----- PARSE ARGS AND DEFINE LEVEL OF USER INTERACTIVITY -------
    # this function defines which user inputs to request in user interactive mode based on command line arguments provided
    #
    def parse_args(self,input,output, src_da, dst_da):
        # ----------------------------------------------
        # this function is used to fetch - for a suffix - the list of files to use 
        def get_destfiles_to_scan(self):
            # ----------------------------------------------
            # TRUE if site  == mgmt site
            def ismgmtsite(suffix):
                if len(suffix)==14 or suffix[14:]=='ber800' or suffix[14:]=='stg810':
                    return True
                else:
                    return False
            # ----------------------------------------------

            cleanlist=[]
            files=os.listdir(output.PATH)

            files_txt = [i for i in files if i.endswith('.json') and (i.find(output.paramsdict["SUFFISSODST"])>-1 and (output.paramsdict["SKIPMGMTSITE"]==False or ismgmtsite(i)==False))]
            for x in files_txt:
                for y in output.FILETYPES:
                    p=x.find(y)
                    if p>-1:
                        value = x[p+len(y)+1:x.find('.json')]
                        condition3= output.paramsdict["SKIPMGMTSITE"]==False or ismgmtsite(value)==False
                        if condition3:
                            cleanlist.append(value)
            cleandict=dict.fromkeys(cleanlist)
            cleanlist=[]
            cleanlist=list(cleandict)
            if len(cleanlist)==0:
                print("ERROR : no Openstack JSONs files found in ./JSON folder.. exiting")
                exit(-1)
            return(cleanlist)


        # ----------------------------------------------------------
        # PARSE ARGUMENTS PASSED TO COMMAND
        # ----------------------------------------------------------
        q=0
        l=0
        try:
            # First all command line arguments are parsed into a  dict (based on their type)
            for x in input:
                if q>0:
                    if x.find("=")==-1:
                        key=output.paramslist[l]
                        value=x
                        l+=1
                    else:
                        key=x.split("=")[0]
                        val=x.split("=")[1]
                        if type(output.paramsdict[key]) is bool:
                            output.paramsdict[key]=val.upper()=='TRUE'
                            #print(MyPARAMSDICT.paramsdict[key])
                        elif type(output.paramsdict[key]) is list:
                            mylist=val.split(",")
                            for y in mylist:
                                output.paramsdict[key].append(y)
                        else:
                            output.paramsdict[key]=val
                q+=1

        except: 
            print("ERROR - parse_args - The following command line parameter is not correct : {:s}".format(x))
            exit(-1)
        l+=1

        # If SUFFISSOSRC CLI argument is not present, the User Interface fetching the input is shown and user input is returned to the parameters dict
        if len(output.paramsdict["SUFFISSOSRC"])==0:
            src_parname = "SUFFISSOSRC"
            output.paramsdict[src_parname]=self.get_fileslist(output, "Source site")
            # in order for the services in each site:suffix to be shown, the array of dicts with all the json must be loaded first
            src_da.load_jsons_into_dictarrays(output,src_parname)
        else:
            src_parname = "SUFFISSOSRC"
            src_da.load_jsons_into_dictarrays(output,src_parname)

        if output.paramsdict["JUSTSOURCE"]==False:        
            if len(output.paramsdict["SUFFISSODST"])==0:
                output.paramsdict["SUFFISSODST"]=self.get_fileslist(output, "Destination site")
                output.DSTSITES.append(output.paramsdict["SUFFISSODST"])
            else:
                    if output.paramsdict["DESTSCAN"]==True:
                        for a in get_destfiles_to_scan():
                            output.DSTSITES.append(a)
                            output.paramsdict["DESTSITESLIST"].append(a)
                            output.paramsdict["SUFFISSODST"]=output.DSTSITES[0]
                    else:
                        output.DSTSITES.append(output.paramsdict["SUFFISSODST"])
            # in order for the services in each site:suffix to be shown, the array of dicts with all the json must be loaded first   
            dst_parname = "SUFFISSODST"
            dst_da.load_jsons_into_dictarrays(output,dst_parname)

        # so that the name(s) of the Services can be either assigned or user selected
        if len(output.paramsdict["SERVICE"])==0:
            src_da.load_jsons_into_dictarrays(output,src_parname)
            output.paramsdict["SERVICE"]=src_da.get_src_prj(output,self )

        output.myprint("------------------ LIST OF PARAMETER ARGUMENTS ---------------------------")	
        output.myprint(json.dumps(output.paramsdict,indent=22))

        return l
    

    def load_svcs_by_prefix(self, params, SUFFISSO):
    # --------------------------------------------------------------
    # Load site data files and finds the list of projects (and total vCPUs for each) in each site:suffix
            COUNT=0
            RESULT=[]

            try:
                    ITEM="server_dict"
                    FILENAME = params.PATH + "/"+ "openstack_" + ITEM + "_" + SUFFISSO +  ".json"
                    with open(FILENAME, 'r') as file1:
                            LOCALSERVERDICT= json.load(file1)
                    ITEM="flavor_list"
                    FILENAME = params.PATH + "/"+ "openstack_" + ITEM + "_" + SUFFISSO +  ".json"
                    with open(FILENAME, 'r') as file1:
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


                                            RESULT.append(str(PROGETTO)+"("+str(VCPU_PER_PRJ)+")")
            except (IOError, EOFError) as e:
                    print("ERROR - file {:s} does not exist".format(FILENAME))
                    exit(-1)
            return sorted(RESULT)
class hw_report(report):
    def __init__(self):
        super().__init__()
        self.ReportType=super().ReportType_HW
        self.ReportTotalUsage=[]
        self. HW_REPORT_KEYS = ("TimeStamp", "Site", "Rack", "HypervisorHostname", "vCPUsAvailPerHV", "vCPUsUsedPerHV", 
                        "MemoryMBperHV", "MemoryMBUsedperHV", 
                        "AZ", "HostAggr", 
                        "ExistingVMs","NewVMs", "Warning")
        self.HW_REPORT_SORTINGKEYS = ["AZ" , "HypervisorHostname"]


    # ---------------------------------------------------------------------------------------------------
    # Produces a report (list of lists); one row per hardware compute based on the global ARRAY of (list,dict) passed as parameter. 
    # ---------------------------------------------------------------------------------------------------
    def produce_hw_report(self,pars, dst_dictarray_object ):
            SUFFISSO = pars.paramsdict["SUFFISSODST"]
            self.Report=[]
            TEMP_RES=[]
            #("TimeStamp", "Site", "Rack", "HypervisorHostname", "vCPUsAvailPerHV", "vCPUsUsedPerHV", "MemoryMBperHV", "MemoryMBUsedperHV", "AZ", "HostAggr")
            for item in [ x for x in dst_dictarray_object.HYPERVISOR_LIST if x["State"] == "up"]:
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
                  
                AGGS =self.cmpt_to_agglist(nodo, dst_dictarray_object.AGGREGATE_LIST)
                self.UpdateLastRecordValueByKey( "AZ",AGGS[0])               
                self.UpdateLastRecordValueByKey( "HostAggr",AGGS[1:]) 

                # DESTINATIONWIPE Parameter implementation
                if pars.paramsdict["DESTINATIONWIPE"]==True:
                    self.UpdateLastRecordValueByKey( "vCPUsUsedPerHV",0)
                    self.UpdateLastRecordValueByKey( "MemoryMBUsedperHV",0)
                    EmptyVMList=[]
                    self.UpdateLastRecordValueByKey( "ExistingVMs",EmptyVMList) 
                else:
                    self.UpdateLastRecordValueByKey( "vCPUsUsedPerHV",item["vCPUs Used"])
                    self.UpdateLastRecordValueByKey( "MemoryMBUsedperHV",item["Memory MB Used"])  
                    #self.UpdateLastRecordValueByKey( "ExistingVMs",WHATTODO??)               
                    self.UpdateLastRecordValueByKey( "ExistingVMs",dst_dictarray_object.get_vms_by_computenode(nodo)) 

                EmptyVMList=[]
                self.UpdateLastRecordValueByKey( "NewVMs",EmptyVMList) 
 # -----------------------------------------------------------------------------------------------------
    #
    #----------------------        AUTOOPTIMIZE RACKS TO AZ ALLOCATION      -------------------------------
    #
    #------------------------------------------------------------------------------------------------------
    def optimize_AZRealignment_in_HWReport(self, pars, MyRackReport,  metric_formula): #sort_formula,
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
            print("ERROR in optimize_AZRealignment_in_HWReport : length of HW report = 0 entries ")
            exit(-1)
        #print(self[0])

        SUFFISSO = pars.paramsdict["SUFFISSODST"]
        stringalinea1 = '{0:_^'+str(pars.ScreenWitdh)+'}'

        #Initialize and produce RACK REPORT . Initialize report for optimixzation results
        pars.myprint (stringalinea1.format(menu.Yellow+SUFFISSO+"  initial layout "+str(SUFFISSO)))
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
        pars.myprint("\tCurrent Metric Value: {:.2f}".format(CurrentMetricValue))
        pars.myprint (stringalinea1.format(menu.Yellow))
        racks=MyRackReport.get_column_by_key("Rack")

        UsageLoadForCurrentRackToAZPerm=[]
        returnarray=[]

        NumberOfAZs = len(racks)/MyRackReport.RacksPerAZ
        if NumberOfAZs-math.floor(NumberOfAZs)>0:
            print(" ERROR -- optimize_AZRealignment_in_HWReport : Number of racks is {:d} vs RacksPerAZ is {:d}".format(len(racks,MyRackReport.RacksPerAZ)))
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
        pars.myprint (stringalinea1.format("\n"+menu.FAIL+ pars.parse_suffisso(SUFFISSO)+menu.Yellow+" -->  brute force scan on rack pairs to optimize AZ resource distribution, based on metric : "+metric_formula+menu.Yellow+" "))

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

            pars.myprint(stringalinea1.format("\n"+menu.Yellow+ " OPTIMIZATION RESULTS "+menu.Yellow))
            pars.myprint("\nOPTIMIZATION OF RACKS DISTRIBUTION TO AZ: FINAL RACK LAYOUT:\n")
            pars.myprint("\tTOTAL MATCHING LAYOUTS ="+str(matches))
            pars.myprint("\tOPTIMIZED RACK LAYOUT:")
            pars.myprint(MyRackReport.Rack_Opt_Memory["rackslayout"])
            pars.myprint("\tDISTRIBUTION OF VCPUS:")
            pars.myprint(MyRackReport.Rack_Opt_Memory["azcpus"])
            MyRackReport.OUTPUTDICT[pars.parse_suffisso(SUFFISSO)]=MyRackReport.Rack_Opt_Memory
            MyRackReport.writeoptimizedrackstofile(pars)
            pars.myprint("\n\t\tREALIGNING RACKS TO AZ IN ACCORDANCE TO RACK-TO-AZ NEW MAP\n \t\tRACK TO AZ MAP={} METRIC={} SIGMA={}".format(MyRackReport.Rack_Opt_Memory["rackslayout"],metric_formula,MyRackReport.Rack_Opt_Memory["sigma2"]))
            pars.myprint (stringalinea1.format(menu.Yellow))

            returnarray.append(MyRackReport.Rack_Opt_Memory["rackslayout"])
            retval=self.after_opt_realign_racks_to_optimizedAZdistro_inHWReport(MyRackReport)
        except :
            print(sys.exc_info())
            print("ERROR in optimize_AZRealignment_in_HWReport : Exiting")
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
class rack_report(report):
    # REPORT USED TO STORE COMPUTED DATA DURING AZ OPTIMIZATION
    

    RacksPerAZ = 2

    def __init__(self):
        super().__init__()
        self.ReportType=super().ReportType_RACK
        self.Report=[]
        self.ReportTotalUsage=[]
        self.RACK_REPORT_KEYS=("Rack","AZ","NOfComputes","VCPUsAvailPerRack","RAMperRack","VCPUsUsedPerRack","RAMUsedperRack")
        self.RACK_REPORT_SORTINGKEYS =  ["AZ" , "Rack"]
        self.RacksPerAZ=2

        self.Rack_Opt_Memory={}
        self.OUTPUTDICT={}
        Rack_Opt_Memory={ "rackslayout":[],"azcpus":[],"sigma2":math.inf, "metric_formula":''}
        screenrows, screencolumns = os.popen('stty size', 'r').read().split()
        self.ScreenWitdh=int(screencolumns)
        self.RackReportKeyForOptimizationMetric='VCPUsAvailPerRack'



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

        nofcmpts_Rackindex=MyRackKeys.index("NOfComputes")
        vcpuavail_Rackindex=MyRackKeys.index("VCPUsAvailPerRack")
        ramavail_Rackindex=MyRackKeys.index("RAMperRack")
        vcpuused_Rackindex=MyRackKeys.index("VCPUsUsedPerRack")
        ramused_Rackindex=MyRackKeys.index("RAMUsedperRack")
        rack_Rackindex=MyRackKeys.index("Rack")
        az_Rackindex=MyRackKeys.index("AZ")

        self.Report=[]
        conta=0
        for myRecord in hwreportbox.Report:
            RackValueFromHWReport = myRecord[rack_hwindex]
            RackFound=False
            MyRackRecord=self.FindRecordByKeyValue("Rack",RackValueFromHWReport)
            
            #print(" {:d} --Compute {:s} .. found record {:}".format(conta,myRecord[cmpt_hwindex],MyRackRecord))
            conta+=1

            if len(MyRackRecord)==0 :
                self.addemptyrecord()
                #racks.append(RackValueFromHWReport)
                self.UpdateLastRecordValueByKey("Rack",RackValueFromHWReport)
                #azperrack.append(myRecord[azindex])
                self.UpdateLastRecordValueByKey("AZ",myRecord[az_hwindex])
                #cpuperrack.append(0)
                self.UpdateLastRecordValueByKey("VCPUsAvailPerRack",myRecord[vcpuavail_hwindex])                
                #ramperrack.append(0)
                self.UpdateLastRecordValueByKey("RAMperRack",myRecord[ramavail_hwindex])                
                #cpuperrack.append(0)
                self.UpdateLastRecordValueByKey("VCPUsUsedPerRack",myRecord[vcpuused_hwindex])                
                #ramperrack.append(0)
                self.UpdateLastRecordValueByKey("RAMUsedperRack",myRecord[ramused_hwindex])
                self.UpdateLastRecordValueByKey("NOfComputes",1)
            else:
                MyRackRecord[vcpuavail_Rackindex]+=myRecord[vcpuavail_hwindex]
                MyRackRecord[ramavail_Rackindex]+=myRecord[ramavail_hwindex]
                MyRackRecord[vcpuused_Rackindex]+=myRecord[vcpuused_hwindex]
                MyRackRecord[ramused_Rackindex]+=myRecord[ramused_hwindex]
                MyRackRecord[nofcmpts_Rackindex]+=1




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
        if len(pars.paramsdict["AZREALIGN"])==0:
            #print(" ### DEBUG - no AZ realign parameter passed to select input file for Rack to AZ realignment")
            return dst_report
        try:
            FILENAME=pars.PATH+'/azrealign_targetracklayout_'+pars.paramsdict["AZREALIGN"]+".json"
            with open(FILENAME,'r') as file1:
                AZRealign=json.load(file1)
                pars.myprint( json.dumps(AZRealign, indent=22))
        except (IOError,EOFError) as e:
            print(" ERROR - file {:s} not found for Rack to AZ realignment".format(pars.paramsdict["AZREALIGN"]))
            exit(1)

        sitename = pars.parse_suffisso(pars.paramsdict["SUFFISSODST"])
        try:
            NEWAZMAP=dict(AZRealign[sitename])
            #print("DEBUG azrealign2:",json.dumps(NEWAZMAP,indent=22))
        except (KeyError) as e:
            print(" --- ERROR : in file {:s} for AZ realignment, the site {:s} has no data for AZ realignment: Rack to AZ mapping is therefore unchanged!".format(MyPARAMSDICT.paramsdict["AZREALIGN"],sitename))
            return(dst_report)
        newracktoazmap={}
        for i in range(len(AZRealign[sitename]["rackslayout"])):
            racknum=AZRealign[sitename]["rackslayout"][i]
            aznum=int(i/2)+1
            azname = "DT_NIMS_AZ"+str(aznum)
            newracktoazmap[racknum]=azname
        #print(json.dumps(newracktoazmap,indent=22))

        for ITEM in dst_report.Report:
            AZINREP=ITEM[dst_report.get_keys().index("AZ")]
            RACKINREP=int(ITEM[dst_report.get_keys().index("Rack")])
            ITEM[dst_report.get_keys().index("AZ")]= newracktoazmap[str(RACKINREP)]

        return AZRealign[sitename]["rackslayout"]
            #print("DEBUG3 - ", newracktoazmap[str(RACKINREP)])
    #        for NEWITEM in NEWAZMAP:
    #            if RACKINREP in NEWAZMAP.get(NEWITEM):
    #                ITEM[HW_REPORT_KEYS.index("AZ")]=str(NEWITEM)
                                # print(" ---- REPORT RACK={:d} NEWRACKS={} ----- >{:b}--- REPLACE: {:s} with {:s} ?".format(RACKINREP,NEWAZMAP.get(NEWITEM),int(RACKINREP) in NEWAZMAP.get(AZINREP), AZINREP,NEWITEM))


    # --------------------------- WRITE OPTIMIZED RACK LAYOUT TO FILE
    def writeoptimizedrackstofile(self, pars):
        FILENAME=pars.PATH+'/'+'azrealign_targetracklayout_'+'OUTPUT'+'.json'
        memorydict=self.OUTPUTDICT
        suffix=pars.paramsdict["SUFFISSODST"]
        if len(memorydict)==0:
            pars.myprint("WARNING writeoptimizedrackstofile: no data in optimized rack layout dict: skipping appending data to {} ".format(FILENAME))
            return False
        sitename=pars.parse_suffisso(suffix)
        pars.myprint(json.dumps(memorydict,indent=22))
        with open(FILENAME,'w') as file1:
            json.dump(memorydict,file1)
            file1.close
        return True

class totalresults_report(report):

    def __init__(self):
        self.TOTALRESULTS_REPORT_KEYS=("Capacity-fits","SourceSuffix", "DestinationSuffix","Service","vCPU_Load_after","Outcome")
        self.TOTALRESULTS_REPORT_SORTINGKEYS=["Capacity-fits"]
        self.ReportType=super().ReportType_TOTALRESULTS
        self.ReportTotalUsage=[]
        self.Report=[]
        super().__init__()
    
    # ----------------------------------------------------------------------------------------------------------------------------------------
    # PRODUCE TOTAL REPORT
    # ----------------------------------------------------------------------------------------------------------------------------------------
    def check_capacity_and_produce_Total_Report(self, pars,  SRC_REPORTBOX, DST_REPORTBOX, metric_formula, myoptimizedrackrecord):
        
        destsitename = pars.parse_suffisso(pars.paramsdict["SUFFISSODST"])
        MODE_OF_OPT_OPS = pars.get_azoptimization_mode()
        
        # Now check if instantiation fits in the newly adjusted report
        DST_REPORTBOX.check_capacity(pars, SRC_REPORTBOX, self)

        return


