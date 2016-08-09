// This macro constructs a function from Ralph's analytical expression for the
// charge signal. 
// This is a ROOT macro so that it can be used by ROOT for fitting, like by
// TH1D::Fit(). This is used for fitting waveforms and for fitting electron
// lifetime. 

// from https://root.cern.ch/root/html534/TF1.html#F3
// test from the command line with: root ralphWF.C

#include "TF1.h"
#include "TMath.h"
#include "TCanvas.h"
#include "TLegend.h"
#include "TH1D.h"
#include "TTree.h"
#include "TFile.h"
#include "TMinuit.h"
#include "TRandom3.h"
#include <iostream>
#include <vector>
#include <sstream>
using namespace std;

// options:
//Double_t diagonal = 3.0; // mm


Double_t f(Double_t x, Double_t y, Double_t z) {
  // from Ralph's definition
  return TMath::ATan(x*y/(z*TMath::Sqrt(x*x + y*y + z*z)));
}

Double_t OnePadRotated(Double_t x, Double_t y, Double_t z) {
  // response from one pad. Coordinates are rotated 45 degrees into pad's
  // coordinate system. 
  Double_t diagonal = 3.0; // mm
  // subtract 10 microns to avoid double counting:
  Double_t side_length = diagonal / TMath::Sqrt(2.0); // - 0.01;

  // calculate new variables in rotated coord system of anode pad:
  Double_t x_n = (x - y)/TMath::Sqrt(2);
  Double_t y_n = (x + y)/TMath::Sqrt(2);

  Double_t x1 = x_n - side_length/2.0;
  Double_t x2 = x_n + side_length/2.0;
  Double_t y1 = y_n - side_length/2.0;
  Double_t y2 = y_n + side_length/2.0;

  // handle things if z goes to zero:
  if ( z <= 0) {
      // if the charge is outside the pad, return 0
      // use asymmetric limits so that two pads can't both see a charge
      if ( x_n <= -side_length/2.0 ) { return 0; }
      if ( x_n > side_length/2.0 ) { return 0; } 
      if ( y_n <= -side_length/2.0 ) { return 0; } 
      if ( y_n > side_length/2.0 ) { return 0; }
      // otherwise return 1
      return 1.0;
  }

  return ( f(x2,y2,z) - f(x1,y2,z) - f(x2,y1,z) + f(x1,y1,z) ) / TMath::TwoPi();
}

Double_t OneStrip(Double_t x, Double_t y, Double_t z) {
  // return amplitude (between 0 and 1) from one strip:
  // x is along the strip's length (along diagonals of pads)
  // y is in the plane of the strip, perpendicular to x
  // z is distance from the strip into the drift dimension
  // (0, 0, 0) is at the intersection of the corners of two pads

  Double_t diagonal = 3.0; // mm
  Double_t amplitude = 0.0;

  // sum over all 30 pads
  //for ( int i_pad = 0; i_pad < 1; i_pad++ ) // FIXME only 1 pad for debugging
  for ( int i_pad = 0; i_pad < 30; i_pad++ ){
      Double_t padX = x + i_pad*diagonal - diagonal*14.0; 

      Double_t onePad = OnePadRotated(x + i_pad*diagonal - diagonal*14.0, y, z);
      //Double_t onePad = OnePadRotated(x, y, z); // FIXME -- only one pad
      //cout << "\t\t pad: "<< i_pad << " | pad x: " << padX << " | amplitude: " << onePad << endl;
      amplitude += onePad;
  }
  return amplitude;
}

Double_t OneStripWithIonAndCathode(Double_t x, Double_t y, Double_t z, Double_t z0, Bool_t doDebug=false) {
  // return instantaneous amplitude due to unit charge at x, y, z, where z0 is
  // ion location

  // options
  Double_t driftDistance = 18.16; // mm

  Double_t ionAmplitude = OneStrip(x,y,z0);
  Double_t electronAmplitude = OneStrip(x,y,z);
  if (doDebug) { cout << "\tion: " << ionAmplitude << endl; }
  ionAmplitude*=(1.0-z0/driftDistance);
  if (doDebug) { cout << "\tion after cathode: " << ionAmplitude << endl; }
  if (doDebug) { cout << "\telectron: " << electronAmplitude << endl; }
  if (z > 0) { 
    electronAmplitude*=(1.0-z/driftDistance); 
    if (doDebug){ cout << "\tz: " << z << endl; }
  }
  if (doDebug) { cout << "\telectron after cathode: " << electronAmplitude << endl; }
  Double_t amplitude = electronAmplitude - ionAmplitude; 
  if (doDebug) { cout << "\tamplitude: " << amplitude << endl; }
  return amplitude; 
}

