//
/***************************************************************************/
/*                                                                         */
/*  Filename: sis3316_root_gui_test1.h                                     */
/*                                                                         */
/*  Funktion:                                                              */
/*                                                                         */
/*  Autor:                TH                                               */
/*  date:                 27.03.2015                                       */
/*  last modification:    01.04.2015                                       */
/*                                                                         */
/* ----------------------------------------------------------------------- */
/*                                                                         */
/*  SIS  Struck Innovative Systeme GmbH                                    */
/*                                                                         */
/*  Harksheider Str. 102A                                                  */
/*  22399 Hamburg                                                          */
/*                                                                         */
/*  Tel. +49 (0)40 60 87 305 0                                             */
/*  Fax  +49 (0)40 60 87 305 20                                            */
/*                                                                         */
/*  http://www.struck.de                                                   */
/*                                                                         */
/*  © 2015                                                                 */
/*                                                                         */
/***************************************************************************/
#ifndef _SIS3316_ROOT_GUI_TEST1_
#define _SIS3316_ROOT_GUI_TEST1_

#include "rootIncludes.h"
#include "fftw3.h"
#include "get_configuration_parameters.h"

#define SIS3316_TEST_WINDOW_WIDTH_RUN			400
#define SIS3316_TEST_WINDOW_WIDTH				600
#define SIS3316_TEST_WINDOW_HIGH				1120
#define SIS3316_TEST_WINDOW_POSTION_X			30
#define SIS3316_TEST_WINDOW_POSTION_Y			10

#define SIS3316_RAW_DATA_WINDOW_WIDTH			800
#define SIS3316_RAW_DATA_WINDOW_HIGH			490
#define SIS3316_RAW_DATA_WINDOW_POSTION_X		395
#define SIS3316_RAW_DATA_WINDOW_POSTION_Y		50


#define SIS3316_HISTOGRAM_WINDOW_WIDTH			700
#define SIS3316_HISTOGRAM_WINDOW_HIGH			1035
#define SIS3316_HISTOGRAM_WINDOW_POSTION_X		1170
//#define SIS3316_HISTOGRAM_WINDOW_POSTION_X		1200
#define SIS3316_HISTOGRAM_WINDOW_POSTION_Y		50

#define SIS3316_MAW_WINDOW_WIDTH				800
#define SIS3316_MAW_DATA_WINDOW_HIGH			490
#define SIS3316_MAW_DATA_WINDOW_POSTION_X		395
#define SIS3316_MAW_DATA_WINDOW_POSTION_Y		565

#define SIS3316_FFT_WINDOW_WIDTH				800
#define SIS3316_FFT_WINDOW_HIGH					490
#define SIS3316_FFT_WINDOW_POSTION_X			395
#define SIS3316_FFT_WINDOW_POSTION_Y			565






//#define MAX_PRETRIGGER_DELAY 2042 // ADC FPGA Version A006 and lower
#define MAX_PRETRIGGER_DELAY 16378 // ADC FPGA Version A007 and higher

//#define MAX_ROOT_PLOT_LENGTH 0x40000 // 262144
//#define MAX_ROOT_PLOT_LENGTH 0x80000 // 524288
//#define MAX_ROOT_PLOT_LENGTH 0x100000 // 1.048.576
//#define MAX_ROOT_PLOT_LENGTH 0x200000 // 2.097.152
#define MAX_ROOT_PLOT_LENGTH 0x100000 //
#define MAX_SAMPLE_LENGTH 0x10000-2 //


#define DefineCanvasBackgroundColor   10
#define DefineChannel_1_Color          2
#define DefineChannel_2_Color          3
#define DefineChannel_3_Color          4
#define DefineChannel_4_Color          6
#define DefineChannel_5_Color          7
#define DefineChannel_6_Color          8
#define DefineChannel_7_Color          9
#define DefineChannel_8_Color         28
#define DefineChannel_9_Color         30
#define DefineChannel_10_Color        40
#define DefineChannel_11_Color        41
#define DefineChannel_12_Color        42
#define DefineChannel_13_Color        43
#define DefineChannel_14_Color        44
#define DefineChannel_15_Color        45
#define DefineChannel_16_Color        46

