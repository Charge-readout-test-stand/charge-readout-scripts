// Ed Callaghan
// Constructs plots of energies against time - plot using drawAll.cxx
// April 2016

TGraph *gSingleChannel(int ich)
{
	double HR_PER_SEC = 1.0/3600.0 ;

	TChain *dataTree = new TChain("tree") ;
	dataTree->Add("../filling_pulser.root") ;

	double file_start_time, first_event_time ;
	dataTree->SetBranchAddress("file_start_timeDouble", &file_start_time) ;
	dataTree->SetBranchAddress("first_event_time", &first_event_time) ;

	double energy[10] ;
	dataTree->SetBranchAddress("energy1_pz", &energy) ;

	double time ;
	dataTree->SetBranchAddress("timestampDouble", &time) ;

	TGraph *gEnergy = new TGraph() ;
	int ipt = 0 ;

	int nEntries = dataTree->GetEntries() ;
	cout << nEntries << '\n' ;

	double timeStart ;
	dataTree->GetEntry(0)  ;
	time = file_start_time - first_event_time + time*40/1e9 ;
	timeStart = -time ;
	for (int iEntry = 0 ; iEntry < nEntries ; iEntry++)
	{
		dataTree->GetEntry(iEntry) ;
		time = file_start_time - first_event_time + time*40/1e9 ;
		time += timeStart ;
		time *= HR_PER_SEC ;

		gEnergy->SetPoint(ipt, time, energy[ich]) ;
		ipt++ ;
	}

	delete dataTree ;

	return gEnergy ;
}

TGraph *gXeMass()
{
	double HR_PER_SEC = 1.0/3600.0 ;

	TChain *slowTree = new TChain("tree") ;
	slowTree->Add("../test_20160307_075550.root") ;

	double slowtime, mXe ;
	slowTree->SetBranchAddress("timeStamp", &slowtime) ;
	slowTree->SetBranchAddress("massXe", &mXe) ;

	TGraph *gXe = new TGraph() ;
	int iptXe = 0 ;

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

//		if (time < slowtime) // only during filling
//			continue ;

		gXe->SetPoint(iptXe, slowtime, mXe) ;
		iptXe++ ;
	}

	delete slowTree ;

	return gXe ;
}

TGraph *gCapacitance()
{
	double HR_PER_SEC = 1.0/3600.0 ;

	TChain *slowTree = new TChain("tree") ;
	slowTree->Add("../test_20160307_075550.root") ;

	double slowtime, ca ;
	slowTree->SetBranchAddress("timeStamp", &slowtime) ;
	slowTree->SetBranchAddress("capacitance", &ca) ;

	TGraph *gCa = new TGraph() ;
	int iptCa = 0 ;

	int nEntries = slowTree->GetEntries() ;
	cout << nEntries << '\n' ;

	double slowStart = 1457366150.0 ; // 20160307_075550 in POSIX
	double mXeStart ;
	slowTree->GetEntry(0) ;
	slowStart = 0.0 ; // FIXME should this be?
	slowStart -= slowtime ;
	for (int iEntry = 0 ; iEntry < nEntries ; iEntry++)
	{
		slowTree->GetEntry(iEntry) ;
		slowtime += slowStart ;
		slowtime *= HR_PER_SEC ;

//		if (time < slowtime) // only during filling
//			continue ;

		gCa->SetPoint(iptCa, slowtime, ca) ;
		iptCa++ ;
	}

	delete slowTree ;

	return gCa ;
}

TGraph *gChargeEnergy()
{
	double HR_PER_SEC = 1.0/3600.0 ;

	TChain *dataTree = new TChain("tree") ;
	dataTree->Add("../filling_pulser.root") ;

	double file_start_time, first_event_time ;
	dataTree->SetBranchAddress("file_start_timeDouble", &file_start_time) ;
	dataTree->SetBranchAddress("first_event_time", &first_event_time) ;

	double energy ;
	dataTree->SetBranchAddress("chargeEnergy", &energy) ;

	double time ;
	dataTree->SetBranchAddress("timestampDouble", &time) ;

	TGraph *gEnergy = new TGraph() ;
	int ipt = 0 ;

	int nEntries = dataTree->GetEntries() ;
	cout << nEntries << '\n' ;

	double timeStart ;
	dataTree->GetEntry(0)  ;
	time = file_start_time - first_event_time + time*40/1e9 ;
	timeStart = -time ;
	for (int iEntry = 0 ; iEntry < nEntries ; iEntry++)
	{
		dataTree->GetEntry(iEntry) ;
		time = file_start_time - first_event_time + time*40/1e9 ;
		time += timeStart ;
		time *= HR_PER_SEC ;

		gEnergy->SetPoint(ipt, time, energy) ;
		ipt++ ;
	}

	delete dataTree ;

	return gEnergy ;
}


void configureChYaxis(TGraph *g)
{
	double x, y ;
	double mean, mean_old, stdv, stdv_old ;

	g->GetPoint(0, x, mean_old) ;
	stdv_old = 0.0 ;

	int npts = g->GetN() ;
	for (int ipt = 1 ; ipt < npts ; ipt++)
	{
		g->GetPoint(ipt, x, y) ;

		mean = mean_old + (y - mean_old)/(ipt + 1) ;
		stdv = stdv_old + (y - mean)*(y - mean_old) ;
	}
	stdv = pow(stdv/npts, 1.0/2.0) ;

	g->GetYaxis()->SetRangeUser(mean - 10.0*stdv, mean + 70.0*stdv) ;
}

