
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
#include "TH2D.h"
#include "TTree.h"
#include "TFile.h"
#include "TMinuit.h"
#include "TRandom3.h"
#include "TStopwatch.h"
#include "TStyle.h"
#include <iostream>
#include <vector>
#include <sstream>
using namespace std;

void style() {
  gStyle->SetOptStat(0);
} 

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
  Int_t iPCD, 
  Bool_t useSameZ, 
  Bool_t doDebug=false 
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

  size_t xIndex = 0 + iPCD*5; //4
  Double_t x = par[xIndex];
  if (doDebug){ cout << "\txIndex: " << xIndex << " x: " << x << endl; }

  size_t yIndex = 1 + iPCD*5;//4
  Double_t y = par[yIndex];
  if (doDebug){ cout << "\tyIndex: " << yIndex << " y: " << y << endl; }

  size_t zIndex = 2 + iPCD*5;//4
  if (useSameZ){ zIndex=2; }
  Double_t z0 = par[zIndex];
  if (doDebug){ cout << "\tzIndex: " << zIndex << " z0: " << z0 << endl; }

  size_t qIndex = 3 + iPCD*5; //+ (!useSameZ)*iPCD;//3
  Double_t q = par[qIndex]; 
  if (doDebug){ cout << "\tqIndex: " << qIndex << " q: " << q << endl; }

  size_t wIndex = 4 + iPCD*5; 
  Double_t w = par[wIndex];
  if (doDebug){ cout << "\twIndex: " << wIndex << " weight: " << w << endl; }

  Double_t z = z0 - (t-triggerTime) * driftVelocity;  

  if (doDebug){ cout << "\tt: " << t << endl; }

  if (t < triggerTime) { return 0.0; } // wfm is 0 for times before drift starts
  
  Double_t weight_center = 0.5*q*(1.0+sin(w));

  Double_t weight_outer = (q*(1.0 - 0.5*(1.0+sin(w))))/8;
  Double_t Q0 = x + 1.0;
  Double_t R1 = y - 1.0;
  Double_t S0 = x - 1.0;
  Double_t T1 = y + 1.0;
  Double_t V0 = x + 0.707;
  Double_t V1 = y - 0.707;
  Double_t W0 = x - 0.707;
  Double_t W1 = V1;
  Double_t X0 = W0;
  Double_t X1 = y + 0.707;
  Double_t U0 = V0;
  Double_t U1 = X1;

  Double_t amplitude = weight_center*OneStripWithIonAndCathode(x, y, z, z0, doDebug);
  amplitude += weight_outer*OneStripWithIonAndCathode(Q0, y, z, z0, doDebug);
  amplitude += weight_outer*OneStripWithIonAndCathode(x, R1, z, z0, doDebug);
  amplitude += weight_outer*OneStripWithIonAndCathode(S0, y, z, z0, doDebug);
  amplitude += weight_outer*OneStripWithIonAndCathode(x, T1, z, z0, doDebug);
  amplitude += weight_outer*OneStripWithIonAndCathode(U0, U1, z, z0, doDebug);
  amplitude += weight_outer*OneStripWithIonAndCathode(V0, V1, z, z0, doDebug);
  amplitude += weight_outer*OneStripWithIonAndCathode(W0, W1, z, z0, doDebug);
  amplitude += weight_outer*OneStripWithIonAndCathode(X0, X1, z, z0, doDebug);
  
  return amplitude; 
}

Double_t OnePCD(Double_t *var, Double_t *par) {
    // We need this function, with the correct arguments, to use when making a
    // TF1
    return OnePCDWithOptions(var, par, 0, false);
}

Double_t TwoPCDsOneZ(Double_t *var, Double_t *par) {
  // reponse of the strip (30 pads in x direction) to two ionizations 
  // with different q, x, y, z, w. 
  // 1 variable: t=time in microseconds
  // 7 parameters:
  //    0: x for PCD 0
  //    1: y for PCD 0
  //    2: z for PCD 0
  //    3: q for PCD 0
  //    4: w for PCD 0
  //    5: x for PCD 1
  //    6: y for PCD 1
  //    7: z for PCD 1
  //    8: q for PCD 1
  //    9: w for PCD 1

  Double_t amplitude = OnePCDWithOptions(var, par, 0, false) + OnePCDWithOptions(var, par, 1, false); 
  return amplitude; 

}

TH1D *hist[60]; 
TF1 *test[60]; 
TCanvas *ca;
UInt_t ncalls = 0; //number of times fcn() gets called
Double_t RMS_noise = 20.44; 
UInt_t a;
UInt_t draw_calls = 0; //number of times draw() gets called (this should correspond to event #)
TFile output_file("output_file.root", "recreate"); //creates output root file
TTree *output_tree = new TTree("output_tree", "Output of MIGRAD"); //creates output tree

void TransformCoord (Double_t *par, Double_t *P, UInt_t i)
{
  if (i<30) { //X channels (0-29)
    P[0] = par[1];   //center x PCD 0
    P[1] = -43.5 + (3*i) - par[0]; //center y PCD 0
  }
  else { //Y channels (30-59)
    P[0] = par[0];
    P[1] = par[1] - (-43.5+(3*(i-30)));
  }

  P[2] = par[2]; //center z PCD 0
  P[3] = par[3]; //center q PCD 0
  P[4] = par[4]; // w PCD 0
}