int SIS3316_WriteBankChannelHeaderToDataFile (FILE *file_data_ptr, unsigned int indentifier, unsigned int bank_loop_no, unsigned int channel_no, unsigned int nof_events, unsigned int event_length, unsigned int maw_length, unsigned int reserved);
int SIS3316_WriteBankChannelEventBufferToDataFile (FILE *file_data_ptr, unsigned int* memory_data_array, unsigned int nof_write_length_lwords);


/*************************************************************************************************************************/
/*************************************************************************************************************************/
/*************************************************************************************************************************/
/*************************************************************************************************************************/
/*************************************************************************************************************************/

#define SIS3316Test_MAX_TABLE_TABS   10
enum ETest1CommandIdentifiers {
   TEST1_FILE_EXIT,
   M_LOAD_CONFIGURATION_DLG,
   M_SAVE_CONFIGURATION_DLG,
   TEST1_HELP_ABOUT 
};

class SIS3316TestDialog : public TGTransientFrame {

private:
	Bool_t         *fBSetup;       // shows if setup is open

   TGMenuBar          *fMenuBar;
   TGPopupMenu        *fMenuFile, *fMenuConfiguration, *fMenuHelp;
   TGLayoutHints      *fMenuBarLayout, *fMenuBarItemLayout, *fMenuBarHelpLayout;

	TGCompositeFrame    *fFrame2   ;
	TGHorizontalFrame   *fFrame1,  *fTGHor_frame1,  *fTGHor_frame2, *fTGHor_tab4a;
	TGHorizontalFrame   *fTGHor_tab3_2_sub[20]  ;
	TGHorizontalFrame   *fTGHor_tab4a_1a_sub[16]  ;
	TGHorizontalFrame   *fTGHor_tab4a_1b_sub[16]  ;
	TGCompositeFrame    *fF1, *fF1A, *fF1B, *fF1C, *fF2, *fF3, *fF4, *fF4A, *fF5, *fF5A , *fF5B , *fF5C, *fF5D , *fF5E   ;
   TGCompositeFrame    *fF_tab1, *fF_tab2, *fF_tab2b, *fF_tab3, *fF_tab3a, *fF_tab4, *fF_tab5, *fF_tab6, *fF_tab7, *fF_tab8;
   TGGroupFrame			*fGrp1;
   TGGroupFrame			*fF_tab1_fGrp1, *fF_tab1_fGrp1A, *fF_tab1_fGrp1B, *fF_tab1_fGrp2, *fF_tab1_fGrp3, *fF_tab1_fGrp4;
   TGGroupFrame			*fF_tab2_fGrp1, *fF_tab2_fGrp2, *fF_tab2_fGrp3, *fF_tab2_fGrp4;
   TGGroupFrame			*fF_tab2b_fGrp1 ;
   TGGroupFrame			*fF_tab3_fGrp1, *fF_tab3_fGrp2, *fF_tab3_fGrp3, *fF_tab3_fGrp4;
   TGGroupFrame			*fF_tab3a_fGrp1, *fF_tab3a_fGrp2 ;
   TGGroupFrame			*fF_tab4_fGrp1, *fF_tab4_fGrp1A, *fF_tab4_fGrp1B, *fF_tab4_fGrp2, *fF_tab4_fGrp3, *fF_tab4_fGrp4;
   TGGroupFrame			*fF_tab5_fGrp1, *fF_tab5_fGrp1A, *fF_tab5_fGrp2  ;
   TGGroupFrame			*fF_tab6_fGrp1, *fF_tab6_fGrp2, *fF_tab6_fGrp3;

 	TGTabElement		*tabel_tab[SIS3316Test_MAX_TABLE_TABS] ;
	unsigned int		sis3316Test1_nof_valid_tabel_tabs ;

   TGHorizontalFrame    *fTGHorizontalFrame;
   TGVerticalFrame		*fTGVerticalFrame;

   TGHorizontalFrame    *fF[16];
   TGVerticalFrame		*fVF[16];
//   TGHorizontalFrame    *fF_ch;
   TGGroupFrame        *fF6, *fF7;
   TGButton            *fQuitButton;
   TGButton            *fStartB, *fStopB, *fClockConfiguration ;
	Pixel_t				fClockConfiguration_background_color; 

   TGButton            *fBtn1, *fBtn2, *fChk1, *fChk2, *fRad1, *fRad2;


