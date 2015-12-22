/*
 
arguments: struck .dat output file(s)

options: -b = batch
check TApplication::GetOptions() for the full list:
https://root.cern.ch/doc/master/classTApplication.html

Note about original code from Struck SIS3316-DT DVD: as far as i can tell, this
opens saved files from sis3316  (in the hard-coded internal directory) and draws
waveforms. 

Fun fact: the struck is numbered 1 through 16 but the channels in the binary
file are labelled 0 to 15. 

changes to original code:
* using argc to determine which files to draw
* turning drawing off if desired
* calc max wfm value
* formatting/indenting changes
* generating an output tree
* printing png file of spectra
*/

//============================================================================
// Name        : sis3316_offline.cpp
// Author      : th
// Version     :
// Copyright   : Your copyright notice
// Description : Hello World in C++, Ansi-style
//============================================================================

#include "project_system_define.h"		//define LINUX or WINDOWS

#include <iostream>
#include <sstream>
#include <climits>
#include <fstream>
using namespace std;

#define CERN_ROOT_PLOT

#ifdef CERN_ROOT_PLOT
	#include "rootIncludes.h"
        #include <TLegend.h>
	#include "sis3316_cern_root_class.h"
	sis_root_graph *gl_graph_raw ;
#endif


/*===========================================================================*/
/* Globals					  			     */
/*===========================================================================*/
#define MAX_NUMBER_LWORDS_64MBYTE			0x1000000       /* 64MByte */

// this is the data read from the file
UInt_t gl_ch_data[MAX_NUMBER_LWORDS_64MBYTE] ;

FILE *gl_FILE_DataEvenFilePointer           ;

/*===========================================================================*/
/* Prototypes			                               		  			     */
/*===========================================================================*/

int ReadBufferHeaderCounterNofChannelToDataFile (UInt_t* indentifier, UInt_t* bank_loop_no, UInt_t* channel_no, UInt_t* nof_events, UInt_t* event_length, UInt_t * maw_length, UInt_t* reserved);
int ReadEventsFromDataFile (UInt_t* memory_data_array, UInt_t nof_write_length_lwords);
int ReadConfigFile(string config_filename_str, Bool_t* is_external, Float_t* sampling_freq_Hz, UShort_t* wfm_delay, UShort_t* maw_delay, Bool_t* is_pospolarity, Bool_t* is_50ohm, Bool_t* is_2Vinput, UShort_t* maw_gap, UShort_t* maw_peaking, UShort_t* maw_thres);


