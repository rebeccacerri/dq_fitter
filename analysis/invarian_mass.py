import yaml
import json
import sys
import argparse
from array import array
import os
import math 
from os import path
import numpy as np
import pandas as pd
import ROOT
from ROOT import TCanvas, TH1F, TH2F, TGraphErrors, TLegend
sys.path.append('../utils')
from plot_library import LoadStyle, SetGraStat, SetGraSyst, SetLegend

ROOT.gROOT.ProcessLineSync(".x ../fit_library/VWGPdf.cxx+")
#ROOT.gROOT.ProcessLineSync(".x ../fit_library/CB2Pdf.cxx+")
ROOT.gROOT.ProcessLineSync(".x ../fit_library/Pol4ExpPdf.cxx+")

def main():
    LoadStyle()
    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetHatchesSpacing(0.3)
    #gStyle.SetHatchesLineWidth(2)

    letexTitle = ROOT.TLatex()
    letexTitle.SetTextSize(0.042)
    letexTitle.SetNDC()
    letexTitle.SetTextFont(42)

    varMin = "0"
    varMax = "90"
    #path = "/Users/lucamicheletti/GITHUB/dq_fitter/analysis/LHC23zzh_pass2"
    path = "/Users/lucamicheletti/GITHUB/dq_fitter/analysis/LHC23_pass3_full"

    if varMin == "0" and varMax == "90":
        histName = "hist_mass_all_histo_PairsMuonSEPM_matchedMchMid"
    else:
        histName = "hist_mass_pt_all_histo_PairsMuonSEPM_muonLowPt210SigmaPDCA_FT0C_" + varMin + "_" + varMax
    #fInName = "CB2_VWG__2.5_4.5"
    fInName = "fit_plot_CB2_CB2_Pol4Exp__2.6_4.0_int"
    
    #print("{}/{}__{}.root".format(path, histName, fInName))
    print("{}/{}.root".format(path, fInName))

    #fIn = ROOT.TFile("{}/{}__{}.root".format(path, histName, fInName), "READ")
    fIn = ROOT.TFile("{}/{}.root".format(path, fInName), "READ")
    #canvasIn = fIn.Get("fit_plot_{}".format(fInName))
    canvasIn = fIn.Get("fit_plot_CB2_CB2_Pol4Exp__2.6_4.0_histBkgSubtrSEPM_Pt210_Int")
    listOfPrimitives = canvasIn.GetListOfPrimitives()

    print(list(listOfPrimitives))
    
    # Frame
    #frame = listOfPrimitives.At(0)
    #frame.GetXaxis().SetRangeUser(2.6, 4.2)
    #if varMin == "0" and varMax == "20":
        #frame.GetYaxis().SetRangeUser(1e3, 3e6)
    #else:
        #frame.GetYaxis().SetRangeUser(1e2, 1e5)
    #frame.SetTitle(" ")
    #frame.GetXaxis().SetTitle("#it{m}_{#mu#mu} (GeV/#it{c}^{2})")
    #frame.GetYaxis().SetTitle("Counts per 20 MeV/#it{c}^{2}")

    frame1 = ROOT.TH2D("histGrid1", "", 100, 2.6, 4, 100, 500, 1e7)
    frame2 = ROOT.TH2D("histGrid2", "", 100, 2.6, 4, 100, 5e2, 1e6)

    # Histograms
    histData = listOfPrimitives.At(4)
    histData.SetMarkerStyle(20)
    histData.SetMarkerColor(ROOT.kBlack)

    # PDFs
    pdfSum = listOfPrimitives.At(5)
    pdfJpsi = listOfPrimitives.At(6)
    pdfPsi2s = listOfPrimitives.At(7)
    pdfBkg = listOfPrimitives.At(8)

    canvasOut = TCanvas("canvasOut", "canvasOut", 800, 800)
    canvasOut.SetTickx(1)
    canvasOut.SetTicky(1)
    ROOT.gPad.SetLogy(1)
    frame1.Draw()
    histData.Draw("EP SAME")
    pdfBkg.Draw("SAME")
    pdfSum.Draw("SAME")
    pdfJpsi.Draw("SAME")
    pdfPsi2s.Draw("SAME")
    

    legend = TLegend(0.65, 0.47, 0.82, 0.82, " ", "brNDC")
    SetLegend(legend)
    legend.SetTextSize(0.04)
    legend.AddEntry(histData,"Data", "P")
    legend.AddEntry(pdfSum,"Fit", "L")
    legend.AddEntry(pdfJpsi,"J/#psi", "L")
    legend.AddEntry(pdfPsi2s,"#psi(2S)", "L")
    legend.AddEntry(pdfBkg,"Background", "L")
    legend.Draw()

    letexTitle.DrawLatex(0.18, 0.88, "ALICE Performance, Pb#minusPb, #sqrt{#it{s}_{NN}} = 5.36 TeV")
    letexTitle.DrawLatex(0.18, 0.81, "Inclusive J/#psi #rightarrow #mu^{+}#mu^{-}, 2.5 < #it{y} < 4, " + varMin + "#minus" + varMax + "%")


    canvasOut.cd()
    pad = ROOT.TPad("pad1", "pad1", 0.6, 0.6, 0.85, 0.85)
    pad.Draw()
    pad.cd()
    frame2.Draw()
    ROOT.gPad.SetLogy(True)
    histData.Draw("EP SAME")
    pdfBkg.Draw("SAME")
    pdfSum.Draw("SAME")
    pdfJpsi.Draw("SAME")
    pdfPsi2s.Draw("SAME")

    canvasOut.Update()

    input()
    canvasOut.SaveAs("figures/invariantMass_pt_" + varMin + "_" + varMax + ".pdf")

    fOut = ROOT.TFile("performance_plot_psi2S.root", "RECREATE")
    fOut.cd()
    canvasOut.Write("canvas")
    histData.Write("histData")
    pdfBkg.Write("pdfBkg")
    pdfSum.Write("pdfSum")
    pdfJpsi.Write("pdfJpsi")
    pdfPsi2s.Write("pdfPsi2s")
    fOut.Close()

if __name__ == '__main__':
    main()