	TGTextEntry			*fTextEntryDataFilePath;
	TGTextButton		*fTextButtonDataFilePath;

   TGButton            *fChkFP_BUS_ClockMaster;
//   TGButton            *fChkChannelInputInvert;
   TGButton            *fChkKeyTrigger, *fChkLemoInTiEnable, *fChkExternalTrigger, *fChkInternalTrigger, *fChkIntertnalSumTrigger, *fChkIntertnalPileupTrigger;

   TGButton            *fChkDisplayAutoZoom;
   TGButton            *fDisplayEnableCh_Set, *fDisplayEnableCh_Clr;

   TGButton            *fChkDisplayAdc[16];
   TGButton            *fChkHistoSum;
   TGButton            *fChkHistoZoomMean;
   TGButton            *fChkHistoGaussFit;
   TGButton            *fChkFFT_Db, *fChkFFT_AutoScale, *fChkFFT_Sum, *fChkFFTLogY;


   TGButton            *fInvertChannel_Set, *fInvertChannel_Clr;
   TGButton            *fChkInvertChannel[16];

   TGLabel			   *fLabel_TerminationChannel ;
   TGButton            *fTerminationChannel_Set, *fTerminationChannel_Clr;
   TGButton            *fChkTerminationChannel[16];

   TGLabel			   *fLabel_InputRange0Channel ;
   TGButton            *fInputRange0Channel_Set, *fInputRange0Channel_Clr;
   TGButton            *fChkInputRange0Channel[16];

   TGButton            *fChkTriggerHeSuppressMode;
   TGButton            *fChkTriggerEnableCh[16+4];
   TGButton            *fTriggerEnableCh_Set, *fTriggerEnableCh_Clr;

  TGComboBox          *fCombo_InternalTriggerCfdSelection;


   TGButton            *fChkInput_50Ohm, *fChkInput_5V_Range, *fChkDacInrementTest;

	TGButton            *fChkStopAfterBanks;
	TGNumberEntry       *fNumericEntriesStopAfterBanks;

	TGButton            *fChkWriteDataToFile, *fChkWriteMultipleFiles, *fChkAppendDateTime;
	TGFileInfo			fileInfoConfFile;
	TGFileInfo			fileInfoDataFile;

	TGButton            *fChkNofEvents_ProBank;
	TGNumberEntry       *fNumericEntries_SampleControl_NofEvents_ProBank;
	TGNumberEntry       *fNumericEntries_SampleControl_MaxNofEvents_ProBank;

	TGButton            *fChk_EventHitParameter_DataFormatBit0, *fChk_EventHitParameter_DataFormatBit2, *fChk_EventHitParameter_DataFormatBit3;

	
 
   TGPictureButton     *fPicBut1;
   TGCheckButton       *fCheck1;
 //  TGCheckButton       *fCheckMulti;
//   TGListBox           *fListBox;
   TGComboBox          *fCombo;
   TGTab               *fTab;
   TGNumberEntry       *fNumericEntries_EventHitParameter[8];
   TGLabel              *fLabel[16];
//   TGTextEntry         *fTxt1, *fTxt2;
   TGLayoutHints       *fL1, *fL2, *fL3, *fL4, *fL5, *fL7;
//   TRootEmbeddedCanvas *fEc1, *fEc2;
//   Int_t                fFirstEntry;
//   Int_t                fLastEntry;
   Bool_t               fSIS3316_Test1;
   TGraph               *fGraph_ch[17];
   TLatex              	*fGraph_Text_ch[17];
   TGraph               *fGraph_maw;
   TH1I                	*iHistoAdc[16];
   TGraph               *fGraph_fft[17];
   //TF1               *fGraph_fft[17];
 //  TGListBox            *fListBox_Display_Histos;

   TGComboBox          *fCombo_SampleControl_BankModus;
   TGComboBox          *fCombo_FP_BUS_ClockOutMux;

   TGComboBox          *fCombo_SampleClock_source;
   TGComboBox          *fCombo_SetInternalClockFreq;
   TGComboBox          *fCombo_SetClockMultiplierMode;
   TGComboBox          *fCombo_SetSelectMAW_TestBuffer;


