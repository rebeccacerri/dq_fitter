from traceback import print_tb
import yaml
import json
import sys
import argparse
from array import array
import os
from os import path
import ROOT
from ROOT import TFile
sys.path.append('../')
from DQFitter import DQFitter
sys.path.append('../utils')
from utils_library import DoSystematics, CheckVariables

def main():
    print('start')
    parser = argparse.ArgumentParser(description='Arguments to pass')
    parser.add_argument('cfgFileName', metavar='text', default='config.yml', help='config file name')
    parser.add_argument("--do_fit", help="run the multi trial", action="store_true")
    args = parser.parse_args()
    print(args)
    print('Loading task configuration: ...', end='\r')

    with open(args.cfgFileName, 'r') as jsonCfgFile:
        inputCfg = json.load(jsonCfgFile)
    print('Loading task configuration: Done!')
    
    if args.do_fit:
        inputFileName  = inputCfg["input"]["input_file_name"]
        outputFileName = inputCfg["output"]["output_file_name"]
        histNames      = inputCfg["input"]["input_name"]
        minFitRanges   = inputCfg["input"]["pdf_dictionary"]["fitRangeMin"]
        maxFitRanges   = inputCfg["input"]["pdf_dictionary"]["fitRangeMax"]
        
        if not path.isdir(outputFileName):
            os.system("mkdir -p %s" % (outputFileName))
        for histName in histNames:
            for minFitRange, maxFitRange in zip(minFitRanges, maxFitRanges):
                # Reload configuration file
                with open(args.cfgFileName, 'r') as jsonCfgFile:
                    inputCfg = json.load(jsonCfgFile)
                pdfDictionary  = inputCfg["input"]["pdf_dictionary"]
                print(inputFileName)
                dqFitter = DQFitter(inputFileName, histName, outputFileName, minFitRange, maxFitRange)
                print(inputCfg["input"]["pdf_dictionary"]["parName"])
                dqFitter.SetFitConfig(pdfDictionary)
                dqFitter.SingleFit()

if __name__ == '__main__':
    main()
