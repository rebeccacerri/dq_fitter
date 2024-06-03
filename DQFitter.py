from telnetlib import DO
import os
import ROOT
from ROOT import TCanvas, TFile, TH1F, TPaveText, RooRealVar, RooDataSet, RooWorkspace, RooDataHist, RooArgSet
from ROOT import gPad, gROOT
from utils.plot_library import DoResidualPlot, DoPullPlot, DoCorrMatPlot, DoAlicePlot, LoadStyle
from utils.utils_library import ComputeSigToBkg, ComputeSignificance

class DQFitter:
    def __init__(self, fInName, fInputName, fOutPath, minDatasetRange, maxDatasetRange):
        self.fPdfDict          = {}
        self.fOutPath          = fOutPath
        self.fFileOutName      = "{}/output__{}_{}.root".format(fOutPath, minDatasetRange, maxDatasetRange)
        self.fFileOut          = TFile(self.fFileOutName, "RECREATE")
        self.fFileIn           = TFile.Open(fInName)
        self.fInputName        = fInputName
        self.fInput            = 0
        self.fRooWorkspace     = RooWorkspace('w','workspace')
        self.fParNames         = []
        self.fFitMethod        = "likelyhood"
        self.fFitRangeMin      = minDatasetRange
        self.fFitRangeMax      = maxDatasetRange
        self.fTrialName        = ""
        self.fMinDatasetRange  = minDatasetRange
        self.fMaxDatasetRange  = maxDatasetRange
        self.fRooMass          = RooRealVar("m", "#it{M} (GeV/#it{c}^{2})", self.fMinDatasetRange, self.fMaxDatasetRange)
        self.fDoResidualPlot   = False
        self.fDoPullPlot       = False
        self.fDoCorrMatPlot    = False
        #self.fPrintSB          = False
        self.fFileOutNameNew   = ""

    def GetFileOutName(self):
        return self.fFileOutNameNew

    def SetFitConfig(self, pdfDict):
        '''
        Method set the configuration of the fit
        '''
        self.fPdfDict = pdfDict
        # Exception to take into account the case in which AnalysisResults.root is used
        if "analysis-same-event-pairing/output" in self.fInputName:
            hlistIn = self.fFileIn.Get("analysis-same-event-pairing/output")
            listName = self.fInputName.replace("analysis-same-event-pairing/output/", "")
            listIn = hlistIn.FindObject(listName.replace("/Mass", ""))
            self.fInput = listIn.FindObject("Mass")
        else:
            self.fInput = self.fFileIn.Get(self.fInputName)

        if not "TTree" in self.fInput.ClassName():
            self.fInput.Rebin(pdfDict["rebin"])
            self.fInput.Sumw2()
        self.fDoResidualPlot = pdfDict["doResidualPlot"]
        self.fDoPullPlot = pdfDict["doPullPlot"]
        self.fDoCorrMatPlot = pdfDict["doCorrMatPlot"]
        pdfList = []
        for pdf in self.fPdfDict["pdf"][:-1]:
            self.fTrialName = self.fTrialName + pdf + "_"
        #if "analysis-same-event-pairing/output" in self.fInputName:
            #self.fTrialName = listName.replace("/Mass", "") + "_" + self.fTrialName + pdf + "_"
        #else:
            #self.fTrialName = self.fInputName + "_" + self.fTrialName + pdf + "_"
        for i in range(0, len(self.fPdfDict["pdf"])):
            if not self.fPdfDict["pdf"][i] == "SUM":
                gROOT.ProcessLineSync(".x ../fit_library/{}Pdf.cxx+".format(self.fPdfDict["pdf"][i]))
        
        for i in range(0, len(self.fPdfDict["pdf"])):
            parVal = self.fPdfDict["parVal"][i]
            parLimMin = self.fPdfDict["parLimMin"][i]
            parLimMax = self.fPdfDict["parLimMax"][i]
            parName = self.fPdfDict["parName"][i]

            if not len(parVal) == len(parLimMin) == len(parLimMax) == len(parName):
                print("WARNING! Different size if the input parameters in the configuration")
                print(parVal)
                print(parLimMin)
                print(parLimMax)
                print(parName)
                exit()

            if not self.fPdfDict["pdf"][i] == "SUM":
                # Filling parameter list
                for j in range(0, len(parVal)):
                    if ("sum" in parName[j]) or ("prod" in parName[j]):
                        self.fRooWorkspace.factory("{}".format(parName[j]))
                        # Replace the exression of the parameter with the name of the parameter
                        r1 = parName[j].find("::") + 2
                        r2 = parName[j].find("(", r1)
                        parName[j] = parName[j][r1:r2]
                        self.fRooWorkspace.factory("{}[{}]".format(parName[j], parVal[j]))
                    else:
                        if (parLimMin[j] == parLimMax[j]):
                            self.fRooWorkspace.factory("{}[{}]".format(parName[j], parVal[j]))
                        else:
                            self.fRooWorkspace.factory("{}[{},{},{}]".format(parName[j], parVal[j], parLimMin[j], parLimMax[j]))

                        self.fParNames.append(parName[j]) # only free parameters will be reported in the histogram of results

                # Define the pdf associating the parametes previously defined
                nameFunc = self.fPdfDict["pdf"][i]
                nameFunc += "Pdf::{}Pdf(m[{},{}]".format(self.fPdfDict["pdfName"][i], self.fMinDatasetRange, self.fMaxDatasetRange)
                pdfList.append(self.fPdfDict["pdfName"][i])
                for j in range(0, len(parVal)):
                    nameFunc += ",{}".format(parName[j])
                nameFunc += ")"
                self.fRooWorkspace.factory(nameFunc)
            else:
                nameFunc = self.fPdfDict["pdf"][i]
                nameFunc += "::sum("
                for j in range(0, len(pdfList)):
                    nameFunc += "{}[{},{},{}]*{}Pdf".format(parName[j], parVal[j], parLimMin[j], parLimMax[j], pdfList[j])
                    self.fParNames.append(parName[j])
                    if not j == len(pdfList) - 1:
                        nameFunc += ","
                nameFunc += ")"
                self.fRooWorkspace.factory(nameFunc)

    def CheckSignalTails(self, fitRangeMin, fitRangeMax):
        '''
        Method to plot the signal tail parameters
        '''
        self.fRooWorkspace.Print()
        self.fRooWorkspace.writeToFile("{}_tails.root".format(self.fTrialName))
        ROOT.gDirectory.Add(self.fRooWorkspace)

    def FitInvMassSpectrum(self, fitMethod, fitRangeMin, fitRangeMax):
        '''
        Method to perform the fit to the invariant mass spectrum
        '''
        LoadStyle()
        trialName = self.fTrialName + "_" + str(fitRangeMin) + "_" + str(fitRangeMax)
        self.fRooWorkspace.Print()
        pdf = self.fRooWorkspace.pdf("sum")
        self.fRooMass.setRange("range", fitRangeMin, fitRangeMax)
        fRooPlot = self.fRooMass.frame(ROOT.RooFit.Title(trialName), ROOT.RooFit.Range("range"))
        fRooPlotExtra = self.fRooMass.frame(ROOT.RooFit.Title(trialName), ROOT.RooFit.Range("range"))
        fRooPlotOff = self.fRooMass.frame(ROOT.RooFit.Title(trialName))
        if "TTree" in self.fInput.ClassName():
            print("########### Perform unbinned fit ###########")
            rooDs = RooDataSet("data", "data", RooArgSet(self.fRooMass), ROOT.RooFit.Import(self.fInput))
        else:
            print("########### Perform binned fit ###########")
            rooDs = RooDataHist("data", "data", RooArgSet(self.fRooMass), ROOT.RooFit.Import(self.fInput))

        # Select the fit method
        if fitMethod == "likelyhood":
            print("########### Perform likelyhood fit ###########")
            rooFitRes = ROOT.RooFitResult(pdf.fitTo(rooDs, ROOT.RooFit.Range(fitRangeMin,fitRangeMax), ROOT.RooFit.Save()))
        #if fitMethod == "chi2":
            #print("########### Perform X2 fit ###########")
            #rooFitRes = ROOT.RooFitResult(pdf.chi2FitTo(rooDs, ROOT.RooFit.Range(fitRangeMin,fitRangeMax),ROOT.RooFit.PrintLevel(-1), ROOT.RooFit.Save()))

        rooDs.plotOn(fRooPlot, ROOT.RooFit.MarkerStyle(20), ROOT.RooFit.MarkerSize(0.6), ROOT.RooFit.Range(fitRangeMin, fitRangeMax))
        pdf.plotOn(fRooPlot, ROOT.RooFit.LineColor(ROOT.kRed+1), ROOT.RooFit.LineWidth(2), ROOT.RooFit.Range(fitRangeMin, fitRangeMax))
        #pdf.plotOn(fRooPlot, ROOT.RooFit.VisualizeError(rooFitRes, 1), ROOT.RooFit.FillColor(ROOT.kRed-10), ROOT.RooFit.Range(fitRangeMin, fitRangeMax))
        rooDs.plotOn(fRooPlot, ROOT.RooFit.MarkerStyle(20), ROOT.RooFit.MarkerSize(0.6), ROOT.RooFit.Range(fitRangeMin, fitRangeMax))
        pdf.plotOn(fRooPlot, ROOT.RooFit.LineColor(ROOT.kRed+1), ROOT.RooFit.LineWidth(2), ROOT.RooFit.Range(fitRangeMin, fitRangeMax))
        for i in range(0, len(self.fPdfDict["pdf"])):
            if not self.fPdfDict["pdfName"][i] == "SUM":
                pdf.plotOn(fRooPlot, ROOT.RooFit.Components("{}Pdf".format(self.fPdfDict["pdfName"][i])), ROOT.RooFit.LineColor(self.fPdfDict["pdfColor"][i]), ROOT.RooFit.LineStyle(self.fPdfDict["pdfStyle"][i]), ROOT.RooFit.LineWidth(2), ROOT.RooFit.Range(fitRangeMin, fitRangeMax))
        
        reduced_chi2 = 0
        if "TTree" in self.fInput.ClassName():
            #Fit with RooChi2Var
            # To Do : Find a way to get the number of bins differently. The following is a temparary solution.
            # WARNING : The largest fit range has to come first in the config file otherwise it does not work
            # Convert unbinned dataset into binned dataset
            rooDsBinned = RooDataHist("rooDsBinned","binned version of rooDs",RooArgSet(self.fRooMass),rooDs)
            nbinsperGev = rooDsBinned.numEntries() / (self.fPdfDict["fitRangeMax"][0] - self.fPdfDict["fitRangeMin"][0])
            nBins = (fitRangeMax - fitRangeMin) * nbinsperGev
        
            chi2 = ROOT.RooChi2Var("chi2", "chi2", pdf, rooDsBinned)
            nPars = rooFitRes.floatParsFinal().getSize()
            ndof = nBins - nPars
            reduced_chi2 = chi2.getVal() / ndof
        else:
            #Fit with RooChi2Var
            # To Do : Find a way to get the number of bins differently. The following is a temparary solution.
            # WARNING : The largest fit range has to come first in the config file otherwise it does not work
            nbinsperGev = rooDs.numEntries() / (self.fPdfDict["fitRangeMax"][0] - self.fPdfDict["fitRangeMin"][0])
            nBins = (fitRangeMax - fitRangeMin) * nbinsperGev
        
            chi2 = ROOT.RooChi2Var("chi2", "chi2", pdf, rooDs)
            nPars = rooFitRes.floatParsFinal().getSize()
            ndof = nBins - nPars
            reduced_chi2 = chi2.getVal() / ndof

        index = 1
        histResults = TH1F("fit_results_{}_{}".format(trialName, self.fInputName), "fit_results_{}_{}".format(trialName, self.fInputName), len(self.fParNames), 0., len(self.fParNames))
        for parName in self.fParNames:
            histResults.GetXaxis().SetBinLabel(index, parName)
            histResults.SetBinContent(index, self.fRooWorkspace.var(parName).getVal())
            histResults.SetBinError(index, self.fRooWorkspace.var(parName).getError())
            index += 1

        histResults.GetXaxis().SetBinLabel(index, "chi2")
        histResults.SetBinContent(index, reduced_chi2)

        extraText = [] # extra text for "propaganda" plots

        paveText = TPaveText(0.60, 0.45, 0.99, 0.94, "brNDC")
        paveText.SetTextFont(42)
        paveText.SetTextSize(0.025)
        paveText.SetFillColor(ROOT.kWhite)
        for parName in self.fParNames:
            paveText.AddText("{} = {:.4f} #pm {:.4f}".format(parName, self.fRooWorkspace.var(parName).getVal(), self.fRooWorkspace.var(parName).getError()))
            if self.fPdfDict["parForAlicePlot"].count(parName) > 0:
                text = self.fPdfDict["parNameForAlicePlot"][self.fPdfDict["parForAlicePlot"].index(parName)]
                if "sig" in parName:
                    extraText.append("{} = {:.0f} #pm {:.0f}".format(text, self.fRooWorkspace.var(parName).getVal(), self.fRooWorkspace.var(parName).getError()))
                else:
                    extraText.append("{} = {:.3f} #pm {:.3f}".format(text, self.fRooWorkspace.var(parName).getVal(), self.fRooWorkspace.var(parName).getError()))
            for i in range(0, len(self.fPdfDict["pdfName"])):
                if self.fPdfDict["pdfName"][i] in parName:
                    (paveText.GetListOfLines().Last()).SetTextColor(self.fPdfDict["pdfColor"][i])

        # Add the chiSquare value
        paveText.AddText("n Par = %3.2f" % (nPars)) 
        paveText.AddText("n Bins = %3.2f" % (nBins))
        paveText.AddText("#bf{#chi^{2}/dof = %3.2f}" % reduced_chi2)
      
        fRooPlot.addObject(paveText)
        extraText.append("#chi^{2}/dof = %3.2f" % reduced_chi2)
     
        # Fit plot
        canvasFit = TCanvas("fit_plot_{}_{}".format(trialName, self.fInputName), "fit_plot_{}_{}".format(trialName, self.fInputName), 800, 600)
        canvasFit.SetLeftMargin(0.15)
        gPad.SetLeftMargin(0.15)
        fRooPlot.GetYaxis().SetTitleOffset(1.4)
        fRooPlot.Draw()

        for parName in self.fPdfDict["parForAlicePlot"]:
            if "sOverB_Jpsi" in parName:
                sig_mean = self.fRooWorkspace.var("mean_Jpsi").getVal()
                sig_width = self.fRooWorkspace.var("width_Jpsi").getVal()
                min_range = sig_mean - 3. * sig_width
                max_range = sig_mean + 3. * sig_width
                sig_to_bkg = ComputeSigToBkg(canvasFit, "JpsiPdf", "BkgPdf", min_range, max_range)
                extraText.append("S/B_{3#sigma} = %3.2f" % sig_to_bkg)
            if "sgnf_Jpsi" in parName:
                sig_mean = self.fRooWorkspace.var("mean_Jpsi").getVal()
                sig_width = self.fRooWorkspace.var("width_Jpsi").getVal()
                min_range = sig_mean - 3. * sig_width
                max_range = sig_mean + 3. * sig_width
                significance = ComputeSignificance(canvasFit, "JpsiPdf", "BkgPdf", min_range, max_range)
                extraText.append("S/#sqrt{(S+B)}_{3#sigma} = %1.0f" % significance)
            if "corrMatrStatus" in parName:
                covMatrixStatus =rooFitRes.covQual()
                extraText.append("Cov. matrix status= %i" % covMatrixStatus)
        
        # Print the fit result
        rooFitRes.Print()
        
        # Official fit plot
        if self.fPdfDict["doAlicePlot"]:
            cosmetics = self.fPdfDict["cosmeticsForAlicePlot"]
            DoAlicePlot(rooDs, pdf, fRooPlotOff, self.fPdfDict, self.fInputName, trialName, self.fOutPath, extraText, cosmetics)

        # Save results
        self.fFileOut.cd()
        histResults.Write()
        canvasFit.Write()

        rooDs.plotOn(fRooPlotExtra, ROOT.RooFit.DataError(ROOT.RooAbsData.SumW2), ROOT.RooFit.Range(fitRangeMin, fitRangeMax))
        pdf.plotOn(fRooPlotExtra, ROOT.RooFit.Range(fitRangeMin, fitRangeMax))

        # Residual plot
        if self.fDoResidualPlot:
            canvasResidual = DoResidualPlot(fRooPlotExtra, self.fRooMass, trialName)
            canvasResidual.Write()

        # Pull plot
        if self.fDoPullPlot:
            canvasPull = DoPullPlot(fRooPlotExtra, self.fRooMass, trialName)
            canvasPull.Write()

        # Correlation matrix plot
        if self.fDoCorrMatPlot:
            canvasCorrMat = DoCorrMatPlot(rooFitRes, trialName)
            canvasCorrMat.Write()

        del self.fRooWorkspace
        self.fFileIn.Close()


    def SingleFit(self):
        '''
        Method to perform a single fit (calling multi-trial from external script)
        '''
        self.FitInvMassSpectrum(self.fFitMethod, self.fFitRangeMin, self.fFitRangeMax)
        self.fFileOut.Close()

        # Update file name
        trialName = self.fInputName + "_" + self.fTrialName + "_" + str(self.fFitRangeMin) + "_" + str(self.fFitRangeMax) + ".root"
        oldFileOutName = self.fFileOutName
        newFileOutName = oldFileOutName.replace(str(self.fFitRangeMin) + "_" + str(self.fFitRangeMax) + ".root", trialName)
        self.fFileOutNameNew = newFileOutName
        os.rename(oldFileOutName, newFileOutName)