   TGComboBox          *fCombo_Display_MAW;
   TGComboBox          *fCombo_Display_Histos_Ch;
   TGComboBox          *fCombo_Display_Histos_Build;
   TGComboBox          *fCombo_Display_FFT_Ch;
   TGComboBox          *fCombo_Display_FFT_Window;

   TGComboBox          *fCombo_Set_ADC_SPI_Input_Voltage;
   TGLabel				*fLabel_fCombo_Set_ADC_SPI_text[4] ;
 
  TGComboBox          *fCombo_InternalTriggerToVMESelection;
  TGComboBox          *fCombo_InternalHeTriggerToVMESelection;
 

   TCanvas              *fCanvas1;
   TCanvas              *fCanvas2;
   TCanvas              *fCanvas3;
   TCanvas              *fCanvas4;
   TPaveText		*histo_pave_text[16];

   	
	
	TGNumberEntry       *fNumericEntriesHistogramXaxisOffset;
	TGNumberEntry       *fNumericEntriesHistogramXaxisDivider;

   TGNumberEntry       *fNumericEntriesGraph_Yaxis[2];
   TGNumberEntry       *fNumericEntriesAnalogOffset[16];
   TGNumberEntry       *fNumericEntriesTapDelay;

   TGNumberEntry       *fNumericEntriesTriggerPulse_length;
   TGNumberEntry       *fNumericEntriesTriggerGap;
   TGNumberEntry       *fNumericEntriesTriggerPeaking;
   TGNumberEntry       *fNumericEntriesTriggerThreshold;
   TGNumberEntry       *fNumericEntriesHeTriggerThreshold;
   TGNumberEntry       *fNumericEntriesPileup_length;
   TGNumberEntry       *fNumericEntriesRepileup_length;


   TGNumberEntry       *fNumericEntriesEnergyGap;
   TGNumberEntry       *fNumericEntriesEnergyPeaking;
   TGNumberEntry       *fNumericEntriesEnergyTauTable;
   TGNumberEntry       *fNumericEntriesEnergyTauFactor;
   TGNumberEntry       *fNumericEntriesEnergyAdditionalAverage;
   TGNumberEntry       *fNumericEntriesEnergyPickupValueIndex;

	TGNumberEntry       *fNumericEntriesAccumulatorStartIndex[6];
	TGNumberEntry       *fNumericEntriesAccumulatorLength[6];
	TGLabel				*fLabel_AccumulatorStartIndex_text[6] ;
	TGLabel				*fLabel_AccumulatorLength_text[6] ;

   TGNumberEntry       *fNumericEntriesNimOutput[3];
	TGButton           *fValidateNimOutputSelction;

   
    Pixel_t tab_color_not_active  ;
    Pixel_t tab_color_active      ;

   
   
   //   int gl_class_SIS3316_device;
//   unsigned int gl_class_adc_tap_delay;



	void SIS3316_Test1();
	void SIS3316_Test_running_dim_widgets(bool dim_state) ;

	void SIS3316_Test_Write_TerminationGain(void);
	void SIS3316_Test_Write_DacOffset(void);
	void SIS3316_Test_Write_NIM_Output_Selection(void);

	void SIS3316_Test_Write_Sample_Clock_Configuration();

	void LoadConfigurationFile();
	void SaveConfigurationFile();

	sis3316_get_configuration_parameters *params;

	void setGuiParameters(sis3316_get_configuration_parameters *params);
	void setAdcParameters(sis3316_get_configuration_parameters *params);
	void getGuiParameters(sis3316_get_configuration_parameters *params);
	void getAdcParameters(sis3316_get_configuration_parameters *params);

	unsigned int sample_clock_configuration_valid_flag ;
	unsigned int adc_fpga_firmware_version ;
	double  double_clock_configure_fft_frequency ;

	unsigned int invert_parameter_has_changed_flag ;
	unsigned int gain_termination_parameter_has_changed_flag ;
	unsigned int offset_parameter_has_changed_flag ;

	unsigned int nim_output_selction_has_changed_flag ;

protected:
	Bool_t fB_openfCanvas1WindowFlag; // shows if Canvas1 window is open
	Bool_t fB_openfCanvas2WindowFlag; // shows if Canvas2 window is open
	Bool_t fB_openfCanvas3WindowFlag; // shows if Canvas3 window is open
	Bool_t fB_openfCanvas4WindowFlag; // shows if Canvas4 window is open


public:
   SIS3316TestDialog(const TGWindow *p, const TGWindow *main, UInt_t w, UInt_t h, Bool_t *b,
               UInt_t options = kVerticalFrame);
   virtual ~SIS3316TestDialog();

