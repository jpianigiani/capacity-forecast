
#from asyncore import file_dispatcher
from email.header import Header
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


class dictarray:
    DICT_ARRAY = []
    AGGREGATE_LIST = []
    HYPERVISOR_LIST = []
    SERVERDICT = {}
    FLAVOR_LIST = []
    VOLUME_LIST = []

    def __init__(self):
        DICT_ARRAY = []
        AGGREGATE_LIST = []
        HYPERVISOR_LIST = []
        SERVERDICT = {}
        FLAVOR_LIST = []
        VOLUME_LIST = []

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
            FILENAME = pars.PATH + "/" + "openstack_" + ITEM + "_" + value + ".json"

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
            " SERVICES AVAILABLE IN SITE "+pars.paramsdict["SUFFISSOSRC"]))
        for x in sortedres:
            print("- {:2d} --- {:20s}".format(index, x))
            index += 1

        src = str(input("Enter source SERVICES separated by <space>:"))
        print("--------------------------------------")
        print(src)
        lista = [int(i) for i in src.split(' ') if i.isdigit()]
        res = []
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

class report:
    # GENERAL - Length of Each KEY in SOURCE REPORT
    FIELDLENGTHS = {"TimeStamp": 10, "Site": 6, "Rack": 3, "HypervisorHostname": 15, 
                    "vCPUsAvailPerHV": 4, "vCPUsUsedPerHV": 4, "MemoryMBperHV": 7,"MemoryMBUsedperHV": 7, 
                    "AZ": 3, "HostAggr": 6,
                    "Project": 26, "VMname": 32, "Flavor": 30, 
                    "vCPUsUSedPerVM": 3, "RAMusedMBperVM": 6, "CephPerVMGB": 6,
                    "TargetHostAggr": 4,
                    "NewVMs": 100, "ExistingVMs":120,
                    "VCPUsAvailPerRack": 4, "RAMperRack": 8, "VCPUsUsedPerRack":4, "RAMUsedperRack" :8, "NOfComputes":5,
                    "Lineup": 4, "vnfname": 4, "vnfcname": 5,
                    "Capacity-fits": 4, "SourceSuffix": 20,"DestinationSuffix": 20, "Service": 20, "Outcome": 60, 
                    "vCPU_Load_after": 6 ,
                    "Item": 3, "Date": 10, "Suffix": 20, "Projects": 20, "Warning": 10, 
                    "default":10
                    }
    FIELDLISTS = [ "HostAggr", "NewVMs", "ExistingVMs"]

    # GENERAL - Function applied during printing of report on each field to transform output
    FIELDTRANSFORMS = {"TimeStamp": 'self.tstoshortdate(value)',
                       "Site": "value",
                       "Rack": 'value.rjust(length)',
                       "HypervisorHostname": 'value[13:28]',
                       "vCPUsAvailPerHV": 'value',
                       "vCPUsUsedPerHV": "value.rjust(length)",
                       "MemoryMBperHV": 'self.mem_show_as_gb(value.rjust(length), True)',
                       "MemoryMBUsedperHV": "self.mem_show_as_gb(value.rjust(length), True)",
                       "AZ": 'self.shorten_az(value).rjust(length)',
                       "HostAggr": 'self.shorten_hostaggs(value).rjust(1)',
                       "Project": 'value.rjust(length)',
                       "VMname": 'value.rjust(length)',
                       "Flavor": 'value.rjust(length)',
                       "vCPUsUSedPerVM": 'value.rjust(length)',
                       "RAMusedMBperVM": "self.mem_show_as_gb(value.rjust(length), True)",
                       "CephPerVMGB": 'self.mem_show_as_gb(value.rjust(length),False)',
                       "TargetHostAggr": 'self.shorten_hostaggs(value).rjust(length)',
                       "ExistingVMs": "self.split_vnfname(value,'vnf-vnfc')+ ' '",
                       "NewVMs": '(value).ljust(10)',
                       "VCPUsPerRack": 'value.ljust(length)',
                       "RAMperRack": "self.mem_show_as_gb(value.ljust(length), True)",
                        "VCPUsUsedPerRack": 'value.ljust(length)',
                       "RAMUsedperRack": "self.mem_show_as_gb(value.ljust(length), True)",
                       "VCPUsUsedPerRack": 'value.ljust(length)',
                       "RAMUsedperRack": "self.mem_show_as_gb(value.ljust(length), True)",
                       "Lineup": "value.rjust(length)",
                       "vnfname": "value.rjust(length)",
                       "vnfcname": "value.rjust(length)",
                       "NOfComputes":"value.rjust(length)",
                       "default": "value.rjust(length)"}

    ReportType_VM = "VM"
    ReportType_HW = "HW"
    ReportType_RACK = "RACK"
    ReportType_TOTALRESULTS = "TOTALRESULTS"
    ReportType_MENU = "MENU"

    ReportTypesList = (ReportType_VM, ReportType_HW, ReportType_RACK,
                       ReportType_TOTALRESULTS, ReportType_MENU)
    ReportKeys = ["VM_REPORT_KEYS",
                  "HW_REPORT_KEYS",
                  "RACK_REPORT_KEYS",
                  "TOTALRESULTS_REPORT_KEYS",
                  "MENU_REPORT_KEYS",
                  "HW_VM_REPORT_KEYS"]

    ReportSortingKeys = ["VM_REPORT_SORTINGKEYS",
                         "HW_REPORT_SORTINGKEYS",
                         "RACK_REPORT_SORTINGKEYS",
                         "TOTALRESULTS_REPORT_SORTINGKEYS",
                         "MENU_REPORT_SORTINGKEYS",
                         "HW_VM_REPORT_SORTINGKEYS"]
    Report = []
    ReportTotalUsage = []

    def __init__(self):
        self.Report = []
        self.ReportTotalUsage = []

    def get_sorting_keys(self):
        try:
            return eval("self."+self.ReportSortingKeys[self.ReportTypesList.index(self.ReportType)])
        except:
            print("__ ERROR __ get_sorting_keys__ reporttype = {} List of vars = {}".format(
                self.ReportType, self.ReportSortingKeys))

    def get_keys(self):
        try:
            return eval("self."+self.ReportKeys[self.ReportTypesList.index(self.ReportType)])
        except:
            print("__ ERROR __ get_keys__ reporttype = {} List of vars = {}".format(
                self.ReportType, self.ReportKeys))

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
        pars.myprint(MyLine.format(str(self.__class__)))
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
                pars.myprint(stringa1.format(myline))
            
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
            pars.myprint(menu.Yellow)
        
        print_keys_on_top_of_report(self)

        for record in self.Report:
            myline = ''
            myformat = ''

            for row_itemnumber in range(self.keys_length()):
                # Fetches each item in the report row into initialvalue and gets what type it is, and what's the length of the output record (FIELDLENGTH)
                if row_itemnumber < len(record):
                    initialvalue = record[row_itemnumber]
                    mytype = type(initialvalue)
                    if row_itemnumber >= self.keys_length():
                        newelement = self.keys_length()-1
                    else:
                        newelement = row_itemnumber
                else:
                    initialvalue = '**'
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
                        myline += stringa1.format(eval(transform))
                        #myline += eval(transform) + " | "
                except:
                    myline += stringa2.format("## |")
            
            pars.myprint("{:s}".format(myline))

        return -1

    # SORT SOURCE REPORT IN ACCORDANCE TO SORTING KEYS
    def sort_report(self, sortkeys):
        try:
            reportkeys = self.get_keys()
            mykeys = []
            myfunc = ''
            for m in sortkeys:
                # GET THE INDEX OF EACH ITEM IN SORTINGKEYs
                val = reportkeys.index(m)
                mykeys.append('x['+str(val)+']')
            myfunc = ",".join(mykeys)
            # print(myfunc)
            # print(reportkeys)
            # print(len(reportkeys))

            self.Report.sort(key=lambda x: eval(myfunc))
        except:
            print("SORT_REPORT: Sorting Keys = {:} \nKeys = {:}".format(
                sortkeys, reportkeys))
            return -1

    def calculate_report_total_usage(self, pars):
        applicable_reporttypes = ['VM', "HW"]
        totvcpuavail = 0
        totvcpuused = 0
        if self.ReportType in applicable_reporttypes:
            for x in self.Report:
                totvcpuavail += x[self.get_keys().index("vCPUsAvailPerHV")]
                totvcpuused += x[self.get_keys().index("vCPUsUsedPerHV")]
                if totvcpuavail > 0:
                    usage = totvcpuused / float(totvcpuavail)
                else:
                    usage = 0
        else:
            usage = 0

        retval = []
        retval.append("TOTAL VCPU USAGE :")
        retval.append(str(int(usage*100))+"%")
        retval.append("TOTAL # OF OBJECTS :")
        retval.append(len(self.Report))
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

    # REMOVES DT_NIMS from AZ/hostaggs
    def shorten_hostaggs(self, x):
        value= x.replace("DT_NIMS_", "")
        return value[0]

    def shorten_az(self, x):
        value= x.replace("DT_NIMS_", "")
        return value

    # -------------- CHECK IF NETWORK SERVICE FITS INTO DEST SITE -----------------
    def check_capacity(self, pars, src, totalreport):

        def hostaggr_match(pars, hostaggr1, hostaggrlist2):
            if pars.paramsdict["IGNOREHOSTAGS"] == True:
                return True
            stringa1 = hostaggr1.upper()
            stringa2 = stringa1.replace("DTNIMS", "DT_NIMS")
            for x in hostaggrlist2:
                x.upper().replace("DTNIMS", "DT_NIMS")
            retval = stringa2 in hostaggrlist2
            return retval

        vmfits = False
        capacity_fit = []
        srcvm = []
        VMNAME = ''
        HOSTAGGRSET = []
        HOSTAGGRLIST = []

        # SORT VMs TO BE 'INSTANTIATED' by Project, VNF, VNFC
        SourceReportSortKeys = ["Project", "vnfname", "vnfcname"]
        src.sort_report(SourceReportSortKeys)

        SrcvCPUsUSedPerVMIndex = src.get_keys().index("vCPUsUSedPerVM")
        SrcRAMusedMBperVMIndex = src.get_keys().index("RAMusedMBperVM")
        SrcAZIndex = src.get_keys().index("AZ")
        SrcVMnameIndex = src.get_keys().index("VMname")
        SrcHostAggrIndex = src.get_keys().index("HostAggr")
        SrcTargetHostAggrIndex = src.get_keys().index("TargetHostAggr")

        DstvCPUsUsedPerHVIndex = self.get_keys().index("vCPUsUsedPerHV")
        DstMemoryMBUsedperHVIndex = self.get_keys().index("MemoryMBUsedperHV")
        DstvCPUAvailIndex = self.get_keys().index("vCPUsAvailPerHV")
        DstMemoryMBperHVIndex = self.get_keys().index("MemoryMBperHV")
        DstAZIndex = self.get_keys().index("AZ")
        DstHostAggrIndex = self.get_keys().index("HostAggr")
        DstNewVMsIndex = self.get_keys().index("NewVMs")

        # CLEAR NEW VMs on DST REPORT
        for dstcmp in self.Report:
            dstcmp[DstNewVMsIndex] = []


        # GO THROUGH ALL VMs in SOURCE REPORT ONE BY ONE....

        for srcvm in src.Report:

            VM_VCPUS = srcvm[SrcvCPUsUSedPerVMIndex]
            VM_RAM = srcvm[SrcRAMusedMBperVMIndex]
            VM_AZ = srcvm[SrcAZIndex]
            VM_VMNAME = srcvm[SrcVMnameIndex]
            VM_HOSTAGGRSET = set(srcvm[SrcHostAggrIndex])
            VM_HOSTAGGRLIST = list(HOSTAGGRSET)
            VM_HOSTAGGR = srcvm[SrcTargetHostAggrIndex]

            # SORT COMPUTES BY LEAST USED VCPU
            if pars.paramsdict["BESTVMDISTRO"]:
                sorted(self.Report,
                       key=lambda x: x[self.get_keys().index("vCPUsUsedPerHV")])

            vmfits = False
            result = []

            for dstcmp in [x for x in self.Report if hostaggr_match(pars, VM_HOSTAGGR, x[DstHostAggrIndex]) and VM_AZ in x[DstAZIndex]]:
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
                            self.split_vnfname(VM_VMNAME, "vnf-vnfc")))

                        vmfits = True
                        break
                    except:
                        print("DSTCMP Record:\n{:}".format(dstcmp))
                        print("DSTCMP DstNewVMsIndex:\n{:}".format(
                            DstNewVMsIndex))
        
        # CALCULATES THE % OF VCPU USED OVER TOTAL
        CumulativeVCPUUsed=0
        CumulativeVCPUAvail=0       
        for x in self.Report:
                hwcpu_total = dstcmp[DstvCPUAvailIndex]
                hwram_total = dstcmp[DstMemoryMBperHVIndex]
                hwcpu_used = dstcmp[DstvCPUsUsedPerHVIndex]
                hwram_used = dstcmp[DstMemoryMBUsedperHVIndex]
                CumulativeVCPUUsed+=hwcpu_used
                CumulativeVCPUAvail+=hwcpu_total
        OverallVCPULoad = "{:d}%".format(int( 100*float (CumulativeVCPUUsed/CumulativeVCPUAvail)))

        # APPEND RESULTS TO TOTAL_REPORT OBJECT
        TotalRepoKeys=totalreport.get_keys()
        MyRecord=totalreport.addemptyrecord()
        MyRecord[TotalRepoKeys.index("Capacity-fits")]=vmfits
        MyRecord[TotalRepoKeys.index("SourceSuffix")]=pars.paramsdict["SUFFISSOSRC"]
        MyRecord[TotalRepoKeys.index("DestinationSuffix")]=pars.paramsdict["SUFFISSODST"]
        MyRecord[TotalRepoKeys.index("Service")]=pars.paramsdict["SERVICE"]
        MyRecord[TotalRepoKeys.index("vCPU_Load_after")]=OverallVCPULoad

        if vmfits == False:
            #result.append(vmfits)
            Description = "VM: {:s} on AZ {:s} and HostAgg {:s} did not have sufficient capacity\n\n".format(
                VMNAME, VM_AZ, VM_HOSTAGGR)
        else:
            Description = "SUCCESS : all source VM instantiated into destination"

        MyRecord[TotalRepoKeys.index("Outcome")]=Description

        return result

