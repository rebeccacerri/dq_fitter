#include <iostream>
#include "TMath.h"
#include "TMath.h"
#include "TF1.h"
#include "TROOT.h"

class  UserFunctionLibrary {
 public:

   struct fFuncPol1
   {
     double operator() (double *x, double *par) {
       return par[0] + par[1] * x[0];
     }
   };

   struct fFuncExp
   {
     double operator() (double *x, double *par) {
       return par[0] * TMath::Exp(-par[1] * x[0]);
     }
   };

   struct fFuncGaus
   {
     double operator() (double *x, double *par) {
       return par[0] * TMath::Exp(-0.5 * ((x[0]-par[1])/par[2]) * ((x[0]-par[1])/par[2]));
     }
   };

   struct fFuncExpGaus
   {
     double operator() (double *x, double *par) {
       return par[0] * TMath::Exp(-par[1] * x[0]) + par[2] * TMath::Exp(-0.5 * ((x[0]-par[3])/par[4]) * ((x[0]-par[3])/par[4]));
     }
   };
};