void TransformCoord2 (Double_t *par, Double_t *P, UInt_t i)
{
  if (i<30) { //X channels (0-29)
    P[0] = par[1];   //center x PCD 0
    P[1] = -43.5 + (3*i) - par[0]; //center y PCD 0
    P[5] = par[6]; //center x PCD 1
    P[6] = -43.5 + (3*i) - par[5]; //center y PCD 1
  }
  else { //Y channels (30-59)
    P[0] = par[0];
    P[1] = par[1] - (-43.5+(3*(i-30)));
    P[5] = par[5];
    P[6] = par[6] - (-43.5+(3*(i-30)));
  }

  P[2] = par[2]; //center z PCD 0
  P[3] = par[3]; //center q PCD 0
  P[4] = par[4]; // w PCD 0
  P[7] = par[7]; //center z PCD 1
  P[8] = par[8]; //center q PCD 1
  P[9] = par[9]; // w PCD 1
}

Double_t ChisqFit(Double_t *par, UInt_t i)   
{
  Double_t delta;
  Double_t NumberOfSamples = 0;
  Double_t chisq_per_channel = 0;
  Double_t P[5]; //P[0] is along the wire, P[1] is transverse dir, P is coord sys of wire (origin=center of wire)
  TransformCoord(par, P, i);
  for (UInt_t n=200; n<750; n++) { //n is time sample; 200 - 600 is 8 - 24 ms (200*0.04=8)
    NumberOfSamples += 1;
    Double_t t = n*.04; //each point in channel waveform separated by 40 ns
    delta = ((hist[i]->GetBinContent(n) - OnePCD(&t, P)))/RMS_noise;
    chisq_per_channel += delta*delta;
  } 
  return chisq_per_channel/NumberOfSamples;//chisq per deg of freedom
}

Double_t ChisqFit2(Double_t *par, UInt_t i)   
{
  Double_t delta;
  Double_t NumberOfSamples = 0;
  Double_t chisq_per_channel = 0;
  Double_t P[10]; //P[0] is along the wire, P[1] is transverse dir, P is coord sys of wire (origin=center of wire)
  TransformCoord2(par, P, i);
  for (UInt_t n=200; n<750; n++) { //n is time sample; 200 - 600 is 8 - 24 ms (200*0.04=8)
    NumberOfSamples += 1;
    Double_t t = n*.04; //each point in channel waveform separated by 40 ns
    delta = ((hist[i]->GetBinContent(n) - TwoPCDsOneZ(&t, P)))/RMS_noise;
    chisq_per_channel += delta*delta;
  } 
  return chisq_per_channel/NumberOfSamples;//chisq per deg of freedom
}
 
void draw(Double_t *par)
{
  cout << "USING DRAW 1" << endl;
  ca->SetGrid();
  ostringstream pdfnameStream;
  pdfnameStream << "Event_" << a << ".pdf"; //a is event number from loop in ralphWF()
  ca->Print((pdfnameStream.str()+"[").c_str());
  cout << "pdf file opened" << endl;

  for (UInt_t i=0; i<60;  i++) { 
    TF1 test("test", OnePCD, 0, 32, 5); 
    Double_t P[5]; //P[0] is along the wire, P[1] is transverse dir, P is coord sys of wire (origin=center of wire)
    TransformCoord(par, P, i);
    test.SetParameter(0, P[0]); // x
    test.SetParameter(1, P[1]); // y
    test.SetParameter(2, P[2]); // z
    test.SetParameter(3, P[3]); // q  
    test.SetParameter(4, P[4]); // w

    Double_t Chisq_per_channel = ChisqFit(par, i);

    hist[i]->Draw();
    ostringstream name;
    name << "Channel " << i << "  x=" << par[0] << "  y=" << par[1] << "  z=" << par[2] << "  q=" << par[3] << "  w=" << par[4] << "  chisq per chan=" << Chisq_per_channel; 
    hist[i]->SetTitle(name.str().c_str());
    test.Draw("same"); 
    test.SetLineColor(kRed);
    test.SetLineStyle(7);
    style();
    ca->Update();
    ca->Print((pdfnameStream.str()).c_str());
    }

//  TFile *inputroot = TFile::Open("~/../manisha2/MC/e1MeV_dcoeff50/digitization_dcoeff50/digi1_e1MeV_dcoef50.root");
  TFile *inputroot = TFile::Open("/nfs/slac/g/exo_data4/users/manisha2/MC/Bi207_Full_Ralph_dcoeff50_Qidong_Efieldhist/digitization_dcoeff50/digi1750_Bi207_Full_Ralph_dcoef50.root");
  TTree *tree = (TTree*) inputroot->Get("evtTree");
  tree->GetEntries();
  Int_t nbins = 21.2/0.53;//x vs y binning
  TH2D *eCloud_point_hist = new TH2D("eCloud_point_hist", "Charge Deposit", nbins, 0, 8, nbins, 0, 8);//x y 
  TH2D *point_charge = new TH2D("point_charge", "", 200, 0, 8, 200, 0, 8);
  point_charge->Fill(par[0], par[1], par[3]); //x, y, q

//  draw_calls += 1;
  ostringstream chargeweightStream;
  chargeweightStream << "(Entry$==" << a << ")*PCDq*0.02204";
  string chargeweight = chargeweightStream.str();

  tree->Draw("PCDy:PCDx >> eCloud_point_hist", chargeweight.c_str());//why do we multiply PCDq by event?
  eCloud_point_hist->Draw("colz");
  point_charge->Draw("same");
  eCloud_point_hist->GetXaxis()->SetTitle("X (mm)");
  eCloud_point_hist->GetYaxis()->SetTitle("Y (mm)");
  eCloud_point_hist->GetXaxis()->CenterTitle();
  eCloud_point_hist->GetYaxis()->CenterTitle();
  style();
  ca->Update();
  ca->Print((pdfnameStream.str()).c_str());
  
  TH2D *eCloud_point_hist2 = new TH2D("eCloud_point_hist2", "Charge Deposit", nbins, 0, 8, nbins, 16, 20);//x z
  TH2D *point_charge2 = new TH2D("point_charge2", "", 200, 0, 8, 550, 0, 22);
  point_charge2->Fill(par[0], par[2], par[3]);
  tree->Draw("(18.16-PCDz):PCDx >> eCloud_point_hist2", chargeweight.c_str());
  eCloud_point_hist2->Draw("colz");
  point_charge2->Draw("same"); //x, z, q
  eCloud_point_hist2->GetXaxis()->SetTitle("X (mm)");
  eCloud_point_hist2->GetYaxis()->SetTitle("Z (mm)");
  eCloud_point_hist2->GetXaxis()->CenterTitle();
  eCloud_point_hist2->GetYaxis()->CenterTitle();
  style();
  ca->Update();
  ca->Print((pdfnameStream.str()).c_str());

  ca->Print((pdfnameStream.str()+"]").c_str());
  cout << "pdf file closed" << endl; 
}

