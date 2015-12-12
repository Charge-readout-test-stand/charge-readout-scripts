//
/***************************************************************************/
/*                                                                         */
/*  Filename: sis3316_root_gui_main.cpp                                    */
/*                                                                         */
/*  Funktion:                                                              */
/*                                                                         */
/*  Autor:                TH                                               */
/*  date:                 27.03.2015                                       */
/*  last modification:    10.08.2015                                       */
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

#include "project_system_define.h"		//define LINUX or WINDOWS
#include "project_interface_define.h"   //define Interface (sis1100/sis310x, sis3150usb or Ethnernet UDP)

#define FIRST_MODULE_BASE_ADDR					0x30000000  

#define MAIN_WINDOW_WIDTH						410
#define MAIN_WINDOW_HIGH						1050
#define MAIN_WINDOW_POSTION_X					0
#define MAIN_WINDOW_POSTION_Y					10

////#include "rootIncludes.h"
#include "sis3316_root_gui_test1.h"		 
#include "sis3316_root_gui_flash.h"
#include "sis3316.h"
#include "rootIncludes.h"



#ifdef WINDOWS

	#pragma comment (lib, "libGui")
	#pragma comment (lib, "libCore")
	#pragma comment (lib, "libCint")
	#pragma comment (lib, "libRIO")
	#pragma comment (lib, "libNet")
	#pragma comment (lib, "libHist")
	#pragma comment (lib, "libGraf")
	#pragma comment (lib, "libGraf3d")
	#pragma comment (lib, "libGpad")
	#pragma comment (lib, "libTree")
	#pragma comment (lib, "libRint")
	#pragma comment (lib, "libPostscript")
	#pragma comment (lib, "libMatrix")
	#pragma comment (lib, "libPhysics")
	#pragma comment (lib, "libMathCore")
	#pragma comment (lib, "libThread")
//	#pragma comment (lib, "liblistDict")


/*****************************************************************************************************/

	#include <iostream>
	#include <iomanip>
	using namespace std;
	#define WIN32_LEAN_AND_MEAN
	#include <windows.h>
	#include <winsock2.h>

	#include <stdlib.h>
	#include <string.h>
	#include <math.h>
#endif



// choose Interface
#include "vme_interface_class.h"

#ifdef PCI_VME_INTERFACE
	#include "sis1100w_vme_class.h"
	sis1100 *gl_vme_crate ;
#endif

#ifdef USB_VME_INTERFACE
	#include "sis3150w_vme_class.h"
	sis3150 *gl_vme_crate ;
#endif

#ifdef USB3_VME_INTERFACE
	#include "sis3153w_vme_class.h"
	sis3153 *gl_vme_crate ;
#endif


#ifdef ETHERNET_UDP_INTERFACE
	#include "sis3316_ethernet_access_class.h"
	sis3316_eth *gl_vme_crate ;
	char  gl_sis3316_ip_addr_string[32] ;

	#ifdef LINUX
		#include <sys/types.h>
		#include <sys/socket.h>
	#endif

	#ifdef WINDOWS
	#include <winsock2.h>
	#pragma comment(lib, "ws2_32.lib")
	//#pragma comment(lib, "wsock32.lib")
	typedef int socklen_t;

	long WinsockStartup()
	{
	  long rc;

	  WORD wVersionRequested;
	  WSADATA wsaData;
	  wVersionRequested = MAKEWORD(2, 1);

	  rc = WSAStartup( wVersionRequested, &wsaData );
	  return rc;
	}
	#endif

#endif

#ifdef ETHERNET_VME_INTERFACE
	#include "sis3153ETH_vme_class.h"
	sis3153eth *gl_vme_crate;
//	char  gl_sis3153_ip_addr_string[32] = "212.60.16.206";
	char  gl_sis3153_ip_addr_string[32] = "192.168.1.11";

	#ifdef LINUX
		#include <sys/types.h>
		#include <sys/socket.h>
	#endif

	#ifdef WINDOWS
	#include <winsock2.h>
	#pragma comment(lib, "ws2_32.lib")
	//#pragma comment(lib, "wsock32.lib")
	typedef int socklen_t;

/*	long WinsockStartup()
	{
	  long rc;

	  WORD wVersionRequested;
	  WSADATA wsaData;
	  wVersionRequested = MAKEWORD(2, 1);

	  rc = WSAStartup( wVersionRequested, &wsaData );
	  return rc;
	}
	*/
	#endif
#endif


unsigned int gl_module_base_addr = FIRST_MODULE_BASE_ADDR   ;

#include "sis3316_class.h"

sis3316_adc *gl_sis3316_adc1 ;



enum ETestCommandIdentifiers {
   M_FILE_EXIT,
   M_SIS3316TEST1_DLG,
   M_FPGA_PROG_MENUE,
   M_HELP_ABOUT,
};


class TestMainFrame : public TGMainFrame {

private:
   TGCompositeFrame    *main_frameh1;
   TGGroupFrame        *main_frameh1_fGrp[4];

   TGHorizontalFrame    *main_framehsub, *main_framehsub0;
   TGLabel *fLabel_main_frameh1[8] ;
   TGLabel *fLabel_main_frameh2[6] ;

   TGDockableFrame    *fMenuDock;
   TGCompositeFrame   *fStatusFrame;
   TGCanvas           *fCanvasWindow;
   TGTextEntry        *fTestText;
   TGTextBuffer        *fTbmsg;

   TGButton           *fTestButton;
   TGColorSelect      *fColorSel;

   TGMenuBar          *fMenuBar;
   TGPopupMenu        *fMenuFile, *fMenuSIS3316Test, *fMenuFpgaProgram, *fMenuHelp;
   TGLayoutHints      *fMenuBarLayout, *fMenuBarItemLayout, *fMenuBarHelpLayout;

   TGNumberEntry      *fNumericEntriesModuleAddress;
   TGTextEntry       *fTextEntryModuleIpString;