   virtual void CloseWindow();
   virtual Bool_t ProcessMessage(Long_t msg, Long_t parm1, Long_t parm2);
};




/*******************************************************************************************************************************/
/***********************       SIS3316TestDialog                                       *****************************************/
	  
#define SIS3316TestDialog_kCM_BUTTON_IRQ_NO_4			4
#define SIS3316TestDialog_kCM_BUTTON_IRQ_NO_5			5
#define SIS3316TestDialog_kCM_BUTTON_IRQ_NO_6			6

#define SIS3316TestDialog_kCM_BUTTON_IRQ_NO_30			30
#define SIS3316TestDialog_kCM_BUTTON_IRQ_NO_31			31

#define SIS3316TestDialog_kCM_BUTTON_IRQ_NO_42			42

#define SIS3316TestDialog_kCM_BUTTON_IRQ_NO_60			60


#define SIS3316TestDialog_kCM_BUTTON_IRQ_NO_70			70
#define SIS3316TestDialog_kCM_BUTTON_IRQ_NO_71			71

#define SIS3316TestDialog_kCM_BUTTON_IRQ_NO_80			80
#define SIS3316TestDialog_kCM_BUTTON_IRQ_NO_81			81
#define SIS3316TestDialog_kCM_BUTTON_IRQ_NO_82			82
#define SIS3316TestDialog_kCM_BUTTON_IRQ_NO_83			83


#define SIS3316TestDialog_kCM_CHECKBUTTON_IRQ_NO_10		10
#define SIS3316TestDialog_kCM_CHECKBUTTON_IRQ_NO_11		11
#define SIS3316TestDialog_kCM_CHECKBUTTON_IRQ_NO_12		12
#define SIS3316TestDialog_kCM_CHECKBUTTON_IRQ_NO_40		40
#define SIS3316TestDialog_kCM_CHECKBUTTON_IRQ_NO_74		74
#define SIS3316TestDialog_kCM_CHECKBUTTON_IRQ_NO_84		84

#define SIS3316TestDialog_kCM_COMBOBOX_IRQ_NO_30		30   
#define SIS3316TestDialog_kCM_COMBOBOX_IRQ_NO_40		40   
#define SIS3316TestDialog_kCM_COMBOBOX_IRQ_NO_90		90   
	  
#define SIS3316TestDialog_kCM_ENTRY_IRQ_NO_40		    40  
#define SIS3316TestDialog_kCM_ENTRY_IRQ_NO_60		    60  

//const char *const SIS3316TestDialog::entrySampleControl_BankModus[2] = {
const char *const entrySampleControl_BankModus[2] = {
   "Single Event/Hit - Single Bank Mode",
   "Multi  Event/Hit - Double Bank Mode "
};




const char *const entryFP_BUS_ClockOutMux[2] = {
   "Use Internal Programmable Clock Oscillator",
   "Use External NIM Clock (via Clock Multiplier) "
};

const char *const entryClock_source[4] = {
   "Use Internal Programmable Clock Oscillator",
   "Use VXS Sample Clock",
   "Use FP-Bus Sample Clock",
   "Use External NIM Clock (via Clock Multiplier) "
};


const char *const entryClock_freq[16] = {
   "Set Internal Sample Clock to 250.000 MHz",
   "Set Internal Sample Clock to 227.273 MHz",
   "Set Internal Sample Clock to 208,333 MHz",
   "Set Internal Sample Clock to 178,571 MHz",
   "Set Internal Sample Clock to 166.667 MHz",
   "Set Internal Sample Clock to 138.889 MHz",
   "Set Internal Sample Clock to 125.000 MHz",
   "Set Internal Sample Clock to 119.048 MHz",
   "Set Internal Sample Clock to 113.636 MHz",
   "Set Internal Sample Clock to 104.167 MHz",
   "Set Internal Sample Clock to 100.000 MHz",
   "Set Internal Sample Clock to  83.333 MHz",
   "Set Internal Sample Clock to  71.429 MHz",
   "Set Internal Sample Clock to  62.500 MHz",
   "Set Internal Sample Clock to  50.000 MHz",
   "Set Internal Sample Clock to  25.000 MHz"
};