void singleChannelFilling()
{
	const int nch = 8 ;

	TCanvas *c = new TCanvas() ;
	TPad *chPad = new TPad("chPad", "", 0, 0, 1, 1) ;
	chPad->Draw() ;

	TPad *xePad = new TPad("xePad", "", 0, 0, 1, 1) ;
	xePad->Draw() ;
	xePad->SetFillStyle(4000) ;
	xePad->SetFillColor(0) ;
	xePad->SetFrameFillStyle(4000) ;

	TPad *caPad = new TPad("caPad", "", 0, 0, 1, 1) ;
	caPad->Draw() ;
	caPad->SetFillStyle(4000) ;
	caPad->SetFillColor(0) ;
	caPad->SetFrameFillStyle(4000) ;

	cout << "Building xenon plot... " ;
	TGraph *gXe = gXeMass() ;
	gXe->GetXaxis()->SetTitle("hours from 03/07/2016 07:55:50") ;
	gXe->GetXaxis()->SetRangeUser(0.0, 3.5) ;
//	gXe->GetYaxis()->SetTitle("mass Xe in cell [kg]") ;
	gXe->GetXaxis()->SetLabelSize(0.0) ;
	gXe->GetXaxis()->SetTickSize(0.0) ;
	gXe->GetYaxis()->SetRangeUser(-0.1, 6.5) ;
	gXe->GetYaxis()->SetAxisColor(6) ;
	gXe->GetYaxis()->SetLabelColor(6) ;
	gXe->GetYaxis()->SetTitleColor(6) ;
	gXe->SetMarkerColor(6) ; // purple

	cout << "Building capacitance plot... " ;
	TGraph *gCa = gCapacitance() ;
	gCa->GetXaxis()->SetTitle("hours from 03/07/2016 07:55:50") ;
	gCa->GetXaxis()->SetRangeUser(0.0, 3.5) ;
//	gCa->GetYaxis()->SetTitle("capacitance [a.u.]") ;
	gCa->GetXaxis()->SetLabelSize(0.0) ;
	gCa->GetXaxis()->SetTickSize(0.0) ;
	gCa->GetYaxis()->SetLabelSize(0.0) ;
	gCa->GetYaxis()->SetTickSize(0.0) ;
	gCa->GetYaxis()->SetRangeUser(31.5, 34.5) ;
//	gCa->GetYaxis()->SetAxisColor(3) ;
//	gCa->GetYaxis()->SetLabelColor(3) ;
//	gCa->GetYaxis()->SetTitleColor(3) ;
	gCa->SetMarkerColor(3) ; // green


	cout << "Building total charge plot... " ;
	TGraph *gCharge = gChargeEnergy() ;
	gCharge->SetTitle("Total Charge Energy - Filling") ;
	gCharge->GetXaxis()->SetRangeUser(0.0, 3.5) ;
	gCharge->GetYaxis()->SetTitle("total charge energy") ;
	configureChYaxis(gCharge) ;
	gCharge->GetYaxis()->SetTitleOffset(1.5) ;

	char title[100] ;
	TGraph *gChs[nch] ;
	for (int ich = 0 ; ich < nch ; ich++)
	{
		cout << "Building channel " << ich << "... " ;
		gChs[ich] = gSingleChannel(ich) ;
		sprintf(title, "Channel %d Charge Energy - Filling", ich) ;
		gChs[ich]->SetTitle(title) ;
		gChs[ich]->GetXaxis()->SetRangeUser(0.0, 3.5) ;
		gChs[ich]->GetYaxis()->SetTitle("energy1_pz") ;
		configureChYaxis(gChs[ich]) ;
		gChs[ich]->GetYaxis()->SetTitleOffset(1.5) ;
	}

	TFile *fout = new TFile("singlePlots.root", "RECREATE") ;
	chPad->cd() ;
	chPad->Clear() ;
	gCharge->Draw("ap") ;
	xePad->cd() ;
	xePad->Clear() ;
	gXe->Draw("apY+") ;
	caPad->cd() ;
	caPad->Clear() ;
	gCa->Draw("apY+") ;
	c->SetName("totalChargeEnergy") ;
	c->Write() ;

	char cname[15] ;
	for (int ich = 0 ; ich < nch ; ich++)
	{
		cout << "Drawing channel " << ich << "...\n" ;

		chPad->cd() ;
		chPad->Clear() ;
//		gChs[ich]->GetYaxis()->SetRangeUser(5000.0, 14000.0) ;
		gChs[ich]->Draw("ap") ;
		xePad->cd() ;
		xePad->Clear() ;
		gXe->Draw("apY+") ;
		caPad->cd() ;
		caPad->Clear() ;
		gCa->Draw("apY+") ;

		sprintf(cname, "timePlot_%d", ich) ;
		c->SetName(cname) ;
		c->Write() ;
	}
	delete fout ;

	delete gCa ;
	delete gXe ;
	delete gCharge ;
	for (int ich = 0 ; ich < nch ; ich++)
		delete gChs[ich] ;
}
