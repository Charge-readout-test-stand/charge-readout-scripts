#include <iostream>
using namespace std;

void NPEActiveChargeCompare()
{
	TChain *tree2 = new TChain("tree");
//	tree2->Add("/nfs/slac/g/exo_data4/users/manisha2/MC/Bi207_Full_Ralph_dcoeff0/tier3/tier3_digi*_Bi207_Full_Ralph_dcoef0.root");//0V/cm
	tree2->Add("/nfs/slac/g/exo_data4/users/manisha2/MC/Bi207_Full_Ralph_dcoeff50_1kV/tier3/tier3_digi*_Bi207_Full_Ralph_dcoef50.root");//1kV/cm

	cout << tree2->GetEntries() << endl;

	TCanvas c1("c1", "");
//	tree2->Draw("NPEactive:chargeEnergy >> h(70, 0, 600, 70, 0, 600", "chargeEnergy<2500 && NPEactive>0", "colz"); //0V/cm
	tree2->Draw("NPEactive:chargeEnergy >> h(70, 0, 1450, 70, 0, 300", "chargeEnergy<2500 && NPEactive>0", "colz"); //1kV/cm

	h->GetXaxis()->SetTitle("chargeEnergy");
	h->GetYaxis()->SetTitle("NPEactive");
	h->GetXaxis()->CenterTitle();
	h->GetYaxis()->CenterTitle();
	gStyle->SetOptStat(0); //supress stat box	
	c1.SetLogz(1);
	c1.Print("NPEActiveChargeComparison.png");
	c1.Update();
	Int_t pause;
	cin >>pause;

}
