/***************************************************************************/
/*                                                                         */
/*  Filename: sis3316_class.cpp                                            */
/*                                                                         */
/*  Funktion:                                                              */
/*                                                                         */
/*  Autor:                TH                                               */
/*  date:                 26.07.2012                                       */
/*  last modification:    25.06.2015                                       */
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
#include "sis3316_class.h"


#ifdef LINUX
	//#include "SisVmeInterface.h"
	#include "vme_interface_class.h"
	//#include "sis3316_adc.h"
	#include <stdio.h>
	#include <string.h>
	#include <stdlib.h>
	#include <unistd.h>

	//#define vme_A32D32_read _vme_A32D32_read
	//#define vme_A32D32_write _vme_A32D32_write
	//#define vme_A32DMA_D32FIFO_write _vme_A32DMA_D32FIFO_write
	//#define vme_A32MBLT64FIFO_read _vme_A32MBLT64FIFO_read

#endif

#ifdef WIN

	//#include "stdafx.h"
	#include <iostream>
	#include <cstdio>
	#include "vme_interface_class.h"

	void usleep(unsigned int uint_usec) ;

	using namespace std;
#endif

/**************************************************************************************/



sis3316_adc::sis3316_adc(vme_interface_class *crate, unsigned int baseaddress)
{
	int return_code ;
//	unsigned int data ;
	unsigned int i_ch ;
	if(crate){
		this->i = crate;
	}
	this->baseaddress = baseaddress;

	this->get_frequency(0,freqSI570_calibrated_value_125MHz );

	// frequency presets setup
	freqPreset62_5MHz[0] = 0x23;
	freqPreset62_5MHz[1] = (0x3 << 6) + (freqSI570_calibrated_value_125MHz[1] & 0x3F);
	freqPreset62_5MHz[2] = freqSI570_calibrated_value_125MHz[2];
	freqPreset62_5MHz[3] = freqSI570_calibrated_value_125MHz[3];
	freqPreset62_5MHz[4] = freqSI570_calibrated_value_125MHz[4];
	freqPreset62_5MHz[5] = freqSI570_calibrated_value_125MHz[5];

	freqPreset125MHz[0] = 0x21;
	freqPreset125MHz[1] = (0x3 << 6) + (freqSI570_calibrated_value_125MHz[1] & 0x3F);
	freqPreset125MHz[2] = freqSI570_calibrated_value_125MHz[2];
	freqPreset125MHz[3] = freqSI570_calibrated_value_125MHz[3];
	freqPreset125MHz[4] = freqSI570_calibrated_value_125MHz[4];
	freqPreset125MHz[5] = freqSI570_calibrated_value_125MHz[5];

	freqPreset250MHz[0] = 0x20;
	freqPreset250MHz[1] = (0x3 << 6) + (freqSI570_calibrated_value_125MHz[1] & 0x3F);
	freqPreset250MHz[2] = freqSI570_calibrated_value_125MHz[2];
	freqPreset250MHz[3] = freqSI570_calibrated_value_125MHz[3];
	freqPreset250MHz[4] = freqSI570_calibrated_value_125MHz[4];
	freqPreset250MHz[5] = freqSI570_calibrated_value_125MHz[5];


	this->adc_125MHz_flag = 0;

	// ADC chip setup via SPI
	return_code=this->adc_spi_setup() ;
	if (return_code != 0) {
		printf("Error adc_spi_setup: return_code = 0x%08x \n", return_code);
	}
	//printf("adc_spi_setup: adc_125MHz_flag = %d \n", this->adc_125MHz_flag);


	// write Header ID registers
	return_code=this->write_channel_header_ID( this->baseaddress & 0xff000000) ;
	if (return_code != 0) {
		printf("Error write_channel_header_ID: return_code = 0x%08x \n", return_code);
	}



	// adc DAC offset configuration  
	return_code=this->configure_all_adc_dac_offsets() ;
	if (return_code != 0) {
		printf("Error configure_all_adc_dac_offsets: return_code = 0x%08x \n", return_code);
	}

	// adc DAC offset setup
	for (i_ch=0;i_ch<16; i_ch++) {
		this->adc_dac_offset_ch_array[i_ch] = 0x8000 ; // middle: 5V range -> -/+2.5V; 2V range -> -/+1V
	}
	return_code=this->write_all_adc_dac_offsets() ;
	if (return_code != 0) {
		printf("Error write_all_adc_dac_offsets: return_code = 0x%08x \n", return_code);
	}


	// channel Gain/Termination setup  
	for (i_ch=0;i_ch<16; i_ch++) {
		this->adc_gain_termination_ch_array[i_ch] = 0x0 ; // (5V Range and 50Ohm termination)
	}
	return_code=this->write_all_gain_termination_values() ;
	if (return_code != 0) {
		printf("Error write_all_gain_termination_values: return_code = 0x%08x \n", return_code);
	}

	return_code=this->register_read(SIS3316_SERIAL_NUMBER_REG, &this->serial_number) ;
	return_code=this->register_read(SIS3316_MODID, &this->vme_fpga_version) ;
	return_code=this->register_read(SIS3316_ADC_CH1_4_FIRMWARE_REG, &this->adc_fpga_version) ;

}





/**************************************************************************************/
int sis3316_adc::register_read (UINT addr, UINT* data)
{
int return_code ;
	return_code = this->i->vme_A32D32_read (this->baseaddress+addr, data);	
	return return_code;
}


/**************************************************************************************/

int sis3316_adc::register_write (UINT addr, UINT data)
{
int return_code ;
	return_code = this->i->vme_A32D32_write (this->baseaddress+addr, data);	
	return return_code;
}











/****************************************************************************************************/

int sis3316_adc::update_firmware(char *path, int offset, void (*cb)(int percentage)){
	int rc;
	FILE *fp;
	char *buf;
	int fileSize;
	int percent, percent_old;
	int written = 0;
	int pageProgramSize;
	unsigned int retry_counter = 0 ;
	unsigned int retry_flag = 0 ;

	if(path == NULL){
		return -100;
	}

#ifdef LINUX
	fp = fopen(path, "rb");
	if(fp == NULL){
		return -101;
	}
#endif

#ifdef WIN
	fopen_s(&fp, path, "rb");
	if(fp == NULL){
		return -101;
	}
#endif

	fseek(fp, 0, SEEK_END);
	fileSize = ftell(fp);
	rewind(fp);

	buf = (char *)malloc(fileSize);
	if(buf == NULL){
		return -102;
	}

	rc = fread(buf, 1, fileSize, fp);
	if(rc != fileSize){
		return -103;
	}

	fclose(fp);

	percent = percent_old = 0;
	if(cb){
		(cb)(percent);
	}


	this->FlashEnableProg();

	while(written < fileSize){
		rc = 0 ;
		// erase
		if((written & (SIS3316_FLASH_ERASE_BLOCKSIZE - 1)) == 0){
			rc = this->FlashEraseBlock((offset + written) & 0xFFFF0000);
			if(rc != 0) { 
				printf("erase: rc = %d \n", rc);
			}
		}

		if(fileSize >= (written + SIS3316_FLASH_PROGRAM_PAGESIZE)){
			pageProgramSize = SIS3316_FLASH_PROGRAM_PAGESIZE;
		}else{
			pageProgramSize = fileSize - written;
		}


#ifdef not_used
		if(rc == 0) { 
			rc = this->FlashProgramPage(offset + written, buf + written, pageProgramSize);
			if(rc != 0) { 
				printf("FlashProgramPage: rc = %d \n", rc);
			}
		}
#endif

#define TRY_RETRY
#ifdef TRY_RETRY

		retry_counter = 0 ;	
		do {
			retry_flag = 0 ;	
			rc = this->FlashProgramPage(offset + written, buf + written, pageProgramSize);
			if(rc != 0) { 
				usleep(10000) ; // 10ms

				retry_counter++ ;
				retry_flag = 0 ;	
				if (retry_counter < 16) {
					retry_flag = 1 ;	
				}
				if (retry_counter > 0) {
					printf("Info: retry_counter = %d   addr = 0x%08X\n", retry_counter, offset + written);
				}
			}
		} while (retry_flag==1) ; 

#endif
		if(rc == 0) { 
			written += pageProgramSize;
		}
		else {
			printf("retry Erase/FlashProgramPage \n");
			 usleep(10000000);
		}

		if(cb){
			percent = written * 100 / fileSize;
			if(percent != percent_old){
				(cb)(percent);
				percent_old = percent;
			}
		}
	}
	
	this->FlashDisableProg();

	free(buf);

	return 0;
}







/****************************************************************************************************/
/****************************************************************************************************/

int sis3316_adc::verify_firmware(char *path, int offset, void (*cb)(int percentage)){
	int rc;
	FILE *fp;
	char *buf;
	char *read_buf;
	int fileSize;
	int percent, percent_old;
	int read = 0;
	int pageProgramSize;

	int page_start_offset  ;
	int page_read_len  ;
	int i;


	//unsigned int retry_counter = 0 ;
	//unsigned int retry_flag = 0 ;
	unsigned int verify_bad_flag = 0 ;

	if(path == NULL){
		return -100;
	}



#ifdef LINUX
	fp = fopen(path, "rb");
	if(fp == NULL){
		return -101;
	}
#endif

#ifdef WIN
	fopen_s(&fp, path, "rb");
	if(fp == NULL){
		return -101;
	}
#endif

	fseek(fp, 0, SEEK_END);
	fileSize = ftell(fp);
	rewind(fp);
	//printf("fileSize  = %d  0x%08X\n", fileSize, fileSize);

	buf = (char *)malloc(fileSize);
	if(buf == NULL){
		return -102;
	}

	rc = fread(buf, 1, fileSize, fp);
	if(rc != fileSize){
		return -103;
	}
	fclose(fp);

	read_buf = (char *)malloc(SIS3316_FLASH_PROGRAM_PAGESIZE);
	if(read_buf == NULL){
		return -102;
	}


	percent = percent_old = 0;
	if(cb){
		(cb)(percent);
	}


	this->FlashEnableProg();

//read = 0xCA700;
	while(read < fileSize){
		//printf("fileSize  = %d  0x%08X      read = %d  0x%08X   \n", fileSize, fileSize, read, read);
		rc = 0 ;

		if(fileSize >= (read + SIS3316_FLASH_PROGRAM_PAGESIZE)){
			pageProgramSize = SIS3316_FLASH_PROGRAM_PAGESIZE;
		}else{
			pageProgramSize = fileSize - read;
		}


		// to read all bytes takes 20 minutes with etherner !
		// instead of read all bytes of a page (256) read only the last 16 bytes of a page

		page_start_offset = 0;
		page_read_len = pageProgramSize;
		if(pageProgramSize == SIS3316_FLASH_PROGRAM_PAGESIZE) {
			page_read_len = 16;
			page_start_offset = (SIS3316_FLASH_PROGRAM_PAGESIZE - page_read_len) ;
		}

		rc = this->FlashRead(offset + read + page_start_offset, &read_buf[page_start_offset], page_read_len);
		//rc = this->FlashRead(offset + read, read_buf, pageProgramSize);
		if(rc != 0) { 
			printf("FlashReadPage: rc = %d \n", rc);
		}

		for (i=page_start_offset;i<pageProgramSize;i++) {
			if(buf[read+i] != read_buf[i]){
				if (verify_bad_flag == 0) {
					printf("error at address =   0x%08X   file = 0x%02X   read = 0x%02X \n", read + i , (unsigned char)buf[read+i], (unsigned char)read_buf[i]);
				}
				verify_bad_flag = 1 ;
			}
			
		}
		 
		read += pageProgramSize;


		if(cb){
			percent = read * 100 / fileSize;
			if(percent != percent_old){
				(cb)(percent);
				percent_old = percent;
			}
		}
	}
	
	this->FlashDisableProg();

	free(buf);
	if(verify_bad_flag == 1) {
		return -1;
	}
	return 0;
}




/***************************************************************/
int sis3316_adc::FlashEnableProg(){
	UINT tmp;
	int rc;

	rc = i->vme_A32D32_read(this->baseaddress + SIS3316_SPI_FLASH_CSR, &tmp);
	if(rc){
		return rc;
	}

	tmp |= (1<<ENABLE_SPI_PROG);

	rc = i->vme_A32D32_write(this->baseaddress + SIS3316_SPI_FLASH_CSR, tmp);
	if(rc){
		return rc;
	}

	return 0;
}
/***************************************************************/

int sis3316_adc::FlashDisableProg(){
	UINT tmp;
	int rc;

	rc = i->vme_A32D32_read(this->baseaddress + SIS3316_SPI_FLASH_CSR, &tmp);
	if(rc){
		return rc;
	}

	tmp &= ~(1<<ENABLE_SPI_PROG);

	rc = i->vme_A32D32_write(this->baseaddress + SIS3316_SPI_FLASH_CSR, tmp);
	if(rc){
		return rc;
	}

	return 0;
}
/***************************************************************/

