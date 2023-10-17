/*****************************************************************************
 * Project: RooFit                                                           *
 *                                                                           *
  * This code was autogenerated by RooClassFactory                            *
 *****************************************************************************/

#ifndef RATIOPOL1POL2PDF
#define RATIOPOL1POL2PDF

#include "RooAbsPdf.h"
#include "RooRealProxy.h"
#include "RooCategoryProxy.h"
#include "RooAbsReal.h"
#include "RooAbsCategory.h"

class RatioPol1Pol2Pdf : public RooAbsPdf {
public:
  RatioPol1Pol2Pdf() {} ;
  RatioPol1Pol2Pdf(const char *name, const char *title,
	    RooAbsReal& _x,
	    RooAbsReal& _P0,
	    RooAbsReal& _P1,
        RooAbsReal& _P2,
        RooAbsReal& _P3,
        RooAbsReal& _P4);
  RatioPol1Pol2Pdf(const RatioPol1Pol2Pdf& other, const char* name=0) ;
  virtual TObject* clone(const char* newname) const { return new RatioPol1Pol2Pdf(*this,newname); }
  inline virtual ~RatioPol1Pol2Pdf() { }

protected:

  RooRealProxy x ;
  RooRealProxy P0 ;
  RooRealProxy P1 ;
  RooRealProxy P2 ;
  RooRealProxy P3 ;
  RooRealProxy P4 ;

  Double_t evaluate() const ;

private:

  ClassDef(RatioPol1Pol2Pdf,1) // Your description goes here...
};

#endif
