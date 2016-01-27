// Macro myfunc.C
// This macro defines a TF1 with Ralph's analytical expression for the charge
// signal. 
// from https://root.cern.ch/root/html534/TF1.html#F3

Double_t f(Double_t x, Double_t y, Double_t z) {
  // from Ralph's definition
  return TMath::ATan(x*y/(z*TMath::Sqrt(x*x + y*y + z*z)));
}

Double_t OnePadRotated(Double_t x, Double_t y, Double_t z) {
  // response from one pad. Coordinates are rotated 45 degrees into pad's
  // coordinate system. 
  Double_t diagonal = 3.0; // mm
  Double_t side_length = diagonal / TMath::Sqrt(2.0);

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
      if ( x_n < x1 ) return 0;
      if ( x_n > x2 ) return 0;
      if ( y_n < y1 ) return 0;
      if ( x_n > y2 ) return 0;
      // otherwise return 1
      return 1.0;
  }

  return ( f(x2,y2,z) - f(x1,y2,z) - f(x2,y1,z) + f(x1,y1,z) ) / TMath::TwoPi();
}

Double_t MyFunction(Double_t *var, Double_t *par) {
  // reponse of the strip (currently just one pad)

  Double_t triggerTime = 8.0; // microseconds
  Double_t driftVelocity = 1.72; // mm/microsecond
  Double_t t = var[0];
  Double_t x = par[0];
  Double_t y = par[1];
  Double_t z0 = par[2];
  Double_t q = par[3]; 
  Double_t z = z0 - (t-triggerTime) * driftVelocity;  
  cout << "t: " << t << endl;
  if (t < triggerTime) { return 0.0; }
  if (z <= 0) { 
      return 1.0; 
  }
  cout << "z: " << z << endl;

  Double_t amplitude = 0.0;
  amplitude += OnePadRotated(x, y, z);
  cout << "amplitude: " << amplitude << endl;
  return q*amplitude; 
}

Double_t myfunc() {
    // a test -- just draw a sample wfm to see if things are working. 

    TF1* test = new TF1("test",MyFunction, 6, 20, 4);
    test->SetParameter(0, 0); // x
    test->SetParameter(1, 0); // y
    test->SetParameter(2, 17.0); // z0
    test->SetParameter(3, 1.0); // q
    test->Draw(); 

    TH1D* frameHist = test->GetHistogram(); 
    frameHist->SetXTitle("time [#mus]");
    frameHist->SetYTitle("charge [arb]");
    test->Draw(); 
}