int sis3316_adc::FlashEnableCS(int chip){
	UINT tmp;
	int rc;

	rc = i->vme_A32D32_read(this->baseaddress + SIS3316_SPI_FLASH_CSR, &tmp);
	if(rc){
		return rc;
	}

	switch(chip){
	case 0:
		tmp |= (1<<CHIPSELECT_1);
		break;
	case 1:
		tmp |= (1<<CHIPSELECT_2);
		break;
	default:
		return -100;
	}

	rc = i->vme_A32D32_write(this->baseaddress + SIS3316_SPI_FLASH_CSR, tmp);
	if(rc){
		return rc;
	}

	return 0;
}

/***************************************************************/

int sis3316_adc::FlashDisableCS(int chip){
	UINT tmp;
	int rc;

	rc = i->vme_A32D32_read(this->baseaddress + SIS3316_SPI_FLASH_CSR, &tmp);
	if(rc){
		return rc;
	}

	switch(chip){
	case 0:
		tmp &= ~(1<<CHIPSELECT_1);
		break;
	case 1:
		tmp &= ~(1<<CHIPSELECT_2);
		break;
	default:
		return -100;
	}

	rc = i->vme_A32D32_write(this->baseaddress + SIS3316_SPI_FLASH_CSR, tmp);
	if(rc){
		return rc;
	}

	return 0;
}

/***************************************************************/


int sis3316_adc::FlashWriteEnable(){
	int rc;
	
	rc = this->FlashEnableCS(0);
	if(rc){
		return rc;
	}
	
	rc = this->FlashXfer(0x06, NULL); // Write Enable command
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}

	rc = this->FlashDisableCS(0);
	if(rc){
		return rc;
	}

	return 0;
}
/***************************************************************/


int sis3316_adc::FlashWriteDisable(){
	int rc;
	
	rc = this->FlashEnableCS(0);
	if(rc){
		return rc;
	}
	
	rc = this->FlashXfer(0x04, NULL); // Write Enable command
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}

	rc = this->FlashDisableCS(0);
	if(rc){
		return rc;
	}

	return 0;
}

/***************************************************************/
int sis3316_adc::FlashRead(int address, char *data, int len){
	int rc;
	char tmp;
	tmp = 0 ;
	if(data == NULL){
		return -100;
	}
	
	//rc = this->FlashWriteEnable();
	//if(rc){
	//	return rc;
	//}

	// program command

	this->FlashDisableCS(0);

	rc = this->FlashEnableCS(0);
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}


	
	rc = this->FlashXfer(0x03, NULL); // Read program command
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}

 
	rc = this->FlashXfer((char)(address >> 16), NULL);
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}
	rc = this->FlashXfer((char)(address >> 8), NULL);
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}
	rc = this->FlashXfer((char)address, NULL);
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}

 

	char char_temp ;
	char_temp=0;
	for(int i = 0;i < len && i < SIS3316_FLASH_PROGRAM_PAGESIZE;i++){
		rc = this->FlashXfer(char_temp, &tmp);
		data[i] = tmp ;
		if(rc){
			this->FlashDisableCS(0);
			return rc;
		}
	}
 
	rc = this->FlashDisableCS(0);
	if(rc){
		return rc;
	}

#ifdef test_remove
	usleep(1000); // testing
	// busy polling
	do{
		rc = this->FlashEnableCS(0);
		if(rc){
			return rc;
		}
	
		rc = this->FlashXfer(0x05, NULL); // read status register 1 command
		if(rc){
			this->FlashDisableCS(0);
			return rc;
		}
		rc = this->FlashXfer(0, &tmp);
		if(rc){
			this->FlashDisableCS(0);
			return rc;
		}

		tmp &= 1;

		rc = this->FlashDisableCS(0);
		if(rc){
			return rc;
		}
		usleep(1000); // testing
	}while(tmp);
#endif
	return 0;
}

/***************************************************************/


int sis3316_adc::FlashProgramPage(int address, char *data, int len){
	int rc;
	int rc_dma_error;
	char tmp;
	UINT utmp;
	UINT dmabuf[SIS3316_FLASH_PROGRAM_PAGESIZE];
	UINT putWords;

	if(data == NULL){
		return -100;
	}
	
	rc = this->FlashWriteEnable();
	if(rc){
		return rc;
	}

	// program command
	rc = this->FlashEnableCS(0);
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}
	
	rc = this->FlashXfer(0x02, NULL); // Page program command
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}
	rc = this->FlashXfer((char)(address >> 16), NULL);
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}
	rc = this->FlashXfer((char)(address >> 8), NULL);
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}
	rc = this->FlashXfer((char)address, NULL);
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}

	// dma d32
	for(int k = 0;k < SIS3316_FLASH_PROGRAM_PAGESIZE;k++){
		dmabuf[k] = (UINT)*(data + k);
	}
	rc_dma_error = 0 ;
	rc = i->vme_A32DMA_D32FIFO_write(this->baseaddress + SIS3316_SPI_FLASH_DATA, dmabuf, SIS3316_FLASH_PROGRAM_PAGESIZE, &putWords);
	if(rc || (putWords != SIS3316_FLASH_PROGRAM_PAGESIZE)){
		//	printf("error vme_A32DMA_D32FIFO_write\n");
		//  printf("address = 0x%08X \n\n",address);
		rc_dma_error = -101 ;
	}
	 
	// busy polling
	do{
		rc = i->vme_A32D32_read(this->baseaddress + SIS3316_SPI_FLASH_CSR, &utmp);
		if(rc){
			return rc;
		}
		utmp &= (1<<FLASH_LOGIC_BUSY^1<<FIFO_NOT_EMPTY);
		usleep(1000); // testing
	}while(utmp != 0);

	// single cycles
#if 0
	for(int i = 0;i < len && i < SIS3316_FLASH_PROGRAM_PAGESIZE;i++){
		rc = this->FlashXfer(*(data + i), NULL);
		if(rc){
			this->FlashDisableCS(0);
			return rc;
		}
	}
#endif

	rc = this->FlashDisableCS(0);
	if(rc){
		return rc;
	}
	usleep(1000); // testing
	// busy polling
	do{
		rc = this->FlashEnableCS(0);
		if(rc){
			return rc;
		}
	
		rc = this->FlashXfer(0x05, NULL); // read status register 1 command
		if(rc){
			this->FlashDisableCS(0);
			return rc;
		}
		rc = this->FlashXfer(0, &tmp);
		if(rc){
			this->FlashDisableCS(0);
			return rc;
		}

		tmp &= 1;

		rc = this->FlashDisableCS(0);
		if(rc){
			return rc;
		}
		usleep(1000); // testing
	}while(tmp);

	if(	rc_dma_error != 0) {
		return -101;
	}

	return 0;
}


/***************************************************************/


int sis3316_adc::FlashEraseBlock(int address){
	int rc;
	char tmp;
	
	rc = this->FlashWriteEnable();
	if(rc){
		return rc;
	}

	// erase command
	rc = this->FlashEnableCS(0);
	if(rc){
		return rc;
	}
	
	rc = this->FlashXfer((char)0xD8, NULL); // 64kB Block erase command
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}
	rc = this->FlashXfer((char)(address >> 16), NULL);
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}
	rc = this->FlashXfer((char)(address >> 8), NULL);
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}
	rc = this->FlashXfer((char)address, NULL);
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}

	rc = this->FlashDisableCS(0);
	if(rc){
		return rc;
	}
	usleep(1000); // testing
	// busy polling
	do{
		rc = this->FlashEnableCS(0);
		if(rc){
			this->FlashDisableCS(0);
			return rc;
		}
	
		rc = this->FlashXfer(0x05, NULL); // read status register 1 command
		if(rc){
			this->FlashDisableCS(0);
			return rc;
		}
		rc = this->FlashXfer(0, &tmp);
		if(rc){
			this->FlashDisableCS(0);
			return rc;
		}

		tmp &= 1;

		rc = this->FlashDisableCS(0);
		if(rc){
			return rc;
		}
		usleep(1000); // testing
	}while(tmp);

	return 0;
}


/***************************************************************/


int sis3316_adc::FlashXfer(char in, char *out){
	UINT tmp;
	char ctmp;
	int rc;

	tmp = in;
	rc = i->vme_A32D32_write(this->baseaddress + SIS3316_SPI_FLASH_DATA, tmp);
	if(rc){
		return rc;
	}
 
	do{
		rc = i->vme_A32D32_read(this->baseaddress + SIS3316_SPI_FLASH_CSR, &tmp);
		if(rc){
			return rc;
		}

		tmp &= (1<<FLASH_LOGIC_BUSY^1<<FIFO_NOT_EMPTY);

		//usleep(1000); // testing

	}while(tmp != 0);
 
	rc = i->vme_A32D32_read(this->baseaddress + SIS3316_SPI_FLASH_DATA, &tmp);
	if(rc){
		return rc;
	}

	ctmp = tmp & 0xFF;
	if(out){
		*out = ctmp;
	}

	return 0;
}


/***************************************************************/


int sis3316_adc::FlashGetId(char *id){
	int rc;

	if(id == NULL){
		return -100;
	}

	rc = this->FlashEnableCS(0);
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}
	
	rc = this->FlashXfer((char)0x9F, NULL); // JEDEC ID command
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}
	rc = this->FlashXfer(0, id);
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}
	rc = this->FlashXfer(0, id+1);
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}
	rc = this->FlashXfer(0, id+2);
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}

	rc = this->FlashDisableCS(0);
	if(rc){
		return rc;
	}

	return 0;
}



int sis3316_adc::FlashReadStatus1(char *status){
	int rc;

	if(status == NULL){
		return -100;
	}

	rc = this->FlashEnableCS(0);
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}
	
	rc = this->FlashXfer((char)0x05, NULL); //  
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}
	rc = this->FlashXfer(0, status);
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}

	rc = this->FlashDisableCS(0);
	if(rc){
		return rc;
	}

	return 0;
}

int sis3316_adc::FlashReadStatus2(char *status){
	int rc;

	if(status == NULL){
		return -100;
	}

	rc = this->FlashEnableCS(0);
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}
	
	rc = this->FlashXfer((char)0x35, NULL); //  
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}
	rc = this->FlashXfer(0, status);
	if(rc){
		this->FlashDisableCS(0);
		return rc;
	}

	rc = this->FlashDisableCS(0);
	if(rc){
		return rc;
	}

	return 0;
}

/********************************************************************************************************************************/

int sis3316_adc::I2cStart(int osc){
	int rc;
	int i;
	UINT tmp;

	if(osc > 3){
		return -101;
	}

	// start
	rc = this->i->vme_A32D32_write(this->baseaddress + SIS3316_ADC_CLK_OSC_I2C_REG + (4 * osc), 1<<I2C_START);
	if(rc){
		return rc;
	}

	i = 0;
	do{
		// poll i2c fsm busy
		rc = this->i->vme_A32D32_read(this->baseaddress + SIS3316_ADC_CLK_OSC_I2C_REG + (4 * osc), &tmp);
		if(rc){
			return rc;
		}
		i++;
	}while((tmp & (1<<I2C_BUSY)) && (i < 1000));

	// register access problem
	if(i == 1000){
		return -100;
	}

	return 0;
}

/***************************************************************/


int sis3316_adc::I2cStop(int osc){
	int rc;
	int i;
	UINT tmp;

	if(osc > 3){
		return -101;
	}

	// stop
	rc = this->i->vme_A32D32_write(this->baseaddress + SIS3316_ADC_CLK_OSC_I2C_REG + (4 * osc), 1<<I2C_STOP);
	if(rc){
		return rc;
	}
	
	i = 0;
	do{
		// poll i2c fsm busy
		rc = this->i->vme_A32D32_read(this->baseaddress + SIS3316_ADC_CLK_OSC_I2C_REG + (4 * osc), &tmp);
		if(rc){
			return rc;
		}
		i++;
	}while((tmp & (1<<I2C_BUSY)) && (i < 1000));

	// register access problem
	if(i == 1000){
		return -100;
	}

	return 0;
}

/***************************************************************/


int sis3316_adc::I2cWriteByte(int osc, unsigned char data, char *ack){
	int rc;
	int i;
	UINT tmp;
	
	if(osc > 3){
		return -101;
	}

	// write byte, receive ack
	rc = this->i->vme_A32D32_write(this->baseaddress + SIS3316_ADC_CLK_OSC_I2C_REG + (4 * osc), 1<<I2C_WRITE ^ data);
	if(rc){
		return rc;
	}
	
	i = 0;
	do{
		// poll i2c fsm busy
		rc = this->i->vme_A32D32_read(this->baseaddress + SIS3316_ADC_CLK_OSC_I2C_REG + (4 * osc), &tmp);
		if(rc){
			return rc;
		}
		i++;
	}while((tmp & (1<<I2C_BUSY)) && (i < 1000));

	// register access problem
	if(i == 1000){
		return -100;
	}

	// return ack value?
	if(ack){
		// yup
		*ack = tmp & 1<<I2C_ACK ? 1 : 0;
	}

	return 0;
}

/***************************************************************/