const char *const entryClock_multiplier_modes[7] = {
   "Set Clock Multiplier: Bypass",  //
   "Set Clock Multiplier: 10 MHz to 250 MHz",  // bw=0    n1_hs=5   n1_clk = 4   n2=500  n3=1   range 10,00 to 11,34 -> 250 to 283
   "Set Clock Multiplier: 20 MHz to 250 MHz",  // bw=0/1  n1_hs=5   n1_clk = 4   n2=250  n3=1   range 19,40 to 22,68 -> 242 to 283
   "Set Clock Multiplier: 50 MHz to 250 MHz",  // bw=1/2  n1_hs=11  n1_clk = 1   n2=110  n3=1   range 44,00 to 51,54 -> 220 to 257
   "Set Clock Multiplier: 10 MHz to 125 MHz",  // bw=0    n1_hs=4   n1_clk = 10  n2=500  n3=1   range 10,00 to 11,34 -> 125 to 141
   "Set Clock Multiplier: 20 MHz to 125 MHz",  // bw=0/1  n1_hs=5   n1_clk = 8   n2=250  n3=1   range 19,40 to 22,68 -> 121 to 141
   "Set Clock Multiplier: 50 MHz to 125 MHz"   // bw=1/2  n1_hs=5   n1_clk = 8   n2=100  n3=1   range 48,50 to 56,70 -> 121 to 141
};

const char *const entryClock_SelectMAW_TestBuffer[2] = {
   "Select Trigger MAW",  //
   "Select Energy  MAW"   //
};



const char *const numlabel[8] = {
   "Pre Trigger Delay",
   "Raw Data Sample Start Index",
   "Raw Data Sample Length",
   "MAW Test Buffer Pre Trigger Delay",
   "MAW Test Start Index",
   "MAW Test Buffer Length",
   "Info: Event Length (32-bit words)",
   "Info: Active Trigger Gate Length"
};

const char *const entryInternalTriggerCfdSelection[3] = {
   "Select -CFD function disable-",
   "Select -CFD function enable with Zero crossing-",
   "Select -CFD function enable with 50% crossing-"
};

 
const char *const entryInternalTriggerToVMESelection[3] = {
   "Select -Internal Trigger-              as -Internal Trigger- to VME FPGA",
   "Select -Internal HE-Trigger-       as -Internal Trigger- to VME FPGA",
   "Select -Pileup detection pulse- as -Internal Trigger- to VME FPGA"
};
const char *const entryInternalHeTriggerToVMESelection[2] = {
   "Select -Internal HE-Trigger-        as -Internal HE-Trigger- to VME FPGA",
   "Select -Pileup detection pulse- as -Internal HE-Trigger- to VME FPGA"
};


const Double_t numinit[8] = {
   1, 2, 3, 4, 5, 6,
   7,
   8
};


// graph
const char *const chkDisAdcLabel[16] = {
   "Ch 1",
   "Ch 2",
   "Ch 3",
   "Ch 4",
   "Ch 5",
   "Ch 6",
   "Ch 7",
   "Ch 8",
   "Ch 9",
   "Ch 10",
   "Ch 11",
   "Ch 12",
   "Ch 13",
   "Ch 14",
   "Ch 15",
   "Ch 16"
};



// MAW (Moving Average Window)
const char *const entryMawLabel[17] = {
   "No MAW",
   "Display MAW Ch 1",
   "Display MAW Ch 2",
   "Display MAW Ch 3",
   "Display MAW Ch 4",
   "Display MAW Ch 5",
   "Display MAW Ch 6",
   "Display MAW Ch 7",
   "Display MAW Ch 8",
   "Display MAW Ch 9",
   "Display MAW Ch 10",
   "Display MAW Ch 11",
   "Display MAW Ch 12",
   "Display MAW Ch 13",
   "Display MAW Ch 14",
   "Display MAW Ch 15",
   "Display MAW Ch 16"
};

