#include <iostream>
using namespace std;

void LightComparison()
{
	TChain *tree1 = new TChain("tree");
	tree1->Add("/nfs/slac/g/exo_data4/users/alexis4/test-stand/2016_03_07_7thLXe/tier3_external/tier3_overnight_cell_full_cathode_bias_1700V_2Vinput_DT1750mV_disc_teed_preamp_extraamplified_trigger_200delay_2016-03*.root");
	TChain *tree2 = new TChain("tree");
	tree2->Add("/nfs/slac/g/exo_data4/users/manisha2/MC/Bi207_Full_Ralph_dcoeff0/tier3/tier3_digi*_Bi207_Full_Ralph_dcoef0.root");
	cout << tree1->GetEntries() << endl; 
	cout << tree2->GetEntries() << endl;

	TCanvas c1("c1", "");
	TH1D *LightComparisonHist = new TH1D("LightComparisonHist", "LightEnergy-NPE Comparison", 100, 0, 3500);
	tree1->Draw("lightEnergy >> LightComparisonHist"); //draw lightEnergy into 100-bin hist	
	tree2->SetLineColor(kRed);	
	tree2->Draw("NPE*2.9", "(NPE>0)*200", "same"); //draw NPE into 100-bin hist

	LightComparisonHist->GetXaxis()->SetTitle("lightEnergy");
	LightComparisonHist->GetYaxis()->SetTitle("counts/90");
	LightComparisonHist->GetXaxis()->CenterTitle();
	LightComparisonHist->GetYaxis()->CenterTitle();

	c1.SetLogy(1);
	c1.Print("LightComparison.pdf");
	c1.Update();
	Int_t pause;
	cin >>pause;

 }