/* ***************************************************************************************************************** */
int main(int argc, char* argv[]) {

  cout << "sis3316_offline" << endl; // prints sis3316_offline

  /******************************************************************************************************************************/
  /* CERN ROOT                                                                                                                  */
  /******************************************************************************************************************************/

  #ifdef CERN_ROOT_PLOT

    printf("--> CERN_ROOT_PLOT is defined \n");
    int root_graph_x ;
    int root_graph_y ;
    int root_graph_x_size ;
    int root_graph_y_size ;
    char root_graph_text[80] ;

    root_graph_x_size = 1000 ;
    root_graph_y_size = 500 ;

    root_graph_x = 10 ;
    root_graph_y = 620 ;

    cout << "argc: " << argc << endl;
    for (int i = 1; i < argc; i++){ cout << "argv[" << i << "]: " << argv[i] << endl; }


    // this root class extracts data from argc and argv, modifying them in the
    // process
    TApplication theApp("SIS3316 Application: Test", &argc, argv);
    strcpy(root_graph_text,"SIS3316 Graph: Raw data") ;
    gl_graph_raw      = new sis_root_graph(root_graph_text, root_graph_x, root_graph_y, root_graph_x_size, root_graph_y_size) ;

  #endif

  #ifdef raus
    printf("--> raus is defined \n");
    // file read
    gl_FILE_DataEvenFilePointer = fopen("ne213/sis3316_test_data.dat","rb") ;
    if (gl_FILE_DataEvenFilePointer == NULL) {
            printf("gl_FILE_DataEvenFilePointer == NULL \n");
            return -1;
    }
    else {
            printf("file is opened \n");
    }
  #endif
  UInt_t valid_BankBufferHeader_valid_flag ;
  int nof_read ;
  UInt_t buffer_no ;
  UInt_t i_event ;
  UInt_t nof_events ;
  UInt_t buffer_length ;
  UInt_t event_length ;
  UInt_t header_length ;
  UInt_t wfm_length ;
  UInt_t channel_no ;
  UInt_t maw_length ;
  UInt_t i_ch ;
  UInt_t headerformat ;
  UInt_t header_indentifier ;
  UInt_t header_reserved ;


  //gl_graph_raw->sis3316_draw_XYaxis (50000); // clear and draw X/Y
  //gl_graph_raw->sis3316_draw_XYaxis (wfm_length); // clear and draw X/Y
  UInt_t bank_buffer_counter ;

  char filename[128]  ;
  int i_file;

  bank_buffer_counter = 8 ;


  bool doDraw = true;
  if ( gROOT->IsBatch() ) {
    doDraw = false; 
    cout << "--> running in batch mode" << endl;
  }

  // loop over enumerated files in internal directory:
  //for (i_file=0; i_file<10; i_file++) {

    //sprintf(filename,"../data_files/sample_test_gui/sis3316_test_data_%d.dat",i_file ) ;
    //sprintf(filename,"../data_files/external/sis3316_test_data_%d.dat",i_file ) ;
    //sprintf(filename,"../data_files/internal/sis3316_test_data_%d.dat",i_file ) ;

  // loop over args:
  for (i_file = 1; i_file<theApp.Argc(); i_file++) {

    //cout << "filename: " <<  argv[i_file+1] << endl;
    //sprintf(filename,"%s",argv[i_file+1]) ;
    sprintf(filename,"%s", theApp.Argv(i_file)) ;

#ifdef CERN_ROOT_PLOT


    string filename_str(filename);
    if ( filename_str.size() < 3 ) { 
      cout << "option: " << filename_str << endl; 
      continue; 
    }
    cout << "filename: " << filename << endl;
    size_t dot = filename_str.find_last_of(".");
    size_t slash = filename_str.find_last_of("/");
    string basename_str = "tier1_" + filename_str.substr(slash+1, dot-slash-1);
    string config_filename_str = filename_str.substr(0, dot) + ".ini";
    cout << "Setting file label " << basename_str << endl;

    // open a root file
    TFile root_file((basename_str + ".root").c_str(), "recreate");

    // make trees
    TTree *tree[16];

    //values for branches
    //global parameters
        Bool_t is_external = false;
        Float_t sampling_freq_Hz = 25e6; // in Hz
        UShort_t wfm_delay = 300;
        UShort_t maw_delay = 600;
        Bool_t is_pospolarity[16];
        Bool_t is_50ohm[16];
        Bool_t is_2Vinput[16];
        UShort_t maw_gap = 250;
        UShort_t maw_peaking = 50;
        UShort_t maw_thres = 60;
        for(int i=0; i<=15; i++) {is_pospolarity[i] = is_50ohm[i] = is_2Vinput[i] = true;}

     //read from config file
        ReadConfigFile(config_filename_str, &is_external, &sampling_freq_Hz, &wfm_delay, &maw_delay, is_pospolarity, is_50ohm, is_2Vinput, &maw_gap, &maw_peaking, &maw_thres);

     //other parameters
        Int_t wfm_max = 0; 
        UShort_t wfm_max_time = 0;
        Int_t wfm_min = 0;
        Int_t maw_max = 0; 
        Int_t maw_min = 0; 
        UChar_t channel = 0;
        ULong64_t timestamp = 0;
        Double_t timestampDouble = 0;
        //ULong64_t timestampLo = 0;
        //ULong64_t timestampHi = 0;
        UShort_t * wfm = new UShort_t[2048*4]; 
        Int_t * maw = new Int_t[2048*4];

    //read configuration file

    for(int i=0; i<=15; i++) { // looping over the 16 trees
        ostringstream treename;
        treename << "tree" << i;
        tree[i] = new TTree(treename.str().c_str(), "tree of SIS waveform data");

        // global parameters
        tree[i]->Branch("is_external", &is_external, "is_external/O");
        tree[i]->Branch("sampling_freq_Hz", &sampling_freq_Hz, "sampling_freq_Hz/F");
        tree[i]->Branch("wfm_delay", &wfm_delay, "wfm_delay/s");
        tree[i]->Branch("wfm_length", &wfm_length, "wfm_length/i");
        tree[i]->Branch("maw_delay", &maw_delay, "maw_delay/s");
        tree[i]->Branch("maw_length", &maw_length, "maw_length/i");
        tree[i]->Branch("is_pospolarity", &is_pospolarity[i], "is_pospolarity/O");
        tree[i]->Branch("is_50ohm", &is_50ohm[i], "is_50ohm/O");
        tree[i]->Branch("is_2Vinput", &is_2Vinput[i], "is_2Vinput/O");
        tree[i]->Branch("maw_gap", &maw_gap, "maw_gap/s");
        tree[i]->Branch("maw_peaking", &maw_peaking, "maw_peaking/s");
        tree[i]->Branch("maw_thres", &maw_thres, "maw_thres/s");

        // create a maximum-value branch
        //UInt_t wfm_max = 0; 
        tree[i]->Branch("wfm_max", &wfm_max, "wfm_max/I");

        // time of waveform max value:
        //UInt_t wfm_max_time = 0;
        tree[i]->Branch("wfm_max_time", &wfm_max_time, "wfm_max_time/s");

        // create a mininum-value branch
        //UInt_t wfm_min = 0; 
        tree[i]->Branch("wfm_min", &wfm_min, "wfm_min/I");

        // create a maximum-value branch
        //signed int maw_max = 0; 
        tree[i]->Branch("maw_max", &maw_max, "maw_max/I");

        // create a mininum-value branch
        //signed int maw_min = 0; 
        tree[i]->Branch("maw_min", &maw_min, "maw_min/I");

        // create a channel branch
        //int channel = 0;
        tree[i]->Branch("channel", &channel, "channel/b"); // 8 bit unsigned integer

        // create a timestamp branch
        //ULong64_t timestamp = 0;
        //double  timestampDouble = 0;
        tree[i]->Branch("timestamp", &timestamp, "timestamp/l"); // 64 bit unsigned integer (ULong64_t)
        tree[i]->Branch("timestampDouble", &timestampDouble, "timestampDouble/D"); // (Double_t)

        // create a buffer number branch
        // tree[i]->Branch("buffer_no", &buffer_no);

        // create an event  number branch
        tree[i]->Branch("event", &i_event, "event/i"); // unsigned integer (UInt_t)
    
        // wfm
        //UShort_t * wfm = new UShort_t[2048*4]; 
        tree[i]->Branch("wfm", wfm, "wfm[wfm_length]/s");

        // maw buffer
        tree[i]->Branch("maw_length", &maw_length);

        // maw
        //signed int * maw = new signed int[2048*4]; 
        tree[i]->Branch("maw", maw, "maw[maw_length]/I");
    }
#endif

    cout << "argc: " << argc << endl;
    for (int i = 1; i < argc; i++){ cout << "argv[" << i << "]: " << argv[i] << endl; }

    //cout << theApp.Argc() << endl;
    //cout << theApp.Argv(i_file) << endl;

    printf("--> processing file: %s\n",filename) ;
    gl_FILE_DataEvenFilePointer = fopen(filename,"rb") ;
    if (gl_FILE_DataEvenFilePointer != NULL) {

      do {

        valid_BankBufferHeader_valid_flag = 0 ;

        // read the buffer header
        nof_read = ReadBufferHeaderCounterNofChannelToDataFile (&header_indentifier, &buffer_no, &channel_no, &nof_events, &event_length, &maw_length, &header_reserved) ;
        buffer_length = event_length * nof_events ;

        printf("\n");
        printf("header information: \tnof_read = %d    \tindentifier = %d   \tbuffer_no = %d  \tchannel_no = %d   \n", nof_read, header_indentifier, buffer_no, channel_no);
        printf("header information: \tnof_events = %d  \tbuffer_length = %d   \tevent_length = %d    \n", nof_events, buffer_length, event_length );
        printf("header information: \tmaw_length = %d \treserved = %d \n",  maw_length, header_reserved);
        unsigned uint_plot_axis_flag;
        if (nof_read == 8) {
          uint_plot_axis_flag = 1 ;
          valid_BankBufferHeader_valid_flag = 1 ;

          // read buffer (of nof_events  events) into gl_ch_data 
          nof_read =  ReadEventsFromDataFile (gl_ch_data, buffer_length);

          // grab header format and channel number from the 0th event; assume
          // this applies to all nof_events 

          // mask to get the header format:
          headerformat =  (gl_ch_data[0] & 0xf) ;

          // mask and bitshift to get the channel number 
          i_ch = (gl_ch_data[0] & 0xfff0) >> 4 ;
          
          printf("nof_read = %d  \tch = %d   \theaderformat = 0x%02X \n", nof_read, i_ch, headerformat);

          if (i_ch != channel_no) {
            cout << "WARNING -- i_ch=" << i_ch << ", channel_no=" << channel_no << endl; 
          }

          header_length = 3 ; // if headerformat == 0
          if((headerformat & 0x1) == 1) {header_length = header_length + 7; }
          if((headerformat & 0x2) == 2) {header_length = header_length + 2; }
          if((headerformat & 0x4) == 4) {header_length = header_length + 3; }
          if((headerformat & 0x8) == 8) {header_length = header_length + 2; }

          // wfm_length is the number of 16-bit ADC samples in each event
       // event_length is the number of 32-bit words in each event
          wfm_length = 2 * (gl_ch_data[header_length-1] & 0x3ffffff) ; // if headerformat == 0

          if(uint_plot_axis_flag == 1) {
                  //printf("uint_plot_axis_flag == 1\n");
                  uint_plot_axis_flag = 0 ;
                  gl_graph_raw->sis3316_draw_XYaxis (wfm_length); // clear and draw X/Y
          }

          // loop over all events in gl_ch_data
          for (i_event = 0; i_event < nof_events; i_event++) {
            //if (i_event<10) { // plot ony the first 10. events
            //if (i_event<1) { // plot ony 1. event

              //cout << sizeof(UInt_t) << endl;
              // gl_ch_data is an UInt_t is 4 bytes (32 bits), at least on
              // Alexis' Mac. Bit mask each part of the timestamp, then bit shift to
              // make the 48-bit timestamp
              // 0xffff = 32 bits, 4 bytes

              size_t event_index = i_event*event_length;

              //cout << "gl_ch_data[event_index + 1] : " << gl_ch_data[event_index + 1] << endl;
              //cout << "gl_ch_data[event_index]: " << gl_ch_data[event_index] << endl;
              //cout << "(gl_ch_data[event_index] & 0xffff0000): " << ( (ULong64_t) (gl_ch_data[event_index] & 0xffff0000)) << endl;
              //cout << "(gl_ch_data[event_index] & 0xffff0000) << 16 :" << ( (ULong64_t) (gl_ch_data[event_index] & 0xffff0000) << 16) << endl;

              timestamp = ( (ULong64_t) (gl_ch_data[event_index] & 0xffff0000) << 16) ;
              timestamp += gl_ch_data[event_index + 1];
              //timestampHi = ( (ULong64_t) (gl_ch_data[event_index] & 0xffff0000) << 16) ;
              //timestampLo = gl_ch_data[event_index + 1];
              timestampDouble = (Double_t) timestamp;


              // find the wfm maximum value
              wfm_max = 0; 
              wfm_max_time = 0;
              wfm_min = pow(2, 14); // max value of ADC
              UShort_t* ushort_adc_buffer_ptr = (UShort_t*) (&gl_ch_data[i_event*(event_length) + header_length]);
              for (UInt_t i = 0; i < wfm_length; i++ ) {
                UInt_t adc_value = (UInt_t) ushort_adc_buffer_ptr[i];
                wfm[i] = adc_value;
                //cout << i << " | " << adc_value << endl;
                if (adc_value > wfm_max){ 
                    wfm_max = adc_value; 
                    wfm_max_time = i;
                }
                if (adc_value < wfm_min){ wfm_min = adc_value; }
              }

              if (doDraw) {
                cout << "wfm_max: " << wfm_max << endl;
                cout << "timestamp: " << timestamp << endl;

                gl_graph_raw->sis3316_draw_chN (wfm_length,
                    &gl_ch_data[event_index + header_length], i_ch&0xf);

                // insert pause 
                cout << "event " << i_event 
                  << " | channel " << i_ch
                  << " |  enter to continue (q=quit, b=batch, p=print)--> ";
                int val = cin.get();
                cout << endl;
                if (val == (int) 'q' || val == (int) 'Q') { return 0; }
                if (val == (int) 'b') { doDraw = false; }
                if (val == (int) 'p') { 

                    ostringstream plotName; 
                    plotName << basename_str  << i_event;
                    gl_graph_raw->c1->Print((plotName.str() + ".png").c_str());
                    gl_graph_raw->c1->Print((plotName.str() + ".pdf").c_str());
                }
              }

              //wfm = (UShort_t*) &(gl_ch_data[event_index + header_length]);

              //------------------------------------------------------------------------------
              // MAW
              //------------------------------------------------------------------------------

              // find the maw maximum value
              // I hope this is the MAW
              maw_max = 0; 
              maw_min = INT_MAX; // max value of MAW

              //UShort_t* maw_adc_buffer_ptr = (UShort_t*)
              //(&gl_ch_data[i_event*(event_length) + header_length +
              //wfm_length/2]);

              // Tino says maw is 32 bits:
              UInt_t* maw_adc_buffer_ptr =
              &gl_ch_data[i_event*(event_length) + header_length +
              wfm_length/2];

              for (UInt_t i = 0; i < maw_length; i++ ) {
                signed int maw_value = maw_adc_buffer_ptr[i] - 0x8000000; // per Tino
                maw[i] = maw_value;

                //cout << i 
                //  << " | maw_adc_buffer_ptr[i]:" << maw_adc_buffer_ptr[i] 
                //  << " | maw_value: " << maw_value 
                //  << " | maw[i] " << maw[i] 
                //  << endl;

                if (maw_value > maw_max){ maw_max = maw_value; }
                if (maw_value < maw_min){ maw_min = maw_value; }
              }

              /*
              if (doDraw) {
                cout << "maw_max: " << maw_max << endl;
                cout << "timestamp: " << timestamp << endl;

                gl_graph_raw->sis3316_draw_chN (wfm_length,
                    &gl_ch_data[event_index + header_length + wfm_length/2], i_ch&0xf);

                // insert pause 
                cout << "event " << i_event 
                  << " | channel " << i_ch
                  << " |  enter to continue (q=quit, b=batch)--> ";
                int val = cin.get();
                cout << endl;
                if (val == (int) 'q' || val == (int) 'Q') { return 0; }
                if (val == (int) 'b') { doDraw = false; }
              }
              */

              channel = (gl_ch_data[event_index] & 0xfff0) >> 4;
              tree[channel]->Fill();

              // each buffer should contain data from only one channel
              if (i_ch != channel_no) {
                cout << "WARNING -- channel=" << channel << ", channel_no=" << channel_no << endl; 
              }

            //} // end limit on n events

          } // end loop over events

        } // end if(nof_read==8)
        else {
                valid_BankBufferHeader_valid_flag = 0 ;
        }
      } while(valid_BankBufferHeader_valid_flag == 1) ;
            printf("\n");

            fclose(gl_FILE_DataEvenFilePointer);
            printf("file closed and finished   \n");
            bank_buffer_counter++;
    }


  gROOT->SetStyle("Plain");     
  gStyle->SetOptStat(0);        
  gStyle->SetPalette(1);        
  gStyle->SetTitleStyle(0);     
  gStyle->SetTitleBorderSize(0);       

  int n_bins = 200;
  int min = 0;
  int max = 16384; 

  const size_t n_channels = 16; 
  const size_t n_colors = 4; 
  TH1D* hist_array[n_channels]; 
  int color[n_colors] = {kRed, kBlue, kGreen+1, kViolet}; 
  int fillStyle[n_channels] = {3004, 3005, 3006, 3007, 3001, 3002, 3003, 3016,
      3017, 3018, 3020, 3021}; 

  TH1D frame_hist("frame_hist","",n_bins, min, max);
  frame_hist.SetXTitle("Waveform max (ADC units)");
  frame_hist.SetYTitle("Counts");


  for (size_t i = 0; i <n_channels; i++) {

    ostringstream name; 
    name << "h" << i;
    TH1D* hist = new TH1D(name.str().c_str(), "", n_bins, min, max);
    int i_color = i % n_colors;
    //cout << i << " | " << name.str() << " | " << i_color << endl;
    hist->SetLineColor(color[i_color]);
    hist->SetFillColor(color[i_color]);
    hist->SetFillStyle(fillStyle[i]);
    hist_array[i] = hist;
  }

  TLegend legend(0.1, 0.81, 0.9, 0.99);
  legend.SetNColumns(4); 

  TCanvas canvas("canvas", "");
  canvas.SetLogy(1); 
  canvas.SetGrid(1,1);
  canvas.SetTopMargin(0.2);

  double hist_max = 0;
  frame_hist.Draw();

  for (size_t i = 0; i < n_channels; i++) {
  
    ostringstream entry;
    ostringstream name;
    ostringstream selection;

    name << "wfm_max >> h" << i;  
    selection << "channel==" << i; 
    int n_counts = tree[0]->Draw(name.str().c_str(), selection.str().c_str(), "same");
    cout << i << " | n counts = " << n_counts << " | " << name.str() << " | " << selection.str() << endl;
    entry << "ch " << i+1 << " (" << n_counts << ")";
    TH1D* hist = hist_array[i];
    legend.AddEntry(hist, entry.str().c_str(), "f");
    if ( n_counts > hist_max ) { hist_max = n_counts; }
  }

  frame_hist.SetMaximum(hist_max*1.1);

  legend.Draw();
  canvas.Update();
  canvas.Print((basename_str + ".png").c_str());
  canvas.Print((basename_str + ".pdf").c_str());

  for(int i=0; i<=15; i++) {tree[i]->Write();}
  canvas.Write();

// create a run_tree with event parameters
  TTree *run_tree = new TTree("run_tree", "run tree");
  run_tree->Branch("is_external", &is_external, "is_external/O");
  run_tree->Branch("sampling_freq_Hz", &sampling_freq_Hz, "sampling_freq_Hz/F");
  run_tree->Branch("wfm_delay", &wfm_delay, "wfm_delay/s");
  run_tree->Branch("wfm_length", &wfm_length, "wfm_length/i");
  run_tree->Branch("maw_delay", &maw_delay, "maw_delay/s");
  run_tree->Branch("maw_length", &maw_length, "maw_length/i");
  run_tree->Branch("maw_gap", &maw_gap, "maw_gap/s");
  run_tree->Branch("maw_peaking", &maw_peaking, "maw_peaking/s");
  run_tree->Branch("maw_thres", &maw_thres, "maw_thres/s");

  run_tree->Fill();
  run_tree->Write();

  } // end loop over arguments/files



  #ifdef raus
  fclose(gl_FILE_DataEvenFilePointer);
  printf("file closed and finished   \n");
  #endif

  /*
  int i = 0; 
  do {
          // what is this?! It just seems to loop forever -- AGS
          gSystem->ProcessEvents();  // handle GUI events
          cout << i << " what is this?!!" << endl;
          i++; 
  } while (1) ;
  */

  return 0;
}


