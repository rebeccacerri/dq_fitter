from re import TEMPLATE
import matplotlib.pyplot as plt
import array as arr
import numpy as np
from array import array
import os
import sys
import math
import re
from statistics import mean
import argparse
import ROOT
from os import path
from ROOT import TGraphErrors, TCanvas, TF1, TFile, TPaveText, TMath, TH1F, TH2F, TString, TLegend, TRatioPlot, TGaxis, TLine, TLatex
from ROOT import gROOT, gBenchmark, gPad, gStyle, kTRUE, kFALSE, kBlack, kRed, kGray, kDashed
from utils.plot_library import LoadStyle, SetLatex

def StoreHistogramsFromFile(fIn, histType):
    '''
    Method which returns all the histograms of a certain class from a given file
    '''
    histArray = []
    for key in fIn.GetListOfKeys():
        kname = key.GetName()
        if (fIn.Get(kname).ClassName() == histType):
            histArray.append(fIn.Get(kname))
    return histArray

def ComputeRMS(parValArray):
    '''
    Method to evaluate the RMS of a sample ()
    '''
    mean = 0
    for parVal in parValArray:
        mean += parVal
    mean = mean / len(parValArray)
    stdDev = 0
    for parVal in parValArray:
        stdDev += (parVal - mean) * (parVal - mean)
    stdDev = math.sqrt(stdDev / len(parValArray))
    return stdDev

def ComputeSigToBkg(canvas, sigName, bkgName, sig, bkg, minRange, maxRange):
    '''
    Method to compute the signal to background ratio after the canvas is created
    '''
    listOfPrimitives = canvas.GetListOfPrimitives()
    for index, primitive in enumerate(listOfPrimitives):
        if sigName in primitive.GetName():
            graphSig = listOfPrimitives.At(index)
        if bkgName in primitive.GetName():
            graphBkg = listOfPrimitives.At(index)

    nPoints = graphSig.GetN()
    histSig = ROOT.TH1F("histSig", "", nPoints, graphSig.GetPointX(0), graphSig.GetPointX(nPoints-1))
    histBkg = ROOT.TH1F("histBkg", "", nPoints, graphSig.GetPointX(0), graphSig.GetPointX(nPoints-1))
    for i in range(0, nPoints):
        histSig.SetBinContent(i+1, graphSig.GetPointY(i))
        histBkg.SetBinContent(i+1, graphBkg.GetPointY(i))

    integralTotSig = histSig.Integral(0, 10000)
    integralTotBkg = histBkg.Integral(0, 10000)
    integralSig = histSig.Integral(histSig.GetXaxis().FindBin(minRange), histSig.GetXaxis().FindBin(maxRange))
    integralBkg = histBkg.Integral(histBkg.GetXaxis().FindBin(minRange), histBkg.GetXaxis().FindBin(maxRange))
    SIG = (integralSig / integralTotSig) * sig
    BKG = (integralBkg / integralTotBkg) * bkg
    print("------------> ", sig, bkg, " => S frac = ", integralSig, integralTotSig, " => B frac", integralBkg, integralTotBkg)
    return SIG / BKG

def ComputeSignificance(canvas, sigName, bkgName, sig, bkg, minRange, maxRange):
    '''
    Method to compute the significance after the canvas is created
    '''
    listOfPrimitives = canvas.GetListOfPrimitives()
    for index, primitive in enumerate(listOfPrimitives):
        if sigName in primitive.GetName():
            graphSig = listOfPrimitives.At(index)
        if bkgName in primitive.GetName():
            graphBkg = listOfPrimitives.At(index)

    nPoints = graphSig.GetN()
    histSig = ROOT.TH1F("histSig", "", nPoints, graphSig.GetPointX(0), graphSig.GetPointX(nPoints-1))
    histBkg = ROOT.TH1F("histBkg", "", nPoints, graphSig.GetPointX(0), graphSig.GetPointX(nPoints-1))
    for i in range(0, nPoints):
        histSig.SetBinContent(i+1, graphSig.GetPointY(i))
        histBkg.SetBinContent(i+1, graphBkg.GetPointY(i))

    integralTotSig = histSig.Integral(0, 10000)
    integralTotBkg = histBkg.Integral(0, 10000)
    integralSig = histSig.Integral(histSig.GetXaxis().FindBin(minRange), histSig.GetXaxis().FindBin(maxRange))
    integralBkg = histBkg.Integral(histBkg.GetXaxis().FindBin(minRange), histBkg.GetXaxis().FindBin(maxRange))
    SIG = (integralSig / integralTotSig) * sig
    BKG = (integralBkg / integralTotBkg) * bkg
    return SIG / math.sqrt(SIG + BKG)

