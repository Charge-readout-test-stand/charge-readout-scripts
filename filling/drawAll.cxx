// Ed Callaghan
// Plotting script - for use with output of singleChannelFilling.cxx
// April 2016

void drawAll()
{
	TFile *fin = new TFile("singlePlots.root") ;
	int nch = 8 ;

	TCanvas *cAll = new TCanvas() ;
	cAll->Divide(3,3) ;

	TGaxis *aCa = new TGaxis(0.95, 0.1, 0.95, 0.9, 31.5, 34.5, 510, "+L") ;
	aCa->SetLineColor(3) ;
	aCa->SetLabelColor(3) ; // green

	TCanvas *ct ;
	char cname[15] ;
	for (int ich = 0 ; ich < nch ; ich++)
	{
		sprintf(cname, "timePlot_%d", ich) ;
		ct = (TCanvas *) fin->Get(cname) ;
		cAll->cd(ich + 1) ;
		ct->DrawClonePad() ;
		aCa->Draw() ;
	}
	ct = (TCanvas *) fin->Get("totalChargeEnergy") ;
	cAll->cd(9) ;
	ct->DrawClonePad() ;
	aCa->Draw() ;

	cAll->SetCanvasSize(2400, 1800) ;
	cAll->SaveAs("all-channels.pdf") ;
	cAll->SaveAs("all-channels.png") ;
	cAll->SetCanvasSize(800, 600) ;
}
