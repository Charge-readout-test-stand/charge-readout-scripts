// This macro constructs a function from Ralph's analytical expression for the
// charge signal. 

// from https://root.cern.ch/root/html534/TF1.html#F3
// test from the command line with: root ralphWF.C

#include "TF1.h"
#include "TMath.h"
#include "TCanvas.h"
#include "TLegend.h"
#include "TH1D.h"

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
  //for ( int i_pad = 0; i_pad < 1; i_pad++ ){ // FIXME only 1 pad for debugging
  for ( int i_pad = 0; i_pad < 30; i_pad++ ){
      Double_t padX = x + i_pad*diagonal - diagonal*14.5; 

      Double_t onePad = OnePadRotated(x + i_pad*diagonal - diagonal*14.5, y, z);
      //Double_t onePad = OnePadRotated(x, y, z); // FIXME -- only one pad
      //cout << "\t\t pad: "<< i_pad << " | pad x: " << padX << " | amplitude: " << onePad << endl;
      amplitude += onePad;
  }
  return amplitude;
}

Double_t OnePCDWithOptions(
  Double_t *var, 
  Double_t *par, 
  Int_t iPCD=0, 
  Bool_t useSameZ = false,
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

  Double_t triggerTime = 8.0; // microseconds
  Double_t driftVelocity = 1.72; // mm/microsecond
  Double_t driftDistance = 17.0; // mm

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

  Double_t z = z0 - (t-triggerTime) * driftVelocity;  

  if (doDebug){ cout << "\tt: " << t << endl; }

  // wfm is 0 for times before drift starts:
  if (t < triggerTime) { return 0.0; }

  Double_t ionAmplitude = OneStrip(x,y,z0);
  Double_t electronAmplitude = OneStrip(x,y,z);
  if (doDebug) { cout << "\tion: " << ionAmplitude << endl; }
  ionAmplitude*=(1.0-z0/driftDistance);
  if (doDebug) { cout << "\telectron: " << electronAmplitude << endl; }
  if (z > 0) { 
    electronAmplitude*=(1.0-z/driftDistance); 
    if (doDebug){ cout << "\tz: " << z << endl; }
  }
  if (doDebug) { cout << "\tion after cathode: " << ionAmplitude << endl; }
  if (doDebug) { cout << "\telectron after cathode: " << electronAmplitude << endl; }
  Double_t amplitude = electronAmplitude - ionAmplitude; 
  if (doDebug) { cout << "\tamplitude: " << amplitude << endl; }
  return q*amplitude; 
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


Double_t ralphWF() {
    // a test -- just draw a sample wfm to see if things are working. 

    // options
    Double_t x = 1.5;
    Double_t y0 = 0.0;
    Double_t y1 = 2.0;
    Double_t z = 14.65;
    Double_t q0 = 100.0;
    Double_t q1 = 300.0;

    Double_t minTime = 14.0;
    Double_t maxTime = 17.0;
    
    TCanvas canvas("canvas","");
    canvas.SetGrid(1,1); 

    TLegend legend(0.1, 0.9, 0.9, 0.99);
    legend.SetNColumns(3);

    // PCD 0
    TF1* test = new TF1("test", OnePCD, minTime, maxTime, 4);
    test->SetParameter(0, x); // x
    test->SetParameter(1, y0); // y
    test->SetParameter(2, z); // z0
    test->SetParameter(3, q0); // q
    test->Draw(); 
    test->SetLineColor(kRed);
    legend.AddEntry(test, "PCD 0", "l"); 
    
    // PCD 1
    TF1* test1 = new TF1("test", OnePCD, minTime, maxTime, 4);
    test1->SetParameter(0, x); // x
    test1->SetParameter(1, y1); // y
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
    //test->Draw("l"); 
    test2->Draw("l");
    test->Draw("lp same"); 
    test1->Draw("l same"); 

    legend.Draw(); 
    canvas.Update();
    cout << "any key to continue" << endl;
    Char_t input; 
    cin >> input;  
}