	TGButton           *fValidateIpAddressButton;
	TGButton            *fChk_JumboFrame;
	TGHorizontalFrame   *fTGHorizontalIpSubFrame1, *fTGHorizontalIpSubFrame2;
	TGNumberEntry       *fNumericEntries_MaxNofPacketsPerReadRequest;
	TGLabel             *fLabel_MaxNofPacketsPerReadRequest;

	TGTextBuffer      *fTextBufferModuleIpString;

	sis3316_flash *fFlashWindow;

protected:
	Bool_t fB_openfMenuSIS3316TestWindowFlag; // shows if setup window is open
	Bool_t fB_openProgramMenueWindowFlag; // shows if setup window is open
	
public:
   TestMainFrame(const TGWindow *p, UInt_t w, UInt_t h);
   virtual ~TestMainFrame();

   virtual void CloseWindow();
   virtual Bool_t ProcessMessage(Long_t msg, Long_t parm1, Long_t);
   int ShowModuleInformation();
};

/*************************************************************************************************************************/
/*************************************************************************************************************************/
/*************************************************************************************************************************/

TestMainFrame::TestMainFrame(const TGWindow *p, UInt_t w, UInt_t h)
      : TGMainFrame(p, w, h)
{
	sis3316_adc  *sis3316_adc1 ;
	// Create test main frame. A TGMainFrame is a top level window.
   // use hierarchical cleaning
	this->SetCleanup(kDeepCleanup);
    this->SetWindowName("SIS3316 Test Menu");
	this->SetIconPixmap("sis1_sis3316.png");

	// open menueWindows
	fB_openfMenuSIS3316TestWindowFlag = kFALSE; // Setup
	fB_openProgramMenueWindowFlag = kFALSE; // Setup

   fMenuBarLayout = new TGLayoutHints(kLHintsTop | kLHintsExpandX);
   fMenuBarItemLayout = new TGLayoutHints(kLHintsTop | kLHintsLeft, 0, 10, 0, 0);
   fMenuBarHelpLayout = new TGLayoutHints(kLHintsTop | kLHintsRight);

   fMenuFile = new TGPopupMenu(fClient->GetRoot());
   fMenuFile->AddEntry("E&xit", M_FILE_EXIT);


// add SIS3316
   //fMenuSIS3316Test = new TGPopupMenu(fClient->GetRoot());
   fMenuSIS3316Test = new TGPopupMenu(gClient->GetDefaultRoot());
   fMenuSIS3316Test->AddLabel("SIS3316 Test");
   fMenuSIS3316Test->AddSeparator();
   fMenuSIS3316Test->AddEntry("&Test 1", M_SIS3316TEST1_DLG);
   fMenuSIS3316Test->DisableEntry(M_SIS3316TEST1_DLG);
 
// add FPGA Programming
	fMenuFpgaProgram = new TGPopupMenu(gClient->GetDefaultRoot());
	fMenuFpgaProgram->AddEntry("FPGA Programming Menu", M_FPGA_PROG_MENUE);
	fMenuFpgaProgram->DisableEntry(M_FPGA_PROG_MENUE);


// fMenuHelp = new TGPopupMenu(fClient->GetRoot());
   fMenuHelp = new TGPopupMenu(gClient->GetDefaultRoot());
   //fMenuHelp->AddSeparator();
   fMenuHelp->AddEntry("&About", M_HELP_ABOUT);

   // Menu button messages are handled by the main frame (i.e. "this")
   // ProcessMessage() method.
   fMenuFile->Associate(this);
   fMenuSIS3316Test->Associate(this);
	fMenuFpgaProgram->Associate(this);

   fMenuBar = new TGMenuBar(this);
   //fMenuBar = new TGMenuBar(fMenuDock, 1, 1, kHorizontalFrame);
   fMenuBar->AddPopup("&File", fMenuFile, fMenuBarItemLayout);
   fMenuBar->AddPopup("SIS3316 Test", fMenuSIS3316Test, fMenuBarItemLayout);
   fMenuBar->AddPopup("FPGA Programming", fMenuFpgaProgram, fMenuBarItemLayout);
   fMenuBar->AddPopup("Help", fMenuHelp, fMenuBarHelpLayout);

   //fMenuDock->AddFrame(fMenuBar, fMenuBarLayout);
	this->AddFrame(fMenuBar, new TGLayoutHints(kLHintsTop | kLHintsExpandX));

	main_frameh1 = new TGCompositeFrame(this, kHorizontalFrame);

	//main_frameh1->SetBackgroundColor(0xee0000); //
	this->AddFrame(main_frameh1, new TGLayoutHints(kLHintsExpandX, 5, 5, 5, 5));

   //fL1 = new TGLayoutHints(kLHintsTop | kLHintsLeft ,  20 ,2, 2, 12); //hints, left, right, top, bottom
   //fL5 = new TGLayoutHints(kLHintsTop | kLHintsLeft | kLHintsExpandX,  20, 2, 50, 2); // hints, left, right, top, bottom

	TGIcon *fIcon1341 = new TGIcon(main_frameh1, "sislogo.bmp");
	fIcon1341->SetName("fIcon1341");
	main_frameh1->AddFrame(fIcon1341, new TGLayoutHints(kLHintsLeft | kLHintsTop, 5, 5, 15, 15));


#ifdef ETHERNET_VME_INTERFACE
	main_frameh1_fGrp[4] = new TGGroupFrame(main_frameh1, "SIS3153 IP Address");
	main_frameh1->AddFrame(main_frameh1_fGrp[4], new TGLayoutHints(kLHintsExpandX, 5, 5, 25, 25)); // hints, left, right, top, bottom
	main_framehsub0 = new TGHorizontalFrame(main_frameh1_fGrp[4], 200, 30);
	main_frameh1_fGrp[4]->AddFrame(main_framehsub0, new TGLayoutHints(kLHintsExpandX, 2, 2, 12, 2));

	strcpy(gl_sis3153_ip_addr_string,"212.60.16.200") ; // SIS3153 IP address
//	strcpy(gl_sis3153_ip_addr_string,"192.168.1.11") ; // SIS3153 IP address

	fTextEntryModuleIpString = new TGTextEntry(main_framehsub0, new TGTextBuffer(32), 9);
	fTextEntryModuleIpString->SetMaxLength(32);
	fTextEntryModuleIpString->Resize(200, fTextEntryModuleIpString->GetDefaultHeight());
 	fTextEntryModuleIpString->SetAlignment(kTextLeft);
	fTextEntryModuleIpString->SetText(gl_sis3153_ip_addr_string);
	//fTextEntryModuleIpString->Resize(83,fTextEntryModuleIpString->GetDefaultHeight());
	fTextEntryModuleIpString->Associate(this);
	main_framehsub0->AddFrame(fTextEntryModuleIpString, new TGLayoutHints(kLHintsCenterY | kLHintsLeft, 2, 2, 2, 2));

#endif

	main_frameh1_fGrp[0] = new TGGroupFrame(main_frameh1, "Interface Information");
	main_frameh1->AddFrame(main_frameh1_fGrp[0], new TGLayoutHints(kLHintsExpandX, 5, 5, 25, 25)); // hints, left, right, top, bottom

	fLabel_main_frameh1[0] = new TGLabel(main_frameh1_fGrp[0]," ");
	fLabel_main_frameh1[0]->SetTextJustify(kTextLeft + kTextCenterX );
	fLabel_main_frameh1[0]->SetMargins(0,0,0,0);
	fLabel_main_frameh1[0]->SetWrapLength(-1);
	main_frameh1_fGrp[0]->AddFrame(fLabel_main_frameh1[0], new TGLayoutHints(kLHintsExpandX,2,2,15,2));

	fLabel_main_frameh1[1] = new TGLabel(main_frameh1_fGrp[0]);
	fLabel_main_frameh1[1]->SetTextJustify(kTextLeft + kTextCenterX);
	fLabel_main_frameh1[1]->SetMargins(0,0,0,0);
	fLabel_main_frameh1[1]->SetWrapLength(-1);
	main_frameh1_fGrp[0]->AddFrame(fLabel_main_frameh1[1], new TGLayoutHints(kLHintsExpandX,2,2,2,5));

	fLabel_main_frameh1[2] = new TGLabel(main_frameh1_fGrp[0]);
	fLabel_main_frameh1[2]->SetTextJustify(kTextLeft + kTextCenterX);
	fLabel_main_frameh1[2]->SetMargins(0,0,0,0);
	fLabel_main_frameh1[2]->SetWrapLength(-1);
	main_frameh1_fGrp[0]->AddFrame(fLabel_main_frameh1[2], new TGLayoutHints(kLHintsExpandX,2,2,5,2));

	fLabel_main_frameh1[3] = new TGLabel(main_frameh1_fGrp[0]);
	fLabel_main_frameh1[3]->SetTextJustify(kTextLeft + kTextCenterX);
	fLabel_main_frameh1[3]->SetMargins(0,0,0,0);
	fLabel_main_frameh1[3]->SetWrapLength(-1);
	main_frameh1_fGrp[0]->AddFrame(fLabel_main_frameh1[3], new TGLayoutHints(kLHintsExpandX,2,2,2,2));

	fLabel_main_frameh1[4] = new TGLabel(main_frameh1_fGrp[0]);
	fLabel_main_frameh1[4]->SetTextJustify(kTextLeft + kTextCenterX);
	fLabel_main_frameh1[4]->SetMargins(0,0,0,0);
	fLabel_main_frameh1[4]->SetWrapLength(-1);
	main_frameh1_fGrp[0]->AddFrame(fLabel_main_frameh1[4], new TGLayoutHints(kLHintsExpandX,2,2,2,2));

	fLabel_main_frameh1[5] = new TGLabel(main_frameh1_fGrp[0]);
	fLabel_main_frameh1[5]->SetTextJustify(kTextLeft + kTextCenterX);
	fLabel_main_frameh1[5]->SetMargins(0,0,0,0);
	fLabel_main_frameh1[5]->SetWrapLength(-1);
	main_frameh1_fGrp[0]->AddFrame(fLabel_main_frameh1[5], new TGLayoutHints(kLHintsExpandX,2,2,2,2));

	fLabel_main_frameh1[6] = new TGLabel(main_frameh1_fGrp[0]);
	fLabel_main_frameh1[6]->SetTextJustify(kTextLeft + kTextCenterX);
	fLabel_main_frameh1[6]->SetMargins(0,0,0,0);
	fLabel_main_frameh1[6]->SetWrapLength(-1);
	main_frameh1_fGrp[0]->AddFrame(fLabel_main_frameh1[6], new TGLayoutHints(kLHintsExpandX,2,2,2,2));

	fLabel_main_frameh1[7] = new TGLabel(main_frameh1_fGrp[0]);
	fLabel_main_frameh1[7]->SetTextJustify(kTextLeft + kTextCenterX);
	fLabel_main_frameh1[7]->SetMargins(0,0,0,0);
	fLabel_main_frameh1[7]->SetWrapLength(-1);
	main_frameh1_fGrp[0]->AddFrame(fLabel_main_frameh1[7], new TGLayoutHints(kLHintsExpandX,2,2,2,15)); // hints, left, right, top, bottom


#ifdef ETHERNET_UDP_INTERFACE

	main_frameh1_fGrp[2] = new TGGroupFrame(main_frameh1, "SIS3316 IP Address");
	main_frameh1->AddFrame(main_frameh1_fGrp[2], new TGLayoutHints(kLHintsExpandX, 5, 5, 25, 25)); // hints, left, right, top, bottom
	main_framehsub = new TGHorizontalFrame(main_frameh1_fGrp[2], 200, 30);
	main_frameh1_fGrp[2]->AddFrame(main_framehsub, new TGLayoutHints(kLHintsExpandX, 2, 2, 12, 2));

	//char  gl_sis3316_ip_addr_string[32] ;
	//strcpy(gl_sis3316_ip_addr_string,"212.60.16.200") ; // SIS3316 IP address
	strcpy(gl_sis3316_ip_addr_string,"169.254.202.151") ; // SIS3316 IP address
	//strcpy(gl_sis3316_ip_addr_string,"sis3316-0161") ; // SIS3316 IP address



	//fTextEntryModuleIpString = new TGTextEntry(main_framehsub, 10);
	fTextEntryModuleIpString = new TGTextEntry(main_framehsub, new TGTextBuffer(32), 10);
	fTextEntryModuleIpString->SetMaxLength(32);
	fTextEntryModuleIpString->Resize(150, fTextEntryModuleIpString->GetDefaultHeight());
 	fTextEntryModuleIpString->SetAlignment(kTextLeft);
	fTextEntryModuleIpString->SetText(gl_sis3316_ip_addr_string);
	//fTextEntryModuleIpString->Resize(83,fTextEntryModuleIpString->GetDefaultHeight());
	fTextEntryModuleIpString->Associate(this);
	main_framehsub->AddFrame(fTextEntryModuleIpString, new TGLayoutHints(kLHintsCenterY | kLHintsLeft, 2, 2, 2, 2));
	fTextEntryModuleIpString->ChangeBackground(GetDefaultFrameBackground()); //

	fValidateIpAddressButton = new TGTextButton(main_framehsub, "  Validate IP address  ", 10);
	fValidateIpAddressButton->ChangeBackground(GetDefaultFrameBackground()); //  
	fValidateIpAddressButton->Associate(this);
	main_framehsub->AddFrame(fValidateIpAddressButton, new TGLayoutHints(kLHintsCenterY | kLHintsLeft, 12, 2, 2, 2));

	gl_module_base_addr =  0x0;
 
#else

	main_frameh1_fGrp[2] = new TGGroupFrame(main_frameh1, "SIS3316 VME Base Address");
	main_frameh1->AddFrame(main_frameh1_fGrp[2], new TGLayoutHints(kLHintsExpandX, 5, 5, 25, 25)); // hints, left, right, top, bottom
	main_framehsub = new TGHorizontalFrame(main_frameh1_fGrp[2], 200, 30);
	main_frameh1_fGrp[2]->AddFrame(main_framehsub, new TGLayoutHints(kLHintsExpandX, 2, 2, 12, 2));
	//fNumericEntriesModuleAddress = new TGNumberEntry(main_framehsub, 0x30000000 /* value */, 18 /* width */, 10 /* irq */ , (TGNumberFormat::kNESHex) ) ; //kNESHex
	fNumericEntriesModuleAddress = new TGNumberEntry(main_framehsub, gl_module_base_addr /* value */, 18 /* width */, 10 /* irq */ , (TGNumberFormat::kNESHex) ) ; //kNESHex
	fNumericEntriesModuleAddress->Associate(this);
	main_framehsub->AddFrame(fNumericEntriesModuleAddress, new TGLayoutHints(kLHintsCenterY | kLHintsLeft, 2, 2, 2, 2));

#endif
 


	main_frameh1_fGrp[1] = new TGGroupFrame(main_frameh1, "SIS3316 Information");
	main_frameh1->AddFrame(main_frameh1_fGrp[1], new TGLayoutHints(kLHintsExpandX, 5, 5, 25, 25)); // hints, left, right, top, bottom

	fLabel_main_frameh2[0] = new TGLabel(main_frameh1_fGrp[1]," ");
	fLabel_main_frameh2[0]->SetTextJustify(kTextLeft + kTextCenterX );
	fLabel_main_frameh2[0]->SetMargins(0,0,0,0);
	fLabel_main_frameh2[0]->SetWrapLength(-1);
	main_frameh1_fGrp[1]->AddFrame(fLabel_main_frameh2[0], new TGLayoutHints(kLHintsExpandX,2,2,15,2));

	fLabel_main_frameh2[1] = new TGLabel(main_frameh1_fGrp[1]);
	fLabel_main_frameh2[1]->SetTextJustify(kTextLeft + kTextCenterX);
	fLabel_main_frameh2[1]->SetMargins(0,0,0,0);
	fLabel_main_frameh2[1]->SetWrapLength(-1);
	main_frameh1_fGrp[1]->AddFrame(fLabel_main_frameh2[1], new TGLayoutHints(kLHintsExpandX,2,2,2,2));

	fLabel_main_frameh2[2] = new TGLabel(main_frameh1_fGrp[1]);
	fLabel_main_frameh2[2]->SetTextJustify(kTextLeft + kTextCenterX);
	fLabel_main_frameh2[2]->SetMargins(0,0,0,0);
	fLabel_main_frameh2[2]->SetWrapLength(-1);
	main_frameh1_fGrp[1]->AddFrame(fLabel_main_frameh2[2], new TGLayoutHints(kLHintsExpandX,2,2,2,2));

	fLabel_main_frameh2[3] = new TGLabel(main_frameh1_fGrp[1]);
	fLabel_main_frameh2[3]->SetTextJustify(kTextLeft + kTextCenterX);
	fLabel_main_frameh2[3]->SetMargins(0,0,0,0);
	fLabel_main_frameh2[3]->SetWrapLength(-1);
	main_frameh1_fGrp[1]->AddFrame(fLabel_main_frameh2[3], new TGLayoutHints(kLHintsExpandX,2,2,2,2));

	fLabel_main_frameh2[4] = new TGLabel(main_frameh1_fGrp[1]);
	fLabel_main_frameh2[4]->SetTextJustify(kTextLeft + kTextCenterX);
	fLabel_main_frameh2[4]->SetMargins(0,0,0,0);
	fLabel_main_frameh2[4]->SetWrapLength(-1);
	main_frameh1_fGrp[1]->AddFrame(fLabel_main_frameh2[4], new TGLayoutHints(kLHintsExpandX,2,2,2,15));

	fLabel_main_frameh2[5] = new TGLabel(main_frameh1_fGrp[1]);
	fLabel_main_frameh2[5]->SetTextJustify(kTextLeft + kTextCenterX);
	fLabel_main_frameh2[5]->SetMargins(0,0,0,0);
	fLabel_main_frameh2[5]->SetWrapLength(-1);
	main_frameh1_fGrp[1]->AddFrame(fLabel_main_frameh2[5], new TGLayoutHints(kLHintsExpandX,2,2,2,15));


#ifdef not_used
   // Create status frame containing a button and a text entry widget
   fStatusFrame = new TGCompositeFrame(this, 160, 220, kHorizontalFrame | kSunkenFrame);

   fTestText = new TGTextEntry(fStatusFrame, fTbmsg = new TGTextBuffer(200));
   //fTestText = new TGTextEntry(fStatusFrame, new TGTextBuffer(200));
//    fTestText->SetToolTipText("This is a text entry widget");
   fTestText->Resize(200, fTestText->GetDefaultHeight());
   fStatusFrame->AddFrame(fTestText, new TGLayoutHints(kLHintsTop | kLHintsLeft, 10, 2, 2, 2));
   AddFrame(fStatusFrame, new TGLayoutHints(kLHintsBottom | kLHintsExpandX,  5, 5, 5, 5));

   fTbmsg->Clear();
   fTbmsg->AddText(0, "message box");
#endif
/******************************************************************************************************************************/
/* VME Master Create, Open and Setup                                                                                          */
/******************************************************************************************************************************/


#ifdef PCI_VME_INTERFACE
	// create SIS1100/SIS310x vme interface device
	sis1100 *vme_crate = new sis1100(0);
#endif

#ifdef USB_VME_INTERFACE
USHORT idVendor;
USHORT idProduct;
USHORT idSerNo;
USHORT idFirmwareVersion;
USHORT idDriverVersion;
	// create SIS3150USB vme interface device
	sis3150 *vme_crate = new sis3150(0);
#endif

#ifdef USB3_VME_INTERFACE
USHORT idVendor;
USHORT idProduct;
USHORT idSerNo;
USHORT idDriverVersion;
USHORT idFxFirmwareVersion;
USHORT idFpgaFirmwareVersion;
	// create SIS3153USB vme interface device
	sis3153 *vme_crate = new sis3153(0);
#endif



CHAR char_messages[128];
UINT nof_found_devices ;
unsigned int return_code ;

char s[64];

#ifdef ETHERNET_UDP_INTERFACE

	char  pc_ip_addr_string[32] ;
	char  sis3316_ip_addr_string[32] ;
	strcpy(sis3316_ip_addr_string, gl_sis3316_ip_addr_string) ; // SIS3316 IP address
	//strcpy(sis3316_ip_addr_string,"212.60.16.200") ; // SIS3316 IP address
	//int return_code ;
	#ifdef WINDOWS
    //return_code = WSAStartup();
    return_code = WinsockStartup();
	#endif
	sis3316_eth *vme_crate = new sis3316_eth;
	// increase read_buffer size
	// SUSE needs following command as su: >sysctl -w net.core.rmem_max=33554432
	int	sockbufsize = 335544432 ; // 0x2000000
	return_code = vme_crate->set_UdpSocketOptionBufSize(sockbufsize) ;

	//strcpy(pc_ip_addr_string,"212.60.16.49") ; // Window example: secocnd Lan interface IP address is 212.60.16.49
	strcpy(pc_ip_addr_string,"") ; // empty if default Lan interface (Window: use IP address to bind in case of 2. 3. 4. .. LAN Interface)
	return_code = vme_crate->set_UdpSocketBindMyOwnPort( pc_ip_addr_string);

	vme_crate->set_UdpSocketSIS3316_IpAddress( sis3316_ip_addr_string);
	vme_crate->udp_reset_cmd();
#endif

#ifdef ETHERNET_VME_INTERFACE
	sis3153eth *vme_crate;
	sis3153eth(&vme_crate, gl_sis3153_ip_addr_string);
#endif 
// open Vme Interface device
	return_code = vme_crate->vmeopen ();  // open Vme interface
	vme_crate->get_vmeopen_messages (char_messages, &nof_found_devices);  // open Vme interface

	fLabel_main_frameh1[0]->SetText(char_messages);
	sprintf(s,"-- found %d vme interface device(s)",nof_found_devices);
	fLabel_main_frameh1[1]->SetText(s);


	//printf("\n%s    (found %d vme interface device[s])\n\n",char_messages, nof_found_devices);


/******************************************************************************************/
// additional Vme interface device informations
#ifdef USB_VME_INTERFACE
	vme_crate->get_device_informations (&idVendor, &idProduct, &idSerNo, &idFirmwareVersion, &idDriverVersion);  //
	//printf("idVendor:           %04X\n",idVendor);
	//printf("idProduct:          %04X\n",idProduct);
	//printf("idSerNo:            %d\n",idSerNo);
	//printf("idFirmwareVersion:  %04X\n",idFirmwareVersion);
	//printf("idDriverVersion:    %04X\n",idDriverVersion);
	//printf("\n\n");

	sprintf(s,"idVendor:           %04X",idVendor);
	fLabel_main_frameh1[2]->SetText(s);
	sprintf(s,"idProduct:          %04X",idProduct);
	fLabel_main_frameh1[3]->SetText(s);
	sprintf(s,"idSerNo:            %d",idSerNo);
	fLabel_main_frameh1[4]->SetText(s);
	sprintf(s,"idFirmwareVersion:  %04X",idFirmwareVersion);
	fLabel_main_frameh1[5]->SetText(s);
	//sprintf((s,"idDriverVersion:    %04X",idDriverVersion);
	//fLabel_main_frameh1[6]->SetText(s);


#endif

#ifdef USB3_VME_INTERFACE
	vme_crate->get_device_informations (&idVendor, &idProduct, &idSerNo, &idDriverVersion, &idFxFirmwareVersion, &idFpgaFirmwareVersion);  //

	sprintf(s,"idVendor:               0x%04X",idVendor);
	fLabel_main_frameh1[2]->SetText(s);
	sprintf(s,"idProduct:              0x%04X",idProduct);
	fLabel_main_frameh1[3]->SetText(s);
	sprintf(s,"idSerNo:                %d",idSerNo);
	fLabel_main_frameh1[4]->SetText(s);
	sprintf(s,"idDriverVersion:        0x%04X",idDriverVersion);
	fLabel_main_frameh1[5]->SetText(s);
	sprintf(s,"idFxFirmwareVersion:    0x%04X",idFxFirmwareVersion);
	fLabel_main_frameh1[6]->SetText(s);
	sprintf(s,"idFpgaFirmwareVersion:  0x%04X",idFpgaFirmwareVersion);
	fLabel_main_frameh1[7]->SetText(s);

#endif



/******************************************************************************************/

	gl_vme_crate = vme_crate ;
	return_code = this->ShowModuleInformation();

	if (return_code == 0) {

		// kill request and grant from vme interface
		gl_vme_crate->vme_A32D32_write(gl_module_base_addr + SIS3316_INTERFACE_ACCESS_ARBITRATION_CONTROL, 0x80000000);
		// arbitrate
		gl_vme_crate->vme_A32D32_write(gl_module_base_addr + SIS3316_INTERFACE_ACCESS_ARBITRATION_CONTROL, 1);

		sis3316_adc1 = new sis3316_adc( gl_vme_crate, gl_module_base_addr);
		gl_sis3316_adc1 = sis3316_adc1 ;
		if (gl_sis3316_adc1->adc_125MHz_flag == 1) {
			sprintf(s,"SIS3316-125MHz-16bit");
		}
		else {
			sprintf(s,"SIS3316-250MHz-14bit");
		}
		fLabel_main_frameh2[5]->SetText(s);
		fMenuSIS3316Test->EnableEntry(M_SIS3316TEST1_DLG);
		fMenuFpgaProgram->EnableEntry(M_FPGA_PROG_MENUE);

	}
	else {
		sis3316_adc1 = NULL  ;
		gl_sis3316_adc1 = sis3316_adc1 ;
		fMenuSIS3316Test->DisableEntry(M_SIS3316TEST1_DLG);
		fMenuFpgaProgram->DisableEntry(M_FPGA_PROG_MENUE);
#ifdef RUN_WITHOUT_HARDWARE
		fMenuSIS3316Test->EnableEntry(M_SIS3316TEST1_DLG);
#endif
	}


/******************************************************************************************/

	this->SetWindowName("SIS3316 Test (10-08-2015)");
	this->SetWMPosition(MAIN_WINDOW_POSTION_X, MAIN_WINDOW_POSTION_Y);
	this->MapSubwindows();
	this->Resize(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HIGH);   // resize to default size
	this-> MapWindow();

}