void draw2(Double_t *par)
{
  cout << "USING DRAW2" << endl;
  ca->SetGrid();
  ostringstream pdfnameStream;
  pdfnameStream << "Event_" << a << ".pdf"; //a is event number from loop in ralphWF()
  ca->Print((pdfnameStream.str()+"[").c_str());
  cout << "pdf file opened" << endl;

  for (UInt_t i=0; i<60;  i++) { 
    TF1 test("test", TwoPCDsOneZ, 0, 32, 10); 
    Double_t P[10]; //P[0] is along the wire, P[1] is transverse dir, P is coord sys of wire (origin=center of wire)
    TransformCoord2(par, P, i);
    test.SetParameter(0, P[0]); // x
    test.SetParameter(1, P[1]); // y
    test.SetParameter(2, P[2]); // z
    test.SetParameter(3, P[3]); // q  
    test.SetParameter(4, P[4]); // w
    test.SetParameter(5, P[5]); // x 1
    test.SetParameter(6, P[6]); // y 1
    test.SetParameter(7, P[7]); // z 1
    test.SetParameter(8, P[8]); // q 1
    test.SetParameter(9, P[9]); // w 1

    Double_t Chisq_per_channel = ChisqFit2(par, i);

    hist[i]->Draw();
    ostringstream name;
    name << "Channel " << i << "  x0=" << par[0] << "  y0=" << par[1] << "  z0=" << par[2] << "  q0=" << par[3] << " x1=" << par[5] << " y1=" << par[6] << " z1=" << par[7] << " q1=" << par[8] <<  " chisq per chan=" << Chisq_per_channel; 
    hist[i]->SetTitle(name.str().c_str());
    test.Draw("same"); 
    test.SetLineColor(kRed);
    test.SetLineStyle(7);
    style();
    ca->Update();
    ca->Print((pdfnameStream.str()).c_str());
    }

//  TFile *inputroot = TFile::Open("~/../manisha2/MC/e1MeV_dcoeff50/digitization_dcoeff50/digi1_e1MeV_dcoef50.root");
  TFile *inputroot = TFile::Open("/nfs/slac/g/exo_data4/users/manisha2/MC/Bi207_Full_Ralph_dcoeff50_Qidong_Efieldhist/digitization_dcoeff50/digi1750_Bi207_Full_Ralph_dcoef50.root");
  TTree *tree = (TTree*) inputroot->Get("evtTree");
  tree->GetEntries();
  Int_t nbins = 21.2/0.53;//x vs y binning
  TH2D *eCloud_point_hist = new TH2D("eCloud_point_hist", "Charge Deposit", nbins, -14, 4, nbins, 16, 30);//x y 
  TH2D *point_charge = new TH2D("point_charge", "", 450, -14, 4, 350, 16, 30);
  TH2D *point_charge2 = new TH2D("point_charge2", "", 200, -14, 4, 350, 16, 30);
 
  point_charge->Fill(par[0], par[1], par[3]); //x, y, q
  point_charge2->Fill(par[5], par[6], par[8]);
//  draw_calls += 1;
  ostringstream chargeweightStream;
  chargeweightStream << "(Entry$==" << a << ")*PCDq*0.02204";
  string chargeweight = chargeweightStream.str();

  tree->Draw("PCDy:PCDx >> eCloud_point_hist", chargeweight.c_str());//why do we multiply PCDq by event?
  eCloud_point_hist->Draw("colz");
  point_charge->Draw("same");
  point_charge2->Draw("same");
  eCloud_point_hist->GetXaxis()->SetTitle("X (mm)");
  eCloud_point_hist->GetYaxis()->SetTitle("Y (mm)");
  eCloud_point_hist->GetXaxis()->CenterTitle();
  eCloud_point_hist->GetYaxis()->CenterTitle();
  style();
  ca->Update();
  ca->Print((pdfnameStream.str()).c_str());
 
  TH2D *eCloud_point_hist2 = new TH2D("eCloud_point_hist2", "Charge Deposit", nbins, 0, 8, nbins, 16, 20);//x z
  TH2D *point_charge3 = new TH2D("point_charge3", "", 200, 0, 8, 550, 0, 22);
  TH2D *point_charge4 = new TH2D("point_charge4", "", 200, 0, 8, 550, 0, 22);
  point_charge3->Fill(par[0], par[2], par[3]);
  point_charge4->Fill(par[5], par[7], par[8]);
  tree->Draw("(18.16-PCDz):PCDx >> eCloud_point_hist2", chargeweight.c_str());
  eCloud_point_hist2->Draw("colz");
  point_charge3->Draw("same"); //x, z, q
  point_charge4->Draw("same");
  eCloud_point_hist2->GetXaxis()->SetTitle("X (mm)");
  eCloud_point_hist2->GetYaxis()->SetTitle("Z (mm)");
  eCloud_point_hist2->GetXaxis()->CenterTitle();
  eCloud_point_hist2->GetYaxis()->CenterTitle();
  style();
  ca->Update();
  ca->Print((pdfnameStream.str()).c_str());

  ca->Print((pdfnameStream.str()+"]").c_str());
  cout << "pdf file closed" << endl;   
}

