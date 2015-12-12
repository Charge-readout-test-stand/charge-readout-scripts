/***************************************************************************/
/*                                                                         */
/*  Filename: sis3316_class.h                                              */
/*                                                                         */
/*  Funktion:                                                              */
/*                                                                         */
/*  Autor:                TH                                               */
/*  date:                 26.07.2012                                       */
/*  last modification:    24.06.2015                                       */
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
/*  � 2015                                                                 */
/*                                                                         */
/***************************************************************************/

#ifndef _SIS3316_CLASS_
#define _SIS3316_CLASS_

#include "project_system_define.h"		//define LINUX or WIN

//#define LINUX

//#ifndef LINUX
//	#define WIN
//#endif

#include "sis3316.h"
#include "sis3316_class.h"

#ifdef LINUX
	#include "vme_interface_class.h"
	//#include "SisVmeInterface.h"

	#include <stdio.h>
	#include <string.h>
	#include <stdlib.h>
	#include <unistd.h>

	//#define vme_A32D32_read _vme_A32D32_read
	//#define vme_A32D32_write _vme_A32D32_write
	//#define vme_A32DMA_D32FIFO_write _vme_A32DMA_D32FIFO_write
#endif


#ifdef WIN
	#include <Windows.h>

	#include "vme_interface_class.h"

	//#include "stdafx.h"
	#include <iostream>
	#include <cstdio>
	//#include "vme_interface_class.h"

	void usleep(unsigned int uint_usec) ;

	using namespace std;
#endif




#define SIS3316_ADC_FPGA_BOOT_CSR		0x30
#define SIS3316_SPI_FLASH_CSR			0x34
 #define ENABLE_SPI_PROG	0
 #define CHIPSELECT_1		1
 #define CHIPSELECT_2		2
 #define FIFO_NOT_EMPTY		14
 #define FLASH_LOGIC_BUSY	31

#define SIS3316_SPI_FLASH_DATA			0x38
#define SIS3316_FLASH_PROGRAM_PAGESIZE	256
#define SIS3316_FLASH_ERASE_BLOCKSIZE	65536

#define SIS3316_ADC_CLK_OSC_I2C_REG		0x40
 #define I2C_ACK			8
 #define I2C_START			9
 #define I2C_REP_START		10
 #define I2C_STOP			11
 #define I2C_WRITE			12
 #define I2C_READ			13
 #define I2C_BUSY			31

#define OSC_ADR	0x55



#define SI5325_SPI_POLL_COUNTER_MAX							100
#define SI5325_SPI_CALIBRATION_READY_POLL_COUNTER_MAX		1000


class sis3316_adc
{
	vme_interface_class *i;
	unsigned int  baseaddress;
private:
	//SISInterface *i;
	// flash stuff
	//int FlashEnableProg(void);
	//int FlashDisableProg(void);
	int FlashEnableCS(int chip);
	int FlashDisableCS(int chip);
	int FlashWriteEnable(void);
	int FlashWriteDisable(void);
	int FlashProgramPage(int address, char *data, int len);
	int FlashEraseBlock(int address);
	//int FlashGetId(char *id);
	int FlashXfer(char in, char *out);
	

	// i2c stuff
	int I2cStart(int osc);
	int I2cStop(int osc);
	int I2cWriteByte(int osc, unsigned char data, char *ack);
	int I2cReadByte(int osc, unsigned char *data, char ack); // changed 20.11.2013
	int Si570FreezeDCO(int osc);
	int Si570Divider(int osc, unsigned char *data);
	int Si570UnfreezeDCO(int osc);
	int Si570NewFreq(int osc);
	int Si570ReadDivider(int osc, unsigned char *data); // new 20.11.2013

	// onewire
	int owReset(int *presence);
	int owRead(unsigned char *data);
	int owWrite(unsigned char data);
	int owEeReadPage(int page, unsigned char *data);
	int owEeWritePage(int page, unsigned char *data);
	int read_ee(int offset, int len, unsigned char *data);

	//int write_ee(int offset, int len, unsigned char *data);
	int ow_id_ee(unsigned char *data);


	int si5325_clk_muliplier_write(unsigned int addr, unsigned int data) ;
	int si5325_clk_muliplier_read(unsigned int addr, unsigned int *data)  ; 
	int si5325_clk_muliplier_internal_calibration_cmd(void)  ;

public:
	int write_ee(int offset, int len, unsigned char *data);
	int write_ow_dhcp_option(unsigned char *data);

public:
	unsigned char freqSI570_calibrated_value_125MHz[6]; // new 20.11.2013
	unsigned char freqPreset62_5MHz[6];
	unsigned char freqPreset125MHz[6];
	unsigned char freqPreset250MHz[6];