def ComputeAlpha(canvas, sigName, bkgName, sig, bkg, minRange, maxRange):
    '''
    Method to compute the S / (S + B) after the canvas is created
    '''
    listOfPrimitives = canvas.GetListOfPrimitives()
    for index, primitive in enumerate(listOfPrimitives):
        if sigName in primitive.GetName():
            graphSig = listOfPrimitives.At(index)
        if bkgName in primitive.GetName():
            graphBkg = listOfPrimitives.At(index)

    nPoints = graphSig.GetN()
    histSig = ROOT.TH1F("histSig", "", nPoints, graphSig.GetPointX(0), graphSig.GetPointX(nPoints-1))
    histBkg = ROOT.TH1F("histBkg", "", nPoints, graphSig.GetPointX(0), graphSig.GetPointX(nPoints-1))
    for i in range(0, nPoints):
        histSig.SetBinContent(i+1, graphSig.GetPointY(i))
        histBkg.SetBinContent(i+1, graphBkg.GetPointY(i))

    integralTotSig = histSig.Integral(0, 10000)
    integralTotBkg = histBkg.Integral(0, 10000)
    integralSig = histSig.Integral(histSig.GetXaxis().FindBin(minRange), histSig.GetXaxis().FindBin(maxRange))
    integralBkg = histBkg.Integral(histBkg.GetXaxis().FindBin(minRange), histBkg.GetXaxis().FindBin(maxRange))
    SIG = (integralSig / integralTotSig) * sig
    BKG = (integralBkg / integralTotBkg) * bkg
    return SIG / (SIG + BKG)