TestMainFrame::~TestMainFrame()
{
   // Delete all created widgets.
   delete fMenuFile;
   delete fMenuSIS3316Test;
   delete fMenuHelp;
   delete gl_vme_crate;
}

void TestMainFrame::CloseWindow()
{
   // Got close message for this MainFrame. Terminate the application
   // or returns from the TApplication event loop (depending on the
   // argument specified in TApplication::Run()).

   gApplication->Terminate(0);
}

/*******************************************************************************************************************************/

int TestMainFrame::ShowModuleInformation()
{
unsigned int return_code, data ;
float modTemp;
char s[64];

	return_code = gl_vme_crate->vme_A32D32_read ( gl_module_base_addr + SIS3316_MODID, &data);
	//printf("vme_A32D32_read: data = 0x%08x     return_code = 0x%08x\n", data, return_code);

	if (return_code == 0) {
		if ((data &0xffff0000) == 0x33160000) {
			sprintf(s,"VME base address = 0x%08x",gl_module_base_addr);
			fLabel_main_frameh2[0]->SetText(s);
			fLabel_main_frameh2[0]->SetBackgroundColor(0x99FF99); // light green
			sprintf(s,"VME FPGA firmware version  = 0x%08x", data);
			fLabel_main_frameh2[1]->SetText(s);

			// kill request and grant from vme interface
			gl_vme_crate->vme_A32D32_write(gl_module_base_addr + SIS3316_INTERFACE_ACCESS_ARBITRATION_CONTROL, 0x80000000);
			// arbitrate
			gl_vme_crate->vme_A32D32_write(gl_module_base_addr + SIS3316_INTERFACE_ACCESS_ARBITRATION_CONTROL, 1);


			gl_vme_crate->vme_A32D32_read ( gl_module_base_addr + SIS3316_ADC_CH1_4_FIRMWARE_REG, &data);
			sprintf(s,"ADC FPGA firmware version = 0x%08x", data);
			fLabel_main_frameh2[2]->SetText(s);

			gl_vme_crate->vme_A32D32_read ( gl_module_base_addr + SIS3316_INTERNAL_TEMPERATURE_REG, &data);
			modTemp = (float)(data & 0x3FF);
			modTemp /= 4;
 			sprintf(s,"Temperature   = %.1f C", modTemp);
			fLabel_main_frameh2[3]->SetText(s);

			gl_vme_crate->vme_A32D32_read ( gl_module_base_addr + SIS3316_SERIAL_NUMBER_REG, &data);
			sprintf(s,"Serial Number = %d", data & 0xffff);
			fLabel_main_frameh2[4]->SetText(s);

		}
		else {
			sprintf(s,"No SIS3316");
			fLabel_main_frameh2[0]->SetText(s);
			fLabel_main_frameh2[0]->SetBackgroundColor(0xFF9999); // light red
			sprintf(s,"address = 0x%08x",gl_module_base_addr);
			fLabel_main_frameh2[1]->SetText(s);
			sprintf(s,"version register = 0x%08x", data);
			fLabel_main_frameh2[2]->SetText(s);
			sprintf(s," ");
			fLabel_main_frameh2[3]->SetText(s);
			fLabel_main_frameh2[4]->SetText(s);
 			fLabel_main_frameh2[5]->SetText(s);
 			return_code = 0x900 ;
		}

	}
	else {
		sprintf(s,"No SIS3316");
		fLabel_main_frameh2[0]->SetText(s);
		fLabel_main_frameh2[0]->SetBackgroundColor(0xFF9999); // light red
		sprintf(s,"address = 0x%08x",gl_module_base_addr);
		fLabel_main_frameh2[1]->SetText(s);
		sprintf(s,"return_code = 0x%08x", return_code);
		fLabel_main_frameh2[2]->SetText(s);
		sprintf(s," ");
		fLabel_main_frameh2[3]->SetText(s);
		fLabel_main_frameh2[4]->SetText(s);
		fLabel_main_frameh2[5]->SetText(s);
	}
	return return_code ;
}

