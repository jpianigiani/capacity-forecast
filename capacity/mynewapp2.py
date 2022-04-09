
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

def goodvector(vector, vector2):
    result=False
    result2=False
    countdigits=0
    countdigits2=0
    for x in range(len(vector)):
        if vector[x].isdigit()==True:
            countdigits+=1
    if countdigits==len(vector):
        result=True
        for x in range(len(vector2)):
            if vector2[x]>0:
                countdigits2+=1
        if countdigits2==len(vector2):
            result2=True
    return result and result2
            

# -------------- CHECK IF SVC IS ALREADY EXISTING IN TARGET DESTINATION SITE -----------------------
def check_if_svc_alreadythere(svc, dictarray_object):

    if svc in dictarray_object.SERVERDICT:
        return True
    else:
        return False

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
    MyLine = '{0:_^'+str(MyMENU.ScreenWitdh)+'}'

    # PARSE CLI COMMAND ARGUMENTS INTO PARAMETERS DICTIONARY
    UIMODE=MyMENU.parse_args(arguments, MyPARAMSDICT,SRC_DA, DST_DA)

    # CREATE SOURCE VM REPORT
    SRC_VM_REPORTBOX.produce_vm_report(MyPARAMSDICT,SRC_DA)
    SRC_VM_REPORTBOX.sort_report(SRC_VM_REPORTBOX.get_sorting_keys())
    SRC_HW_REPORTBOX.produce_hw_report(MyPARAMSDICT, SRC_DA)

    # PRINT SOURCE VM REPORT
    if MyPARAMSDICT.is_silentmode()==False:
        MyPARAMSDICT.myprint( MyLine.format("SOURCE"))
        SRC_VM_REPORTBOX.print_report(MyPARAMSDICT)
        MyPARAMSDICT.myprint(SRC_VM_REPORTBOX.calculate_report_total_usage(MyPARAMSDICT))

    if(SRC_VM_REPORTBOX.length()==0):
        print("ERROR !! - {:s} service(s) could not be found in {:s}".format(MyPARAMSDICT.paramsdict["SERVICE"], MyPARAMSDICT.paramsdict["SUFFISSOSRC"]))
        exit(-1)
    # IF PARAMETER JUSTSOURCE report is set, then exit
    if MyPARAMSDICT.paramsdict["JUSTSOURCE"]:
        MyPARAMSDICT.show_cli_command()
        exit(-1)


    RACK_REPORTBOX = rack_report()


    # now scanning all the destination suffix files that match the parameter entered in SUFFISSODST parameter
    for CURRENTDSTSITE in MyPARAMSDICT.DSTSITES:
        MyPARAMSDICT.paramsdict["SUFFISSODST"]=CURRENTDSTSITE
        destsitename=MyPARAMSDICT.parse_suffisso(CURRENTDSTSITE)

        if MyPARAMSDICT.is_silentmode()==False:
            MyPARAMSDICT.myprint(MyLine.format(""))
            stringa1 = menu.FAIL+"################### SITE {:s} : HARDWARE CAPACITY: BEFORE RACK REALIGNMENT AND BEFORE INSTANTIATION ###################"+menu.Yellow
            MyPARAMSDICT.myprint(stringa1.format(MyPARAMSDICT.parse_suffisso(CURRENTDSTSITE)))
            MyPARAMSDICT.myprint(MyLine.format(destsitename+" : "+CURRENTDSTSITE))


        # CREATE NEW DICTARRRAY FOR DESTINATION SITE DATA AND LOADS DATA INTO DST DICTARRAY
        del DST_DA
        DST_DA=dictarray()
        dst_paramname="SUFFISSODST"
        DST_DA.load_jsons_into_dictarrays(MyPARAMSDICT, dst_paramname)

        # FIRST, produce fresh HW report for Destination
        DST_REPORTBOX.produce_hw_report(MyPARAMSDICT, DST_DA)
        DST_REPORTBOX.sort_report(DST_REPORTBOX.get_sorting_keys())
        DST_REPORTBOX.print_report(MyPARAMSDICT)
        Stringa=DST_REPORTBOX.calculate_report_total_usage(MyPARAMSDICT)
        MyPARAMSDICT.myprint(Stringa)
            
        # AZ to Rack Realign based on JSON input file or AUTOOPTIMIZE: for first parameter on CLI is the filename to use in the same path  as the other JSON files from openstack
        # if AZREALIGN=OPTIMIZE then instead of using an external JSON , the optimal distribution ofracks to AZ is calculated to minimize differences between AZs
        # ----------------------------- OPTIMIZE RACK LAYOUT LOOP ------------------------------------------
        # IF OPTIMIZATION BY FILE OR BY CALCULATION
        if MyPARAMSDICT.get_azoptimization_mode() in [MyPARAMSDICT.OPTIMIZE_BY_CALC, MyPARAMSDICT.OPTIMIZE_BY_FILE]: 
            # OPTIMIZATION = true. Can either be based on RACK to AZ map in JSON or Self-optimized

            if MyPARAMSDICT.get_azoptimization_mode()  == MyPARAMSDICT.OPTIMIZE_BY_CALC:
                # SELF CALCULATED OPTIMIZATION==TRUE
            
                for metric_formula in list(MyPARAMSDICT.metricformulas):
                    # for every formula
                    # SCan through the optmimized HW dst reports after being optimized in accordance to the selected formulas...
                    DST_REPORTBOX.produce_hw_report(MyPARAMSDICT, DST_DA)
                    DST_REPORTBOX.sort_report(DST_REPORTBOX.get_sorting_keys())

                    for myoptimizedrackrecord in DST_REPORTBOX.optimize_AZRealignment_in_HWReport(MyPARAMSDICT,RACK_REPORTBOX,metric_formula):
                        #go through the resulting hw report, optimized through the previous formulas
                        # ADJUST REOPTIMIZATION ON HW REPORT = remap rack to AZs in accordance to the result of optimization
                        DST_REPORTBOX.sort_report(DST_REPORTBOX.get_sorting_keys())
                        DST_REPORTBOX.print_report(MyPARAMSDICT)
                        RACK_REPORTBOX.produce_rack_report(MyPARAMSDICT,DST_REPORTBOX)
                        RACK_REPORTBOX.print_report(MyPARAMSDICT)
                        FINAL_REPORTBOX.produce_Total_Report(MyPARAMSDICT,SRC_VM_REPORTBOX, DST_REPORTBOX, metric_formula,myoptimizedrackrecord)
						# --------------------- END OF REPLACE with FUNCTION 


            else:

            # OPTIMIZATION OF RACKS TO AZ BASED ON JSON FILE 
                result=[]
                myoptimizedrackrecord=[]
                myoptimizedrackrecord= RACK_REPORTBOX.realignAZinhwreport(MyPARAMSDICT, DST_REPORTBOX)
                metric_formula=''
                DST_REPORTBOX.sort_report(DST_REPORTBOX.get_sorting_keys())
                DST_REPORTBOX.print_report(MyPARAMSDICT)
                RACK_REPORTBOX.produce_rack_report(MyPARAMSDICT,DST_REPORTBOX)
                RACK_REPORTBOX.print_report(MyPARAMSDICT)
                FINAL_REPORTBOX.produce_Total_Report(MyPARAMSDICT,SRC_VM_REPORTBOX, DST_REPORTBOX, metric_formula, myoptimizedrackrecord)

                
        # -------------------------------------- USE PLAIN HW REPORT TO INSTANTIATE
        if MyPARAMSDICT.get_azoptimization_mode() in [ MyPARAMSDICT.NO_OPTIMIZATION ] :
            # NO OPTIMIZATION OF RACKS TO AZ
            # INstantiate and print updated dest report
            result=[]
            metric_formula=""
            myoptimizedrackrecord=[]
            RACK_REPORTBOX.produce_rack_report(MyPARAMSDICT,DST_REPORTBOX)
            RACK_REPORTBOX.print_report(MyPARAMSDICT)
            FINAL_REPORTBOX.produce_Total_Report(MyPARAMSDICT, SRC_VM_REPORTBOX, DST_REPORTBOX,  metric_formula,myoptimizedrackrecord)

    
    # SHOW Parameters dump plus CLI command for subsequent executions via CLI command          
    MyPARAMSDICT.show_cli_command()

    # Print Total Report of Results
    MyPARAMSDICT.myprint(menu.Yellow+MyLine.format(''))
    MyPARAMSDICT.myprint(MyLine.format('SUMMARY OF RESULTS'))
    FINAL_REPORTBOX.print_report(MyPARAMSDICT)
    MyPARAMSDICT.myprint(menu.Yellow+MyLine.format(''))

if __name__ == '__main__':
    main(sys.argv)
