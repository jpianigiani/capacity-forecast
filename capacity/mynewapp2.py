
#from asyncore import file_dispatcher
import json
import string
import sys
import glob
import os
import itertools
import math
import operator
from datetime import datetime
from mycapacitymodule import report, menu, dictarray, parameters
from mycapacitymodule2 import menu_report, rack_report, vm_report, hw_report,totalresults_report



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
    SRC_VM_REPORTBOX = vm_report()
    SRC_HW_REPORTBOX = hw_report()
    DST_REPORTBOX = hw_report()
    MyMENU = menu_report()
    FINAL_REPORTBOX = totalresults_report()
    FINAL_REPORTBOX.Report=[]
    MyLine = '{0:_^'+str(MyMENU.ScreenWitdh)+'}'
    SRC_RACK_REPORTBOX = rack_report()
    DST_RACK_REPORTBOX = rack_report()
    # PARSE CLI COMMAND ARGUMENTS INTO PARAMETERS DICTIONARY
    UIMODE=MyMENU.parse_args(arguments, MyPARAMSDICT,SRC_DA, DST_DA)

    # CREATE SOURCE VM REPORT
    SRC_VM_REPORTBOX.produce_vm_report(MyPARAMSDICT,SRC_DA)
    SRC_VM_REPORTBOX.sort_report(SRC_VM_REPORTBOX.get_sorting_keys())
    SRC_HW_REPORTBOX.produce_hw_report(MyPARAMSDICT, SRC_DA)
    SRC_RACK_REPORTBOX.produce_rack_report(MyPARAMSDICT,SRC_HW_REPORTBOX)
  
    # PRINT SOURCE VM REPORT
    if MyPARAMSDICT.is_silentmode()==False:
        MyPARAMSDICT.myprint( MyLine.format(menu.OKBLUE+" SOURCE SITE {:} - VM REPORT "+menu.Yellow))
        SRC_VM_REPORTBOX.print_report(MyPARAMSDICT)
        MyPARAMSDICT.myprint(SRC_VM_REPORTBOX.calculate_report_total_usage(MyPARAMSDICT))
        MyPARAMSDICT.myprint( MyLine.format(menu.OKBLUE+" SOURCE SITE - HARDWARE REPORT "+menu.Yellow))
        SRC_HW_REPORTBOX.print_report(MyPARAMSDICT)  
        MyPARAMSDICT.myprint( MyLine.format(menu.OKBLUE+" SOURCE SITE - RACK REPORT "+menu.Yellow))
        SRC_RACK_REPORTBOX.print_report(MyPARAMSDICT)  

    if(SRC_VM_REPORTBOX.length()==0):
        print("ERROR !! - {:s} service(s) could not be found in {:s}".format(MyPARAMSDICT.paramsdict["SERVICE"], MyPARAMSDICT.paramsdict["SUFFISSOSRC"]))
        exit(-1)
    # IF PARAMETER JUSTSOURCE report is set, then exit
    if MyPARAMSDICT.paramsdict["JUSTSOURCE"]:
        MyPARAMSDICT.show_cli_command()
        exit(-1)





    # now scanning all the destination suffix files that match the parameter entered in SUFFISSODST parameter
    for CURRENTDSTSITE in MyPARAMSDICT.DSTSITES:
        MyPARAMSDICT.paramsdict["SUFFISSODST"]=CURRENTDSTSITE
        destsitename=MyPARAMSDICT.parse_suffisso(CURRENTDSTSITE)




        # CREATE NEW DICTARRRAY FOR DESTINATION SITE DATA AND LOADS DATA INTO DST DICTARRAY
        del DST_DA
        DST_DA=dictarray()
        dst_paramname="SUFFISSODST"
        DST_DA.load_jsons_into_dictarrays(MyPARAMSDICT, dst_paramname)

        # FIRST, produce fresh HW report for Destination
        #DST_REPORTBOX.produce_hw_report(MyPARAMSDICT, DST_DA)
        #DST_REPORTBOX.sort_report(DST_REPORTBOX.get_sorting_keys())
        #DST_REPORTBOX.print_report(MyPARAMSDICT)
        #Stringa=DST_REPORTBOX.calculate_report_total_usage(MyPARAMSDICT)
        #MyPARAMSDICT.myprint(Stringa)
            
        # AZ to Rack Realign based on JSON input file or AUTOOPTIMIZE: for first parameter on CLI is the filename to use in the same path  as the other JSON files from openstack
        # if AZREALIGN=OPTIMIZE then instead of using an external JSON , the optimal distribution ofracks to AZ is calculated to minimize differences between AZs
        # ----------------------------- OPTIMIZE RACK LAYOUT LOOP ------------------------------------------
        # IF OPTIMIZATION BY FILE OR BY CALCULATION
        #if MyPARAMSDICT.get_azoptimization_mode() in [MyPARAMSDICT.OPTIMIZE_BY_CALC, MyPARAMSDICT.OPTIMIZE_BY_FILE]: 
            # OPTIMIZATION = true. Can either be based on RACK to AZ map in JSON or Self-optimized

        if MyPARAMSDICT.get_azoptimization_mode()  == MyPARAMSDICT.OPTIMIZE_BY_CALC:
        # SELF CALCULATED OPTIMIZATION==TRUE
            
            for metric_formula in list(MyPARAMSDICT.metricformulas):
                    # for every formula
                    # SCan through the optmimized HW dst reports after being optimized in accordance to the selected formulas...
                stringa1 = MyLine.format(menu.FAIL+"  DESTINATION SITE -  BEFORE RACK REALIGNMENT AND BEFORE INSTANTIATION ###################"+menu.Yellow)
                MyPARAMSDICT.myprint(stringa1.format(MyPARAMSDICT.parse_suffisso(CURRENTDSTSITE)))
                DST_REPORTBOX.produce_hw_report(MyPARAMSDICT, DST_DA)
                DST_REPORTBOX.sort_report(DST_REPORTBOX.get_sorting_keys())
                DST_REPORTBOX.print_report(MyPARAMSDICT)

                for myoptimizedrackrecord in DST_REPORTBOX.optimize_AZRealignment_in_HWReport(MyPARAMSDICT,DST_RACK_REPORTBOX,metric_formula):
                        #go through the resulting hw report, optimized through the previous formulas
                        # ADJUST REOPTIMIZATION ON HW REPORT = remap rack to AZs in accordance to the result of optimization
                    DST_REPORTBOX.sort_report(DST_REPORTBOX.get_sorting_keys())

                    DST_REPORTBOX.print_report(MyPARAMSDICT)
                    MyPARAMSDICT.myprint(stringa1)
                    MyPARAMSDICT.myprint(stringa1.format(MyPARAMSDICT.parse_suffisso(CURRENTDSTSITE)))
                    DST_RACK_REPORTBOX.produce_rack_report(MyPARAMSDICT,DST_REPORTBOX)
                    DST_RACK_REPORTBOX.print_report(MyPARAMSDICT)
                    FINAL_REPORTBOX.check_capacity_and_produce_Total_Report(MyPARAMSDICT,SRC_VM_REPORTBOX, DST_REPORTBOX, metric_formula,myoptimizedrackrecord)
                    stringa1 = MyLine.format(menu.FAIL+"  DESTINATION SITE - AFTER RACK REALIGNMENT AND AFTER INSTANTIATION ###################"+menu.Yellow)
                    MyPARAMSDICT.myprint(stringa1.format(MyPARAMSDICT.parse_suffisso(CURRENTDSTSITE)))
                    DST_REPORTBOX.print_report(MyPARAMSDICT)
                    DST_RACK_REPORTBOX.produce_rack_report(MyPARAMSDICT,DST_REPORTBOX)
                    DST_RACK_REPORTBOX.print_report(MyPARAMSDICT)



        elif MyPARAMSDICT.get_azoptimization_mode()  == MyPARAMSDICT.OPTIMIZE_BY_FILE:

            # OPTIMIZATION OF RACKS TO AZ BASED ON JSON FILE 
            stringa1 = MyLine.format(menu.FAIL+"  DESTINATION SITE - AFTER RACK REALIGNMENT AND AFTER INSTANTIATION "+menu.Yellow)
            MyPARAMSDICT.myprint(stringa1)
            result=[]
            myoptimizedrackrecord=[]
            myoptimizedrackrecord= DST_RACK_REPORTBOX.realignAZinhwreport(MyPARAMSDICT, DST_REPORTBOX)
            metric_formula=''
            DST_REPORTBOX.produce_hw_report(MyPARAMSDICT, DST_DA)
            DST_REPORTBOX.sort_report(DST_REPORTBOX.get_sorting_keys())

            DST_REPORTBOX.print_report(MyPARAMSDICT)
            DST_RACK_REPORTBOX.produce_rack_report(MyPARAMSDICT,DST_REPORTBOX)
            DST_RACK_REPORTBOX.print_report(MyPARAMSDICT)
            FINAL_REPORTBOX.check_capacity_and_produce_Total_Report(MyPARAMSDICT,SRC_VM_REPORTBOX, DST_REPORTBOX, metric_formula, myoptimizedrackrecord)
            MyPARAMSDICT.myprint(stringa1)
            DST_REPORTBOX.print_report(MyPARAMSDICT)
            DST_RACK_REPORTBOX.produce_rack_report(MyPARAMSDICT,DST_REPORTBOX)
            DST_RACK_REPORTBOX.print_report(MyPARAMSDICT)

                
        # -------------------------------------- USE PLAIN HW REPORT TO INSTANTIATE
        elif MyPARAMSDICT.get_azoptimization_mode() == MyPARAMSDICT.NO_OPTIMIZATION :
            stringa1 = MyLine.format(menu.FAIL+" HARDWARE CAPACITY: NO RACK OPTIMIZATION AND AFTER INSTANTIATION "+menu.Yellow)

            # NO OPTIMIZATION OF RACKS TO AZ
            # INstantiate and print updated dest report
            result=[]
            metric_formula=""
            myoptimizedrackrecord=[]
            DST_REPORTBOX.produce_hw_report(MyPARAMSDICT, DST_DA)
            DST_REPORTBOX.sort_report(DST_REPORTBOX.get_sorting_keys())
            DST_REPORTBOX.print_report(MyPARAMSDICT)
            DST_RACK_REPORTBOX.produce_rack_report(MyPARAMSDICT,DST_REPORTBOX)
            DST_RACK_REPORTBOX.print_report(MyPARAMSDICT)
            FINAL_REPORTBOX.check_capacity_and_produce_Total_Report(MyPARAMSDICT, SRC_VM_REPORTBOX, DST_REPORTBOX,  metric_formula,myoptimizedrackrecord)
            MyPARAMSDICT.myprint(stringa1.format(MyPARAMSDICT.parse_suffisso(CURRENTDSTSITE)))
            DST_REPORTBOX.print_report(MyPARAMSDICT)
            DST_RACK_REPORTBOX.produce_rack_report(MyPARAMSDICT,DST_REPORTBOX)
            DST_RACK_REPORTBOX.print_report(MyPARAMSDICT)
        else:
            print("MAIN - - ERROR 1")
            exit(-1)
            
    

    # Print Total Report of Results
    MyPARAMSDICT.myprint(MyLine.format('SUMMARY OF RESULTS'))
    FINAL_REPORTBOX.print_report(MyPARAMSDICT)
    # SHOW Parameters dump plus CLI command for subsequent executions via CLI command          
    MyPARAMSDICT.show_cli_command()

if __name__ == '__main__':
    main(sys.argv)