Double_t FinalAmplitude(
  Double_t *var, 
  Double_t *par 
) {

  // return "final" amplitude -- this is the steady-state value that we see
  // after charge has arrived at the anode. 
  // parameters:
  // 1 variable: dist from anode (location z0)
  // 0: x0
  // 1: y0
  // 2: tau
  // 3; energy
  Double_t driftVelocity = 2.0; // mm/microsecond
  Double_t x = par[0];
  Double_t y = par[1];
  Double_t tau = par[2]; // electron lifetime
  Double_t energy = par[3];
  Double_t z0 = var[0];
  Double_t z = 0.0; // final value
  Double_t amplitude = OneStripWithIonAndCathode(x, y, z, z0, false);
  Double_t driftTime = z0/driftVelocity;  
  amplitude*=exp(-driftTime/tau)*energy;
  return amplitude;
}

Double_t OnePCDWithOptions(
  Double_t *var, 
  Double_t *par,
  Int_t iPCD=0, 
  Bool_t useSameZ = false,
  Bool_t doDebug = false
) {
  // reponse of the strip (30 pads in x direction) to one ionization of
  // magnitude q, starting from location x,y,z
  // including ion signal and cathode effect
  // 1 variable: t=time in microseconds
  // 4 parameters:
  //    0: x
  //    1: y
  //    2: z
  //    3: q
  //    4: w (charge weight)

  Double_t triggerTime = 8.0; // microseconds
  Double_t driftVelocity = 2.0; // mm/microsecond

  Double_t t = var[0];
  
  if (doDebug){ cout << "PCD: " << iPCD << " useSameZ: " << useSameZ << endl; }

  size_t xIndex = 0 + iPCD*4;
  Double_t x = par[xIndex];
  if (doDebug){ cout << "\txIndex: " << xIndex << " x: " << x << endl; }

  size_t yIndex = 1 + iPCD*4;
  Double_t y = par[yIndex];
  if (doDebug){ cout << "\tyIndex: " << yIndex << " y: " << y << endl; }

  size_t zIndex = 2 + iPCD*4;
  if (useSameZ){ zIndex=2; }
  Double_t z0 = par[zIndex];
  if (doDebug){ cout << "\tzIndex: " << zIndex << " z0: " << z0 << endl; }

  size_t qIndex = 3 + iPCD*3 + (!useSameZ)*iPCD;
  Double_t q = par[qIndex]; 
  if (doDebug){ cout << "\tqIndex: " << qIndex << " q: " << q << endl; }

  size_t wIndex = 4 + iPCD*4; //what is iPCD*4? 
  Double_t w = par[wIndex];
  if (doDebug){ cout << "\twIndex: " << wIndex << " weight: " << w << endl; }

  Double_t z = z0 - (t-triggerTime) * driftVelocity;  

  if (doDebug){ cout << "\tt: " << t << endl; }

  if (t < triggerTime) { return 0.0; } // wfm is 0 for times before drift starts
  
  //w = TMath::Pi(); 
  Double_t weight_center = 0.5*q*(1.0+sin(w));
  Double_t weight_outer = (q*(1.0 - 0.5*(1.0+sin(w))))/4;
  Double_t Q0 = x + 0.3;
  Double_t R1 = y - 0.3;
  Double_t S0 = x - 0.3;
  Double_t T1 = y + 0.3;
  
  Double_t amplitude = weight_center*OneStripWithIonAndCathode(x, y, z, z0, doDebug);
  amplitude += weight_outer*OneStripWithIonAndCathode(Q0, y, z, z0, doDebug);
  amplitude += weight_outer*OneStripWithIonAndCathode(x, R1, z, z0, doDebug);
  amplitude += weight_outer*OneStripWithIonAndCathode(S0, y, z, z0, doDebug);
  amplitude += weight_outer*OneStripWithIonAndCathode(x, T1, z, z0, doDebug);
  
  return amplitude; 
}