def DoSystematics(path, varBin, parName, fOut):
    '''
    Method to evaluate the systematic errors from signal extraction
    '''
    LoadStyle()
    gStyle.SetOptStat(0)
    gStyle.SetOptFit(0)
    nameTrialArray = []
    trialIndexArray  = array( 'f', [] )
    parValArray  = array( 'f', [] )
    parErrArray = array( 'f', [] )

    sigFuncList = ["CB2", "NA60"]
    bkgFuncList = ["VWG", "Pol4Exp"]

    # Lambda function to check the content of the name
    contains_any = lambda substr_list, s: any(sub in s for sub in substr_list)

    fInNameAllList = os.listdir(path)
    fInNameSelList = [path + "/" + fInName for fInName in fInNameAllList if varBin in fInName]
    fInNameSelList = [fInName for fInName in fInNameSelList if ".root" in fInName]
    fInNameSelList.sort()
    
    index = 0.5
    for fInName in fInNameSelList:
        fIn = TFile.Open(fInName)
        for key in fIn.GetListOfKeys():
            kname = key.GetName()
            if "fit_results" in fIn.Get(kname).GetName():
                trialIndexArray.append(index)
                if "data_tails" in fInName:
                    nums = re.findall(r'[\d\.\d]+', kname)
                    fitRange = list(filter(lambda x: '.' in x, nums))[:2]
                    found_sigFuncs = [sub for sub in sigFuncList if contains_any([sub], kname)]
                    found_bkgFuncs = [sub for sub in bkgFuncList if contains_any([sub], kname)]
                    nameTrialArray.append(found_sigFuncs[0] + " + " + found_bkgFuncs[0] + " " + fitRange[0] + " - " + fitRange[1] + " data tails")
                if "MC_tails" in fInName:
                    nums = re.findall(r'[\d\.\d]+', kname)
                    fitRange = list(filter(lambda x: '.' in x, nums))[:2]
                    found_sigFuncs = [sub for sub in sigFuncList if contains_any([sub], kname)]
                    found_bkgFuncs = [sub for sub in bkgFuncList if contains_any([sub], kname)]
                    nameTrialArray.append(found_sigFuncs[0] + " + " + found_bkgFuncs[0] + " " + fitRange[0] + " - " + fitRange[1] + " MC tails")
                parValArray.append(fIn.Get(kname).GetBinContent(fIn.Get(kname).GetXaxis().FindBin(parName)))
                parErrArray.append(fIn.Get(kname).GetBinError(fIn.Get(kname).GetXaxis().FindBin(parName)))
                index = index + 1

    graParVal = TGraphErrors(len(parValArray), trialIndexArray, parValArray, 0, parErrArray)
    graParVal.SetMarkerStyle(24)
    graParVal.SetMarkerSize(1.2)
    graParVal.SetMarkerColor(kBlack)
    graParVal.SetLineColor(kBlack)

    funcParVal = TF1("funcParVal", "[0]", 0, len(trialIndexArray))
    graParVal.Fit(funcParVal, "R0Q")
    funcParVal.SetLineColor(kRed)
    funcParVal.SetLineWidth(2)

    centralVal = mean(parValArray)
    statError = mean(parErrArray)
    systError = ComputeRMS(parValArray)

    trialIndexWidthArray = array( 'f', [] )
    parValSystArray = array( 'f', [] )
    parErrSystArray = array( 'f', [] )
    for i in range(0, len(parValArray)):
        trialIndexWidthArray.append(0.5)
        parValSystArray.append(centralVal)
        parErrSystArray.append(ComputeRMS(parValArray))

    graParSyst = TGraphErrors(len(parValArray), trialIndexArray, parValSystArray, trialIndexWidthArray, parErrSystArray)
    graParSyst.SetFillColorAlpha(kGray+1, 0.3)

    linePar = TLine(0, centralVal, len(trialIndexArray), centralVal)
    linePar.SetLineColor(kRed)
    linePar.SetLineWidth(2)

    lineParStatUp = TLine(0, centralVal + statError, len(trialIndexArray), centralVal + statError)
    lineParStatUp.SetLineStyle(kDashed)
    lineParStatUp.SetLineColor(kGray+1)

    lineParStatDown = TLine(0, centralVal - statError, len(trialIndexArray), centralVal - statError)
    lineParStatDown.SetLineStyle(kDashed)
    lineParStatDown.SetLineColor(kGray+1)

    latexTitle = TLatex()
    SetLatex(latexTitle)

    canvasParVal = TCanvas("canvasParVal", "canvasParVal", 800, 600)
    canvasParVal.SetBottomMargin(0.5)
    histGrid = TH2F("histGrid", "", len(parValArray), 0, len(parValArray), 100, centralVal-7*systError, centralVal+7*systError)

    for indexLabel, nameTrial in enumerate(nameTrialArray):
        histGrid.GetXaxis().SetBinLabel(indexLabel+1, nameTrial)

    histGrid.GetXaxis().LabelsOption("v")
    histGrid.Draw("same")
    linePar.Draw("same")
    lineParStatUp.Draw("same")
    lineParStatDown.Draw("same")
    graParSyst.Draw("E2same")
    graParVal.Draw("EPsame")

    if "sig" in parName:
        if "Jpsi" in parName: latexParName = "N_{J/#psi}"
        if "Psi2s" in parName: latexParName = "N_{#psi(2S)}"
    if "width" in parName:
        if "Jpsi" in parName: latexParName = "#sigma_{J/#psi}"
        if "Psi2s" in parName: latexParName = "#sigma_{#psi(2S)}"
    if "mean" in parName:
        if "Jpsi" in parName: latexParName = "#mu_{J/#psi}"
        if "Psi2s" in parName: latexParName = "#mu_{#psi(2S)}"
    if "chi2" in parName: latexParName = "#chi^{2}_{FIT}"
    if "sig_to_bkg" in parName: latexParName = "(S / B)_{3#sigma}"
    if "significance" in parName: latexParName = "(S / #sqrts{S + B})_{3#sigma}"
    if "alpha_vn" in parName: latexParName = "#alpha = (S / [S + B])_{3#sigma}"

    latexTitle.DrawLatex(0.25, 0.89, "%s = #bf{%3.2f} #pm #bf{%3.2f} (%3.2f %%) #pm #bf{%3.2f} (%3.2f %%)" % (latexParName, centralVal, statError, (statError/centralVal)*100, systError, (systError/centralVal)*100))
    print("%s -> %1.0f ± %1.0f (%3.2f%%) ± %1.0f (%3.2f%%)" % (varBin, centralVal, statError, (statError/centralVal)*100, systError, (systError/centralVal)*100))

    num = re.findall(r'[\d\.\d]+', path)
    fOut.write("%3.2f %3.2f %3.2f %3.2f %3.2f \n" % (float(num[4]), float(num[5]), centralVal, statError, systError))
    #fOut.write("%3.2f %3.2f %3.2f %3.2f %3.2f \n" % (0, 20, centralVal, statError, systError))
    canvasParVal.SaveAs("{}/systematics/{}_{}.pdf".format(path, varBin, parName))

