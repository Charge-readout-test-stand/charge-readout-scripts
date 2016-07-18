#include <iostream>
using namespace std;

void NPEtier3()
{
	TChain *tree = new TChain("tree");
	tree->Add("/nfs/slac/g/exo_data4/users/manisha2/MC/Bi207_Full_Ralph_dcoeff50/tier3/tier3_digi*_Bi207_Full_Ralph_dcoef50.root");
//	TFile *tier3 = TFile::Open("/nfs/slac/g/exo_data4/users/manisha2/MC/Bi207_Full_Ralph_dcoeff50/tier3/tier3_digi0_Bi207_Full_Ralph_dcoef50.root"); //Opens existing TFile tier3_digi0
// 	TTree *tree = tier3->Get("tree"); //get TTree data from tier3_digi0
	cout << tree->GetEntries() << endl; 
	
	TCanvas c1("c1", "");

 
	tree->Draw("NPE >> h(100)", "NPE>0"); //draw NPE into 100-bin hist
	c1.SetLogy(1);
	c1.Update();
	c1.Print("NPEtier3.pdf");
	Int_t pause;
	cin >> pause;
 }