	unsigned int serial_number ;
	unsigned int vme_fpga_version ;
	unsigned int adc_fpga_version ;
	unsigned int adc_125MHz_flag ;

	unsigned int adc_dac_offset_ch_array[16];
	unsigned int adc_gain_termination_ch_array[16];
	unsigned int nim_output_selection_array[3];


public:
	sis3316_adc(vme_interface_class *crate, unsigned int baseaddress);

	int register_read (UINT addr, UINT* data);
	int register_write (UINT addr, UINT data);


	//sis3316_adc(SISInterface *i, int baseaddress);
	//int update_firmware(char *path, int offset, static void (*cb)(int percentage));
	int update_firmware(char *path, int offset, void (*cb)(int percentage));
	int verify_firmware(char *path, int offset, void (*cb)(int percentage));
	int FlashRead(int address, char *data, int len);
	int FlashReadStatus1(char *status);
	int FlashReadStatus2(char *status);
	int FlashEnableProg(void);
	int FlashDisableProg(void);

	int change_frequency_HSdiv_N1div(int osc, unsigned hs_div_val, unsigned n1_div_val); // new 20.11.2013
	int get_frequency(int osc, unsigned char *values); // new 20.11.2013
	int set_frequency(int osc, unsigned char *values);
	int set_external_clock_multiplier(unsigned int bw_sel, unsigned int n1_hs, unsigned int n1_clk1, unsigned int n1_clk2, unsigned int n2, unsigned int n3, unsigned int clkin1_mhz );
	int bypass_external_clock_multiplier(void );
	int get_status_external_clock_multiplier(unsigned int *status );

	int configure_adc_fpga_iob_delays(unsigned int iob_delay_value);
	int reset_adc_fpga_sample_clock_PLL(void);
	int reset_adc_fpga_and_DDR_memory(void);

	int write_channel_header_ID(unsigned int channel_header_id_reg_value);

	int poll_on_adc_dac_offset_busy(void) ;
	int write_all_adc_dac_offsets(void);
	int configure_all_adc_dac_offsets(void );
	int write_all_gain_termination_values(void);
	int write_nim_output_selection_values(void);



	int internal_sum_trigger_generation_setup(unsigned int uint_sum_trigger_threshold_reg, unsigned int uint_sum_he_trigger_threshold_reg, unsigned int uint_sum_trigger_setup_reg, unsigned int adc_fpga_group /* 0 to 3 */ );
	int internal_trigger_generation_setup(unsigned int uint_trigger_threshold_reg, unsigned int uint_he_trigger_threshold_reg, unsigned int uint_trigger_setup_reg, unsigned int channel_no /* 0 to 15 */);

	int FlashGetId(char *id);

	int adc_spi_setup(void );
	int adc_spi_reg_enable_adc_outputs(void );
	int adc_spi_read(unsigned int adc_fpga_group, unsigned int adc_chip, unsigned int spi_addr, unsigned int* spi_data ); // changed 2.12.2014
	int adc_spi_write(unsigned int adc_fpga_group, unsigned int adc_chip, unsigned int spi_addr, unsigned int spi_data ); // changed 2.12.2014

	int read_DMA_Channel_PreviousBankDataBuffer(unsigned int bank2_read_flag, unsigned int channel_no /* 0 to 15 */,
			unsigned int  max_read_nof_words, unsigned int*  dma_got_no_of_words, unsigned int* uint_adc_buffer );

	int read_MBLT64_Channel_PreviousBankDataBuffer(unsigned int bank2_read_flag, unsigned int channel_no /* 0 to 15 */, 
							 unsigned int*  dma_got_no_of_words, unsigned int* uint_adc_buffer);

	int read_Channel_PreviousSampleAddress(unsigned int bank2_read_flag, unsigned int channel_no /* 0 to 15 */, unsigned int*  previous_sample_address );

	int read_Channel_EnergyHistogramBuffer(unsigned int channel_no /* 0 to 15 */, unsigned int lenght, unsigned int* uint_adc_buffer );

	int read_Channel_TofHistogramBuffer(unsigned int channel_no /* 0 to 15 */, int histogram_index, unsigned int lenght, unsigned int* uint_buffer );
	int read_Channel_ShapeHistogramBuffer(unsigned int channel_no /* 0 to 15 */, int histogram_index, unsigned int lenght, unsigned int* uint_buffer );
	int read_Channel_ChargeHistogramBuffer(unsigned int channel_no /* 0 to 15 */, int histogram_index, unsigned int lenght, unsigned int* uint_buffer );

	~sis3316_adc(void);
};





#endif