int sis3316_adc::I2cReadByte(int osc, unsigned char *data, char ack){
	int rc;
	int i;
	UINT tmp;
	unsigned char char_tmp;	
	if(osc > 3){
		return -101;
	}

	// read byte, put ack
	tmp = 1<<I2C_READ;
	tmp |= ack ? 1<<I2C_ACK : 0;
	rc = this->i->vme_A32D32_write(this->baseaddress + SIS3316_ADC_CLK_OSC_I2C_REG + (4 * osc), tmp);
	if(rc){
		return rc;
	}
	
	i = 0;
	do{
		// poll i2c fsm busy
		rc = this->i->vme_A32D32_read(this->baseaddress + SIS3316_ADC_CLK_OSC_I2C_REG + (4 * osc), &tmp);
		if(rc){
			return rc;
		}
		i++;
	}while((tmp & (1<<I2C_BUSY)) && (i < 1000));

	// register access problem
	if(i == 1000){
		return -100;
	}
	char_tmp = (unsigned char) (tmp & 0xff) ;
	*data = char_tmp ;
	return 0;
}
//int sis3316_adc::get_frequency(int osc, unsigned char *values){
//Si570ReadDivider
//I2cReadByte
	
/***************************************************************/


int sis3316_adc::Si570FreezeDCO(int osc){
	int rc;
	char ack;

	// start
	rc = this->I2cStart(osc);
	if(rc){
		this->I2cStop(osc);
		return rc;
	}

	// address
	rc = this->I2cWriteByte(osc, OSC_ADR<<1, &ack);
	if(rc){
		this->I2cStop(osc);
		return rc;
	}

	if(!ack){
		this->I2cStop(osc);
		return -101;
	}

	// register offset
	rc = this->I2cWriteByte(osc, 0x89, &ack);
	if(rc){
		this->I2cStop(osc);
		return rc;
	}

	if(!ack){
		this->I2cStop(osc);
		return -101;
	}

	// write data
	rc = this->I2cWriteByte(osc, 0x10, &ack);
	if(rc){
		this->I2cStop(osc);
		return rc;
	}

	if(!ack){
		this->I2cStop(osc);
		return -101;
	}

	// stop
	rc = this->I2cStop(osc);
	if(rc){
		return rc;
	}

	return 0;
}

/***************************************************************/

int sis3316_adc::Si570ReadDivider(int osc, unsigned char *data){
	int rc;
	char ack;
	int i;

	// start
	rc = this->I2cStart(osc);
	if(rc){
		this->I2cStop(osc);
		return rc;
	}

	// address
	rc = this->I2cWriteByte(osc, OSC_ADR<<1, &ack);
	if(rc){
		this->I2cStop(osc);
		return rc;
	}

	if(!ack){
		this->I2cStop(osc);
		return -101;
	}

	// register offset
	rc = this->I2cWriteByte(osc, 0x0D, &ack);
	if(rc){
		this->I2cStop(osc);
		return rc;
	}

	if(!ack){
		this->I2cStop(osc);
		return -101;
	}


	rc = this->I2cStart(osc);
	if(rc){
		this->I2cStop(osc);
		return rc;
	}

	// address + 1
	rc = this->I2cWriteByte(osc, (OSC_ADR<<1) + 1, &ack);
	if(rc){
		this->I2cStop(osc);
		return rc;
	}

	if(!ack){
		this->I2cStop(osc);
		return -101;
	}


	// read data
	for(i = 0;i < 6;i++){
		ack = 1 ;
		if (i==5) {ack = 0;}
		rc = this->I2cReadByte(osc, &data[i], ack);
		if(rc){
			this->I2cStop(osc);
			return rc;
		}

	}

	// stop
	rc = this->I2cStop(osc);
	if(rc){
		return rc;
	}

	return 0;
}

/***************************************************************/

/***************************************************************/

int sis3316_adc::Si570Divider(int osc, unsigned char *data){
	int rc;
	char ack;
	int i;

	// start
	rc = this->I2cStart(osc);
	if(rc){
		this->I2cStop(osc);
		return rc;
	}

	// address
	rc = this->I2cWriteByte(osc, OSC_ADR<<1, &ack);
	if(rc){
		this->I2cStop(osc);
		return rc;
	}

	if(!ack){
		this->I2cStop(osc);
		return -101;
	}

	// register offset
	rc = this->I2cWriteByte(osc, 0x0D, &ack);
	if(rc){
		this->I2cStop(osc);
		return rc;
	}

	if(!ack){
		this->I2cStop(osc);
		return -101;
	}

	// write data
	for(i = 0;i < 2;i++){
		rc = this->I2cWriteByte(osc, data[i], &ack);
		if(rc){
			this->I2cStop(osc);
			return rc;
		}

		if(!ack){
			this->I2cStop(osc);
			return -101;
		}
	}

	// stop
	rc = this->I2cStop(osc);
	if(rc){
		return rc;
	}

	return 0;
}

/***************************************************************/


int sis3316_adc::Si570UnfreezeDCO(int osc){
	int rc;
	char ack;

	// start
	rc = this->I2cStart(osc);
	if(rc){
		this->I2cStop(osc);
		return rc;
	}

	// address
	rc = this->I2cWriteByte(osc, OSC_ADR<<1, &ack);
	if(rc){
		this->I2cStop(osc);
		return rc;
	}

	if(!ack){
		this->I2cStop(osc);
		return -101;
	}

	// register offset
	rc = this->I2cWriteByte(osc, 0x89, &ack);
	if(rc){
		this->I2cStop(osc);
		return rc;
	}

	if(!ack){
		this->I2cStop(osc);
		return -101;
	}

	// write data
	rc = this->I2cWriteByte(osc, 0x00, &ack);
	if(rc){
		this->I2cStop(osc);
		return rc;
	}

	if(!ack){
		this->I2cStop(osc);
		return -101;
	}

	// stop
	rc = this->I2cStop(osc);
	if(rc){
		return rc;
	}

	return 0;
}


/***************************************************************/

int sis3316_adc::Si570NewFreq(int osc){
	int rc;
	char ack;
	// start
	rc = this->I2cStart(osc);
	if(rc){
		this->I2cStop(osc);
		return rc;
	}

	// address
	rc = this->I2cWriteByte(osc, OSC_ADR<<1, &ack);
	if(rc){
		this->I2cStop(osc);
		return rc;
	}
	if(!ack){
		this->I2cStop(osc);
		return -101;
	}

	// register offset
	rc = this->I2cWriteByte(osc, 0x87, &ack);
	if(rc){
		this->I2cStop(osc);
		return rc;
	}

	if(!ack){
		this->I2cStop(osc);
		return -101;
	}

	// write data
	rc = this->I2cWriteByte(osc, 0x40, &ack);
	if(rc){
		this->I2cStop(osc);
		return rc;
	}

	if(!ack){
		this->I2cStop(osc);
		return -101;
	}

	// stop
	rc = this->I2cStop(osc);
	if(rc){
		return rc;
	}

	return 0;
}



/****************************************************************************************************/

int sis3316_adc::set_frequency(int osc, unsigned char *values){
	int rc;

	if(values == NULL){
		return -100;
	}
	if(osc > 3 || osc < 0){
		return -100;
	}

	rc = this->Si570FreezeDCO(osc);
	if(rc){
		return rc;
	}

	rc = this->Si570Divider(osc, values);
	if(rc){
		return rc;
	}

	rc = this->Si570UnfreezeDCO(osc);
	if(rc){
		return rc;
	}

	rc = this->Si570NewFreq(osc);
	if(rc){
		return rc;
	}

// min. 10ms wait
	usleep(15000); // 15 ms

	// DCM Reset  
	rc = this->i->vme_A32D32_write(this->baseaddress + 0x438 , 0);
	if(rc){
		return rc;
	}
	// DCM Reset -> the DCM/PLL of the ADC-FPGAs will be stable after max. 5ms
	//              or check the DCM OK bits (ADC FPGA Status registers bit 20)
	usleep(5000); // 5 ms


	return 0;
}




/****************************************************************************************************/
/****************************************************************************************************/

int sis3316_adc::owReset(int *presence){
	int rc;
	UINT data;

	rc = this->i->vme_A32D32_write(this->baseaddress + 0x24, 1<<10); // reset
	if(rc){
		return rc;
	}

	do{
		rc = this->i->vme_A32D32_read(this->baseaddress + 0x24, &data);
		if(rc){
			return rc;
		}
	}while(data & 1<<31); // while busy

	if(presence){
		*presence = (data & 1<<0) ? 0 : 1;
	}

	return 0;
}

/***********************************************************/

int sis3316_adc::owRead(unsigned char *data){
	int rc;
	UINT reg;

	rc = this->i->vme_A32D32_write(this->baseaddress + 0x24, 1<<8);
	if(rc){
		return rc;
	}

	do{
		rc = this->i->vme_A32D32_read(this->baseaddress + 0x24, &reg);
		if(rc){
			return rc;
		}
	}while(reg & 1<<31); // while busy

	if(data){
		*data = reg & 0xFF;
	}

	return 0;
}

/***********************************************************/

int sis3316_adc::owWrite(unsigned char data){
	int rc;
	UINT reg;

	rc = this->i->vme_A32D32_write(this->baseaddress + 0x24, 1<<9 ^ data);
	if(rc){
		return rc;
	}

	do{
		rc = this->i->vme_A32D32_read(this->baseaddress + 0x24, &reg);
		if(rc){
			return rc;
		}
	}while(reg & 1<<31); // while busy

	return 0;
}

/***********************************************************/

int sis3316_adc::owEeReadPage(int page, unsigned char *data){
	int rc;
	int i;

	if(page >= 80){
		return -1;
	}
	if(data == NULL){
		return -2;
	}

	// presence
	rc = this->owReset(&i);
	if(rc){
		return rc;
	}
	if(!i){
		return -3;
	}

	// read page
	rc = this->owWrite(0xCC); // skip rom
	if(rc){
		return rc;
	}

	rc = this->owWrite(0xF0); // read memory
	if(rc){
		return rc;
	}

	rc = this->owWrite((page * 32) & 0xFF); // adr lo
	if(rc){
		return rc;
	}

	rc = this->owWrite(((page * 32) >> 8) & 0xFF); // adr hi
	if(rc){
		return rc;
	}

	for(i = 0;i < 32;i++){
		rc = this->owRead(data + i); // data in
		if(rc){
			this->owReset(NULL);
			return rc;
		}
	}

	this->owReset(NULL);

	return 0;
}

/***********************************************************/

int sis3316_adc::owEeWritePage(int page, unsigned char *data){
	int rc;
	int i;
	unsigned char aLo, aHi, esReg;
	unsigned char vfyData[32];

	if(page >= 80){
		return -1;
	}
	if(data == NULL){
		return -2;
	}

	// Step 1, copy page to eeprom internal scratchpad sram

	// presence
	rc = this->owReset(&i);
	if(rc){
		return rc;
	}
	if(!i){
		return -3;
	}

	// read page
	rc = this->owWrite(0xCC); // skip rom
	if(rc){
		return rc;
	}

	rc = this->owWrite(0x0F); // write scratchpad
	if(rc){
		return rc;
	}

	rc = this->owWrite((page * 32) & 0xFF); // adr lo
	if(rc){
		return rc;
	}

	rc = this->owWrite(((page * 32) >> 8) & 0xFF); // adr hi
	if(rc){
		return rc;
	}

	for(i = 0;i < 32;i++){
		rc = this->owWrite(*(data + i)); // data in
		if(rc){
			this->owReset(NULL);
			return rc;
		}
	}

	this->owReset(NULL);

	// Step 2, verify the scratchpad

	// presence
	rc = this->owReset(&i);
	if(rc){
		return rc;
	}
	if(!i){
		return -3;
	}

	// read page
	rc = this->owWrite(0xCC); // skip rom
	if(rc){
		return rc;
	}

	rc = this->owWrite(0xAA); // read scratchpad
	if(rc){
		return rc;
	}

	rc = this->owRead(&aLo); // adr lo
	if(rc){
		return rc;
	}

	rc = this->owRead(&aHi); // adr hi
	if(rc){
		return rc;
	}

	rc = this->owRead(&esReg); // es reg
	if(rc){
		return rc;
	}

	for(i = 0;i < 32;i++){
		rc = this->owRead(vfyData + i); // data in
		if(rc){
			this->owReset(NULL);
			return rc;
		}
	}

	this->owRead(NULL); // crc16
	this->owRead(NULL); // crc16

	this->owReset(NULL);

	// Step 3, copy scratchpad to eeprom array

	// presence
	rc = this->owReset(&i);
	if(rc){
		return rc;
	}
	if(!i){
		return -3;
	}

	// read page
	rc = this->owWrite(0xCC); // skip rom
	if(rc){
		return rc;
	}

	rc = this->owWrite(0x55); // copy scratchpad
	if(rc){
		return rc;
	}

	rc = this->owWrite(aLo); // adr lo
	if(rc){
		return rc;
	}

	rc = this->owWrite(aHi); // adr hi
	if(rc){
		return rc;
	}

	rc = this->owWrite(esReg); // es reg
	if(rc){
		return rc;
	}

	usleep(50000);

	this->owReset(NULL);

	return 0;
}

/***********************************************************/