//---------------------------------------------------------------------------

int ReadBufferHeaderCounterNofChannelToDataFile (UInt_t* indentifier, UInt_t* bank_loop_no, UInt_t* channel_no, UInt_t* nof_events, UInt_t* event_length, UInt_t* maw_length, UInt_t* reserved)
{
int nof_read ;
int data ;
  //header
	nof_read=fread(&data, 0x4, 0x1, gl_FILE_DataEvenFilePointer);
	nof_read=nof_read+fread(indentifier, 0x4, 0x1, gl_FILE_DataEvenFilePointer);
	nof_read=nof_read+fread(bank_loop_no, 0x4, 0x1, gl_FILE_DataEvenFilePointer);
	nof_read=nof_read+fread(channel_no, 0x4, 0x1, gl_FILE_DataEvenFilePointer);
	nof_read=nof_read+fread(nof_events, 0x4, 0x1, gl_FILE_DataEvenFilePointer);
	nof_read=nof_read+fread(event_length, 0x4, 0x1, gl_FILE_DataEvenFilePointer);
	nof_read=nof_read+fread(maw_length, 0x4, 0x1, gl_FILE_DataEvenFilePointer);
	nof_read=nof_read+fread(reserved, 0x4, 0x1, gl_FILE_DataEvenFilePointer);

 	return nof_read;
}


