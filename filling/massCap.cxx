
void massCap()
{
	double HR_PER_SEC = 1.0/3600.0 ;

	TChain *slowTree = new TChain("tree") ;
	slowTree->Add("../test_20160307_075550.root") ;

	double slowtime, mXe, ca ;
	slowTree->SetBranchAddress("timeStamp", &slowtime) ;
	slowTree->SetBranchAddress("massXe", &mXe) ;
	slowTree->SetBranchAddress("capacitance", &ca) ;

	TGraph *gXe = new TGraph() ;
	TGraph *gCa = new TGraph() ;
	TGraph *gBoth = new TGraph() ;
	int ipt = 0;

	int nEntries = slowTree->GetEntries() ;
	cout << nEntries << '\n' ;

	double slowStart = 1457366150.0 ; // 20160307_075550 in POSIX
	double mXeStart ;
	slowTree->GetEntry(0) ;
	slowStart = 0.0 ; // FIXME should this be?
	slowStart -= slowtime ;
	mXeStart = mXe ;
	for (int iEntry = 0 ; iEntry < nEntries ; iEntry++)
	{
		slowTree->GetEntry(iEntry) ;
		slowtime += slowStart ;
		slowtime *= HR_PER_SEC ;
		mXe = mXeStart - mXe ;

		gXe->SetPoint(ipt, slowtime, mXe) ;
		gCa->SetPoint(ipt, slowtime, ca) ;

		if (((0.0 < slowtime) && (slowtime < 5.0)) || ((28.0 < slowtime) && (slowtime < 31.0)))
			gBoth->SetPoint(ipt, mXe, ca) ;
		ipt++ ;
	}

	delete slowTree ;

	gXe->SetMarkerColor(6) ;
	gXe->SetLineColor(6) ;
	gCa->SetMarkerColor(3) ;
	gCa->SetLineColor(3) ;

	TMultiGraph *mg = new TMultiGraph() ;
	mg->Add(gXe) ;
	mg->Add(gCa) ;

	TCanvas *cStacked = new TCanvas() ;
	mg->Draw("ap") ;
	mg->GetXaxis()->SetTitle("hours from 03/07/2016 07:55:50") ;
	mg->GetXaxis()->SetRangeUser(0.0, 40.0) ;
	mg->GetYaxis()->SetTitle("a.u.") ;
	gPad->Modified() ;

	TLine *lf1 = new TLine(0.0, 0.0, 0.0, 35.0) ;
	TLine *lf2 = new TLine(5.0, 0.0, 5.0, 35.0) ;
	TLine *lr1 = new TLine(28.0, 0.0, 28.0, 35.0) ;
	TLine *lr2 = new TLine(31.0, 0.0, 31.0, 35.0) ;

	lf1->SetLineStyle(3) ;
	lf2->SetLineStyle(3) ;
	lr1->SetLineStyle(3) ;
	lr2->SetLineStyle(3) ;

	lf1->Draw() ;
	lf2->Draw() ;
	lr1->Draw() ;
	lr2->Draw() ;

	TLegend *legend = new TLegend(0.25, 0.25, 0.5, 0.5) ;
	legend->AddEntry(gXe, "mass Xe [kg]", "l") ;
	legend->AddEntry(gCa, "capacitance [a.u.]", "l") ;
	legend->Draw() ;

	TCanvas *cBoth = new TCanvas() ;
	gBoth->SetTitle("Capactiance vs Xe Mass") ;
	gBoth->GetXaxis()->SetTitle("mass Xe [kg]") ;
	gBoth->GetXaxis()->SetRangeUser(-1.0, 21.0) ;
	gBoth->GetYaxis()->SetTitle("capacitance [a.u.]") ;
	gBoth->GetYaxis()->SetRangeUser(23.0, 37.0) ;
	gBoth->Draw("ap") ;

	TCanvas *cBothZoom = new TCanvas() ;
	gBoth->SetTitle("Capacitance vs Xe mass - Filling") ;
	gBoth->GetXaxis()->SetRangeUser(0.0, 7.0) ;
	gBoth->GetYaxis()->SetRangeUser(31.0, 36.0) ;
	gBoth->Draw("ap") ;
}
