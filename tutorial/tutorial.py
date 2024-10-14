from traceback import print_tb
import yaml
import json
import sys
import argparse
from array import array
import os
from os import path
import ROOT
from ROOT import TFile, TF1, TH1F, TTree
from ROOT import gRandom
sys.path.append('../')
#from DQFitter import DQFitter
from DQFitter import DQFitter

def GenerateTutorialSample():
    print("----------- GENERATE TUTORIAL SAMPLE -----------")
    nEvents = 100000
    SigOverBkg1 = 0.03
    SigOverBkg2 = SigOverBkg1 / 10.
    
    fOut = TFile("tutorial.root", "RECREATE")

    funcMassBkg = TF1("funcMassBkg", "expo", 0., 5.)
    funcMassBkg.SetParameter(0, 0.00)
    funcMassBkg.SetParameter(1, -0.5)

    funcMassSig1 = TF1("funcMassSig1", "gaus", 0., 5.)
    funcMassSig1.SetParameter(0, 1.0)
    funcMassSig1.SetParameter(1, 3.096)
    funcMassSig1.SetParameter(2, 0.070)

    funcMassSig2 = TF1("funcMassSig2", "gaus", 0., 5.)
    funcMassSig2.SetParameter(0, 1.0)
    funcMassSig2.SetParameter(1, 3.686)
    funcMassSig2.SetParameter(2, 1.05 * 0.070)

    histMass = TH1F("histMass", "histMass", 100, 0., 5.) # histo di massa invariante
    histMass.FillRandom("funcMassBkg", int(nEvents - (nEvents * SigOverBkg1)))
    histMass.FillRandom("funcMassSig1", int(nEvents * SigOverBkg1))
    histMass.FillRandom("funcMassSig2", int(nEvents * SigOverBkg2))
    histMass.Write()

    print("Data histogram")
    print("counter J/psi = %f" % (int(nEvents * SigOverBkg1)))
    print("counter Psi(2S) = %f" % (int(nEvents * SigOverBkg2)))

    counterSig1 = 0
    counterSig2 = 0

    fMass = array('f', [0.]) # creo il tree
    tree = TTree("data", "data")
    tree.Branch("fMass", fMass, "fMass/F")

    for iEvent in range(0, nEvents): # Fillo i tree in maniera un pò diversa rispetto a come popolo l'histo (per ora non capito il perchè)
        seed = gRandom.Rndm()
        if seed > SigOverBkg1:
            fMass[0] = funcMassBkg.GetRandom()
        else:
            if seed > SigOverBkg2:
                fMass[0] = funcMassSig1.GetRandom()
                counterSig1 = counterSig1 + 1
            else:
                fMass[0] = funcMassSig2.GetRandom()
                counterSig2 = counterSig2 + 1
        tree.Fill()
    tree.Write()

    fOut.Close()

    print("Data tree")
    print("counter J/psi = %f" % (counterSig1))
    print("counter Psi(2S) = %f" % (counterSig2))

def main():
    print('start')
    parser = argparse.ArgumentParser(description='Arguments to pass') # Crea un nuovo oggetto parser che gestirà gli argomenti da linea di comando. description='Arguments to pass': Fornisce una descrizione per il parser, che sarà mostrata quando si richiede aiuto (--help).
    parser.add_argument('cfgFileName', metavar='text', default='config.yml', help='config file name') # 'cfgFileName': Nome dell'argomento posizionale che deve essere passato alla riga di comando. metavar='text': Specifica come apparirà l'argomento nella documentazione di aiuto. default='config.yml': Imposta un valore predefinito nel caso in cui l'argomento non venga fornito.
    parser.add_argument("--gen_tutorial", help="generate tutorial sample", action="store_true") # Opzione che, se presente, sarà trattata come True. action="store_true": Se l'opzione è specificata, args.gen_tutorial sarà True, altrimenti sarà Fals
    parser.add_argument("--do_fit", help="run the multi trial", action="store_true")
    args = parser.parse_args() # Analizza gli argomenti passati dalla riga di comando e li memorizza in un oggetto args. Ogni argomento può essere accessibile come attributo dell'oggetto args
    print(args) # Stampa l'oggetto args che contiene i valori degli argomenti passati dalla riga di comando
    print('Loading task configuration: ...', end='\r')

    with open(args.cfgFileName, 'r') as jsonCfgFile: # 'r' -> Indica che il file deve essere aperto in modalità di lettura. 'with' -> serve per chiudere il file correttamente
        inputCfg = json.load(jsonCfgFile)
        
    print('Loading task configuration: Done!')

    if args.gen_tutorial:
        GenerateTutorialSample()
    
    if args.do_fit:
        inputFileName  = inputCfg["input"]["input_file_name"]
        outputFileName = inputCfg["output"]["output_file_name"]
        histNames      = inputCfg["input"]["input_name"]
        minFitRanges   = inputCfg["input"]["pdf_dictionary"]["fitRangeMin"]
        maxFitRanges   = inputCfg["input"]["pdf_dictionary"]["fitRangeMax"]
        
        if not path.isdir(outputFileName): # path.isdir(outputFileName): Questa funzione della libreria os.path verifica se il percorso specificato da outputFileName esiste e se è una directory. Restituisce True se il percorso è una directory esistente, altrimenti False
            os.system("mkdir -p %s" % (outputFileName)) # s.system(...): Questo comando esegue un comando di sistema. Qui, viene utilizzato per eseguire il comando mkdir della shell. "mkdir -p %s" % (outputFileName): Costruisce una stringa per il comando di shell. %s viene sostituito con il valore di outputFileName
        for histName in histNames: # for su histoNames, che è una lista di histos. In questo tutorial c'è solo un histo (guarda file di configurazione)
            for minFitRange, maxFitRange in zip(minFitRanges, maxFitRanges): # Lista di minFitRanges e maxFitRanges. Attenzione: se 2 e 2  -> itera 2 volte
                # Reload configuration file (Capire perchè fare il reload)
                with open(args.cfgFileName, 'r') as jsonCfgFile: 
                    inputCfg = json.load(jsonCfgFile)
                pdfDictionary  = inputCfg["input"]["pdf_dictionary"] # Prendo la maggior parte delle info di tutto quello che voglio fare per il fit dal file di configurazione
                dqFitter = DQFitter(inputFileName, histName, outputFileName, minFitRange, maxFitRange) # tipo 'dqFitter = DQFitter("data.root", "histogram1", "/output", 0, 100)' -> Questo comando creerà un oggetto DQFitter: Apre il file ROOT data.root. Legge l'istogramma chiamato histogram1. Crea un file di output chiamato /output/output__0_100.root (range di fitting (con Roofit) tra 0 e 100). Inizializza un workspace RooWorkspace per gestire le variabili di fitting
                print(inputCfg["input"]["pdf_dictionary"]["parName"]) # classico print
                dqFitter.SetFitConfig(pdfDictionary) # Il metodo SetFitConfig viene utilizzato per configurare il fitting, e il parametro passato, pdfDictionary, sembra essere un dizionario che contiene le PDF (funzioni di densità di probabilità) e altre configurazioni necessarie per il fitting
                dqFitter.SingleFit() # fa un singolo fit


if __name__ == '__main__': # Se importi questo script in un altro file, ad esempio: import script, Il codice all'interno di if __name__ == '__main__': non verrà eseguito automaticamente, evitando di eseguire il codice principale per errore.
    main()