/*******************************************************************************************************************************/

Bool_t TestMainFrame::ProcessMessage(Long_t msg, Long_t parm1, Long_t)
{
   // Handle messages send to the TestMainFrame object. E.g. all menu button
   // messages.
	CHAR char_messages[128];
	UINT nof_found_devices ;	
	int return_code;
	char s[64];
	TString tstring_temp = "                                 ";
	sis3316_adc  *sis3316_adc1 ;

   switch (GET_MSG(msg)) {
       //printf("switch (GET_MSG(msg) %d\n", GET_MSG(msg));


      case kC_COMMAND:
         //printf("kC_COMMAND\n");
         switch (GET_SUBMSG(msg)) {

            case kCM_MENUSELECT:
               //printf("kCM_MENUSELECT id=%ld\n", parm1);
               break;

            case kCM_MENU:
               //printf("kCM_MENU id=%ld\n", parm1);
               switch (parm1) {

                  case M_FILE_EXIT:
                     CloseWindow();   // this also terminates theApp
                     break;

				  case M_SIS3316TEST1_DLG:
						if(fB_openfMenuSIS3316TestWindowFlag == kFALSE){
							 //printf("M_SIS3316TEST1_DLG\n");
							new SIS3316TestDialog(fClient->GetRoot(), this, 800, 800, &fB_openfMenuSIS3316TestWindowFlag);
							fB_openfMenuSIS3316TestWindowFlag = kTRUE;
						}
						break;

				  case M_FPGA_PROG_MENUE:
						 //printf("M_FPGA_PROG_MENUE\n");
						if(fB_openProgramMenueWindowFlag == kFALSE){
							fB_openProgramMenueWindowFlag = kTRUE;
							fFlashWindow = new sis3316_flash(gClient->GetRoot(), 360, 700, &fB_openProgramMenueWindowFlag);
						}
						else{
							fFlashWindow->RequestFocus();
						}
						break;
						

                  default:
                     break;
               } // kCM_MENU switch (parm1)
               break;

	
/********************************************/
		#ifdef ETHERNET_UDP_INTERFACE
			case kCM_BUTTON:
				switch(parm1) {
					case 10:

						fValidateIpAddressButton->ChangeBackground(GetDefaultFrameBackground()); // 
						fTextEntryModuleIpString->ChangeBackground(GetDefaultFrameBackground());  
						tstring_temp = fTextEntryModuleIpString->GetText();
						strcpy(gl_sis3316_ip_addr_string,tstring_temp) ; // SIS3316 IP address

						return_code = gl_vme_crate->set_UdpSocketSIS3316_IpAddress( gl_sis3316_ip_addr_string);
						gl_vme_crate->udp_reset_cmd();
						gl_module_base_addr = 0x0 ;

						// Set  Receive Timeout
						//gl_vme_crate->recv_timeout_sec  = 0 ;
						//gl_vme_crate->recv_timeout_usec = 10000 ; // default 10ms
						//gl_vme_crate->set_UdpSocketOptionTimeout() ;

						fMenuSIS3316Test->DisableEntry(M_SIS3316TEST1_DLG);
						fMenuFpgaProgram->DisableEntry(M_FPGA_PROG_MENUE);
	
						return_code = this->ShowModuleInformation();
						if (return_code == 0) {
							// kill request and grant from vme interface
							gl_vme_crate->vme_A32D32_write(gl_module_base_addr + SIS3316_INTERFACE_ACCESS_ARBITRATION_CONTROL, 0x80000000);
							// arbitrate
							gl_vme_crate->vme_A32D32_write(gl_module_base_addr + SIS3316_INTERFACE_ACCESS_ARBITRATION_CONTROL, 1);
							if (gl_sis3316_adc1 == NULL) {
								delete gl_sis3316_adc1;
							}
							sis3316_adc1 = new sis3316_adc( gl_vme_crate, gl_module_base_addr);
							gl_sis3316_adc1 = sis3316_adc1 ;
							if (gl_sis3316_adc1->adc_125MHz_flag == 1) {
								sprintf(s,"SIS3316-125MHz-16bit");
							}
							else {
								sprintf(s,"SIS3316-250MHz-14bit");
							}
							fLabel_main_frameh2[5]->SetText(s);
							fMenuSIS3316Test->EnableEntry(M_SIS3316TEST1_DLG);
							fMenuFpgaProgram->EnableEntry(M_FPGA_PROG_MENUE);

						};
						// Set  Receive Timeout
						//gl_vme_crate->recv_timeout_sec  = 0 ;
						//gl_vme_crate->recv_timeout_usec = 50000 ; // default 50ms
						//printf("recv_timeout_sec = %d   recv_timeout_usec = %d\n",this->recv_timeout_sec, this->recv_timeout_usec);
						//gl_vme_crate->set_UdpSocketOptionTimeout() ;

						break;


					default:
						break;

				} //switch(parm1)
			break; //case kCM_BUTTON
		#endif
 /********************************************/

            default:
               break;
         } // kC_COMMAND switch (GET_SUBMSG(msg))
         break;

	  case kC_TEXTENTRY:
			//printf("kC_TEXTENTRY item %ld activated\n", parm1);
              switch (parm1) {
				 case 9:
					#ifdef ETHERNET_VME_INTERFACE
						tstring_temp = fTextEntryModuleIpString->GetText();
						strcpy(gl_sis3153_ip_addr_string,tstring_temp) ; // SIS3316 IP address

						sis3153eth(&gl_vme_crate, gl_sis3153_ip_addr_string);

						// open Vme Interface device
						return_code = gl_vme_crate->vmeopen ();  // open Vme interface
						gl_vme_crate->get_vmeopen_messages (char_messages, &nof_found_devices);  // open Vme interface

						fLabel_main_frameh1[0]->SetText(char_messages);
						sprintf(s,"-- found %d vme interface device(s)",nof_found_devices);
						fLabel_main_frameh1[1]->SetText(s);

						fMenuSIS3316Test->DisableEntry(M_SIS3316TEST1_DLG);

						return_code = this->ShowModuleInformation();
						if (return_code == 0) {
							// kill request and grant from vme interface
							gl_vme_crate->vme_A32D32_write(gl_module_base_addr + SIS3316_INTERFACE_ACCESS_ARBITRATION_CONTROL, 0x80000000);
							// arbitrate
							gl_vme_crate->vme_A32D32_write(gl_module_base_addr + SIS3316_INTERFACE_ACCESS_ARBITRATION_CONTROL, 1);
							if (gl_sis3316_adc1 == NULL) {
								delete gl_sis3316_adc1;
							}
							sis3316_adc1 = new sis3316_adc( gl_vme_crate, gl_module_base_addr);
							gl_sis3316_adc1 = sis3316_adc1 ;
							if (gl_sis3316_adc1->adc_125MHz_flag == 1) {
								sprintf(s,"SIS3316-125MHz-16bit");
							}
							else {
								sprintf(s,"SIS3316-250MHz-14bit");
							}
							fLabel_main_frameh2[5]->SetText(s);
							fMenuSIS3316Test->EnableEntry(M_SIS3316TEST1_DLG);
							fMenuFpgaProgram->EnableEntry(M_FPGA_PROG_MENUE);

						};

					#endif


					 break;



				 case 10:
					#ifdef ETHERNET_UDP_INTERFACE
						fTextEntryModuleIpString->ChangeBackground(0xffff00); //light yellow
						fValidateIpAddressButton->ChangeBackground(0x99FF99); // light green
					#else
						gl_module_base_addr =  fNumericEntriesModuleAddress->GetIntNumber() ;
						fMenuSIS3316Test->DisableEntry(M_SIS3316TEST1_DLG);

						return_code = this->ShowModuleInformation();
						if (return_code == 0) {
							// kill request and grant from vme interface
							gl_vme_crate->vme_A32D32_write(gl_module_base_addr + SIS3316_INTERFACE_ACCESS_ARBITRATION_CONTROL, 0x80000000);
							// arbitrate
							gl_vme_crate->vme_A32D32_write(gl_module_base_addr + SIS3316_INTERFACE_ACCESS_ARBITRATION_CONTROL, 1);
							if (gl_sis3316_adc1 == NULL) {
								delete gl_sis3316_adc1;
							}
							sis3316_adc1 = new sis3316_adc( gl_vme_crate, gl_module_base_addr);
							gl_sis3316_adc1 = sis3316_adc1 ;
							if (gl_sis3316_adc1->adc_125MHz_flag == 1) {
								sprintf(s,"SIS3316-125MHz-16bit");
							}
							else {
								sprintf(s,"SIS3316-250MHz-14bit");
							}
							fLabel_main_frameh2[5]->SetText(s);
							fMenuSIS3316Test->EnableEntry(M_SIS3316TEST1_DLG);
							fMenuFpgaProgram->EnableEntry(M_FPGA_PROG_MENUE);

						};
					#ifdef ETHERNET_UDP_INTERFACE
						// Set  Receive Timeout
						gl_vme_crate->recv_timeout_sec  = 0 ;
						gl_vme_crate->recv_timeout_usec = 100000 ; // default 100ms
						//printf("recv_timeout_sec = %d   recv_timeout_usec = %d\n",this->recv_timeout_sec, this->recv_timeout_usec);
						gl_vme_crate->set_UdpSocketOptionTimeout() ;
					#endif
					#endif

						break;


				 default:
                     break;
               } // kC_TEXTENTRY switch (parm1)
         break;

 

	  default:
         break;
   } // switch (GET_MSG(msg)
   return kTRUE;
}

#ifdef not_used
	case kC_TEXTENTRY:
      printf("kC_TEXTENTRY item %ld activated\n", parm1);
	  switch (GET_SUBMSG(msg)) {
	      case kTE_TEXTCHANGED:
				switch(parm1) {
					  case 20:
						printf("\n pressed 20\n");
						break;
					  case 21:
						printf("\n pressed 21\n");
						break;
				}
			break;
	  }
	  break;
#endif











//---- Main program ------------------------------------------------------------

int main(int argc, char **argv)
{
   TApplication theApp("App", &argc, argv);
//#ifdef raus // warum
   if (gROOT->IsBatch()) {
      fprintf(stderr, "%s: cannot run in batch mode\n", argv[0]);
      return 1;
   }
//#endif
   //TestMainFrame mainWindow(gClient->GetRoot(), 400, 220);
	new TestMainFrame(gClient->GetRoot(), 400, 220);

   theApp.Run();

   return 0;
}