int sis3316_adc::read_ee(int offset, int len, unsigned char *data){
	int rc;
	//int i;
	int pageNum, localLen = len, pageOffs, localOffs = offset;
	int copyLen;
	unsigned char page[32];

	if(data == NULL){
		return -1;
	}
	if(offset + len > 2560){
		return -2;
	}
	if(len == 0){
		return -3;
	}

	// page loop
	// read
	while(localLen){
		// page to start
		pageNum = localOffs / 32;
		// offset within first page
		pageOffs = localOffs % 32;

		// read
		rc = this->owEeReadPage(pageNum, page);
		if(rc){
			return rc;
		}
		
		if((pageOffs + localLen) > 32){
			copyLen = 32 - pageOffs;
		}else{
			copyLen = localLen;
		}

		// copy back
		memcpy(data, page + pageOffs, copyLen);

		// adjust
		localLen -= copyLen;
		localOffs += copyLen;
		data += copyLen;
	}

	return 0;
}

/***********************************************************/

int sis3316_adc::write_ee(int offset, int len, unsigned char *data){
	int rc;
	//int i;
	int pageNum, localLen = len, pageOffs, localOffs = offset;
	int copyLen;
	unsigned char page[32];

	if(data == NULL){
		return -1;
	}
	if(offset + len > 2560){
		return -2;
	}
	if(len == 0){
		return -3;
	}

	// page loop
	// read-modify-write
	while(localLen){
		// page to start
		pageNum = localOffs / 32;
		// offset within first page
		pageOffs = localOffs % 32;

		// read
		rc = this->owEeReadPage(pageNum, page);
		if(rc){
			return rc;
		}

		if((pageOffs + localLen) > 32){
			copyLen = 32 - pageOffs;
		}else{
			copyLen = localLen;
		}

		// modify
		memcpy(page + pageOffs, data, copyLen);

		// write
		rc = this->owEeWritePage(pageNum, page);
		if(rc){
			return 0;
		}

		// adjust
		localLen -= copyLen;
		localOffs += copyLen;
		data += copyLen;
	}

	return 0;
}

/***********************************************************/

int sis3316_adc::ow_id_ee(unsigned char *data){
	int rc;
	int i;

	// presence
	rc = this->owReset(&i);
	if(rc){
		return rc;
	}
	if(!i){
		return -1;
	}

	// read rom cmd
	rc = this->owWrite(0x33);
	if(rc){
		return rc;
	}

	// read data
	for(i = 0;i < 8;i++){
		rc = this->owRead(data + i);
		if(rc){
			return rc;
		}
	}

	return 0;
}

/***********************************************************/
	int sis3316_adc::write_ow_dhcp_option(unsigned char *data){
	int rc;
		rc = this->write_ee(2, 1, data);
		if(rc){
			return rc;
		}

	return 0;
}


/****************************************************************************************************/
/****************************************************************************************************/


/****************************************************************************************************/
/*                                                                                                  */
/*     change_frequency_HSdiv_N1div                                                                 */
/*     hs_div_val: allowed values are [4, 5, 6, 7, 9, 11]                                           */
/*     n1_div_val: allowed values are [2, 4, 6, .... 124, 126]                                      */
/*     Sample Frequence =  5 GHz / (hs_div_val * n1_div_val)                                        */
/*                                                                                                  */
/*     example:                                                                                     */
/*     hs_div_val = 5                                                                               */
/*     n1_div_val = 4                                                                               */
/*     Sample Frequence =  5 GHz / 20 = 250 MHz                                                     */
/*                                                                                                  */
/****************************************************************************************************/

int sis3316_adc::change_frequency_HSdiv_N1div(int osc, unsigned hs_div_val, unsigned n1_div_val){
	int rc;
	unsigned i ;
	unsigned N1div ;
	unsigned HSdiv ;
	unsigned HSdiv_reg[6] ;
	unsigned HSdiv_val[6] ;
	unsigned char freqSI570_high_speed_rd_value[6];
	unsigned char freqSI570_high_speed_wr_value[6];
	
	if(osc > 3 || osc < 0){
		return -100;
	}

	HSdiv_reg[0] =  0 ;
	HSdiv_val[0] =  4 ;

	HSdiv_reg[1] =  1 ;
	HSdiv_val[1] =  5 ;

	HSdiv_reg[2] =  2 ;
	HSdiv_val[2] =  6 ;

	HSdiv_reg[3] =  3 ;
	HSdiv_val[3] =  7 ;

	HSdiv_reg[4] =  5 ;
	HSdiv_val[4] =  9 ;

	HSdiv_reg[5] =  7 ;
	HSdiv_val[5] =  11 ;

	HSdiv = 0xff ;
	for (i=0;i<6;i++){
		if (HSdiv_val[i] == hs_div_val) {
			HSdiv = HSdiv_reg[i] ;
		}
	}
	if (HSdiv > 11) {
		return -101;
	}

	// gt than 127 or odd then return
	if((n1_div_val > 127) || ((n1_div_val & 0x1) == 1) || (n1_div_val == 0) ) {
		return -102;
	}
	N1div = n1_div_val - 1 ;

	rc = this->Si570ReadDivider(osc, freqSI570_high_speed_rd_value);
	if(rc){
		printf("Si570ReadDivider = %d \n",rc);
		return rc;
	}
	freqSI570_high_speed_wr_value[0] = ((HSdiv & 0x7) << 5) + ((N1div & 0x7c) >> 2);
	freqSI570_high_speed_wr_value[1] = ((N1div & 0x3) << 6) + (freqSI570_high_speed_rd_value[1] & 0x3F);
	freqSI570_high_speed_wr_value[2] = freqSI570_high_speed_rd_value[2];
	freqSI570_high_speed_wr_value[3] = freqSI570_high_speed_rd_value[3];
	freqSI570_high_speed_wr_value[4] = freqSI570_high_speed_rd_value[4];
	freqSI570_high_speed_wr_value[5] = freqSI570_high_speed_rd_value[5];


	rc = this->set_frequency(osc, freqSI570_high_speed_wr_value);
	if(rc){
		printf("set_frequency = %d \n",rc);
		return rc;
	}

	return 0;
}

/****************************************************************************************************/
int sis3316_adc::get_frequency(int osc, unsigned char *values){
	int rc;

	if(values == NULL){
		return -100;
	}
	if(osc > 3 || osc < 0){
		return -100;
	}
	rc = this->Si570ReadDivider(osc, values);
	if(rc){
		return rc;
	}

	return 0;
}

/****************************************************************************************************/


/****************************************************************************************************/

int sis3316_adc::configure_adc_fpga_iob_delays(unsigned int iob_delay_value){
	int rc;


	rc = this->i->vme_A32D32_write(this->baseaddress + SIS3316_ADC_CH1_4_INPUT_TAP_DELAY_REG, 0xf00 ); // Calibrate IOB _delay Logic
	if(rc){
		return rc;
	}
	rc = this->i->vme_A32D32_write(this->baseaddress + SIS3316_ADC_CH5_8_INPUT_TAP_DELAY_REG, 0xf00 ); // Calibrate IOB _delay Logic
	if(rc){
		return rc;
	}
	rc = this->i->vme_A32D32_write(this->baseaddress + SIS3316_ADC_CH9_12_INPUT_TAP_DELAY_REG, 0xf00 ); // Calibrate IOB _delay Logic
	if(rc){
		return rc;
	}
	rc = this->i->vme_A32D32_write(this->baseaddress + SIS3316_ADC_CH13_16_INPUT_TAP_DELAY_REG, 0xf00 ); // Calibrate IOB _delay Logic
	if(rc){
		return rc;
	}
	usleep(10) ;
	rc = this->i->vme_A32D32_write(this->baseaddress + SIS3316_ADC_CH1_4_INPUT_TAP_DELAY_REG, 0x300 + iob_delay_value ); // set IOB _delay Logic
	if(rc){
		return rc;
	}
	rc = this->i->vme_A32D32_write(this->baseaddress + SIS3316_ADC_CH5_8_INPUT_TAP_DELAY_REG, 0x300 + iob_delay_value ); // set IOB _delay Logic
	if(rc){
		return rc;
	}
	rc = this->i->vme_A32D32_write(this->baseaddress + SIS3316_ADC_CH9_12_INPUT_TAP_DELAY_REG, 0x300 + iob_delay_value ); // set IOB _delay Logic
	if(rc){
		return rc;
	}
	rc = this->i->vme_A32D32_write(this->baseaddress + SIS3316_ADC_CH13_16_INPUT_TAP_DELAY_REG, 0x300 + iob_delay_value ); // set IOB _delay Logic
	if(rc){
		return rc;
	}
	usleep(100) ;

	return 0;
}


/****************************************************************************************************/
// Sample Clock DCM/PLL Reset on each SIS3316 FPGA ;  
int sis3316_adc::reset_adc_fpga_sample_clock_PLL(void){
	int rc;
	rc = this->i->vme_A32D32_write(this->baseaddress + SIS3316_KEY_ADC_CLOCK_DCM_RESET, 0x0 ); //  
	// min. 10ms wait or check if PLL is locked
	usleep(20000);

	return rc;
}
/****************************************************************************************************/
// Sample Clock DCM/PLL Reset on each SIS3316 FPGA ;  
int sis3316_adc::reset_adc_fpga_and_DDR_memory(void){
	int rc;
	rc = this->i->vme_A32D32_write(this->baseaddress + SIS3316_KEY_ADC_FPGA_RESET, 0x0 ); //  
	// 
	usleep(20000);

	return rc;
}


/****************************************************************************************************/
/****************************************************************************************************/

int sis3316_adc::si5325_clk_muliplier_write(unsigned int addr, unsigned int data) 
{
	unsigned int return_code ;
	unsigned int write_data, read_data ;
	unsigned int poll_counter   ;
// write address
	write_data = 0x0000 + (addr & 0xff) ; // write ADDR Instruction + register addr
	return_code = this->i->vme_A32D32_write(this->baseaddress + SIS3316_NIM_CLK_MULTIPLIER_SPI_REG, write_data ); //  
	if (return_code != 0) {	return -1 ;	}
		usleep(10000) ;

	poll_counter = 0 ;
	do {
		poll_counter++;
		this->i->vme_A32D32_read(this->baseaddress + SIS3316_NIM_CLK_MULTIPLIER_SPI_REG, &read_data ); //  
	} while (((read_data & 0x80000000) == 0x80000000) && (poll_counter < SI5325_SPI_POLL_COUNTER_MAX)) ;
	if (poll_counter == SI5325_SPI_POLL_COUNTER_MAX) {	return -2 ;	}
		usleep(10000) ;

// write data
	write_data = 0x4000 + (data & 0xff) ; // write Instruction + data
	return_code = this->i->vme_A32D32_write(this->baseaddress + SIS3316_NIM_CLK_MULTIPLIER_SPI_REG, write_data ); //  
	if (return_code != 0) {	return -1 ;	}
		usleep(10000) ;

	poll_counter = 0 ;
	do {
		poll_counter++;
		this->i->vme_A32D32_read(this->baseaddress + SIS3316_NIM_CLK_MULTIPLIER_SPI_REG, &read_data ); //  
	} while (((read_data & 0x80000000) == 0x80000000) && (poll_counter < SI5325_SPI_POLL_COUNTER_MAX)) ;
	if (poll_counter == SI5325_SPI_POLL_COUNTER_MAX) {	return -2 ;	}
	
	return 0 ;
}



/****************************************************************************************************/

int sis3316_adc::si5325_clk_muliplier_read(unsigned int addr, unsigned int *data)   
{
	unsigned int return_code ;
	unsigned int write_data, read_data ;
	unsigned int poll_counter   ;
// read address
	write_data = 0x0000 + (addr & 0xff) ; // read ADDR Instruction + register addr
	return_code = this->i->vme_A32D32_write(this->baseaddress + SIS3316_NIM_CLK_MULTIPLIER_SPI_REG, write_data ); //  
	if (return_code != 0) {	return -1 ;	}

	poll_counter = 0 ;
	do {
		poll_counter++;
		this->i->vme_A32D32_read(this->baseaddress + SIS3316_NIM_CLK_MULTIPLIER_SPI_REG, &read_data ); //  
	} while (((read_data & 0x80000000) == 0x80000000) && (poll_counter < SI5325_SPI_POLL_COUNTER_MAX)) ;
	if (poll_counter == SI5325_SPI_POLL_COUNTER_MAX) {	return -2 ;	}
		usleep(10000) ;

// read data
	write_data = 0x8000  ; // read Instruction + data
	return_code = this->i->vme_A32D32_write(this->baseaddress + SIS3316_NIM_CLK_MULTIPLIER_SPI_REG, write_data ); //  
	if (return_code != 0) {	return -1 ;	}
		usleep(10000) ;

	poll_counter = 0 ;
	do {
		poll_counter++;
		this->i->vme_A32D32_read(this->baseaddress + SIS3316_NIM_CLK_MULTIPLIER_SPI_REG, &read_data ); //  
	} while (((read_data & 0x80000000) == 0x80000000) && (poll_counter < SI5325_SPI_POLL_COUNTER_MAX)) ;
	if (poll_counter == SI5325_SPI_POLL_COUNTER_MAX) {	return -2 ;	}
	//*data = (read_data & 0xff) ;
	*data = (read_data ) ;
	return (0) ;
}
/****************************************************************************************************/