//---------------------------------------------------------------------------
int ReadEventsFromDataFile (UInt_t* memory_data_array, UInt_t nof_write_length_lwords)
{
int nof_read ;

	nof_read=fread(memory_data_array, 0x4, nof_write_length_lwords, gl_FILE_DataEvenFilePointer);
 	return nof_read;
}


// This function reads the parameters from the config file.
// It reads line by line, and records the parameter if the keyword is matched
int ReadConfigFile(string config_filename_str, Bool_t* is_external, Float_t* sampling_freq_Hz, UShort_t* wfm_delay, UShort_t* maw_delay, Bool_t* is_pospolarity, Bool_t* is_50ohm, Bool_t* is_2Vinput, UShort_t* maw_gap, UShort_t* maw_peaking, UShort_t* maw_thres)
{
    string line;
    ifstream config_file(config_filename_str.c_str(), ifstream::in);
    bool flag = false; //this flag records whether is_external has been set, to avoid settings
                       //where both or neither of external and interal trigger are set
    if(config_file.is_open()) {
        while(!config_file.eof()) {
            getline(config_file, line);
            istringstream line_stream(line);
            string keyword;
            int n;

            if(line_stream >> keyword) { //first read the keyword
                //cout << keyword << endl;
                if(keyword.compare("PARAMETER_PRE_TRIGGER_DELAY") == 0) // wfm_delay
                    {line_stream >> n; *wfm_delay = n; continue;}

                else if(keyword.compare("PARAMETER_MAW_TEST_BUFFER_DELAY") == 0) // maw_delay
                    {line_stream >> n; *maw_delay = n; continue;}

                else if(keyword.compare("PARAMETER_TRIGGER_COND_ADC_EXTERNAL") == 0) { // is_external
                    line_stream >> n;
                    if(flag && *is_external != bool(n)) { //if is_external has been set and is in conflict with current value
                        cout << "Error in external/internal trigger settings! ... skipping the file" << endl;
                        exit(0);    
                    }
                    else {
                        *is_external = bool(n);
                        flag = true;
                    }
                }

                else if(keyword.compare("PARAMETER_TRIGGER_COND_ADC_INTERNAL") == 0) { // is_external
                    line_stream >> n;
                    if(flag && *is_external == bool(n)) { //if is_external has been set and is in conflict with current value
                        cout << "Error in external/internal trigger settings! ... skipping the file" << endl;
                        exit(0);    
                    }
                    else {
                        *is_external = !(bool(n));
                        flag = true;
                    }
                }

                else if(keyword.compare("PARAMETER_CHANNEL_POLARITY_INVERT") == 0) { // is_pospolarity
                    //NOTE: values in .ini file goes from channel 15 to channel 0
                    for(int i = 15; i >= 0; i--) {
                        line_stream >> n;
                        is_pospolarity[i] = !(bool(n));
                    }
                }

                else if(keyword.compare("PARAMETER_CHANNEL_RANGE_2V") == 0) { // is_2Vinput
                    for(int i = 15; i >= 0; i--) {
                        line_stream >> n;
                        is_2Vinput[i] = bool(n);
                    }
                }
                
                else if(keyword.compare("PARAMETER_CHANNEL_50OHM_TERMINATION_DISABLE") == 0) { // is_50ohm
                    for(int i = 15; i >= 0; i--) {
                        line_stream >> n;
                        is_50ohm[i] = !(bool(n));
                    }
                }

                else if(keyword.compare("PARAMETER_CHANNEL_TRIGGER_GENERATION_GAP") == 0) // maw_gap
                    {line_stream >> n; *maw_gap = n; continue;}

                else if(keyword.compare("PARAMETER_CHANNEL_TRIGGER_GENERATION_PEAKING") == 0) // maw_peaking
                    {line_stream >> n; *maw_peaking = n; continue;}

                else if(keyword.compare("PARAMETER_CHANNEL_TRIGGER_GENERATION_THRESHOLD") == 0) // maw_thres
                    {line_stream >> n; *maw_thres = n; continue;}

                else if(keyword.compare("PARAMETER_INTERNAL_SAMPLE_CLOCK_IDX") == 0) { // samping_freq
                    line_stream >> n;
                    switch(n) {
                        case 0: *sampling_freq_Hz = 250.000e6; break;
                        case 1: *sampling_freq_Hz = 227.273e6; break;
                        case 2: *sampling_freq_Hz = 208.333e6; break;
                        case 3: *sampling_freq_Hz = 178.571e6; break;
                        case 4: *sampling_freq_Hz = 166.667e6; break;
                        case 5: *sampling_freq_Hz = 138.889e6; break;
                        case 6: *sampling_freq_Hz = 125.000e6; break;
                        case 7: *sampling_freq_Hz = 119.048e6; break;
                        case 8: *sampling_freq_Hz = 113.636e6; break;
                        case 9: *sampling_freq_Hz = 104.167e6; break;
                        case 10: *sampling_freq_Hz = 100.000e6; break;
                        case 11: *sampling_freq_Hz = 83.333e6; break;
                        case 12: *sampling_freq_Hz = 71.429e6; break;
                        case 13: *sampling_freq_Hz = 62.500e6; break;
                        case 14: *sampling_freq_Hz = 50.000e6; break;
                        case 15: *sampling_freq_Hz = 25.000e6; break;
                        default: cout << "Wrong sampling clock configuration! skipping file..." << endl;
                                 exit(0);
                    }
                }
            }
        }
    }

    else { // fail to open config file
        cout << ".ini file does not exist! Using default parameters..." << endl;
        return 0;
    }
    return 1;
}
