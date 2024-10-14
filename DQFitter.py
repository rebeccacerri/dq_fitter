from telnetlib import DO
import os
import ROOT
from ROOT import TCanvas, TFile, TH1F, TPaveText, RooRealVar, RooDataSet, RooWorkspace, RooDataHist, RooArgSet
from ROOT import gPad, gROOT
from utils.plot_library import DoResidualPlot, DoPullPlot, DoCorrMatPlot, DoAlicePlot, LoadStyle
from utils.utils_library import ComputeSigToBkg, ComputeSignificance, ComputeAlpha

class DQFitter:
    def __init__(self, fInName, fInputName, fOutPath, minDatasetRange, maxDatasetRange): # fInName: nome del file di input, fInputName: nome dell'oggetto specifico che si vuole leggere dal file di input, come un istogramma o una distribuzione salvata nel file ROOT, fOutPath:  percorso di output
        self.fPdfDict          = {} # Inizializza un dizionario vuoto chiamato fPdfDict. È vuoto all'inizio, ma verrà popolato più avanti tramite un metodo come SetFitConfig()
        self.fOutPath          = fOutPath
        self.fFileOutName      = "{}/output__{}_{}.root".format(fOutPath, minDatasetRange, maxDatasetRange)
        self.fFileOut          = TFile(self.fFileOutName, "RECREATE")
        self.fFileIn           = TFile.Open(fInName)
        self.fInputName        = fInputName
        self.fInput            = 0 # self.fInput è un segnaposto per l'oggetto che verrà letto dal file ROOT. Inizializzando la variabile a 0, si indica che l'input non è ancora stato caricato
        self.fRooWorkspace     = RooWorkspace('w','workspace') # Inizializza un workspace di RooFit chiamato 'workspace' e lo assegna alla variabile self.fRooWorkspace. 'w': è il nome abbreviato del workspace. 'workspace': è il nome esteso o descrittivo del workspace. RooWorkspace è una classe di RooFit, un framework per il fitting statistico utilizzato in ROOT.
        self.fParNames         = [] # direi inizializza un set di parametri vuoto.
        self.fFitMethod        = "likelyhood"
        self.fFitRangeMin      = minDatasetRange #  range specifico per il fitting
        self.fFitRangeMax      = maxDatasetRange #  range specifico per il fitting
        self.fTrialName        = "" #  Inizializza la variabile di istanza fTrialName con una stringa vuota (""). fTrialName sembra essere una variabile utilizzata per memorizzare un nome specifico associato a un tentativo o un'esecuzione del fit. Inizializzarla con una stringa vuota significa che, al momento della creazione dell'oggetto, non c'è ancora un nome specifico assegnato per il "tentativo" o l'esecuzione corrente.
        self.fMinDatasetRange  = minDatasetRange # limiti del range del dataset (potrebbe essere uguale a fFitRangeMin, ma non è detto. Potrebbe essere anche più grande perchè magari mi serve prendere ampi range per qualcosa e poi alla fine fare il fit in zone più piccole)
        self.fMaxDatasetRange  = maxDatasetRange # limiti del range del dataset
        self.fRooMass          = RooRealVar("fMass", "#it{M} (GeV/#it{c}^{2})", self.fMinDatasetRange, self.fMaxDatasetRange) # reando una variabile chiamata fRooMass utilizzando la classe RooRealVar di RooFit. RooRealVar è una classe di RooFit che definisce una variabile reale, spesso utilizzata nel contesto del fitting statistico per rappresentare grandezze fisiche, come una massa. "#it{M} (GeV/#it{c}^{2})": Questo è il titolo o etichetta assegnato alla variabile.
        self.fDoResidualPlot   = False # Questa variabile controlla se deve essere generato un residual plot. Un residual plot mostra la differenza tra i dati osservati e i valori previsti dal modello di fitting (residui), permettendo di vedere visivamente quanto bene il modello si adatta ai dati. ----> Residuo = (Dato osservato) - (Dato previsto dal fit).
        self.fDoPullPlot       = False # Questa variabile controlla se deve essere generato un pull plot. Un pull plot rappresenta i pull dei dati, che sono la differenza normalizzata tra i dati osservati e il modello di fit, divisa per l'errore associato a ciascun punto di misura                  ----> Pull = (Datoosservato−Datoprevisto)/Errore(Datoosservato−Datoprevisto)/Errore
        self.fDoCorrMatPlot    = False # Questa variabile controlla se deve essere generata una correlation matrix plot (matrice di correlazione). Una matrice di correlazione mostra le correlazioni tra i parametri del modello di fitting. Ogni elemento della matrice rappresenta la correlazione tra due parametri, con valori compresi tra -1 (fortemente anticorrelato) e 1 (fortemente correlato). Se self.fDoCorrMatPlot viene impostato a True, verrà generato un grafico della matrice di correlazione. Questo tipo di grafico è utile per capire quanto i parametri del fit sono correlati tra loro
        self.fFileOutNameNew   = "" #  istanza chiamata fFileOutNameNew e viene inizializzata come una stringa vuota (""

    def GetFileOutName(self): # questo metodo è progettato per restituire il nome del file di output memorizzato nella variabile self.fFileOutNameNew
        return self.fFileOutNameNew

    def SetFitConfig(self, pdfDict):
        '''
        Method set the configuration of the fit
        '''
        self.fPdfDict = pdfDict
        # Exception to take into account the case in which AnalysisResults.root is used
        if "analysis-same-event-pairing/output" in self.fInputName:
            hlistIn = self.fFileIn.Get("analysis-same-event-pairing/output") # sta recuperando un oggetto, probabilmente un histogramma o una lista di oggetti, dal file ROOT self.fFileIn, situato nel percorso "analysis-same-event-pairing/output". Questo oggetto può quindi essere analizzato o visualizzato in base alle necessità dell'analisi fisica
            listName = self.fInputName.replace("analysis-same-event-pairing/output/", "") # rimuove la parte "analysis-same-event-pairing/output/" da self.fInputName e assegna il risultato a listName. Questo permette di ottenere il nome puro di un oggetto senza il percorso completo, semplificando il suo utilizzo nelle operazioni successive del programma
            listIn = hlistIn.FindObject(listName.replace("/Mass", "")) # listName.replace("/Mass", ""): Qui viene utilizzato il metodo replace per modificare il valore di listName. Viene cercata la sottostringa "/Mass" all'interno di listName e, se trovata, viene rimossa (sostituita con una stringa vuota ""). Per esempio: "histogram_mass/Mass" dopo il replace, diventa: "histogram_mass". hlistIn.FindObject(): Il metodo tenta di trovare un oggetto specifico nella collezione basato sul nome modificato. Se l'oggetto viene trovato, viene assegnato a listIn. listIn: Questa variabile conterrà il riferimento all'oggetto trovato all'interno di hlistIn, se esiste. Se l'oggetto non viene trovato, listIn sarà probabilmente None
            self.fInput = listIn.FindObject("Mass")
        else:
            self.fInput = self.fFileIn.Get(self.fInputName)

        # Per Tree
        #if "analysis-same-event-pairing/output" in self.fInputName:
        #    hlistIn = self.fFileIn.Get("analysis-same-event-pairing/output") # sta recuperando un oggetto, probabilmente un histogramma o una lista di oggetti, dal file ROOT self.fFileIn, situato nel percorso "analysis-same-event-pairing/output". Questo oggetto può quindi essere analizzato o visualizzato in base alle necessità dell'analisi fisica
        #    listName = self.fInputName.replace("analysis-same-event-pairing/output/", "") # rimuove la parte "analysis-same-event-pairing/output/" da self.fInputName e assegna il risultato a listName. Questo permette di ottenere il nome puro di un oggetto senza il percorso completo, semplificando il suo utilizzo nelle operazioni successive del programma
        #    listIn = hlistIn.FindObject(listName.replace("/Mass", "")) # listName.replace("/Mass", ""): Qui viene utilizzato il metodo replace per modificare il valore di listName. Viene cercata la sottostringa "/Mass" all'interno di listName e, se trovata, viene rimossa (sostituita con una stringa vuota ""). Per esempio: "histogram_mass/Mass" dopo il replace, diventa: "histogram_mass". hlistIn.FindObject(): Il metodo tenta di trovare un oggetto specifico nella collezione basato sul nome modificato. Se l'oggetto viene trovato, viene assegnato a listIn. listIn: Questa variabile conterrà il riferimento all'oggetto trovato all'interno di hlistIn, se esiste. Se l'oggetto non viene trovato, listIn sarà probabilmente None
        #    self.fInput = listIn.FindObject("Mass")
        #elif "DF_2338657052269120/O2rtdileptmtree" in self.fInputName:
        #    hlistIn = self.fFileIn.Get("DF_2338657052269120/O2rtdileptmtree")  # Recupera il TTree
        #    if isinstance(hlistIn, ROOT.TTree):  # Verifica che hlistIn sia un TTree
        #        branchName = "fMass"  # Nome del branch 
        #        self.fInput = hlistIn.GetBranch(branchName)  # Usa GetBranch per accedere al branch
        #        if not self.fInput:
        #            print(f"Branch {branchName} non trovato nel TTree.")
        #    else:
        #        self.fInput = None  # Se hlistIn non è un TTree, non può contenere branch
        #else:
        #    self.fInput = self.fFileIn.Get(self.fInputName) 
        #


        if not "TTree" in self.fInput.ClassName():
            self.fInput.Rebin(pdfDict["rebin"]) # Si assicura che le operazioni successive, come Rebin() e Sumw2(), vengano eseguite solo se l'oggetto non è un TTree, poiché queste operazioni sono tipicamente applicate a istogrammi e non a TTrees
            self.fInput.Sumw2()
        self.fDoResidualPlot = pdfDict["doResidualPlot"] # pdfDict è un dizionario che contiene parametri di configurazione per l'analisi. In questo caso, "doResidualPlot" è una chiave del dizionario che si presume contenga un valore booleano (True o False). Questo valore è probabilmente impostato da una configurazione esterna (ad esempio, un file di configurazione o parametri passati all'inizio dell'analisi). Un grafico dei residui mostra la differenza tra i valori osservati e quelli previsti da un modello (i "residui"). Questo tipo di grafico è utile per verificare se il modello scelto è appropriato per i dati. Se i residui sono distribuiti in modo casuale attorno allo zero, il modello è buono; se mostrano uno schema sistematico, il modello potrebbe non essere adatto.
        self.fDoPullPlot = pdfDict["doPullPlot"] # rappresentare le differenze normalizzate tra i valori osservati e quelli attesi, tenendo conto delle incertezze. I "pulls" vengono calcolati come: pull = osservato - previsto / incertezze. Questo aiuta a capire quanto i dati si discostano dalle aspettative del modello in modo normalizzato. Un pull vicino allo zero indica una buona corrispondenza, mentre pull molto grandi suggeriscono possibili discrepanze.
        self.fDoCorrMatPlot = pdfDict["doCorrMatPlot"] # mostra la correlazione tra variabili o parametri (Il grafico della matrice di correlazione visualizza le correlazioni tra variabili in un dataset o i parametri di un modello. Ogni cella nella matrice rappresenta il coefficiente di correlazione tra due variabili. Un valore vicino a 1 indica una forte correlazione positiva, mentre valori vicini a -1 indicano una correlazione negativa. Un valore di 0 significa che non c’è correlazione. Questo tipo di grafico è utile per visualizzare le relazioni tra diversi parametri.)
        pdfList = [] # sta creando una lista vuota chiamata pdfList
        for pdf in self.fPdfDict["pdf"][:-1]: # self.fPdfDict["pdf"][:-1]: questo accede alla chiave "pdf" del dizionario self.fPdfDict, che presumo contenga una lista di nomi o stringhe. Lo slicing [:-1] esclude l'ultimo elemento della lista, quindi il ciclo for itera solo sugli elementi fino al penultimo. Qui, ogni elemento della lista (tranne l'ultimo) viene assegnato alla variabile pdf durante ogni iterazione.
            self.fTrialName = self.fTrialName + pdf + "_" # Ogni stringa pdf viene concatenata a self.fTrialName insieme a un underscore _ . Se, ad esempio, i valori nella lista sono ["file1", "file2", "file3"], il ciclo costruirà una stringa come: self.fTrialName = "file1_file2_".
        #if "analysis-same-event-pairing/output" in self.fInputName:
            #self.fTrialName = listName.replace("/Mass", "") + "_" + self.fTrialName + pdf + "_"
        #else:
            #self.fTrialName = self.fInputName + "_" + self.fTrialName + pdf + "_"
        for i in range(0, len(self.fPdfDict["pdf"])): # Il ciclo for scorre attraverso l'indice di tutti gli elementi della lista self.fPdfDict["pdf"].
            if not self.fPdfDict["pdf"][i] == "SUM": # esegue uno script C++ corrispondente per ciascun PDF, a meno che il nome non sia "SUM". Se l'elemento è diverso da "SUM", il codice procede all'esecuzione di quanto scritto nel corpo del if. La condizione impedisce l'esecuzione per il PDF con nome "SUM" (che potrebbe essere un tipo speciale o una somma di più PDF)
                gROOT.ProcessLineSync(".x ../fit_library/{}Pdf.cxx+".format(self.fPdfDict["pdf"][i])) # gROOT.ProcessLineSync: Questa funzione appartiene alla libreria ROOT e permette di eseguire comandi ROOT direttamente dal codice Python (o anche da C++). È utile per eseguire script ROOT o codice C++ a runtime. .x ../fit_library/{}Pdf.cxx+".format(self.fPdfDict["pdf"][i]): Qui viene costruito dinamicamente un comando che ROOT eseguirà. Il comando caricherà ed eseguirà un file C++ (.cxx) dalla directory ../fit_library/. Il + alla fine del file .cxx dice a ROOT di compilare e caricare dinamicamente la classe o funzione definita in quel file. Per ciascun PDF che non è "SUM", carica ed esegue il corrispondente file C++ che dovrebbe contenere la definizione del PDF o altre istruzioni necessarie. ATTENZIONE: in realtà non sta ancora eseguendo il fit sui dati, ma sta solo caricando e compilando i file C++ necessari che contengono la definizione delle funzioni di probabilità (PDF).
        
        for i in range(0, len(self.fPdfDict["pdf"])):
            parVal = self.fPdfDict["parVal"][i] # Qui si ottiene la lista dei valori dei parametri associati al PDF corrente (indice i)
            parLimMin = self.fPdfDict["parLimMin"][i] # parLimMin è una lista che contiene i limiti inferiori per ciascun parametro del PDF corrente.
            parLimMax = self.fPdfDict["parLimMax"][i]
            parName = self.fPdfDict["parName"][i] # parName è la lista che contiene i nomi dei parametri associati al PDF corrente.

            if not len(parVal) == len(parLimMin) == len(parLimMax) == len(parName):
                print("WARNING! Different size if the input parameters in the configuration")
                print(parVal)
                print(parLimMin)
                print(parLimMax)
                print(parName)
                exit()

            if not self.fPdfDict["pdf"][i] == "SUM":
                # Filling parameter list
                for j in range(0, len(parVal)): # Viene avviato un ciclo per iterare sui parametri di ciascun PDF. Ogni parametro ha un nome (parName[j]), un valore (parVal[j]), e limiti inferiori e superiori (parLimMin[j] e parLimMax[j]).
                    if ("sum" in parName[j]) or ("prod" in parName[j]):
                        self.fRooWorkspace.factory("{}".format(parName[j])) # Se il nome contiene "sum" o "prod", viene creata un'istanza di questo parametro nella workspace usando la funzione factory di ROOT.
                        # Replace the exression of the parameter with the name of the parameter
                        r1 = parName[j].find("::") + 2 # Qui si manipola la stringa parName[j] per estrarre il nome effettivo del parametro. Viene cercato il delimitatore ::, che probabilmente separa un namespace o una categoria dal vero nome del parametro, e poi si trova la parentesi aperta ( che potrebbe essere parte di un'espressione. r1 è l'indice subito dopo ::.
                        r2 = parName[j].find("(", r1) # r2 è l'indice della prima parentesi aperta ( dopo r1.
                        parName[j] = parName[j][r1:r2] #  Il nome viene quindi ridotto alla sottostringa tra questi due indici.
                        self.fRooWorkspace.factory("{}[{}]".format(parName[j], parVal[j])) # Il parametro appena estratto viene aggiunto alla workspace con il valore parVal[j]. Questa è una forma semplificata in cui il parametro ha solo un valore (nessun limite minimo o massimo specificato).
                    else:
                        if (parLimMin[j] == parLimMax[j]):
                            self.fRooWorkspace.factory("{}[{}]".format(parName[j], parVal[j])) #  Se il limite inferiore è uguale a quello superiore (parLimMin[j] == parLimMax[j]), viene creato un parametro "fisso" nella workspace, cioè un parametro con un solo valore (non variabile).
                        else:
                            self.fRooWorkspace.factory("{}[{},{},{}]".format(parName[j], parVal[j], parLimMin[j], parLimMax[j])) # Se i limiti sono diversi, viene creato un parametro "libero" con un valore iniziale (parVal[j]) e limiti inferiore e superiore (parLimMin[j] e parLimMax[j])

                        self.fParNames.append(parName[j]) # only free parameters will be reported in the histogram of results

                # Define the pdf associating the parametes previously defined
                nameFunc = self.fPdfDict["pdf"][i] # self.fPdfDict["pdf"][i]: Qui si prende il nome del PDF corrente dalla lista self.fPdfDict["pdf"]. Ad esempio, se self.fPdfDict["pdf"][i] == "Gaussian", allora il nome del PDF sarà "Gaussian"
                nameFunc += "Pdf::{}Pdf(fMass[{},{}]".format(self.fPdfDict["pdfName"][i], self.fMinDatasetRange, self.fMaxDatasetRange) # "Pdf::{}Pdf(fMass[{},{}]": Questa parte sta costruendo la sintassi che verrà passata alla funzione factory di ROOT. Es "GaussianPdf::gaussPdf(fMass[100, 200]"
                pdfList.append(self.fPdfDict["pdfName"][i]) # Viene aggiunto il nome del PDF alla lista pdfList, che tiene traccia dei PDF già processati.
                for j in range(0, len(parVal)):
                    nameFunc += ",{}".format(parName[j]) # Per ogni parametro definito (parVal e parName), viene aggiunto alla stringa nameFunc. Ad esempio, se parName[j] è "mean", verrà aggiunto come ",mean". Es "GaussianPdf::gaussPdf(fMass[100,200],mean,sigma)"
                nameFunc += ")" # Questa linea completa la definizione del PDF e lo inserisce nella workspace. es "GaussianPdf::gaussPdf(fMass[100,200],mean,sigma)"
                self.fRooWorkspace.factory(nameFunc)
            else:
                nameFunc = self.fPdfDict["pdf"][i]
                nameFunc += "::sum(" # Qui il nome della funzione inizia con il nome del PDF seguito da "::sum(", segnalando che il PDF è una combinazione di altri PDF, probabilmente una somma ponderata.
                for j in range(0, len(pdfList)):
                    nameFunc += "{}[{},{},{}]*{}Pdf".format(parName[j], parVal[j], parLimMin[j], parLimMax[j], pdfList[j]) # es "coeff[1,0,2]*gaussPdf"
                    self.fParNames.append(parName[j])
                    if not j == len(pdfList) - 1: # Se ci sono più PDF, vengono separati da virgole (,) con l'ultima parte. "Gaussian::sum(coeff[1,0,2]*gaussPdf, othercoeff[0.5,0,1]*expPdf)"
                        nameFunc += ","
                nameFunc += ")"
                self.fRooWorkspace.factory(nameFunc)

    def CheckSignalTails(self, fitRangeMin, fitRangeMax):
        '''
        Method to plot the signal tail parameters
        '''
        self.fRooWorkspace.Print() #  Stampa tutte le informazioni riguardanti il contenuto della workspace. Questo è utile per diagnosticare il contenuto e verificare che tutti i PDF e i parametri siano stati definiti correttamente.
        self.fRooWorkspace.writeToFile("{}_tails.root".format(self.fTrialName)) # Questo è utile per salvare lo stato attuale della workspace, che include definizioni di PDF, parametri, e altre configurazioni. Può essere utile per l'analisi successiva o per la condivisione dei risultati con altri.
        ROOT.gDirectory.Add(self.fRooWorkspace) # Aggiunge la RooWorkspace attuale alla directory ROOT globale (gDirectory).

    def FitInvMassSpectrum(self, fitMethod, fitRangeMin, fitRangeMax):
        '''
        Method to perform the fit to the invariant mass spectrum
        '''
        LoadStyle()
        trialName = self.fTrialName + "_" + str(fitRangeMin) + "_" + str(fitRangeMax)
        self.fRooWorkspace.Print()
        pdf = self.fRooWorkspace.pdf("sum") # Il metodo pdf("sum") cerca e restituisce un PDF (probability density function) dalla RooWorkspace utilizzando il nome specificato, in questo caso "sum".
        self.fRooMass.setRange("range", fitRangeMin, fitRangeMax) # DA QUI 
        fRooPlot = self.fRooMass.frame(ROOT.RooFit.Title(trialName), ROOT.RooFit.Range("range"))
        fRooPlotExtra = self.fRooMass.frame(ROOT.RooFit.Title(trialName), ROOT.RooFit.Range("range"))
        fRooPlotOff = self.fRooMass.frame(ROOT.RooFit.Title(trialName))
        if "TTree" in self.fInput.ClassName():
            print("########### Perform unbinned fit ###########")
            if self.fPdfDict["sPlot"]["sRun"]:
                sRooVar = RooRealVar(self.fPdfDict["sPlot"]["sVar"], self.fPdfDict["sPlot"]["sVarName"], self.fPdfDict["sPlot"]["sRangeMin"], self.fPdfDict["sPlot"]["sRangeMax"]) # RooRealVar è una classe della libreria RooFit
                sRooVar.setBins(self.fPdfDict["sPlot"]["sBins"])
            rooDs = RooDataSet("data", "data", RooArgSet(self.fRooMass, sRooVar), ROOT.RooFit.Import(self.fInput))
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

        # Code to run sPlot
        if ("TTree" in self.fInput.ClassName()) and self.fPdfDict["sPlot"]["sRun"]:
            sPars = self.fPdfDict["sPlot"]["sPars"]
            sRooPars = []
            for iPar, sPar in enumerate(sPars):
                sRooPars.append(self.fRooWorkspace.var(sPar))

            # TO BE CHECKED: necessary to setConstant the other fit parameters?
            sData = ROOT.RooStats.SPlot("sData", "An SPlot", rooDs, pdf, ROOT.RooArgList(*sRooPars))

            getattr(self.fRooWorkspace, 'import')(rooDs, ROOT.RooFit.Rename("dataWithSWeights"))
            sRooDs = self.fRooWorkspace.data("dataWithSWeights")

            # Create a dataset with sWeights
            dataSw = []
            for iPar, sPar in enumerate(sPars):
                dataSw.append(RooDataSet(sRooDs.GetName(), sRooDs.GetTitle(), sRooDs, sRooDs.get(), "", sPar + "_sw"))

            # Fill histograms with sWeights
            histSw = []
            for iPar, sPar in enumerate(sPars):
                histSw.append(dataSw[iPar].createHistogram(self.fPdfDict["sPlot"]["sVar"]))

            # Write the histograms with sWeights
            self.fFileOut.cd()
            for iPar, sPar in enumerate(sPars):
                histSw[iPar].Write(sPar + "_sw")

        rooDs.plotOn(fRooPlot, ROOT.RooFit.MarkerStyle(20), ROOT.RooFit.MarkerSize(0.6), ROOT.RooFit.Range(fitRangeMin, fitRangeMax))
        pdf.plotOn(fRooPlot, ROOT.RooFit.LineColor(ROOT.kRed+1), ROOT.RooFit.LineWidth(2), ROOT.RooFit.Range(fitRangeMin, fitRangeMax))
        rooDs.plotOn(fRooPlot, ROOT.RooFit.MarkerStyle(20), ROOT.RooFit.MarkerSize(0.6), ROOT.RooFit.Range(fitRangeMin, fitRangeMax))
        pdf.plotOn(fRooPlot, ROOT.RooFit.LineColor(ROOT.kRed+1), ROOT.RooFit.LineWidth(2), ROOT.RooFit.Range(fitRangeMin, fitRangeMax))
        for i in range(0, len(self.fPdfDict["pdf"])):
            if not self.fPdfDict["pdfName"][i] == "SUM":
                pdf.plotOn(fRooPlot, ROOT.RooFit.Components("{}Pdf".format(self.fPdfDict["pdfName"][i])), ROOT.RooFit.LineColor(self.fPdfDict["pdfColor"][i]), ROOT.RooFit.LineStyle(self.fPdfDict["pdfStyle"][i]), ROOT.RooFit.LineWidth(2), ROOT.RooFit.Range(fitRangeMin, fitRangeMax))
        
        reduced_chi2 = 0
        if "TTree" in self.fInput.ClassName():
            # Fit with RooChi2Var
            # To Do : Find a way to get the number of bins differently. The following is a temparary solution.
            # WARNING : The largest fit range has to come first in the config file otherwise it does not work
            # Convert unbinned dataset into binned dataset
            rooDsBinned = RooDataHist("rooDsBinned","binned version of rooDs",RooArgSet(self.fRooMass),rooDs)
            nbinsperGev = rooDsBinned.numEntries() / (self.fPdfDict["fitRangeMax"][0] - self.fPdfDict["fitRangeMin"][0])
            nBins = (fitRangeMax - fitRangeMin) * nbinsperGev
        
            chi2 = ROOT.RooChi2Var("chi2", "chi2", pdf, rooDsBinned, False, ROOT.RooDataHist.SumW2)
            nPars = rooFitRes.floatParsFinal().getSize()
            ndof = nBins - nPars
            reduced_chi2 = chi2.getVal() / ndof
        else:
            # Fit with RooChi2Var
            # To Do : Find a way to get the number of bins differently. The following is a temparary solution.
            # WARNING : The largest fit range has to come first in the config file otherwise it does not work
            nbinsperGev = rooDs.numEntries() / (self.fPdfDict["fitRangeMax"][0] - self.fPdfDict["fitRangeMin"][0])
            nBins = (fitRangeMax - fitRangeMin) * nbinsperGev
        
            chi2 = ROOT.RooChi2Var("chi2", "chi2", pdf, rooDs, False, ROOT.RooDataHist.SumW2)
            nPars = rooFitRes.floatParsFinal().getSize()
            ndof = nBins - nPars
            reduced_chi2 = chi2.getVal() / ndof

        index = 1
        histResults = TH1F("fit_results_{}_{}".format(trialName, self.fInputName), "fit_results_{}_{}".format(trialName, self.fInputName), len(self.fParNames)+4, 0., len(self.fParNames)+4)
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
                sigForIntegral = self.fRooWorkspace.var("sig_Jpsi").getVal()
                bkgForIntegral = self.fRooWorkspace.var("bkg").getVal()
                min_range = sig_mean - 3. * sig_width
                max_range = sig_mean + 3. * sig_width
                sig_to_bkg = ComputeSigToBkg(canvasFit, "JpsiPdf", "BkgPdf", sigForIntegral, bkgForIntegral, min_range, max_range)
                extraText.append("S/B_{3#sigma} = %5.4f" % sig_to_bkg)
                histResults.GetXaxis().SetBinLabel(index+1, "sig_to_bkg")
                histResults.SetBinContent(index+1, sig_to_bkg)
            if "sgnf_Jpsi" in parName:
                sig_mean = self.fRooWorkspace.var("mean_Jpsi").getVal()
                sig_width = self.fRooWorkspace.var("width_Jpsi").getVal()
                sigForIntegral = self.fRooWorkspace.var("sig_Jpsi").getVal()
                bkgForIntegral = self.fRooWorkspace.var("bkg").getVal()
                min_range = sig_mean - 3. * sig_width
                max_range = sig_mean + 3. * sig_width
                significance = ComputeSignificance(canvasFit, "JpsiPdf", "BkgPdf", sigForIntegral, bkgForIntegral, min_range, max_range)
                extraText.append("S/#sqrt{(S+B)}_{3#sigma} = %1.0f" % significance)
                histResults.GetXaxis().SetBinLabel(index+2, "significance")
                histResults.SetBinContent(index+2, significance)
            if "alpha_vn_Jpsi" in parName:
                sig_mean = self.fRooWorkspace.var("mean_Jpsi").getVal()
                sig_width = self.fRooWorkspace.var("width_Jpsi").getVal()
                sigForIntegral = self.fRooWorkspace.var("sig_Jpsi").getVal()
                bkgForIntegral = self.fRooWorkspace.var("bkg").getVal()
                min_range = sig_mean - 3. * sig_width
                max_range = sig_mean + 3. * sig_width
                alpha_vn = ComputeAlpha(canvasFit, "JpsiPdf", "BkgPdf", sigForIntegral, bkgForIntegral, min_range, max_range)
                extraText.append("(S/S+B)_{3#sigma} = %5.4f" % alpha_vn)
                histResults.GetXaxis().SetBinLabel(index+3, "alpha_vn")
                histResults.SetBinContent(index+3, alpha_vn)
            if "corrMatrStatus" in parName:
                covMatrixStatus = rooFitRes.covQual()
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

