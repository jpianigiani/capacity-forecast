
# Author Jacopo Pianigiani jacopopianigiani@juniper.net
# Written in 2022

import json
import string
import sys
import glob
import os
import itertools
import math
import operator
from datetime import datetime

from mycapacitymodule import *
from mycapacitymodule2 import *
from aop_logger import *
#import resource_analysis 

DEBUG=0


# ------------------------------------------------------   MAIN  ---------------------------------
# ------------------------------------------------------   MAIN  ---------------------------------
def main(arguments):
#-------------------------------------------------------------------------------------------------------------------------
    os.system('clear')  

    # Initialization of global variables
    MyPARAMSDICT=parameters()
    SRC_DA= dictarray()
    DST_DA= dictarray()
    ERROR_REPORTBOX = error_report(MyPARAMSDICT)
    SRC_VM_REPORTBOX = vm_report(MyPARAMSDICT)
    SRC_HW_REPORTBOX = hw_report(MyPARAMSDICT)
    DST_HW_REPORTBOX = hw_report(MyPARAMSDICT)
    MyMENU = menu_report(MyPARAMSDICT)
    MyMENU.set_name("MENU")
    FINAL_REPORTBOX = totalresults_report(MyPARAMSDICT)
    FINAL_REPORTBOX.ClearData()
    SRC_RACK_REPORTBOX = rack_report(MyPARAMSDICT)
    DST_RACK_REPORTBOX = rack_report(MyPARAMSDICT)
    SRC_SITE_REPORTBOX = site_report(MyPARAMSDICT)
    SRC_SERVICEGRAPH_REPORTBOX = servicegraph_report(MyPARAMSDICT)
    SRC_HWNUMA_REPORTBOX=hw_vcpu_report(MyPARAMSDICT)

    MyLine = '{0:_^'+str(MyMENU.ScreenWitdh)+'}'

    # PARSE CLI COMMAND ARGUMENTS INTO PARAMETERS DICTIONARY
    UIMODE=MyMENU.parse_args(arguments, MyPARAMSDICT,SRC_DA, DST_DA)


    # CREATE SOURCE VM REPORT
    for CURRENTSRCSITE in MyPARAMSDICT.paramsdict["SRCSITESLIST"]:
        SRC_VM_REPORTBOX.ClearData()
        SRC_HW_REPORTBOX.ClearData()
        SRC_RACK_REPORTBOX.ClearData()
        SRC_SITE_REPORTBOX.ClearData()
        SRC_HWNUMA_REPORTBOX.ClearData()
        
        MyPARAMSDICT.set_service_to_initialvalue()

        # SETS THE PARAMETER FOR SOURCE FILES TO CURRENT SOURCE SITE SUFFIX AND LOADS DATA FROM FILES INTO DICTARRAY
        src_paramname="SOURCE_SITE_SUFFIX"
        MyPARAMSDICT.paramsdict[src_paramname]=CURRENTSRCSITE
        srcsitename = MyPARAMSDICT.parse_suffisso(CURRENTSRCSITE).upper()
        del SRC_DA
        SRC_DA=dictarray()
        SRC_DA.load_jsons_into_dictarrays(MyPARAMSDICT, src_paramname)

        # CREATE OBJECTS FOR EACH REPORT FOR SOURCE SITE: VM, HW, RACK, SITE; FINALREPORT IS CREATED ONLY IF DEST SITE USED
        FINAL_REPORTBOX.set_name("TOTALRESULTS-"+srcsitename)
  
        SRC_VM_REPORTBOX.set_name("SRC-"+srcsitename+SRC_VM_REPORTBOX.ReportType)
        SRC_VM_REPORTBOX.produce_vm_report(MyPARAMSDICT,SRC_DA)
        SRC_VM_REPORTBOX.calculate_report_total_usage(MyPARAMSDICT)
        SRC_VM_REPORTBOX.sort_report(SRC_VM_REPORTBOX.get_sorting_keys())

        SRC_HW_REPORTBOX.set_name("SRC-"+srcsitename+SRC_HW_REPORTBOX.ReportType)
        SRC_HW_REPORTBOX.produce_hw_report(CURRENTSRCSITE,MyPARAMSDICT, SRC_DA)
        SRC_HW_REPORTBOX.sort_report(SRC_HW_REPORTBOX.get_sorting_keys())
        SRC_HW_REPORTBOX.calculate_report_total_usage(MyPARAMSDICT)

        SRC_RACK_REPORTBOX.set_name("SRC-"+srcsitename+SRC_RACK_REPORTBOX.ReportType)
        SRC_RACK_REPORTBOX.produce_rack_report(MyPARAMSDICT,SRC_HW_REPORTBOX)
        SRC_RACK_REPORTBOX.sort_report(SRC_RACK_REPORTBOX.get_sorting_keys())

        SRC_SITE_REPORTBOX.set_name("SRC-"+srcsitename+SRC_SITE_REPORTBOX.ReportType)
        SRC_SITE_REPORTBOX.produce_site_report(MyPARAMSDICT,SRC_VM_REPORTBOX,SRC_HW_REPORTBOX)
        SRC_SITE_REPORTBOX.sort_report(SRC_SITE_REPORTBOX.get_sorting_keys())

        SRC_HWNUMA_REPORTBOX.set_name("SRC-"+srcsitename+SRC_HWNUMA_REPORTBOX.ReportType)
        SRC_HWNUMA_REPORTBOX.produce_hw_vcpu_report(CURRENTSRCSITE,MyPARAMSDICT, SRC_DA)
        SRC_HWNUMA_REPORTBOX.sort_report(SRC_HWNUMA_REPORTBOX.get_sorting_keys())

        SRC_SERVICEGRAPH_REPORTBOX.set_name("SRC-"+srcsitename+SRC_SERVICEGRAPH_REPORTBOX.ReportType)
        SRC_SERVICEGRAPH_REPORTBOX.produce_servicegraphreport(MyPARAMSDICT, SRC_DA)
        SRC_SERVICEGRAPH_REPORTBOX.sort_report(SRC_SERVICEGRAPH_REPORTBOX.get_sorting_keys())
        # PRINT EACH REPORT WITH REPORT HEADERS AND HEADER LINES
        if MyPARAMSDICT.is_silentmode()==False:
            SRC_VM_REPORTBOX.set_state(MyLine.format(menu.OKBLUE+" SOURCE SITE {:} - VM REPORT ").format(srcsitename))
            SRC_VM_REPORTBOX.print_report(MyPARAMSDICT)
            
            SRC_HW_REPORTBOX.set_state(MyLine.format(menu.OKBLUE+" SOURCE SITE {:} - HARDWARE REPORT ").format(srcsitename))
            SRC_HW_REPORTBOX.print_report(MyPARAMSDICT)  

            SRC_RACK_REPORTBOX.set_state( MyLine.format(menu.OKBLUE+" SOURCE SITE {:} - RACK REPORT ").format(srcsitename))
            SRC_RACK_REPORTBOX.print_report(MyPARAMSDICT)  
 
            SRC_SITE_REPORTBOX.set_state( MyLine.format(menu.OKBLUE+" SOURCE SITE {:} - SITE REPORT ").format(srcsitename))
            SRC_SITE_REPORTBOX.print_report(MyPARAMSDICT)  

            SRC_HWNUMA_REPORTBOX.set_state( MyLine.format(menu.OKBLUE+" SOURCE SITE {:} - NUMA REPORT ").format(srcsitename))
            SRC_HWNUMA_REPORTBOX.print_report(MyPARAMSDICT)  

            SRC_SITE_REPORTBOX.set_state( MyLine.format(menu.Grey+" SOURCE SITE {:} - SERVICEGRAPH REPORT ").format(srcsitename))
            SRC_SERVICEGRAPH_REPORTBOX.print_report(MyPARAMSDICT)

        if(SRC_VM_REPORTBOX.length()==0):
            print("WARNING !! - {:} service(s) could not be found in {:}".format(MyPARAMSDICT.paramsdict["SERVICE"], MyPARAMSDICT.paramsdict["SOURCE_SITE_SUFFIX"]))
            #exit(-1)


        if MyPARAMSDICT.paramsdict["JUSTSOURCE"]==False:
            # now scanning all the destination suffix files that match the parameter entered in DESTINATION_SITE_SUFFIX parameter
            for CURRENTDSTSITE in MyPARAMSDICT.paramsdict["DESTSITESLIST"]:
                MyPARAMSDICT.paramsdict["DESTINATION_SITE_SUFFIX"]=CURRENTDSTSITE
                destsitename=MyPARAMSDICT.parse_suffisso(CURRENTDSTSITE).upper()
                DST_HW_REPORTBOX.set_name("DST-"+destsitename+DST_HW_REPORTBOX.ReportType)
                DST_RACK_REPORTBOX.set_name("DST-"+destsitename+DST_RACK_REPORTBOX.ReportType)
                
                # CREATE NEW DICTARRRAY FOR DESTINATION SITE DATA AND LOADS DATA INTO DST DICTARRAY
                del DST_DA
                DST_DA=dictarray()
                dst_paramname="DESTINATION_SITE_SUFFIX"
                DST_DA.load_jsons_into_dictarrays(MyPARAMSDICT, dst_paramname)

                # FIRST, produce fresh HW report for Destination
                
                # AZ to Rack Realign based on JSON input file or AUTOOPTIMIZE: for first parameter on CLI is the filename to use in the same path  as the other JSON files from openstack
                # if HW_OPTIMIZATION_MODE=OPTIMIZE then instead of using an external JSON , the optimal distribution ofracks to AZ is calculated to minimize differences between AZs
                # ----------------------------- OPTIMIZE RACK LAYOUT LOOP ------------------------------------------
                # IF OPTIMIZATION BY FILE OR BY CALCULATION
                #if MyPARAMSDICT.get_azoptimization_mode() in [MyPARAMSDICT.OPTIMIZE_BY_CALC, MyPARAMSDICT.OPTIMIZE_BY_FILE]: 
                    # OPTIMIZATION = true. Can either be based on RACK to AZ map in JSON or Self-optimized

                if MyPARAMSDICT.get_azoptimization_mode()  == MyPARAMSDICT.OPTIMIZE_BY_CALC:
                # SELF CALCULATED OPTIMIZATION==TRUE
                    
                    for metric_formula in MyPARAMSDICT.metricformulas:
                            # for every formula
                            # SCan through the optmimized HW dst reports after being optimized in accordance to the selected formulas...
                        

                        DST_HW_REPORTBOX.set_state(MyLine.format(menu.FAIL+"  DESTINATION SITE {:}- HARDWARE REPORT - -  BEFORE RACK OPTIMIZATION "+menu.FAIL+" BEFORE INSTANTIATION "+menu.Yellow).format(destsitename))
                        DST_HW_REPORTBOX.produce_hw_report(CURRENTDSTSITE ,MyPARAMSDICT, DST_DA)
                        DST_RACK_REPORTBOX.set_state(MyLine.format(menu.FAIL+"  DESTINATION SITE {:}- RACK REPORT - -  BEFORE RACK OPTIMIZATION "+menu.FAIL+" BEFORE INSTANTIATION "+menu.Yellow).format(destsitename))

                        for myoptimizedrackrecord in DST_HW_REPORTBOX.Hardware_Layout_Optimization_ByRackAndAZ(MyPARAMSDICT,DST_RACK_REPORTBOX,metric_formula):
                                #go through the resulting hw report, optimized through the previous formulas
                                # ADJUST REOPTIMIZATION ON HW REPORT = remap rack to AZs in accordance to the result of optimization
                            DST_HW_REPORTBOX.sort_report(DST_HW_REPORTBOX.get_sorting_keys())
                            DST_HW_REPORTBOX.print_report(MyPARAMSDICT)
                            
                            DST_RACK_REPORTBOX.set_state(MyLine.format(menu.FAIL+"  DESTINATION SITE {:}- RACK REPORT - AFTER RACK OPTIMIZATION "+menu.FAIL+" BEFORE INSTANTIATION "+menu.Yellow).format(destsitename))
                            DST_RACK_REPORTBOX.produce_rack_report(MyPARAMSDICT,DST_HW_REPORTBOX)
                            DST_RACK_REPORTBOX.print_report(MyPARAMSDICT)

                            FINAL_REPORTBOX.set_state(MyLine.format(menu.FAIL+"  TOTAL RESULTS REPORT {:} - OPTIMIZE BY CALC -  AFTER RACK OPTIMIZATION - "+menu.OKBLUE+"AFTER INSTANTIATION "+menu.Yellow).format(destsitename))
                            FINAL_REPORTBOX.check_capacity_and_produce_Total_Report(MyPARAMSDICT,SRC_VM_REPORTBOX, DST_HW_REPORTBOX, metric_formula,myoptimizedrackrecord)
                            
                            DST_HW_REPORTBOX.set_state(MyLine.format(menu.FAIL+"  DESTINATION SITE {:}- HARDWARE REPORT - AFTER RACK OPTIMIZATION "+menu.OKBLUE+" AFTER INSTANTIATION "+menu.Yellow).format(destsitename))
                            DST_HW_REPORTBOX.print_report(MyPARAMSDICT)
                            
                            DST_RACK_REPORTBOX.set_state(MyLine.format(menu.FAIL+"  DESTINATION SITE {:}- RACK REPORT - AFTER RACK OPTIMIZATION "+menu.OKBLUE+" AFTER INSTANTIATION "+menu.Yellow).format(destsitename))
                            DST_RACK_REPORTBOX.produce_rack_report(MyPARAMSDICT,DST_HW_REPORTBOX)
                            DST_RACK_REPORTBOX.print_report(MyPARAMSDICT)



                elif MyPARAMSDICT.get_azoptimization_mode()  == MyPARAMSDICT.OPTIMIZE_BY_FILE:
                    # OPTIMIZATION OF RACKS TO AZ BASED ON JSON FILE 
                    result=[]
                    myoptimizedrackrecord=[]
                    myoptimizedrackrecord= DST_RACK_REPORTBOX.realignAZinhwreport(MyPARAMSDICT, DST_HW_REPORTBOX)
                    metric_formula=''
                    DST_HW_REPORTBOX.produce_hw_report(CURRENTDSTSITE ,MyPARAMSDICT, DST_DA)
                    DST_HW_REPORTBOX.sort_report(DST_HW_REPORTBOX.get_sorting_keys())
                    DST_HW_REPORTBOX.set_state(MyLine.format(menu.FAIL+"  DESTINATION SITE {:} - HARDWARE REPORT - OPTIMIZE RACK BY FILE - AFTER RACK REALIGNMENT "+menu.FAIL+" BEFORE INSTANTIATION "+menu.Yellow).format(destsitename))
                    DST_HW_REPORTBOX.print_report(MyPARAMSDICT)

                    DST_RACK_REPORTBOX.produce_rack_report(MyPARAMSDICT,DST_HW_REPORTBOX)
                    DST_RACK_REPORTBOX.set_state(MyLine.format(menu.FAIL+"  DESTINATION SITE {:} - RACK REPORT - OPTIMIZE RACK BY FILE - AFTER RACK REALIGNMENT "+menu.FAIL+" BEFORE INSTANTIATION "+menu.Yellow).format(destsitename))
                    DST_RACK_REPORTBOX.print_report(MyPARAMSDICT)

                    FINAL_REPORTBOX.set_state(format(menu.FAIL+"  TOTAL RESULTS REPORT {:} - OPTIMIZE RACK BY FILE - AFTER RACK REALIGNMENT "+menu.OKBLUE+" AFTER INSTANTIATION "+menu.Yellow).format(destsitename))
                    FINAL_REPORTBOX.check_capacity_and_produce_Total_Report(MyPARAMSDICT,SRC_VM_REPORTBOX, DST_HW_REPORTBOX, metric_formula, myoptimizedrackrecord)
                    
                    DST_HW_REPORTBOX.set_state(format(menu.FAIL+"  DESTINATION SITE {:} - HARDWARE REPORT- OPTIMIZE RACK BY FILE - AFTER RACK REALIGNMENT "+menu.OKBLUE+" AFTER INSTANTIATION "+menu.Yellow).format(destsitename))
                    DST_HW_REPORTBOX.print_report(MyPARAMSDICT)

                    DST_RACK_REPORTBOX.set_state(MyLine.format(menu.FAIL+"  DESTINATION SITE {:} - RACK REPORT- OPTIMIZE RACK BY FILE - AFTER RACK REALIGNMENT "+menu.OKBLUE+" AFTER INSTANTIATION "+menu.Yellow).format(destsitename))
                    DST_RACK_REPORTBOX.produce_rack_report(MyPARAMSDICT,DST_HW_REPORTBOX)
                    DST_RACK_REPORTBOX.print_report(MyPARAMSDICT)

                        
                # -------------------------------------- USE PLAIN HW REPORT TO INSTANTIATE
                elif MyPARAMSDICT.get_azoptimization_mode() == MyPARAMSDICT.NO_OPTIMIZATION :
                    # NO OPTIMIZATION OF RACKS TO AZ
                    # Instantiate and print updated dest report
                    result=[]
                    metric_formula=""
                    myoptimizedrackrecord=[]
                    DST_HW_REPORTBOX.set_state (MyLine.format(menu.FAIL+"  DESTINATION SITE {:} - HARDWARE REPORT -  NO RACK OPTIMIZATION - "+menu.FAIL+"BEFORE INSTANTIATION "+menu.Yellow).format(destsitename))
                    DST_HW_REPORTBOX.produce_hw_report(CURRENTDSTSITE ,MyPARAMSDICT, DST_DA)
                    DST_HW_REPORTBOX.sort_report(DST_HW_REPORTBOX.get_sorting_keys())
                    DST_HW_REPORTBOX.print_report(MyPARAMSDICT)

                    DST_RACK_REPORTBOX.set_state(MyLine.format(menu.FAIL+"  DESTINATION SITE {:} - RACK REPORT -  NO RACK OPTIMIZATION - "+menu.FAIL+"BEFORE INSTANTIATION "+menu.Yellow).format(destsitename))
                    DST_RACK_REPORTBOX.produce_rack_report(MyPARAMSDICT,DST_HW_REPORTBOX)
                    DST_RACK_REPORTBOX.print_report(MyPARAMSDICT)

                    FINAL_REPORTBOX.set_state(MyLine.format(menu.FAIL+"  TOTAL RESULTS REPORT {:}  -  NO RACK OPTIMIZATION - "+menu.OKBLUE+"AFTER INSTANTIATION "+menu.Yellow).format(destsitename))
                    FINAL_REPORTBOX.check_capacity_and_produce_Total_Report(MyPARAMSDICT, SRC_VM_REPORTBOX, DST_HW_REPORTBOX,  metric_formula,myoptimizedrackrecord)

                    DST_HW_REPORTBOX.set_state (MyLine.format(menu.FAIL+"  DESTINATION SITE {:} - HARDWARE REPORT -  NO RACK OPTIMIZATION - "+menu.FAIL+"AFTER INSTANTIATION "+menu.Yellow).format(destsitename))
                    DST_HW_REPORTBOX.print_report(MyPARAMSDICT)

                    DST_RACK_REPORTBOX.set_state(MyLine.format(menu.FAIL+"  DESTINATION SITE {:} - RACK REPORT -  NO RACK OPTIMIZATION - "+menu.OKBLUE+"AFTER INSTANTIATION "+menu.Yellow).format(destsitename))
                    DST_RACK_REPORTBOX.produce_rack_report(MyPARAMSDICT,DST_HW_REPORTBOX)
                    DST_RACK_REPORTBOX.print_report(MyPARAMSDICT)
                else:
                    print("MAIN - - ERROR 1")
                    exit(-1)
            
            

        # Print Total Report of Results
        
            stringa1 = MyLine.format(menu.FAIL+"  SUMMARY OF RESULTS "+menu.Yellow)
            MyPARAMSDICT.myprint(MyLine.format(stringa1))
            FINAL_REPORTBOX.print_report(MyPARAMSDICT)
    # SHOW Parameters dump plus CLI command for subsequent executions via CLI command  
    ERROR_REPORTBOX.set_name("ERRORS_REPORT")
    ERROR_REPORTBOX.produce_error_report(MyPARAMSDICT)
    ERROR_REPORTBOX.sort_report(ERROR_REPORTBOX.get_sorting_keys())
    ERROR_REPORTBOX.print_report(MyPARAMSDICT)    

    MyPARAMSDICT.show_cli_command()



if __name__ == '__main__':
    main(sys.argv)