int sis3316_adc::si5325_clk_muliplier_internal_calibration_cmd(void)  
{
	unsigned int return_code ;
	unsigned int write_data, read_data ;
	unsigned int poll_counter, cal_poll_counter  ;
// write address
	write_data = 0x0000 + 136 ; // write ADDR Instruction + register addr
	return_code = this->i->vme_A32D32_write(this->baseaddress + SIS3316_NIM_CLK_MULTIPLIER_SPI_REG, write_data ); //  
	if (return_code != 0) {	return -1 ;	}

	poll_counter = 0 ;
	do {
		poll_counter++;
		this->i->vme_A32D32_read(this->baseaddress + SIS3316_NIM_CLK_MULTIPLIER_SPI_REG, &read_data ); //  
	} while (((read_data & 0x80000000) == 0x80000000) && (poll_counter < SI5325_SPI_POLL_COUNTER_MAX)) ;
	if (poll_counter == SI5325_SPI_POLL_COUNTER_MAX) {	return -2 ;	}

// write data
	write_data = 0x4000 + 0x40 ; // write Instruction + data
	return_code = this->i->vme_A32D32_write(this->baseaddress + SIS3316_NIM_CLK_MULTIPLIER_SPI_REG, write_data ); //  
	if (return_code != 0) {	return -1 ;	}

	poll_counter = 0 ;
	do {
		poll_counter++;
		this->i->vme_A32D32_read(this->baseaddress + SIS3316_NIM_CLK_MULTIPLIER_SPI_REG, &read_data ); //  
	} while (((read_data & 0x80000000) == 0x80000000) && (poll_counter < SI5325_SPI_POLL_COUNTER_MAX)) ;
	if (poll_counter == SI5325_SPI_POLL_COUNTER_MAX) {	return -2 ;	}

// poll until Calibration is ready 
	cal_poll_counter = 0 ;
	do {
		cal_poll_counter++;
		// read data
		write_data = 0x8000  ; // read Instruction + data
		return_code = this->i->vme_A32D32_write(this->baseaddress + SIS3316_NIM_CLK_MULTIPLIER_SPI_REG, write_data ); //  
		if (return_code != 0) {	return -1 ;	}

		poll_counter = 0 ;
		do {
			poll_counter++;
			this->i->vme_A32D32_read(this->baseaddress + SIS3316_NIM_CLK_MULTIPLIER_SPI_REG, &read_data ); //  
		} while (((read_data & 0x80000000) == 0x80000000) && (poll_counter < SI5325_SPI_POLL_COUNTER_MAX)) ;
		if (poll_counter == SI5325_SPI_POLL_COUNTER_MAX) {	return -2 ;	}

	} while (((read_data & 0x40) == 0x40) && (cal_poll_counter < SI5325_SPI_CALIBRATION_READY_POLL_COUNTER_MAX)) ;
	if (cal_poll_counter == SI5325_SPI_CALIBRATION_READY_POLL_COUNTER_MAX) {	return -3 ;	}

	return 0 ;
}

/****************************************************************************************************/


int sis3316_adc::get_status_external_clock_multiplier(unsigned int *status  ){
	int rc;
	unsigned int data ;
	rc = si5325_clk_muliplier_read( 128, &data); //  
	*status = data & 0x1 ;
	rc = si5325_clk_muliplier_read( 129, &data); //  
	*status = *status + (data & 0x2) ;
	return rc ;
}
/****************************************************************************************************/

int sis3316_adc::bypass_external_clock_multiplier(void ){
	int rc;
	rc = si5325_clk_muliplier_write( 0, 0x2); // Bypass 
	rc = si5325_clk_muliplier_write(11, 0x02); //  PowerDown clk2 
	return rc ;
}
/****************************************************************************************************/

int sis3316_adc::set_external_clock_multiplier(unsigned int bw_sel, unsigned int n1_hs, unsigned int n1_clk1, unsigned int n1_clk2, unsigned int n2, unsigned int n3, unsigned int clkin1_mhz ){
	volatile unsigned int n1_val ;
	volatile unsigned int n1_hs_val ;
	volatile unsigned int n2_val ;
	volatile unsigned int n3_val ;

	// input frequency
	if ((clkin1_mhz < 10) || (clkin1_mhz > 250)) {
		return -2 ;
	}
	// bw_sel : see DSPLLsinm for setting
	if (bw_sel > 15) {
		return -3 ;
	}
	// n1_hs
	if ((n1_hs < 4) || (n1_hs > 11)) {
		return -4 ;
	}


	// n1_clk1
	if (n1_clk1 == 0)  {
		return -5 ;
	}
	else {
		if ((((n1_clk1) & 0x1) == 1) && (n1_clk1 != 1) ) { // odd but not 1
			return -5 ;
		}
		if ((n1_clk1 & 0xfff00000) != 0)  { // > 2**20
			return -5 ;
		}
	}

	// n1_clk2
	if (n1_clk2 == 0)  {
		return -6 ;
	}
	else {
		if ((((n1_clk2) & 0x1) == 1) && (n1_clk2 != 1) ) { // odd but not 1
			return -6 ;
		}
		if ((n1_clk2 & 0xfff00000) != 0)  { // > 2**20
			return -6 ;
		}
	}


	// n2
	if ((n2 < 32) || (n2 > 512)) {
		return -7 ;
	}
	else {
		if ((n2 & 0x1) == 1)  { // odd
			return -7 ;
		}
	}

	// n3
	if (n3 == 0)  {
		return -8 ;
	}
	else {
		if ((n3 & 0xfff80000) != 0)  { // > 2**19
			return -8 ;
		}
	}


	si5325_clk_muliplier_write( 0, 0x0); // No Bypass 
	si5325_clk_muliplier_write(11, 0x02); //  PowerDown clk2 

	// N3 = 1
	n3_val = n3 - 1 ;
	si5325_clk_muliplier_write(43, ((n3_val >> 16) & 0x7) );       //  N3 bits 18:16
	si5325_clk_muliplier_write(44, ((n3_val >> 8) & 0xff));       //  N3 bits 15:8
	si5325_clk_muliplier_write(45, (n3_val  & 0xff) );       //  N3 bits 7:0

	n2_val = n2  ;
	si5325_clk_muliplier_write(40, 0x00);						//    N2_LS bits 19:16
	si5325_clk_muliplier_write(41, ((n2_val >> 8) & 0xff));     //  N2_LS bits 15:8
	si5325_clk_muliplier_write(42, (n2_val  & 0xff));			//  N2_LS bits 7:0

	n1_hs_val = n1_hs - 4 ;
	si5325_clk_muliplier_write(25, (n1_hs_val << 5)); //   

	n1_val = n1_clk1 - 1 ;
	si5325_clk_muliplier_write(31, ((n1_val >> 16) & 0xf));       //  NC1_LS (low speed divider) bits 19:16
	si5325_clk_muliplier_write(32, ((n1_val >> 8) & 0xff));       //  NC1_LS (low speed divider) bits 15:8
	si5325_clk_muliplier_write(33, (n1_val  & 0xff) );       //  NC1_LS (low speed divider) bits 7:0

	n1_val = n1_clk2 - 1 ;
	si5325_clk_muliplier_write(34, ((n1_val >> 16) & 0xf));       //  NC2_LS (low speed divider) bits 19:16
	si5325_clk_muliplier_write(35, ((n1_val >> 8) & 0xff));       //  NC2_LS (low speed divider) bits 15:8
	si5325_clk_muliplier_write(36, (n1_val  & 0xff));       //  NC2_LS (low speed divider) bits 7:0


	si5325_clk_muliplier_write( 2, (bw_sel << 5) ); //BWSEL_REG 

	si5325_clk_muliplier_internal_calibration_cmd();

	return 0;
}
 

/************************************************************************************************************************************************/



// adc_fpga_group: 0,1,2,3
// adc_chip: 0 or 1
//				-1 : not all adc chips have the same chip ID
//				>0 : VME Error Code

int sis3316_adc::adc_spi_setup(void ){
	int return_code;
	unsigned int adc_chip_id;
	unsigned int addr, data;
	unsigned i_adc_fpga_group; 
	unsigned i_adc_chip; 

	// disable ADC output
	for (i_adc_fpga_group = 0; i_adc_fpga_group < 4; i_adc_fpga_group++) {
		addr = SIS3316_ADC_CH1_4_SPI_CTRL_REG +  ((i_adc_fpga_group & 0x3) * SIS3316_FPGA_ADC_REG_OFFSET) ;
		return_code = i->vme_A32D32_write(this->baseaddress + addr, 0x0); //  
		if (return_code != 0) {return return_code ; }
	}


	// dummy loop to access each adc chip one time after power up -- add 12.02.2015
	for (i_adc_fpga_group = 0; i_adc_fpga_group < 4; i_adc_fpga_group++) {
		for (i_adc_chip = 0; i_adc_chip < 2; i_adc_chip++) {
			this->adc_spi_read( i_adc_fpga_group, i_adc_chip, 1, &data);
		}
	}






// reset 
	for (i_adc_fpga_group = 0; i_adc_fpga_group < 4; i_adc_fpga_group++) {
		for (i_adc_chip = 0; i_adc_chip < 2; i_adc_chip++) {
			return_code = this->adc_spi_write( i_adc_fpga_group, i_adc_chip, 0x0, 0x24); // soft reset
		}
		 usleep(10) ; // after reset
	}

	return_code = this->adc_spi_read( 0, 0, 1, &adc_chip_id); // read chip Id from adc chips ch1/2

	for (i_adc_fpga_group = 0; i_adc_fpga_group < 4; i_adc_fpga_group++) {
		for (i_adc_chip = 0; i_adc_chip < 2; i_adc_chip++) {
			this->adc_spi_read( i_adc_fpga_group, i_adc_chip, 1, &data);
			//printf("i_adc_fpga_group = %d   i_adc_chip = %d    data = 0x%08x     adc_chip_id = 0x%08x     \n", i_adc_fpga_group, i_adc_chip, data, adc_chip_id);
			if (data != adc_chip_id) {
				printf("i_adc_fpga_group = %d   i_adc_chip = %d    data = 0x%08x     adc_chip_id = 0x%08x     \n", i_adc_fpga_group, i_adc_chip, data, adc_chip_id);
				return -1 ;
			}
		}
	}

	this->adc_125MHz_flag = 0;
	if ((adc_chip_id&0xff) == 0x32) {
		this->adc_125MHz_flag = 1;
	}


	// reg 0x14 : Output mode
	if (this->adc_125MHz_flag == 0) { // 250 MHz chip AD9643
		data = 0x04 ; 	//  Output inverted (bit2 = 1)
	}
	else { // 125 MHz chip AD9268
		data = 0x40 ; 	// Output type LVDS (bit6 = 1), Output inverted (bit2 = 0) !
	}
	for (i_adc_fpga_group = 0; i_adc_fpga_group < 4; i_adc_fpga_group++) {
		for (i_adc_chip = 0; i_adc_chip < 2; i_adc_chip++) {
			this->adc_spi_write( i_adc_fpga_group, i_adc_chip, 0x14, data); 
		}
	}
 

// reg 0x18 : Reference Voltage / Input Span
	if (this->adc_125MHz_flag == 0) { // 250 MHz chip AD9643
		data = 0x0 ; 	//  1.75V
	}
	else { // 125 MHz chip AD9268
		//data = 0x8 ; 	//  1.75V
		data = 0xC0 ; 	//  2.0V
	}
	for (i_adc_fpga_group = 0; i_adc_fpga_group < 4; i_adc_fpga_group++) {
		for (i_adc_chip = 0; i_adc_chip < 2; i_adc_chip++) {
			this->adc_spi_write( i_adc_fpga_group, i_adc_chip, 0x18, data); 
		}
	}



// reg 0xff : register update
	data = 0x01 ; 	// update
	for (i_adc_fpga_group = 0; i_adc_fpga_group < 4; i_adc_fpga_group++) {
		for (i_adc_chip = 0; i_adc_chip < 2; i_adc_chip++) {
			this->adc_spi_write( i_adc_fpga_group, i_adc_chip, 0xff, data); 
		}
	}

	// enable ADC output
	for (i_adc_fpga_group = 0; i_adc_fpga_group < 4; i_adc_fpga_group++) {
		addr = SIS3316_ADC_CH1_4_SPI_CTRL_REG +  ((i_adc_fpga_group & 0x3) * SIS3316_FPGA_ADC_REG_OFFSET) ;
		return_code = i->vme_A32D32_write(this->baseaddress + addr, 0x1000000); //  set bit 24
		if (return_code != 0) {return return_code ; }
	}


	return 0 ;
}

/*******************************************************************************/