void fcn(Int_t &npar, Double_t *gin, Double_t &f, Double_t *par, Int_t iflag)
{ 
  Double_t chisq = 0.0;  
  ncalls += 1;
  for (UInt_t i=0; i<60; i++) {
    chisq += ChisqFit(par, i)/60;
  }
  //cout << "ncalls " << ncalls << " chisq " << chisq << " x " << par[0] << " y " << par[1] << " z " << par[2] << " q " << par[3] << " w " << par[4] << endl; //test
  f = chisq; 
}

void fcn2(Int_t &npar, Double_t *gin, Double_t &f2, Double_t *par, Int_t iflag)
{
  Double_t chisq2 = 0.0;
  for (UInt_t i=0; i<60; i++) {
    chisq2 += ChisqFit2(par, i)/60;
  }
  f2 = chisq2;
}

Double_t ralphWF(UInt_t first_event, UInt_t last_event) { //to run from command line: root "ralphWF.C+(0,2)" where first_event=0 & last_event=1
  //TFile *inputroot = TFile::Open("~/../manisha2/MC/e1MeV_dcoeff50/digitization_dcoeff50/digi1_e1MeV_dcoef50.root");
  TFile *inputroot = TFile::Open("/nfs/slac/g/exo_data4/users/manisha2/MC/Bi207_Full_Ralph_dcoeff50_Qidong_Efieldhist/digitization_dcoeff50/digi1750_Bi207_Full_Ralph_dcoef50.root");
  TTree *tree = (TTree*) inputroot->Get("evtTree");
  vector<vector<double> > *ChannelWaveform=0; //defines pointer to vector of vectors
  cout << "number of events: " << tree->GetEntries() << endl;
  tree->SetBranchAddress("ChannelWaveform", &ChannelWaveform);

  Double_t val0;
  Double_t val1;
  Double_t val2;
  Double_t val3;
  Double_t val4;
  Double_t val5;
  Double_t val6;
  Double_t val7;
  Double_t val8;
  Double_t val9;
  Double_t amin;
  Int_t icstat;
  
  TBranch *Event = output_tree->Branch("Event", &a, "event/i");
  TBranch *Fit_x = output_tree->Branch("MIGRAD x", &val0, "MINUIT_x/D" ); //creates new branches for x, y, z, q, w, fcn, and icstat
  TBranch *Fit_y = output_tree->Branch("MIGRAD y", &val1, "MINUIT_y/D"); 
  TBranch *Fit_z = output_tree->Branch("MIGRAD z", &val2, "MINUIT_z/D"); 
  TBranch *Fit_q = output_tree->Branch("MIGRAD q", &val3, "MINUIT_q/D"); 
  TBranch *Fit_w = output_tree->Branch("MIGRAD w", &val4, "MINUIT_w/D");
  TBranch *Fit_x1 = output_tree->Branch("MIGRAD x1", &val5, "MINUIT_x1/D"); 
  TBranch *Fit_y1 = output_tree->Branch("MIGRAD y1", &val6, "MINUIT_y1/D"); 
  TBranch *Fit_z1 = output_tree->Branch("MIGRAD z1", &val7, "MINUIT_z1/D"); 
  TBranch *Fit_q1 = output_tree->Branch("MIGRAD q1", &val8, "MINUIT_q1/D"); 
  TBranch *Fit_w1 = output_tree->Branch("MIGRAD w1", &val9, "MINUIT_w1/D"); 
  
  TBranch *Min_chisq = output_tree->Branch("MIGRAD chisq", &amin, "chisquare_dof/D"); 
  TBranch *Evaluation_of_fit = output_tree->Branch("icstat", &icstat, "icstat/I"); 

  for (a=first_event; a<(last_event); a++)  {
    tree->GetEntry(a);
    cout << a << endl;
    //cout << "size of ChannelWaveform: " << (*ChannelWaveform).size() << endl; //number of channels (should be 60)
    //cout << "size of ChannelWaveform[20]: " << ((*ChannelWaveform)[20]).size() << endl; //print out size of nth channel
    //cout << "entry ChannelWaveform[0, 200]: " << ((*ChannelWaveform)[0])[200] << endl; //200th time sample from 0th channel
    //if (val3<200) //NOTE: THIS SHOULDN'T BE VAL3, IT SHOULD BE PCD Q FROM INPUT ROOT FILE
    //  break;
    ostringstream canvasStream;
    canvasStream << "canvas" << a;
    string canvas = canvasStream.str();
    ca = new TCanvas(canvas.c_str(), "");
    TRandom3 *generator = new TRandom3(0);//random number generator initialized by TUUID object
    
    UInt_t XChannelHit1=0;
    UInt_t XChannelHit2=0;
    UInt_t XChannelHit3=0;
    UInt_t XChannelHit4=0;
    UInt_t YChannelHit1=0;
    UInt_t YChannelHit2=0;
    UInt_t YChannelHit3=0;
    UInt_t YChannelHit4=0;
    Double_t XChannelPos=0.0;
    Double_t XChannelPos2=0.0;
    Double_t YChannelPos=0.0;
    Double_t YChannelPos2=0.0;
//    Double_t YChannelPos=0.0;
    UInt_t XChannelIncrement=0;
    UInt_t YChannelIncrement=0;
    Double_t EnergyOfDeposit=0.0;
    for (UInt_t i=0; i<60; i++) {
      ostringstream name;
      name << "Channel " << i; 
      hist[i] = new TH1D(name.str().c_str(), name.str().c_str(), 800, 0, 32);//wfm_hist in fit_wfm.py gets assigned to this
      hist[i]->GetXaxis()->SetTitle("time (microsec)");
      hist[i]->GetYaxis()->SetTitle("Energy of Charge Deposit (keV)");
      hist[i]->GetXaxis()->CenterTitle();
      hist[i]->GetYaxis()->CenterTitle();
      //test[i] = new TF1("test", OnePCD, 0, 32, 5); //5 is # of params
      for (UInt_t n=0; n<800;  n++) { //800 time samples
        Double_t noise = generator->Gaus(0, RMS_noise); //mean=0, std dev (variation)=20
       /* Double_t Q = 0.0;
        for (n=600; n<800; n++) {
          Q += (((*ChannelWaveform)[i])[n])*0.022004;
          }
        Double_t AveQ = Q/200;
        cout << "ave q: " << AveQ << endl; */
        Double_t ChannelWFelement = (((*ChannelWaveform)[i])[n])*0.022004; //convert to keV
        ChannelWFelement += noise;
        hist[i]->SetBinContent(n+1, ChannelWFelement); //plots charge deposit energy in keV
      }
//      EnergyOfDeposit += (((*ChannelWaveform)[i])[625])*0.022004; //Total energy of the event in keV
      cout << "Energy of Channel " << i  << ": " << (((*ChannelWaveform)[i])[625])*0.022004 << endl;
      if (i<30) {
        if ((((*ChannelWaveform)[i])[625])*0.022004 > 5) {
          cout << "Hit Channel " << i << endl;
          XChannelIncrement += 1;
          EnergyOfDeposit += (((*ChannelWaveform)[i])[625])*0.022004; //Total energy of the event in keV
          if (XChannelIncrement == 1) {
            XChannelHit1 = i;
            cout << XChannelHit1 << endl;
            }
          if (XChannelIncrement == 2) {
            XChannelHit2 = i;
            cout << XChannelHit2 << endl;
            }
          if (XChannelIncrement == 3) {
            XChannelHit3 = i;
            cout << XChannelHit3 << endl;
            }
          if (XChannelIncrement == 4) {
            XChannelHit4 = i;
            cout << XChannelHit4 << endl;
            }
          }     
        }
      if (i>=30 && i<60) {
        if ((((*ChannelWaveform)[i])[625])*0.022004 > 5) {
          cout << "Hit Channel " << i << endl;
          YChannelIncrement += 1;
          EnergyOfDeposit += (((*ChannelWaveform)[i])[625])*0.022004; //Total energy of the event in keV
          if (YChannelIncrement == 1) {
            YChannelHit1 = i;
            }
          if (YChannelIncrement == 2) {
            YChannelHit2 = i;
            }
          if (YChannelIncrement == 3) {
            YChannelHit3 = i;
            }
          if (YChannelIncrement == 4) {
            YChannelHit4 = i;
            cout << YChannelHit4 << endl;
            }
          }    
        }
      }

    cout << "YChannelHit1 " << YChannelHit1 << endl;
    cout << "YChannelHit2 " << YChannelHit2 << endl;
    cout << "YChannelHit3 " << YChannelHit3 << endl;

    cout << "Total Energy of deposits at 25 ms: " << EnergyOfDeposit << endl;
  
//Two options: if X Channel hits are 2 or more channels apart, uses fcn2 (TwoPCDsOneZ). If not, uses fcn (OnePCDWithOptions)
  if (XChannelIncrement >= 2 && (((XChannelHit2-XChannelHit1)) >= 2 || ((XChannelHit3-XChannelHit1) >= 2) || ((XChannelHit3-XChannelHit2) >= 2)))
  {
    cout << "USING TWO PCDs FIT" << endl;

    TMinuit *gMinuit = new TMinuit(10);  //initialize TMinuit with a maximum of 10 params 
    gMinuit->SetFCN(fcn2); 
    
    if ((((*ChannelWaveform)[XChannelHit1])[625]) > (((*ChannelWaveform)[XChannelHit2])[625]) && (((*ChannelWaveform)[XChannelHit1])[625]) > (((*ChannelWaveform)[XChannelHit3])[625]) && (((*ChannelWaveform)[XChannelHit2])[625]) > (((*ChannelWaveform)[XChannelHit3])[625])) {  
      XChannelPos = -43.5 + 3*XChannelHit1;
      XChannelPos2 = -43.5 + 3*XChannelHit2;
    }
    if ((((*ChannelWaveform)[XChannelHit2])[625]) > (((*ChannelWaveform)[XChannelHit1])[625]) && (((*ChannelWaveform)[XChannelHit2])[625]) > (((*ChannelWaveform)[XChannelHit3])[625]) && (((*ChannelWaveform)[XChannelHit1])[625]) > (((*ChannelWaveform)[XChannelHit3])[625])) {
    cout << "using this option" << endl;
    XChannelPos = -43.5 + 3*XChannelHit1;
    XChannelPos2 = -43.5 + 3*XChannelHit2;
    }
    if ((((*ChannelWaveform)[XChannelHit3])[625]) > (((*ChannelWaveform)[XChannelHit1])[625]) && (((*ChannelWaveform)[XChannelHit3])[625]) > (((*ChannelWaveform)[XChannelHit2])[625]) && (((*ChannelWaveform)[XChannelHit1])[625]) > (((*ChannelWaveform)[XChannelHit2])[625])) {
    XChannelPos = -43.5 + 3*XChannelHit1;
    XChannelPos2 = -43.5 + 3*XChannelHit3;
    }
    if ((((*ChannelWaveform)[XChannelHit3])[625]) > (((*ChannelWaveform)[XChannelHit1])[625]) && (((*ChannelWaveform)[XChannelHit3])[625]) > (((*ChannelWaveform)[XChannelHit2])[625]) && (((*ChannelWaveform)[XChannelHit2])[625]) > (((*ChannelWaveform)[XChannelHit1])[625])) {
    XChannelPos = -43.5 + 3*XChannelHit2;
    XChannelPos2 = -43.5 + 3*XChannelHit3;
    }

    if ((((*ChannelWaveform)[YChannelHit1])[625]) > (((*ChannelWaveform)[YChannelHit2])[625]) && (((*ChannelWaveform)[YChannelHit1])[625]) > (((*ChannelWaveform)[YChannelHit3])[625]) && (((*ChannelWaveform)[YChannelHit2])[625]) > (((*ChannelWaveform)[YChannelHit3])[625])) {    
    YChannelPos = -43.5 + 3*(YChannelHit1-30); 
    YChannelPos2 = -43.5 + 3*(YChannelHit2-30);
    }
    if ((((*ChannelWaveform)[YChannelHit2])[625]) > (((*ChannelWaveform)[YChannelHit1])[625]) && (((*ChannelWaveform)[YChannelHit2])[625]) > (((*ChannelWaveform)[YChannelHit3])[625]) && (((*ChannelWaveform)[YChannelHit1])[625]) > (((*ChannelWaveform)[YChannelHit3])[625])) {
    YChannelPos = -43.5 + 3*(YChannelHit1-30);
    YChannelPos2 = -43.5 + 3*(YChannelHit2-30);
    }
    if ((((*ChannelWaveform)[YChannelHit3])[625]) > (((*ChannelWaveform)[YChannelHit1])[625]) && (((*ChannelWaveform)[YChannelHit3])[625]) > (((*ChannelWaveform)[YChannelHit2])[625]) && (((*ChannelWaveform)[YChannelHit1])[625]) > (((*ChannelWaveform)[YChannelHit2])[625])) {
    YChannelPos = -43.5 + 3*(YChannelHit1-30);
    YChannelPos2 = -43.5 + 3*(YChannelHit3-30);
    }
    if ((((*ChannelWaveform)[YChannelHit3])[625]) > (((*ChannelWaveform)[YChannelHit1])[625]) && (((*ChannelWaveform)[YChannelHit3])[625]) > (((*ChannelWaveform)[YChannelHit2])[625]) && (((*ChannelWaveform)[YChannelHit2])[625]) > (((*ChannelWaveform)[YChannelHit1])[625])) {
    YChannelPos = -43.5 + 3*(YChannelHit2-30);
    YChannelPos2 = -43.5 + 3*(YChannelHit3-30);
    }
    if ((((*ChannelWaveform)[YChannelHit1])[625]) > (((*ChannelWaveform)[YChannelHit2])[625]) && (((*ChannelWaveform)[YChannelHit1])[625]) > (((*ChannelWaveform)[YChannelHit3])[625]) && (((*ChannelWaveform)[YChannelHit2])[625]) == (((*ChannelWaveform)[YChannelHit3])[625])) {
    YChannelPos = -43.5 + 3*(YChannelHit1-30);
    YChannelPos2 = 0.0;
    }

    cout << "XChannelPos: " << XChannelPos << " YChannelPos: " << YChannelPos << "   XChannelPos2: " << XChannelPos2 << " YChannelPos2: " << YChannelPos2 << endl;
    Int_t pause;
    cin >> pause;

    cout << "TMinuit has begun" << endl; 

    Double_t arglist[10]; //# of params
    Int_t ierflg = 0;
    arglist[0] = 1;
    gMinuit->mnexcm("SET ERR", arglist ,1,ierflg);
    gMinuit->mnparm(0, "x0", XChannelPos, 1, 0, 0, ierflg);//mm
    gMinuit->mnparm(1, "y0", YChannelPos, 1, 0, 0, ierflg);//mm
    gMinuit->mnparm(2, "z0", 17, 1, 0, 0, ierflg);//mm
    gMinuit->mnparm(3, "q0", EnergyOfDeposit/2, 100, 0, 0, ierflg); //keV
    gMinuit->mnparm(4, "w0", TMath::Pi(), 0.125*TMath::Pi(), 0, 2*TMath::Pi(), ierflg); //radians
    gMinuit->mnparm(5, "x1", XChannelPos2, 1, 0, 0, ierflg);//mm
    gMinuit->mnparm(6, "y1", YChannelPos2, 1, 0, 0, ierflg);//mm
    gMinuit->mnparm(7, "z1", 17, 1, 0, 0, ierflg);//mm
    gMinuit->mnparm(8, "q1", EnergyOfDeposit/2, 100, 0, 0, ierflg); //keV
    gMinuit->mnparm(9, "w1", TMath::Pi(), 0.125*TMath::Pi(), 0, 2*TMath::Pi(), ierflg); //radians

    cout << "Parameters initialized, Minimization starting" << endl;

    arglist[0] = 10000; //this is somehow related to number of calls
    arglist[1] = 1;
    cout << "arglist set" << endl;

    Double_t edm, errdef;
    Int_t nvpar, nparx; 
    Int_t nfit=0;
    for (nfit=0; nfit<8; nfit++) {
      gMinuit->mnexcm("MIGRAD", arglist, 2, ierflg);
      gMinuit->mnstat(amin, edm, errdef, nvpar, nparx, icstat);
      cout << "best function value found so far: " << amin << " vertical dist remaining to min: " << edm << " how good is fit? 0=bad, 1=approx, 2=full matrix but forced positive-definite, 3=good: " << icstat << endl;
      if (icstat==3) {
        break;
      }
    }  

    Double_t  error0, bnd10, bnd20;
    Int_t num0=0;
    Int_t ivarbl0;
    TString chnam0;
    gMinuit->mnpout(num0, chnam0, val0, error0, bnd10, bnd20, ivarbl0);
    cout << "x 0: " << val0  << endl;

    Double_t error1, bnd11, bnd21;
    Int_t num1=1;
    Int_t ivarbl1;
    TString chnam1;
    gMinuit->mnpout(num1, chnam1, val1, error1, bnd11, bnd21, ivarbl1);
    cout << "y 0: " << val1  << endl;
    
    Double_t  error2, bnd12, bnd22;
    Int_t num2=2;
    Int_t ivarbl2;
    TString chnam2;
    gMinuit->mnpout(num2, chnam2, val2, error2, bnd12, bnd22, ivarbl2);
    cout << "z 0: " << val2  << endl;

    Double_t  error3, bnd13, bnd23;
    Int_t num3=3;
    Int_t ivarbl3;
    TString chnam3;
    gMinuit->mnpout(num3, chnam3, val3, error3, bnd13, bnd23, ivarbl3);
    cout << "q 0: " << val3  << endl;

    Double_t  error4, bnd14, bnd24;
    Int_t num4=4;
    Int_t ivarbl4;
    TString chnam4;
    gMinuit->mnpout(num4, chnam4, val4, error4, bnd14, bnd24, ivarbl4);
    cout << "w 0: " << val4 << endl;

    Double_t  error5, bnd15, bnd25;
    Int_t num5=5;
    Int_t ivarbl5;
    TString chnam5;
    gMinuit->mnpout(num5, chnam5, val5, error5, bnd15, bnd25, ivarbl5);
    cout << "x 1: "  << val5  << endl;

    Double_t error6, bnd16, bnd26;
    Int_t num6=6;
    Int_t ivarbl6;
    TString chnam6;
    gMinuit->mnpout(num6, chnam6, val6, error6, bnd16, bnd26, ivarbl6);
    cout << "y 1: "  <<  val6  << endl;
    
    Double_t error7, bnd17, bnd27;
    Int_t num7=7;
    Int_t ivarbl7;
    TString chnam7;
    gMinuit->mnpout(num7, chnam7, val7, error7, bnd17, bnd27, ivarbl7);
    cout << "z 1: " << val7 << endl;

    Double_t error8, bnd18, bnd28;
    Int_t num8=8;
    Int_t ivarbl8;
    TString chnam8;
    gMinuit->mnpout(num8, chnam8, val8, error8, bnd18, bnd28, ivarbl8);
    cout << "q 1: " << val8 << endl;

    Double_t error9, bnd19, bnd29;
    Int_t num9=9;
    Int_t ivarbl9;
    TString chnam9;
    gMinuit->mnpout(num9, chnam9, val9, error9, bnd19, bnd29, ivarbl9);
    cout << "w 1: " << val9 << endl;

    Double_t par[10]; 
    par[0] = val0;
    par[1] = val1;
    par[2] = val2;
    par[3] = val3;
    par[4] = val4;
    par[5] = val5;
    par[6] = val6;
    par[7] = val7;
    par[8] = val8;
    par[9] = val9;
   
    cout << "draw2 is being executed" << endl;
    draw2(par);
     
    output_tree->Fill();
    //parameters re-set to 0  
    val0 = 0.0;
    val1 = 0.0;
    val2 = 0.0;
    val3 = 0.0;
    val4 = 0.0;
    val5 = 0.0;
    val6 = 0.0; 
    val7 = 0.0;
    val8 = 0.0;
    val9 = 0.0;
    amin = 0.0;
    icstat = 0.0; 
  
  } 

  else 
  {
    cout << "USING ONE PCD FIT" << endl;
    
    TMinuit *gMinuit = new TMinuit(5);  //initialize TMinuit with a maximum of 5 params 
    gMinuit->SetFCN(fcn); 
    
    if ((((*ChannelWaveform)[XChannelHit1])[625]) > (((*ChannelWaveform)[XChannelHit2])[625])) {  
      XChannelPos = -43.5 + 3*XChannelHit1; 
    }
    else {
      XChannelPos = -43.5 + 3*XChannelHit2;
    }
    
    YChannelPos = -43.5 + 3*(YChannelHit1-30);
    cout << "XChannelPos: " << XChannelPos << " YChannelPos: " << YChannelPos << endl;
    cout << "TMinuit has begun" << endl; 
    Double_t arglist[5]; //# of params
    Int_t ierflg = 0;
    arglist[0] = 1;
    gMinuit->mnexcm("SET ERR", arglist ,1,ierflg);
    gMinuit->mnparm(0, "x", XChannelPos, 1, 0, 0, ierflg);//mm
    gMinuit->mnparm(1, "y", YChannelPos, 1, 0, 0, ierflg);//mm
    gMinuit->mnparm(2, "z", 17, 1, 0, 0, ierflg);//mm
    gMinuit->mnparm(3, "q", EnergyOfDeposit, 100, 0, 0, ierflg); //keV
    gMinuit->mnparm(4, "w", TMath::Pi(), 0.125*TMath::Pi(), 0, 2*TMath::Pi(), ierflg); //radians
    cout << "Parameters set, Minimization starting" << endl;

    arglist[0] = 10000; //this is somehow related to number of calls
    arglist[1] = 1;
   
    Double_t edm, errdef;
    Int_t nvpar, nparx; 
    Int_t nfit=0;
    for (nfit=0; nfit<4; nfit++) {
      gMinuit->mnexcm("MIGRAD", arglist, 2, ierflg);
      gMinuit->mnstat(amin, edm, errdef, nvpar, nparx, icstat);
      cout << "best function value found so far: " << amin << " vertical dist remaining to min: " << edm << " how good is fit? 0=bad, 1=approx, 2=full matrix but forced positive-definite, 3=good: " << icstat << endl;
    }  

    Double_t  error0, bnd10, bnd20;
    Int_t num0=0;
    Int_t ivarbl0;
    TString chnam0;
    gMinuit->mnpout(num0, chnam0, val0, error0, bnd10, bnd20, ivarbl0);
    cout << "x: "  << val0  << endl;
    
    Double_t error1, bnd11, bnd21;
    Int_t num1=1;
    Int_t ivarbl1;
    TString chnam1;
    gMinuit->mnpout(num1, chnam1, val1, error1, bnd11, bnd21, ivarbl1);
    cout << "y: "  << val1 << endl;
    
    Double_t  error2, bnd12, bnd22;
    Int_t num2=2;
    Int_t ivarbl2;
    TString chnam2;
    gMinuit->mnpout(num2, chnam2, val2, error2, bnd12, bnd22, ivarbl2);
    cout << "z: " << val2 << endl;

    Double_t  error3, bnd13, bnd23;
    Int_t num3=3;
    Int_t ivarbl3;
    TString chnam3;
    gMinuit->mnpout(num3, chnam3, val3, error3, bnd13, bnd23, ivarbl3);
    cout << "q: " << val3 << endl;

    Double_t  error4, bnd14, bnd24;
    Int_t num4=4;
    Int_t ivarbl4;
    TString chnam4;
    gMinuit->mnpout(num4, chnam4, val4, error4, bnd14, bnd24, ivarbl4);
    cout << "w: " << val4 << endl;

    Double_t par[5];
    par[0] = val0;
    par[1] = val1;
    par[2] = val2;
    par[3] = val3;
    par[4] = val4;
    cout << "draw is being executed" << endl;
    draw(par);
     
    output_tree->Fill();
    //parameters re-set to 0  
    val0 = 0.0;
    val1 = 0.0;
    val2 = 0.0;
    val3 = 0.0;
    val4 = 0.0;
    amin = 0.0;
    icstat = 0.0;  
   }  
 } 
 
  output_file.Write();
}
  
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
  


