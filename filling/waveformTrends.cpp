// Ed Callaghan
// Early waveform studies
// April 2016

#include <iostream>
#include <cmath>

#include <stdio.h>
#include <stdlib.h>

#include "argParse.h"

#include <TAxis.h>
#include <TF1.h>
#include <TFile.h>
#include <TGraph.h>
#include <TTree.h>
#include <TProfile.h>

using namespace std ;

int wformA(char *fname, char *oname) ;

int main(int argc, char **argv)
{
	char *fname ;
	char *oname ;

	if (cmdOptionExists(argv, argv+argc, "-i"))
		fname = getCmdOption(argv, argv+argc, "-i") ;
	else
	{
		fprintf(stderr, "err: supply -i filename -o outname\n") ;
		return 1 ;
	}

	if (cmdOptionExists(argv, argv+argc, "-o"))
		oname = getCmdOption(argv, argv+argc, "-o") ;
	else
		oname = "trends.root" ;

	wformA(fname, oname) ;

	return 0 ;
}

int wformA(char *fname, char *oname)
{
	const int nch = 8 ;

//	TFile *fin = new TFile("../tier1_cathode_pulser_while_filling_2016-03-07_11-11-38.root") ;
	TFile *fin = new TFile(fname) ;
	TTree *tCh[nch] ;
	char tname[15] ;
	for (int ich = 0 ; ich < nch ; ich++)
	{
		sprintf(tname, "tree%d", ich) ;
		tCh[ich] = (TTree *) fin->Get(tname) ;
	}

	bool sameEntries = true ;
	int nEntries = tCh[0]->GetEntries() ;
	for (int ich = 1 ; ich < nch ; ich++)
	if (tCh[ich]->GetEntries() != nEntries)
		sameEntries = false ;
	if (!sameEntries)
	{
		fprintf(stderr, "err: channel trees not of same length\n") ;
		return 1 ;
	}

/*	if (tCh[ich]->GetEntries() < nEntries)
	{
		fprintf(stderr, "err: channel trees not of same length\n") ;
		nEntries = tCh[ich]->GetEntries() ;
	} */

	TTree *runtree = (TTree *) fin->Get("run_tree") ;
	unsigned int wfmLength ; // Rtypes.h
	runtree->SetBranchAddress("wfm_length", &wfmLength) ;
	runtree->GetEntry(0) ;
	cout << "Waveform length: " << wfmLength << '\n' ;
	unsigned short *wfm = new unsigned short [wfmLength] ;
	for (int ich = 0 ; ich < nch ; ich++)
		tCh[ich]->SetBranchAddress("wfm", wfm) ;

	TGraph *gWfm[nch] ;
	TGraph *gTrend[nch] ;
	TProfile *hTrend[nch] ;
	char hname[15] ;
	char htitle[50] ;
	for (int ich = 0 ; ich < nch ; ich++)
	{
		gWfm[ich] = new TGraph() ;
		gTrend[ich] = new TGraph() ;

		sprintf(hname, "hTrend_%d", ich) ;
		sprintf(htitle, "Y'/Y Channel %d", ich) ;
		hTrend[ich] = new TProfile(hname, htitle, 100, 0.0, wfmLength) ;
	}

	TF1 *lfit = new TF1("lfit", "[0] + [1]*x") ;
	const int fitlength = 50 ;
	double scale = 1.0e9 ;
	double x, y ;
	int iqt ;

	for (int ich = 0 ; ich < nch ; ich++) {
		cout << "Processing channel " << ich << "...\n" ;
		iqt = 0 ;
	for (int iEntry = 0 ; iEntry < nEntries ; iEntry++)
	{
		tCh[ich]->GetEntry(iEntry) ;

		for (int ipt = 0 ; ipt < wfmLength ; ipt++)
			gWfm[ich]->SetPoint(ipt, ipt, wfm[ipt]) ;

		for (int ipt = fitlength/2 ; ipt < wfmLength - fitlength/2 ; ipt += fitlength/4)
		{
			gWfm[ich]->GetPoint(ipt, x, y) ;
			if (y < 9.0e3)
				continue ;

			lfit->SetRange(ipt - fitlength/2, ipt + fitlength/2) ;
			gWfm[ich]->Fit(lfit, "RQ") ;

			gTrend[ich]->SetPoint(iqt, ipt, scale*lfit->GetParameter(1)/y) ;
			iqt++ ;

			hTrend[ich]->Fill(ipt, scale*lfit->GetParameter(1)/y) ;
		}
	} }

	TFile *fout = new TFile(oname, "RECREATE") ;
	char name[50] ;
	for (int ich = 0 ; ich < nch ; ich++)
	{
		sprintf(name, "Y'/Y Channel %d", ich) ;
		gTrend[ich]->SetTitle(name) ;
		gTrend[ich]->GetXaxis()->SetTitle("sample number") ;
		gTrend[ich]->GetYaxis()->SetTitle("Y'/Y") ;

		sprintf(name, "gTrend_%d", ich) ;
		gTrend[ich]->SetName(name) ;
		gTrend[ich]->Write() ;

		hTrend[ich]->GetXaxis()->SetTitle("sample number") ;
		hTrend[ich]->GetYaxis()->SetTitle("Y'/Y") ;
		hTrend[ich]->Write() ;
	}
	delete fout ;

	delete[] wfm ;
	for (int ich = 0 ; ich < nch ; ich++)
	{
		delete gWfm[ich] ;
		delete gTrend[ich] ;
		delete hTrend[ich] ;
		delete tCh[ich] ;
	}
	delete fin ;

	return 0 ;
}