int sis3316_adc::adc_spi_reg_enable_adc_outputs(void ){
	int return_code;
	unsigned int addr ;
	unsigned i_adc_fpga_group; 

	// enable ADC output
	for (i_adc_fpga_group = 0; i_adc_fpga_group < 4; i_adc_fpga_group++) {
		addr = SIS3316_ADC_CH1_4_SPI_CTRL_REG +  ((i_adc_fpga_group & 0x3) * SIS3316_FPGA_ADC_REG_OFFSET) ;
		return_code = i->vme_A32D32_write(this->baseaddress + addr, 0x1000000); //  set bit 24
		if (return_code != 0) {return return_code ; }
	}

	return 0 ;
}

/*******************************************************************************/

// adc_fpga_group: 0,1,2,3
// adc_chip: 0 or 1
// return codes
//				-1 : invalid parameter
//				-2 : timeout
//				>0 : VME Error Code


//#define TEST_DEBUG
int sis3316_adc::adc_spi_read(unsigned int adc_fpga_group, unsigned int adc_chip, unsigned int spi_addr, unsigned int* spi_data ){
	int return_code;
	unsigned int data ;
	unsigned int addr ;
	unsigned int uint_adc_mux_select;
	unsigned int pollcounter;

	pollcounter = 1000;

	if (adc_fpga_group > 4) {return -1;}
	if (adc_chip > 2) {return -1;}
	if (spi_addr > 0x1fff) {return -1;}

	if (adc_chip == 0) {
		uint_adc_mux_select = 0 ;	// adc chip ch1/ch2	
	}
	else {
		uint_adc_mux_select = 0x400000 ; // adc chip ch3/ch4 		
	}

	// read register to get the information of bit 24 (adc output enabled)
	addr = SIS3316_ADC_CH1_4_SPI_CTRL_REG +  ((adc_fpga_group & 0x3) * SIS3316_FPGA_ADC_REG_OFFSET) ;
	return_code = i->vme_A32D32_read(this->baseaddress + addr, &data); //  
	if (return_code != 0) {
		#ifdef TEST_DEBUG
			printf("adc_spi_read vme_A32D32_read 1: return_code = 0x%08x     \n", return_code);
		#endif
		return return_code ; 
	}
	data = data & 0x01000000 ; // save bit 24


	data =  data + 0xC0000000 + uint_adc_mux_select + ((spi_addr & 0x1fff) << 8)  ;
	addr = SIS3316_ADC_CH1_4_SPI_CTRL_REG +  ((adc_fpga_group & 0x3) * SIS3316_FPGA_ADC_REG_OFFSET) ;
	return_code = i->vme_A32D32_write(this->baseaddress + addr, data); //  
	#ifdef TEST_DEBUG
	if (return_code != 0) {
			printf("adc_spi_read vme_A32D32_write 1: return_code = 0x%08x     \n", return_code);
	}
	#endif


	addr = SIS3316_ADC_FPGA_SPI_BUSY_STATUS_REG ;
	do { // the logic is appr. 20us busy 
		return_code = i->vme_A32D32_read(this->baseaddress + addr, &data); //  
		#ifdef TEST_DEBUG
		if (return_code != 0) {
			printf("adc_spi_read vme_A32D32_read 2: return_code = 0x%08x     \n", return_code);
		}
		#endif
		pollcounter--;
	//} while (((data & 0x80000000) == 0x80000000) && (pollcounter > 0) && (return_code == 0)); // VME FPGA Version 0x0006 and higher
	} while (((data & 0x0000000f) != 0x00000000) && (pollcounter > 0) && (return_code == 0)); // changed 2.12.2014,  VME FPGA Version 0x0005 and lower
	#ifdef TEST_DEBUG
			printf("adc_spi_read pollcounter: pollcounter = 0x%08x     \n", pollcounter);
	#endif

	if (return_code != 0) {return return_code ; }
	if (pollcounter == 0) {
		return -2 ; 
	}

	usleep(20) ; //

	//addr = SIS3316_ADC_CH1_4_SPI_READBACK_REG  ; // removed 21.01.2015
	addr = SIS3316_ADC_CH1_4_SPI_READBACK_REG +  ((adc_fpga_group & 0x3) * SIS3316_FPGA_ADC_REG_OFFSET) ; // changed 21.01.2015
	return_code = i->vme_A32D32_read(this->baseaddress + addr, &data); //  
	#ifdef TEST_DEBUG
	if (return_code != 0) {
				printf("adc_spi_read vme_A32D32_read 3: return_code = 0x%08x     \n", return_code);
	}
	#endif
	if (return_code != 0) {return return_code ; }

	*spi_data = data & 0xff ;
	return 0 ;
}


int sis3316_adc::adc_spi_write(unsigned int adc_fpga_group, unsigned int adc_chip, unsigned int spi_addr, unsigned int spi_data ){
	volatile int return_code;
	unsigned int data ;
	unsigned int addr ;
	unsigned int uint_adc_mux_select;
	unsigned int pollcounter;
	pollcounter = 1000;

	if (adc_fpga_group > 4) {return -1;}
	if (adc_chip > 2) {return -1;}
	if (spi_addr > 0xffff) {return -1;}

	if (adc_chip == 0) {
		uint_adc_mux_select = 0 ;	// adc chip ch1/ch2	
	}
	else {
		uint_adc_mux_select = 0x400000 ; // adc chip ch3/ch4 		
	}

	// read register to get the information of bit 24 (adc output enabled)
	addr = SIS3316_ADC_CH1_4_SPI_CTRL_REG +  ((adc_fpga_group & 0x3) * SIS3316_FPGA_ADC_REG_OFFSET) ;
	return_code = i->vme_A32D32_read(this->baseaddress + addr, &data); //  
	if (return_code != 0) {return return_code ; }
	data = data & 0x01000000 ; // save bit 24

	data =  data + 0x80000000 + uint_adc_mux_select + ((spi_addr & 0xffff) << 8) + (spi_data & 0xff) ;
	addr = SIS3316_ADC_CH1_4_SPI_CTRL_REG +  ((adc_fpga_group & 0x3) * SIS3316_FPGA_ADC_REG_OFFSET) ;
	return_code = i->vme_A32D32_write(this->baseaddress + addr, data); //  

	//usleep(1000) ; //

	addr = SIS3316_ADC_FPGA_SPI_BUSY_STATUS_REG ;
	//printf("poll_on_spi_busy: pollcounter = 0x%08x    \n", pollcounter );
	do { // the logic is appr. 20us busy
		return_code = i->vme_A32D32_read(this->baseaddress + addr, &data); //  
		pollcounter--;
	//} while (((data & 0x80000000) == 0x80000000) && (pollcounter > 0) && (return_code == 0)); // VME FPGA Version 0x0006 and higher
	} while (((data & 0x0000000f) != 0x00000000) && (pollcounter > 0) && (return_code == 0)); // changed 2.12.2014,  VME FPGA Version 0x0005 and lower
	//printf("poll_on_spi_busy: pollcounter = 0x%08x   data = 0x%08x   return_code = 0x%08x \n", pollcounter, data, return_code);
	if (return_code != 0) {return return_code ; }
	if (pollcounter == 0) {return -2 ; }
	return 0 ;
}







/******************************************************************************************************************************************************************************/

int sis3316_adc::write_channel_header_ID(unsigned int channel_header_id_reg_value ){
	int return_code;
	unsigned int data ;

	// Channel Header ID register
	data =   channel_header_id_reg_value ;
	return_code = i->vme_A32D32_write(this->baseaddress +  SIS3316_ADC_CH1_4_CHANNEL_HEADER_REG,   data ); //
	if (return_code != 0) {return return_code ; }
	return_code = i->vme_A32D32_write(this->baseaddress +  SIS3316_ADC_CH5_8_CHANNEL_HEADER_REG,   data + 0x400000 ); //
	if (return_code != 0) {return return_code ; }
	return_code = i->vme_A32D32_write(this->baseaddress +  SIS3316_ADC_CH9_12_CHANNEL_HEADER_REG,  data + 0x800000  ); //
	if (return_code != 0) {return return_code ; }
	return_code = i->vme_A32D32_write(this->baseaddress +  SIS3316_ADC_CH13_16_CHANNEL_HEADER_REG, data + 0xC00000  ); //
	if (return_code != 0) {return return_code ; }
	return 0 ;
}
/******************************************************************************************************************************************************************************/


int sis3316_adc::poll_on_adc_dac_offset_busy(void){
	volatile int return_code;
	unsigned int data ;
	unsigned int poll_counter ;

	poll_counter = 1000 ;
	do {
		poll_counter-- ;
		return_code = i->vme_A32D32_read(this->baseaddress + SIS3316_ADC_FPGA_SPI_BUSY_STATUS_REG, &data); //   
	} while ( ((data & 0xf) != 0) && (poll_counter > 0) && (return_code == 0)) ;
	//printf("Error poll_on_adc_dac_offset_busy: poll_counter = 0x%08x \n", poll_counter);
	if (return_code != 0) {return return_code ; }
	if (poll_counter == 0) {return 0x900 ; }
	return 0 ;
}



int sis3316_adc::write_all_adc_dac_offsets(void){
	int return_code;
	unsigned int dac_offset ;
	unsigned int i_adc_fpga_group; 

	for (i_adc_fpga_group=0;i_adc_fpga_group<4;i_adc_fpga_group++) {
		dac_offset = this->adc_dac_offset_ch_array[(i_adc_fpga_group*4) + 0] ;
		return_code = i->vme_A32D32_write(this->baseaddress + (i_adc_fpga_group*SIS3316_FPGA_ADC_REG_OFFSET) + SIS3316_ADC_CH1_4_DAC_OFFSET_CTRL_REG, 0x80000000 + 0x2000000 +  0x000000 + ((dac_offset & 0xffff) << 4) );  // clear error Latch bits
		return_code = this->poll_on_adc_dac_offset_busy(); 
		if (return_code != 0) {return return_code ; }

		dac_offset = this->adc_dac_offset_ch_array[(i_adc_fpga_group*4) + 1] ;
		return_code = i->vme_A32D32_write(this->baseaddress + (i_adc_fpga_group*SIS3316_FPGA_ADC_REG_OFFSET) + SIS3316_ADC_CH1_4_DAC_OFFSET_CTRL_REG, 0x80000000 + 0x2000000 +  0x100000 + ((dac_offset & 0xffff) << 4) );  // clear error Latch bits
		return_code = this->poll_on_adc_dac_offset_busy(); 
		if (return_code != 0) {return return_code ; }

		dac_offset = this->adc_dac_offset_ch_array[(i_adc_fpga_group*4) + 2] ;
		return_code = i->vme_A32D32_write(this->baseaddress + (i_adc_fpga_group*SIS3316_FPGA_ADC_REG_OFFSET) + SIS3316_ADC_CH1_4_DAC_OFFSET_CTRL_REG, 0x80000000 + 0x2000000 +  0x200000 + ((dac_offset & 0xffff) << 4) );  // clear error Latch bits
		return_code = this->poll_on_adc_dac_offset_busy(); 
		if (return_code != 0) {return return_code ; }

		dac_offset = this->adc_dac_offset_ch_array[(i_adc_fpga_group*4) + 3] ;
		return_code = i->vme_A32D32_write(this->baseaddress + (i_adc_fpga_group*SIS3316_FPGA_ADC_REG_OFFSET) + SIS3316_ADC_CH1_4_DAC_OFFSET_CTRL_REG, 0x80000000 + 0x2000000 +  0x300000 + ((dac_offset & 0xffff) << 4) );  // clear error Latch bits
		return_code = this->poll_on_adc_dac_offset_busy(); 
		if (return_code != 0) {return return_code ; }


		return_code = i->vme_A32D32_write(this->baseaddress +  (i_adc_fpga_group*SIS3316_FPGA_ADC_REG_OFFSET) + SIS3316_ADC_CH1_4_DAC_OFFSET_CTRL_REG, 0xC0000000 );  // CMD: DAC LDAC (load) 
		return_code = this->poll_on_adc_dac_offset_busy(); 
		if (return_code != 0) {return return_code ; }
	}

	return 0 ;
}


int sis3316_adc::configure_all_adc_dac_offsets(void ){
	int return_code;
	unsigned int dac_offset ;
	unsigned int i_adc_fpga_group; 

	for (i_adc_fpga_group=0;i_adc_fpga_group<4;i_adc_fpga_group++) {
		dac_offset = this->adc_dac_offset_ch_array[(i_adc_fpga_group*4) + 0] ;
		return_code = i->vme_A32D32_write(this->baseaddress + (i_adc_fpga_group*SIS3316_FPGA_ADC_REG_OFFSET) + SIS3316_ADC_CH1_4_DAC_OFFSET_CTRL_REG, 0x80000000 + 0x8000000 +  0xf00000 + 0x1); // Standalone mode, set Internal Reference 
		if (return_code != 0) {return return_code ; }
		return_code = this->poll_on_adc_dac_offset_busy(); 
		if (return_code != 0) {return return_code ; }

		return_code = i->vme_A32D32_write(this->baseaddress +  (i_adc_fpga_group*SIS3316_FPGA_ADC_REG_OFFSET) + SIS3316_ADC_CH1_4_DAC_OFFSET_CTRL_REG, 0xC0000000 );  // CMD: DAC LDAC (load) 
		if (return_code != 0) {return return_code ; }
		return_code = this->poll_on_adc_dac_offset_busy(); 
		if (return_code != 0) {return return_code ; }
	}

	return 0 ;
}