def CheckVariables(fInNames, parNames, xMin, xMax, fOutName, obs):
    '''
    Method to chech the variable evolution vs file in the list
    '''
    LoadStyle()
    gStyle.SetOptStat(0)
    gStyle.SetOptFit(0)

    xBins  = array( 'f', [] )
    xCentr  = array( 'f', [] )
    xError = array( 'f', [] )

    for i in range(0, len(xMin)):
        xCentr.append((xMax[i] + xMin[i]) / 2.)
        xError.append((xMax[i] - xMin[i]) / 2.)
        xBins.append(xMin[i])
    xBins.append(xMax[len(xMin)-1])
    

    fOut = TFile("{}/myAnalysis_{}.root".format(fOutName,obs), "RECREATE")

    for parName in parNames:
        parValArray  = array( 'f', [] )
        parErrArray = array( 'f', [] )
        for fInName in fInNames:
            fIn = TFile.Open(fInName)
            for key in fIn.GetListOfKeys():
                kname = key.GetName()
                if "fit_results" in fIn.Get(kname).GetName():
                    parValArray.append(fIn.Get(kname).GetBinContent(fIn.Get(kname).GetXaxis().FindBin(parName)))
                    parErrArray.append(fIn.Get(kname).GetBinError(fIn.Get(kname).GetXaxis().FindBin(parName)))
        
        histParVal = TH1F("hist_{}".format(parName), "", len(xMin), xBins)

        for i in range(0, len(xMin)):
            histParVal.SetBinContent(i+1, parValArray[i])
            histParVal.SetBinError(i+1, parErrArray[i])

        graParVal = TGraphErrors(len(parValArray), xCentr, parValArray, xError, parErrArray)
        graParVal.SetMarkerStyle(24)
        graParVal.SetMarkerSize(1.2)
        graParVal.SetMarkerColor(kBlack)
        graParVal.SetLineColor(kBlack)

        fOut.cd()
        histParVal.Write("hist_{}".format(parName))
        graParVal.Write("gra_{}".format(parName))

    

    #canvasParVal = TCanvas("canvasParVal", "canvasParVal", 800, 600)
    #histGrid = TH2F("histGrid", "", 100, xMin[0], xMax[len(xMax)-1], 100, 0.7 * min(parValArray), 1.3 * max(parValArray))
    #histGrid.Draw("same")
    #graParVal.Draw("EPsame")

def ToCArray(values, ctype="float", name="table", formatter=str, colcount=8):
    # apply formatting to each element
    values = [formatter(v) for v in values]

    # split into rows with up to `colcount` elements per row
    rows = [values[i:i+colcount] for i in range(0, len(values), colcount)]

    # separate elements with commas, separate rows with newlines
    body = ',\n    '.join([', '.join(r) for r in rows])

    # assemble components into the complete string
    return '{} {}[] = {{\n    {}}};'.format(ctype, name, body)


    