Double_t OnePCD(Double_t *var, Double_t *par) {
    // We need this function, with the correct arguments, to use when making a
    // TF1
    return OnePCDWithOptions(var, par);
}

Double_t TwoPCDsOneZ(Double_t *var, Double_t *par) {
  // reponse of the strip (30 pads in x direction) to two ionizations 
  // with the same z, different q, x, y. 
  // 1 variable: t=time in microseconds
  // 7 parameters:
  //    0: x for PCD 0
  //    1: y for PCD 0
  //    2: z for PCDs 0 and 1
  //    3: q for PCD 0
  //    4: x for PCD 1
  //    5: y for PCD 1
  //    6: q for PCD 1

  Double_t amplitude = OnePCDWithOptions(var, par, 0, false) + OnePCDWithOptions(var, par, 1, true); 
  return amplitude; 

}

TH1D *hist[60]; 
TF1 *test[60]; 
TCanvas *c1;
UInt_t ncalls = 0;
Double_t RMS_noise = 1; //20.44;


//Model cloud of charge: P = center, Q = right, R-S-T clockwise
void TransformCoord (Double_t *par, Double_t *P, UInt_t i)
{
  if (i<30) { //X channels (0-29)
    P[0] = par[1];   //center x
    P[1] = -43.5 + (3*i) - par[0]; //center y
  }
  else { //Y channels (30-59)
    P[0] = par[0];
    P[1] = par[1] - (-43.5+(3*(i-30)));
  }

  P[2] = par[2]; //center z
  P[3] = par[3]; //center q
  P[4] = par[4];
}

void draw(Double_t *par)
{
  c1->SetGrid();
  c1->Print("chisqfits_entry2.pdf[");
  for (UInt_t i=0; i<60;  i++) { 
    Double_t P[5]; //P[0] is along the wire, P[1] is transverse dir, P is coord sys of wire (origin=center of wire)
    TransformCoord(par, P, i);
    test[i]->SetParameter(0,P[0]); // x
    test[i]->SetParameter(1,P[1]); // y
    test[i]->SetParameter(2, par[2]); // z
    test[i]->SetParameter(3, par[3]); // q  
    test[i]->SetParameter(4, par[4]);
    
    hist[i]->Draw();
    test[i]->Draw("same"); 
    test[i]->SetLineColor(kRed);
    test[i]->SetLineStyle(7);
    c1->Update();
    c1->Print("chisqfits_entry2.pdf");
  }
    c1->Print("chisqfits_entry2.pdf]");
    cout << "Hists and fits drawn" << endl;
    Int_t pause;
    cin >> pause; 
}

void fcn(Int_t &npar, Double_t *gin, Double_t &f, Double_t *par, Int_t iflag)
{     
  Double_t delta;
  Double_t chisq = 0.0;
  ncalls += 1;
  for (UInt_t i=0; i<60; i++) { //i is channel #
    Int_t nbins = hist[i]->GetNbinsX();
    Double_t P[5]; //P[0] is along the wire, P[1] is transverse dir, P is coord sys of wire (origin=center of wire)
    TransformCoord(par, P, i);
    for (UInt_t n=200; n<610; n++) { //n is time sample
      Double_t t = n*.04; //each point in channel waveform separated by 40 ns
      delta = ((hist[i]->GetBinContent(n) - OnePCD(&t, P)))/RMS_noise;
      chisq += delta*delta/410.0/60.0;//chisq per deg of freedom
     } 
  }
//  cout << "ncalls " << ncalls << " chisq " << chisq << " x " << par[0] << " y " << par[1] << " z " << par[2] << " q " << par[3] << endl;

  f = chisq; 
}