/******************************************************************************************************************************************************************************/



int sis3316_adc::write_all_gain_termination_values(void){
	int return_code;
	unsigned int gain_termintion_reg_value ;
	unsigned int i_adc_fpga_group; 

	for (i_adc_fpga_group=0; i_adc_fpga_group<4; i_adc_fpga_group++) {
		gain_termintion_reg_value = (this->adc_gain_termination_ch_array[(i_adc_fpga_group*4) + 0] & 0xff) ; // ch 1, 5, 9, 13
		gain_termintion_reg_value = gain_termintion_reg_value + ((this->adc_gain_termination_ch_array[(i_adc_fpga_group*4) + 1] & 0xff) << 8) ; // ch 2, 6, 10, 14
		gain_termintion_reg_value = gain_termintion_reg_value + ((this->adc_gain_termination_ch_array[(i_adc_fpga_group*4) + 2] & 0xff) << 16) ; // ch 3, 7, 11, 15
		gain_termintion_reg_value = gain_termintion_reg_value + ((this->adc_gain_termination_ch_array[(i_adc_fpga_group*4) + 3] & 0xff) << 24) ; // ch 4, 8, 12, 16
		return_code = i->vme_A32D32_write(this->baseaddress + (i_adc_fpga_group*SIS3316_FPGA_ADC_REG_OFFSET) + SIS3316_ADC_CH1_4_ANALOG_CTRL_REG, gain_termintion_reg_value); // 
		if (return_code != 0) {return return_code ; }
	}
	return 0 ;
}
/******************************************************************************************************************************************************************************/
int sis3316_adc::write_nim_output_selection_values(void){
	int return_code;
		return_code = i->vme_A32D32_write(this->baseaddress + SIS3316_LEMO_OUT_CO_SELECT_REG, nim_output_selection_array[0]); // 
		if (return_code != 0) {return return_code ; }
		return_code = i->vme_A32D32_write(this->baseaddress + SIS3316_LEMO_OUT_TO_SELECT_REG, nim_output_selection_array[1]); // 
		if (return_code != 0) {return return_code ; }
		return_code = i->vme_A32D32_write(this->baseaddress + SIS3316_LEMO_OUT_UO_SELECT_REG, nim_output_selection_array[2]); // 
		if (return_code != 0) {return return_code ; }
	return 0 ;
}

/******************************************************************************************************************************************************************************/




int sis3316_adc::internal_sum_trigger_generation_setup(unsigned int uint_sum_trigger_threshold_reg, unsigned int uint_sum_he_trigger_threshold_reg, unsigned int uint_sum_trigger_setup_reg, unsigned int adc_fpga_group /* 0 to 3 */ ){

	int return_code;
	if(adc_fpga_group > 3) {return 0x900 ; }
	return_code = i->vme_A32D32_write(this->baseaddress + (adc_fpga_group*SIS3316_FPGA_ADC_REG_OFFSET) + SIS3316_ADC_CH1_4_SUM_FIR_TRIGGER_SETUP_REG, 0); // //  clear FIR Trigger Setup -> a following Setup will reset the logic ! 
	if (return_code != 0) {return return_code ; }
	return_code = i->vme_A32D32_write(this->baseaddress + (adc_fpga_group*SIS3316_FPGA_ADC_REG_OFFSET) + SIS3316_ADC_CH1_4_SUM_FIR_TRIGGER_THRESHOLD_REG, 0); // // disable all ch_sum
	if (return_code != 0) {return return_code ; }

	return_code = i->vme_A32D32_write(this->baseaddress + (adc_fpga_group*SIS3316_FPGA_ADC_REG_OFFSET) + SIS3316_ADC_CH1_4_SUM_FIR_HIGH_ENERGY_THRESHOLD_REG, uint_sum_he_trigger_threshold_reg); // //   
	if (return_code != 0) {return return_code ; }
	return_code = i->vme_A32D32_write(this->baseaddress + (adc_fpga_group*SIS3316_FPGA_ADC_REG_OFFSET) + SIS3316_ADC_CH1_4_SUM_FIR_TRIGGER_THRESHOLD_REG, uint_sum_trigger_threshold_reg); // //   
	if (return_code != 0) {return return_code ; }
	return_code = i->vme_A32D32_write(this->baseaddress + (adc_fpga_group*SIS3316_FPGA_ADC_REG_OFFSET) + SIS3316_ADC_CH1_4_SUM_FIR_TRIGGER_SETUP_REG, uint_sum_trigger_setup_reg); // //   
	if (return_code != 0) {return return_code ; }

	return 0 ;
}

int sis3316_adc::internal_trigger_generation_setup(unsigned int uint_trigger_threshold_reg, unsigned int uint_he_trigger_threshold_reg, unsigned int uint_trigger_setup_reg, unsigned int channel_no /* 0 to 15 */){

	int return_code;
	if(channel_no > 15) {return 0x900 ; }
	return_code = i->vme_A32D32_write(this->baseaddress + (((channel_no >> 2) & 0x3)*SIS3316_FPGA_ADC_REG_OFFSET) + (SIS3316_ADC_CH1_FIR_TRIGGER_SETUP_REG + ((channel_no  & 0x3) * 0x10)), 0); // //  clear FIR Trigger Setup -> a following Setup will reset the logic ! 
	if (return_code != 0) {return return_code ; }
	return_code = i->vme_A32D32_write(this->baseaddress + (((channel_no >> 2) & 0x3)*SIS3316_FPGA_ADC_REG_OFFSET) + (SIS3316_ADC_CH1_FIR_TRIGGER_THRESHOLD_REG + ((channel_no  & 0x3) * 0x10)), 0); // // disable all ch_sum
	if (return_code != 0) {return return_code ; }

	return_code = i->vme_A32D32_write(this->baseaddress + (((channel_no >> 2) & 0x3)*SIS3316_FPGA_ADC_REG_OFFSET) + (SIS3316_ADC_CH1_FIR_HIGH_ENERGY_THRESHOLD_REG + ((channel_no  & 0x3) * 0x10)), uint_he_trigger_threshold_reg); // //   
	if (return_code != 0) {return return_code ; }
	return_code = i->vme_A32D32_write(this->baseaddress + (((channel_no >> 2) & 0x3)*SIS3316_FPGA_ADC_REG_OFFSET) + (SIS3316_ADC_CH1_FIR_TRIGGER_THRESHOLD_REG + ((channel_no  & 0x3) * 0x10)), uint_trigger_threshold_reg); // //   
	if (return_code != 0) {return return_code ; }
	return_code = i->vme_A32D32_write(this->baseaddress + (((channel_no >> 2) & 0x3)*SIS3316_FPGA_ADC_REG_OFFSET) + (SIS3316_ADC_CH1_FIR_TRIGGER_SETUP_REG + ((channel_no  & 0x3) * 0x10)), uint_trigger_setup_reg); // //   
	if (return_code != 0) {return return_code ; }

	return 0 ;
}



/******************************************************************************************************************************************************************************/
int sis3316_adc::read_MBLT64_Channel_PreviousBankDataBuffer(unsigned int bank2_read_flag, unsigned int channel_no /* 0 to 15 */,
							 unsigned int*  dma_got_no_of_words, unsigned int* uint_adc_buffer ){
	int return_code;
	unsigned int  max_read_nof_words;
	max_read_nof_words = 0xffffff ;
	return_code = this->read_DMA_Channel_PreviousBankDataBuffer(bank2_read_flag, channel_no, max_read_nof_words, dma_got_no_of_words, uint_adc_buffer ) ;

	return return_code ;
}



int sis3316_adc::read_DMA_Channel_PreviousBankDataBuffer(unsigned int bank2_read_flag, unsigned int channel_no /* 0 to 15 */,
		unsigned int  max_read_nof_words, unsigned int*  dma_got_no_of_words, unsigned int* uint_adc_buffer ){
	int return_code;
	unsigned int data ;
	unsigned int addr ;
	unsigned int previous_bank_addr_value ;
	unsigned int req_nof_32bit_words ;
	unsigned int got_nof_32bit_words ;
	unsigned int memory_bank_offset_addr ;
	unsigned int max_poll_counter ;
	
	// read previous Bank sample address
	// poll until it is valid.
	addr = SIS3316_ADC_CH1_PREVIOUS_BANK_SAMPLE_ADDRESS_REG + ((channel_no & 0x3) * 4) + (((channel_no >> 2) & 0x3) * SIS3316_FPGA_ADC_REG_OFFSET) ;
	max_poll_counter = 10000;
	*dma_got_no_of_words = 0;
	do {
		return_code = i->vme_A32D32_read(this->baseaddress + addr, &previous_bank_addr_value); //  
		//return_code = i->vme_A32D32_read(this->baseaddress + addr, &previous_bank_addr_value); //  only if version VME _V0002
		if(return_code != 0) { 
			printf("Error: vme_A32D32_read: return_code = 0x%08x   addr = 0x%08x \n", return_code,  this->baseaddress + addr);
			return return_code;
		}
		max_poll_counter--;
		if (max_poll_counter == 0) { 
			printf("Error: max_poll_counter = 0x%08x   \n", max_poll_counter);
			return 0x900;
		}
	} while (((previous_bank_addr_value & 0x1000000) >> 24 )  != bank2_read_flag) ; // previous Bank sample address is valid if bit 24 is equal bank2_read_flag 

	if((previous_bank_addr_value & 0xffffff) == 0) { // no data sampled !
		*dma_got_no_of_words = 0;
		return 0;	
	} 

	// start Readout FSM
	if (bank2_read_flag == 1) {		
		memory_bank_offset_addr = 0x01000000; // Bank2 offset
	}
	else {
		memory_bank_offset_addr = 0x00000000; // Bank1 offset
	}

	if ((channel_no & 0x1) != 0x1) { // 0,1 	
		memory_bank_offset_addr = memory_bank_offset_addr + 0x00000000; // channel 1 , 3, ..... 15
	}
	else {
		memory_bank_offset_addr = memory_bank_offset_addr + 0x02000000; // channel 2 , 4, ..... 16
	}

	if ((channel_no & 0x2) != 0x2) { // 0,2 	
		memory_bank_offset_addr = memory_bank_offset_addr + 0x00000000; // channel 0,1 , 4,5, .....
	}
	else {
		memory_bank_offset_addr = memory_bank_offset_addr + 0x10000000; // channel 2,3 , 6,7 ..... 
	}


	// in case of using ETHERNET_UDP_INTERFACE it is possible to lose packets (observed with WIN7 using a "company-net", not observed with WIN7 and direct connection and not observed with LINUX)
	// 
	unsigned int retry_counter = 0 ;
	unsigned int retry_flag = 0 ;

	do {
			addr = SIS3316_DATA_TRANSFER_CH1_4_CTRL_REG + (((channel_no >> 2) & 0x3) * 4) ;
			data = 0x80000000 + memory_bank_offset_addr ;
			return_code = i->vme_A32D32_write(this->baseaddress + addr, data);
			if(return_code != 0) { 
				//	printf("Error: vme_A32D32_write: return_code = 0x%08x   addr = 0x%08x  data = 0x%08x \n", return_code,  this->baseaddress + addr, data);
				//return return_code;
			}
			else {
				// readout 
				addr = SIS3316_FPGA_ADC1_MEM_BASE + (((channel_no >> 2) & 0x3 )* SIS3316_FPGA_ADC_MEM_OFFSET)  ;

				req_nof_32bit_words = previous_bank_addr_value & 0xffffff ;
				if (req_nof_32bit_words > max_read_nof_words){
					req_nof_32bit_words = max_read_nof_words ;
				}
				return_code = i->vme_A32MBLT64FIFO_read(this->baseaddress + addr, uint_adc_buffer, ((req_nof_32bit_words + 1) & 0xfffffE) , &got_nof_32bit_words); // N * 8-byte length  !!! 
				if(return_code != 0) { 
						//printf("Error: vme_A32MBLT64FIFO_read: return_code = 0x%08x   addr = 0x%08x  req_nof_32bit_words = 0x%08x \n", return_code,  this->baseaddress + addr, req_nof_32bit_words);
					//return return_code;
				}
				*dma_got_no_of_words = req_nof_32bit_words ;
			}
			retry_flag = 0 ;	
			if(return_code != 0) { 
				retry_counter++ ;
				retry_flag = 0 ;	
				if (retry_counter < 16) {
					retry_flag = 1 ;	
				}
				if (retry_counter > 1) {
					printf("Info: retry_counter = %d \n", retry_counter);
				}
			}

			// reset FSM again
			addr = SIS3316_DATA_TRANSFER_CH1_4_CTRL_REG + (((channel_no >> 2) & 0x3) * 4) ;
			data = 0x00000000  ; // Reset
			return_code = i->vme_A32D32_write(this->baseaddress + addr, data);
			if(return_code != 0) { 
				//printf("Error: vme_A32D32_write: return_code = 0x%08x   addr = 0x%08x  data = 0x%08x \n", return_code,  this->baseaddress + addr, data);
				//return return_code;
			}

	} while (retry_flag==1) ; 


	
	if (retry_counter > 15) {
		return -1 ;
	}

	return 0 ;
}
	
	