class parameters():
    # -------------------------------------------------------------------------------------------------------------------------
    # GLOBAL DICTIONARIES: these are used to store command line arguments values or user input values (so that the behavior is consistent between User interactive mode and CLI mode)

    PATH = './JSON'
    FILETYPES = ('aggregate_list', 'hypervisor_list',
                 'server_dict', 'flavor_list', 'volume_list')
    MODE_OF_OPT_OPS = 0

    paramsdict = {'TIMESTAMP': '', 'SUFFISSOSRC': '', 'SUFFISSODST': '', 'SERVICE': [], 'IGNOREHOSTAGS': False,
                  'DESTINATIONWIPE': False, 'BESTVMDISTRO': True, 'DESTSCAN': False, 'DESTSITESLIST': [],
                  'SILENTMODE': False, 'AZREALIGN': '', 'SKIPMGMTSITE': False, 'OUTPUTTOFILE': False, 'JUSTSOURCE': False}

    paramslist = ('SUFFISSOSRC', 'SUFFISSODST', 'SERVICE', 'IGNOREHOSTAGS',
                  'DESTINATIONWIPE', 'BESTVMDISTRO', 'DESTSCAN', 'SILENTMODE', 'AZREALIGN', 'SKIPMGMTSITE', 'OUTPUTTOFILE', 'JUSTSOURCE')

    # -------------------------------------------------------------------------------------------------------------------------
    # FORMULAS FOR 1) SORTING 2) DISTANCE CALCULATION FROM TARGET
    # -------------------------------------------------------------------------------------------------------------------------
    # ,   '(currentvalue-average)**2'  , '(currentvalue-minimum)' ]
    sortingformulas = ['abs(currentvalue-average)']
    # , 'abs(currentvalue-average)',  '(currentvalue-minimum)**4']
    metricformulas = ['(currentvalue-average)**2']
    # -------------------------------------------------------------------------------------------------------------------------
    NO_OPTIMIZATION = 0
    OPTIMIZE_BY_CALC = 1
    OPTIMIZE_BY_FILE = 2

    DSTSITES = []

    def __init__(self):
        now = datetime.now()  # current date and time
        date_time = now.strftime("%d/%m/%Y %H:%M:%S")
        #date_time = now.strftime("%d/%m/%Y")
        self.paramsdict["TIMESTAMP"] = date_time
        self.MYGLOBALFILE = open('./capacity-forecast.results', 'w')
        self.DSTSITES = []
        screenrows, screencolumns = os.popen('stty size', 'r').read().split()
        self.ScreenWitdh = int(screencolumns)

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
        if len(self.paramsdict["AZREALIGN"]) == 0:
            MODE_OF_OPT_OPS = self.NO_OPTIMIZATION
        else:
            if self.paramsdict["AZREALIGN"].find('OPTIMIZE') > -1:
                MODE_OF_OPT_OPS = self.OPTIMIZE_BY_CALC
            else:
                MODE_OF_OPT_OPS = self.OPTIMIZE_BY_FILE
        return MODE_OF_OPT_OPS

    def show_cli_command(self):
        MyLine = '{0:_^'+str(self.ScreenWitdh)+'}'
        self.myprint(MyLine.format('\n\n'))
        self.myprint(MyLine.format('LIST OF PARAMETER ARGUMENTS'))
        self.myprint(json.dumps(self.paramsdict,indent=22))
        self.myprint(MyLine.format(''))
        # PRINT CLI COMMAND AND PARAMETERS USED
        CMD = "python3 mynewapp2.py"
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

# --------------------EXTRACTS SITENAME FROM SUFFISSO note : STG810 specific parsing
    def parse_suffisso(self, suffisso):
        if len(suffisso) == 20:
            # NOTE: STG810 does not show stg810 in the suffix as the cc-jumphost hostname is configured wrongly
            return suffisso[14:]
        else:
            return "stg810"

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

    def __init__(self):
        os.system(self.Black)
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
                    os.system('sleep 0.5')
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