// graph
const char *const AdcHistogramLabel[16] = {
   "Histogram Ch 1",
   "Histogram Ch 2",
   "Histogram Ch 3",
   "Histogram Ch 4",
   "Histogram Ch 5",
   "Histogram Ch 6",
   "Histogram Ch 7",
   "Histogram Ch 8",
   "Histogram Ch 9",
   "Histogram Ch 10",
   "Histogram Ch 11",
   "Histogram Ch 12",
   "Histogram Ch 13",
   "Histogram Ch 14",
   "Histogram Ch 15",
   "Histogram Ch 16"
};




// histogram build option
const char *const entryHistoDisplayOption[3] = {
   "Display ADC Output Code Histogram",
    "reserved for Display FIR Energy Histogram",
	"reserved"
//   "Read internal FIR Energy Histogram"
};


// histogram channel
const char *const entryHistoLabel[18] = {
   "No Histogramming",
   "Display Histogram Ch 1",
   "Display Histogram Ch 2",
   "Display Histogram Ch 3",
   "Display Histogram Ch 4",
   "Display Histogram Ch 5",
   "Display Histogram Ch 6",
   "Display Histogram Ch 7",
   "Display Histogram Ch 8",
   "Display Histogram Ch 9",
   "Display Histogram Ch 10",
   "Display Histogram Ch 11",
   "Display Histogram Ch 12",
   "Display Histogram Ch 13",
   "Display Histogram Ch 14",
   "Display Histogram Ch 15",
   "Display Histogram Ch 16",
   "Display Histogram Ch 1-16"
};


const char *const entryDisplayFFTLabel[17] = {
   "No FFT",
   "Display FFT Ch 1",
   "Display FFT Ch 2",
   "Display FFT Ch 3",
   "Display FFT Ch 4",
   "Display FFT Ch 5",
   "Display FFT Ch 6",
   "Display FFT Ch 7",
   "Display FFT Ch 8",
   "Display FFT Ch 9",
   "Display FFT Ch 10",
   "Display FFT Ch 11",
   "Display FFT Ch 12",
   "Display FFT Ch 13",
   "Display FFT Ch 14",
   "Display FFT Ch 15",
   "Display FFT Ch 16"
};


const char *const entryDisplayFFTWindowLabel[6] = {
   "Rectangular window (no window)",
   "Hamming window",
   "Hann window",
   "Blackmann window",
   "Blackmann-Harris window",
   "No"
};


const char *const accuStartIndexlabel[6] = {
   "Start Index of Accumulator 1",
   "Start Index of Accumulator 2",
   "Start Index of Accumulator 3",
   "Start Index of Accumulator 4",
   "Start Index of Accumulator 5",
   "Start Index of Accumulator 6"
};

const char *const accuLengthlabel[6] = {
   "Length of Accumulator 1",
   "Length of Accumulator 2",
   "Length of Accumulator 3",
   "Length of Accumulator 4",
   "Length of Accumulator 5",
   "Length of Accumulator 6"
};


const char *const entryADC_SPI_InputVoltage[3] = {
   "ADC chip full scale 1.50V input range",
   "ADC chip full scale 1.75V input range",
   "ADC chip full scale 2.00V input range"
};








// graph
const char *const chkTriggerEnableChLabel[16+4] = {
   "Ch 1",
   "Ch 2",
   "Ch 3",
   "Ch 4",
   "Ch 5",
   "Ch 6",
   "Ch 7",
   "Ch 8",
   "Ch 9",
   "Ch 10",
   "Ch 11",
   "Ch 12",
   "Ch 13",
   "Ch 14",
   "Ch 15",
   "Ch 16",
   "Ch_Sum 1 to 4",
   "Ch_Sum 5 to 8",
   "Ch_Sum 9 to 12",
   "Ch_Sum 13 to 16"
};

const char *const SIS3316_devices_txt[6] = {
   "/dev/SIS3316-0",
   "/dev/SIS3316-1",
   "/dev/SIS3316-2",
   "/dev/SIS3316-3",
   "/dev/SIS3316-4",
   "/dev/SIS3316-5",
};
const char *const chkChLabel[16] = {
   "Ch 1",
   "Ch 2",
   "Ch 3",
   "Ch 4",
   "Ch 5",
   "Ch 6",
   "Ch 7",
   "Ch 8",
   "Ch 9",
   "Ch 10",
   "Ch 11",
   "Ch 12",
   "Ch 13",
   "Ch 14",
   "Ch 15",
   "Ch 16"
};



#endif