/****************************************************************************************************/


int sis3316_adc::read_Channel_PreviousSampleAddress(unsigned int bank2_read_flag, unsigned int channel_no /* 0 to 15 */, unsigned int*  previous_sample_address ){
	int return_code;
	//unsigned int data ;
	unsigned int addr ;
	unsigned int previous_bank_addr_value ;
	//unsigned int req_nof_32bit_words ;
	//unsigned int got_nof_32bit_words ;
	//unsigned int memory_bank_offset_addr ;
	unsigned int max_poll_counter ;

	// read previous Bank sample address
	// poll until it is valid.
	addr = SIS3316_ADC_CH1_PREVIOUS_BANK_SAMPLE_ADDRESS_REG + ((channel_no & 0x3) * 4) + (((channel_no >> 2) & 0x3) * SIS3316_FPGA_ADC_REG_OFFSET) ;
	max_poll_counter = 10000;
	*previous_sample_address = 0;
	do {
		return_code = i->vme_A32D32_read(this->baseaddress + addr, &previous_bank_addr_value); //
		if(return_code != 0) { return return_code;}
		max_poll_counter--;
		if (max_poll_counter == 0) {
			return 0x900;
		}
	} while (((previous_bank_addr_value & 0x1000000) >> 24 )  != bank2_read_flag) ; // previous Bank sample address is valid if bit 24 is equal bank2_read_flag
	*previous_sample_address = ( previous_bank_addr_value & 0xffffff);


	return 0 ;
}






/****************************************************************************************************/

int sis3316_adc::read_Channel_EnergyHistogramBuffer(unsigned int channel_no /* 0 to 15 */, unsigned int lenght, unsigned int* uint_adc_buffer ){
	int return_code;
	unsigned int data ;
	unsigned int addr ;
	unsigned int req_nof_32bit_words ;
	unsigned int got_nof_32bit_words ;
	unsigned int memory_bank_offset_addr ;
//	unsigned int max_poll_counter ;
	
	memory_bank_offset_addr = 0x00FF0000; // Histogram offset

	if ((channel_no & 0x1) != 0x1) { // 0,1 	
		memory_bank_offset_addr = memory_bank_offset_addr + 0x00000000; // channel 1 , 3, ..... 15
	}
	else {
		memory_bank_offset_addr = memory_bank_offset_addr + 0x02000000; // channel 2 , 4, ..... 16
	}

	if ((channel_no & 0x2) != 0x2) { // 0,2 	
		memory_bank_offset_addr = memory_bank_offset_addr + 0x00000000; // channel 0,1 , 4,5, .....
	}
	else {
		memory_bank_offset_addr = memory_bank_offset_addr + 0x10000000; // channel 2,3 , 6,7 ..... 
	}

	addr = SIS3316_DATA_TRANSFER_CH1_4_CTRL_REG + (((channel_no >> 2) & 0x3) * 4) ;
	data = 0x80000000 + memory_bank_offset_addr ;
	return_code = i->vme_A32D32_write(this->baseaddress + addr, data);
	if(return_code != 0) { return return_code;}

	// readout 
	addr = SIS3316_FPGA_ADC1_MEM_BASE + (((channel_no >> 2) & 0x3 )* SIS3316_FPGA_ADC_MEM_OFFSET)  ;
	req_nof_32bit_words = lenght   ;
	return_code = i->vme_A32MBLT64FIFO_read(this->baseaddress + addr, uint_adc_buffer, ((req_nof_32bit_words + 1) & 0xfffffE) , &got_nof_32bit_words); // N * 8-byte length  !!! 
	if(return_code != 0) { return return_code;}


// new
	addr = SIS3316_DATA_TRANSFER_CH1_4_CTRL_REG + (((channel_no >> 2) & 0x3) * 4) ;
	data = 0x00000000  ; // Reset
	return_code = i->vme_A32D32_write(this->baseaddress + addr, data);
	if(return_code != 0) { return return_code;}


	return 0 ;
}
	







/************************************************************************************************************************************************/
/************************************************************************************************************************************************/
/************************************************************************************************************************************************/
/*                                                                                                                                              */
/*  read_Channel_TofHistogramBuffer requires the ADC-FPGA Firmware V_0101 (SIS3316-14bit-250MHz)                                                */
/*                                                                                                                                              */
int sis3316_adc::read_Channel_TofHistogramBuffer(unsigned int channel_no /* 0 to 15 */, int histogram_index, unsigned int lenght, unsigned int* uint_buffer ){
	int return_code;
	unsigned int data ;
	unsigned int addr ;
	unsigned int req_nof_32bit_words ;
	unsigned int got_nof_32bit_words ;
	unsigned int memory_bank_offset_addr ;
//	unsigned int max_poll_counter ;

	if(histogram_index == 0) {
		memory_bank_offset_addr = 0x00C00000; // Histogram offset Beam On
	}
	else {
		memory_bank_offset_addr = 0x00D00000; // Histogram offset Beam OFF
	}

	if ((channel_no & 0x1) != 0x1) { // 0,1
		memory_bank_offset_addr = memory_bank_offset_addr + 0x00000000; // channel 1 , 3, ..... 15
	}
	else {
		memory_bank_offset_addr = memory_bank_offset_addr + 0x02000000; // channel 2 , 4, ..... 16
	}

	if ((channel_no & 0x2) != 0x2) { // 0,2
		memory_bank_offset_addr = memory_bank_offset_addr + 0x00000000; // channel 0,1 , 4,5, .....
	}
	else {
		memory_bank_offset_addr = memory_bank_offset_addr + 0x10000000; // channel 2,3 , 6,7 .....
	}

	addr = SIS3316_DATA_TRANSFER_CH1_4_CTRL_REG + (((channel_no >> 2) & 0x3) * 4) ;
	data = 0x80000000 + memory_bank_offset_addr ;
	return_code = i->vme_A32D32_write(this->baseaddress + addr, data);
	if(return_code != 0) { return return_code;}

	// readout
	addr = SIS3316_FPGA_ADC1_MEM_BASE + (((channel_no >> 2) & 0x3 )* SIS3316_FPGA_ADC_MEM_OFFSET)  ;
	req_nof_32bit_words = lenght   ;
	return_code = i->vme_A32MBLT64FIFO_read(this->baseaddress + addr, uint_buffer, ((req_nof_32bit_words + 1) & 0xfffffE) , &got_nof_32bit_words); // N * 8-byte length  !!!
	if(return_code != 0) { return return_code;}


// new
	addr = SIS3316_DATA_TRANSFER_CH1_4_CTRL_REG + (((channel_no >> 2) & 0x3) * 4) ;
	data = 0x00000000  ; // Reset
	return_code = i->vme_A32D32_write(this->baseaddress + addr, data);
	if(return_code != 0) { return return_code;}


	return 0 ;
}






/************************************************************************************************************************************************/
/************************************************************************************************************************************************/
/************************************************************************************************************************************************/
/*                                                                                                                                              */
/*  read_Channel_ShapeHistogramBuffer requires the ADC-FPGA Firmware V_0101 (SIS3316-14bit-250MHz)                                              */
/*                                                                                                                                              */

int sis3316_adc::read_Channel_ShapeHistogramBuffer(unsigned int channel_no /* 0 to 15 */, int histogram_index, unsigned int lenght, unsigned int* uint_buffer ){
	int return_code;
	unsigned int data ;
	unsigned int addr ;
	unsigned int req_nof_32bit_words ;
	unsigned int got_nof_32bit_words ;
	unsigned int memory_bank_offset_addr ;
//	unsigned int max_poll_counter ;

	if(histogram_index == 0) {
		memory_bank_offset_addr = 0x00E00000; // Histogram offset Beam On
	}
	else {
		memory_bank_offset_addr = 0x00E40000; // Histogram offset Beam OFF
	}

	if ((channel_no & 0x1) != 0x1) { // 0,1
		memory_bank_offset_addr = memory_bank_offset_addr + 0x00000000; // channel 1 , 3, ..... 15
	}
	else {
		memory_bank_offset_addr = memory_bank_offset_addr + 0x02000000; // channel 2 , 4, ..... 16
	}

	if ((channel_no & 0x2) != 0x2) { // 0,2
		memory_bank_offset_addr = memory_bank_offset_addr + 0x00000000; // channel 0,1 , 4,5, .....
	}
	else {
		memory_bank_offset_addr = memory_bank_offset_addr + 0x10000000; // channel 2,3 , 6,7 .....
	}

	addr = SIS3316_DATA_TRANSFER_CH1_4_CTRL_REG + (((channel_no >> 2) & 0x3) * 4) ;
	data = 0x80000000 + memory_bank_offset_addr ;
	return_code = i->vme_A32D32_write(this->baseaddress + addr, data);
	if(return_code != 0) { return return_code;}

	// readout
	addr = SIS3316_FPGA_ADC1_MEM_BASE + (((channel_no >> 2) & 0x3 )* SIS3316_FPGA_ADC_MEM_OFFSET)  ;
	req_nof_32bit_words = lenght   ;
	//printf("req_nof_32bit_words    = %d     \n", req_nof_32bit_words);

	return_code = i->vme_A32MBLT64FIFO_read(this->baseaddress + addr, uint_buffer, ((req_nof_32bit_words + 1) & 0xfffffE) , &got_nof_32bit_words); // N * 8-byte length  !!!
	if(return_code != 0) { return return_code;}


// new
	addr = SIS3316_DATA_TRANSFER_CH1_4_CTRL_REG + (((channel_no >> 2) & 0x3) * 4) ;
	data = 0x00000000  ; // Reset
	return_code = i->vme_A32D32_write(this->baseaddress + addr, data);
	if(return_code != 0) { return return_code;}


	return 0 ;
}

/************************************************************************************************************************************************/
/************************************************************************************************************************************************/
/************************************************************************************************************************************************/
/************************************************************************************************************************************************/
/*                                                                                                                                              */
/*  read_Channel_ChargeHistogramBuffer requires the ADC-FPGA Firmware V_0101 (SIS3316-14bit-250MHz)                                             */
/*                                                                                                                                              */

int sis3316_adc::read_Channel_ChargeHistogramBuffer(unsigned int channel_no /* 0 to 15 */, int histogram_index, unsigned int lenght, unsigned int* uint_buffer ){
	int return_code;
	unsigned int data ;
	unsigned int addr ;
	unsigned int req_nof_32bit_words ;
	unsigned int got_nof_32bit_words ;
	unsigned int memory_bank_offset_addr ;
//	unsigned int max_poll_counter ;

	if(histogram_index == 0) {
		memory_bank_offset_addr = 0x00F00000; // Histogram offset Beam On
	}
	else {
		memory_bank_offset_addr = 0x00F10000; // Histogram offset Beam OFF
	}

	if ((channel_no & 0x1) != 0x1) { // 0,1
		memory_bank_offset_addr = memory_bank_offset_addr + 0x00000000; // channel 1 , 3, ..... 15
	}
	else {
		memory_bank_offset_addr = memory_bank_offset_addr + 0x02000000; // channel 2 , 4, ..... 16
	}

	if ((channel_no & 0x2) != 0x2) { // 0,2
		memory_bank_offset_addr = memory_bank_offset_addr + 0x00000000; // channel 0,1 , 4,5, .....
	}
	else {
		memory_bank_offset_addr = memory_bank_offset_addr + 0x10000000; // channel 2,3 , 6,7 .....
	}

	addr = SIS3316_DATA_TRANSFER_CH1_4_CTRL_REG + (((channel_no >> 2) & 0x3) * 4) ;
	data = 0x80000000 + memory_bank_offset_addr ;
	return_code = i->vme_A32D32_write(this->baseaddress + addr, data);
	if(return_code != 0) { return return_code;}

	// readout
	addr = SIS3316_FPGA_ADC1_MEM_BASE + (((channel_no >> 2) & 0x3 )* SIS3316_FPGA_ADC_MEM_OFFSET)  ;
	req_nof_32bit_words = lenght   ;
	return_code = i->vme_A32MBLT64FIFO_read(this->baseaddress + addr, uint_buffer, ((req_nof_32bit_words + 1) & 0xfffffE) , &got_nof_32bit_words); // N * 8-byte length  !!!
	if(return_code != 0) { return return_code;}


// new
	addr = SIS3316_DATA_TRANSFER_CH1_4_CTRL_REG + (((channel_no >> 2) & 0x3) * 4) ;
	data = 0x00000000  ; // Reset
	return_code = i->vme_A32D32_write(this->baseaddress + addr, data);
	if(return_code != 0) { return return_code;}


	return 0 ;
}




/************************************************************************************************************************************************/

sis3316_adc::~sis3316_adc(void)
{
}
/************************************************************************************************************************************************/



#ifdef WIN

void usleep(unsigned int uint_usec)
{
    unsigned int msec;
	if (uint_usec <= 1000) {
		msec = 1 ;
	}
	else {
		msec = (uint_usec+999) / 1000 ;
	}
	Sleep(msec);

}
#endif