Double_t ralphWF() {
  TFile *inputroot = TFile::Open("~/../manisha2/MC/e1MeV_dcoeff0/digitization_dcoeff0/digi1_e1MeV_dcoef0.root");
  TTree *tree = (TTree*) inputroot->Get("evtTree");
  vector<vector<double> > *ChannelWaveform=0; //defines pointer to vector of vectors
  cout << "n entries: " << tree->GetEntries() << endl;
  tree->SetBranchAddress("ChannelWaveform", &ChannelWaveform);
  tree->GetEntry(2);

  cout << "size of ChannelWaveform: " << (*ChannelWaveform).size() << endl; //number of channels (should be 60)
  cout << "size of ChannelWaveform[20]: " << ((*ChannelWaveform)[20]).size() << endl; //print out size of nth channel
  cout << "entry ChannelWaveform[0, 200]: " << ((*ChannelWaveform)[0])[200] << endl; //200th time sample from 0th channel
  c1 = new TCanvas("c1", "");
  TRandom3 *generator = new TRandom3(0);//random number generator initialized by TUUID object
 
  for (UInt_t i=0; i<60; i++) {
    ostringstream name;
    name << "Channel" << i; 
    hist[i] = new TH1D(name.str().c_str(), name.str().c_str(), 800, 0, 32);//wfm_hist in fit_wfm.py gets assigned to this
    hist[i]->GetXaxis()->SetTitle("time (microsec)");
    hist[i]->GetYaxis()->SetTitle("Energy of Charge Deposit (keV)");
    hist[i]->GetXaxis()->CenterTitle();
    hist[i]->GetYaxis()->CenterTitle();
    test[i] = new TF1("test", OnePCD, 0, 32, 4);
    for (UInt_t n=0; n<800;  n++) { //800 time samples
      Double_t noise = generator->Gaus(0, RMS_noise);
     /* Double_t Q = 0.0;
      for (n=600; n<800; n++) {
        Q += (((*ChannelWaveform)[i])[n])*0.022004;
        }
      Double_t AveQ = Q/200;
      cout << "ave q: " << AveQ << endl; */
      Double_t ChannelWFelement = (((*ChannelWaveform)[i])[n])*0.022004; //convert to keV
      ChannelWFelement += noise;
      hist[i]->SetBinContent(n+1, ChannelWFelement); //plots charge deposit energy in keV CHECK UNIT CONVERSION FOR NOISE      
     }
//    cout << "contents of bin " << hist[0]->GetBinContent(100) << endl;
    }
 
  cout << "Hists filled" << endl; 

  TMinuit *gMinuit = new TMinuit(5);  //initialize TMinuit with a maximum of 4 params CHANGED FROM 4
  gMinuit->SetFCN(fcn); 

//  Int_t nvpar, nparx, icstat;
//  if (icstat < 3 ) { //repeat TMinuit multiple times in loop

  cout << "TMinuit has begun" << endl; 
  Double_t arglist[5]; //CHANGED FROM 4
  Int_t ierflg = 0;
  arglist[0] = 1;
  gMinuit->mnexcm("SET ERR", arglist ,1,ierflg);
  gMinuit->mnparm(0, "x", 5, 3, 0, 0, ierflg);//mm
  gMinuit->mnparm(1, "y", 3, 3, 0, 0, ierflg);//mm
  gMinuit->mnparm(2, "z", 18, 3, 0, 0, ierflg);//mm
  gMinuit->mnparm(3, "q", 980, 100, 0, 0, ierflg); //16: 720; 46: 260
  gMinuit->mnparm(4, "w", TMath::Pi(), 0.125*TMath::Pi(), 0, 0, ierflg);
  cout << "Parameters set, Minimization starting" << endl;

  arglist[0] = 10000; //this is somehow related to number of calls
  arglist[1] = 1;
  gMinuit->mnexcm("MIGRAD", arglist, 2, ierflg);
  
  Double_t val0, error0, bnd10, bnd20;
  Int_t num0=0;
  Int_t ivarbl0;
  TString chnam0;
  gMinuit->mnpout(num0, chnam0, val0, error0, bnd10, bnd20, ivarbl0);
  cout << "x: "  << " value0 " << val0  << endl;
  
  Double_t val1, error1, bnd11, bnd21;
  Int_t num1=1;
  Int_t ivarbl1;
  TString chnam1;
  gMinuit->mnpout(num1, chnam1, val1, error1, bnd11, bnd21, ivarbl1);
  cout << "y: "  << " value1 " << val1  << endl;
  
  Double_t val2, error2, bnd12, bnd22;
  Int_t num2=2;
  Int_t ivarbl2;
  TString chnam2;
  gMinuit->mnpout(num2, chnam2, val2, error2, bnd12, bnd22, ivarbl2);
  cout << "z: " << " value2 " << val2  << endl;

  Double_t val3, error3, bnd13, bnd23;
  Int_t num3=3;
  Int_t ivarbl3;
  TString chnam3;
  gMinuit->mnpout(num3, chnam3, val3, error3, bnd13, bnd23, ivarbl3);
  cout << "q: " <<  " value3 " << val3  << endl;

  Double_t val4, error4, bnd14, bnd24;
  Int_t num4=4;
  Int_t ivarbl4;
  TString chnam4;
  gMinuit->mnpout(num4, chnam4, val4, error4, bnd14, bnd24, ivarbl4);
  cout << "w: " <<  " value4 " << val4  << endl;
 

  Int_t pause;
  cin >> pause;
  Double_t par[5];
  par[0] = val0;
  par[1] = val1;
  par[2] = val2;
  par[3] = val3;
  par[4] = val4;
  draw(par);

  cout << "Printing out results: " << endl; 
  Double_t amin, edm, errdef;
  Int_t nvpar, nparx, icstat;
  gMinuit->mnstat(amin, edm, errdef, nvpar, nparx, icstat);
  cout << "best function value found so far: " << amin << " vertical dist remaining to min: " << edm << " how good is fit? 0=bad, 1=approx, 2=full matrix but forced positive-definite, 3=good: " << icstat << endl;
  

/*
    // a test -- just draw a sample wfm to see if things are working. 

    // options
    Double_t x = 1.5;
    Double_t y0 = 0.0;
    Double_t y1 = 2.0;
    Double_t z = 14.65;
    Double_t q0 = 100.0;
    Double_t q1 = 300.0;

    Double_t minTime = 0.0;
    Double_t maxTime = 32.0;
    
//    TCanvas canvas("canvas","");
  //  canvas.SetGrid(1,1); 

    TF1* test1 = new TF1("test1", OnePCD, minTime, maxTime, 4);
    test1->SetParameter(0, 1.5); // x
    test1->SetParameter(1, 1.6); // y
    test1->SetParameter(2, z); // z0
    test1->SetParameter(3, q1); // q
    test1->SetLineColor(kGreen+2); 
    legend.AddEntry(test1, "PCD 1", "l"); 
    test1->Draw(); 

    // two PCDs: PCD 0 + PCD1
    TF1* test2 = new TF1("test2", TwoPCDsOneZ, minTime, maxTime, 7);
    test2->SetParameter(0, x); // x for PCD 0
    test2->SetParameter(1, y0); // y for PCD 0
    test2->SetParameter(2, z); // z for PCDs 0, 1
    test2->SetParameter(3, q0); // q for POCD 0
    test2->SetParameter(4, x); // x for PCD 1
    test2->SetParameter(5, y1); // y for PCD 1
    test2->SetParameter(6, q1); // q for PCD 1
    test2->SetLineColor(kBlue);
    test2->Draw(); 
    legend.AddEntry(test2, "PCD 0 + 1", "l"); 

    //TH1D* frameHist = (TH1D*) test2->GetHistogram(); 
    TH1D* frameHist = (TH1D*) test->GetHistogram(); 
    frameHist->SetTitle("");
    frameHist->SetXTitle("time [#mus]");
    frameHist->SetYTitle("charge [arb]");
    frameHist->SetMinimum(0); 
    frameHist->SetAxisRange(5, 22);
    //test->Draw("l"); 
    test2->Draw("l");
    test->Draw("lp same"); 
    test1->Draw("l same"); 

    //double t[1] = {25.0};
    //double par[4] = {x, y0, z, q0};
    //cout << "final value: " << OnePCDWithOptions(t, par, 0, false, true) << endl;
    legend.Draw(); 
    canvas.Update();
    cout << "any key to continue" << endl;
    Char_t input; 
    cin >> input;  
    return 0;
*/
}


