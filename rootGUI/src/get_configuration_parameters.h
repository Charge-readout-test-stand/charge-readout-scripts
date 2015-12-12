/***************************************************************************/
/*                                                                         */
/*  Filename: get_configuration_parameters.h                               */
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

#ifndef GET_CONFIGURATION_PARAMETERS_H_
#define GET_CONFIGURATION_PARAMETERS_H_

/*  SIS3316_root_gui configuration parameters   */


#define TEXT_PARAMETER_STOP_AFTER_NOF_LOOPS_ENABLE 			"PARAMETER_STOP_AFTER_NOF_LOOPS_ENABLE"
#define TEXT_PARAMETER_STOP_AFTER_NOF_LOOPS_VALUE 			"PARAMETER_STOP_AFTER_NOF_LOOPS_VALUE"

#define TEXT_PARAMETER_WRITE_DATA_TO_FILE_ENABLE			"PARAMETER_WRITE_DATA_TO_FILE_ENABLE"
#define TEXT_PARAMETER_WRITE_MULTIPLE_FILES_ENABLE			"PARAMETER_WRITE_MULTIPLE_FILES_ENABLE"
#define TEXT_PARAMETER_APPEND_DATETIME_ENABLE				"PARAMETER_APPEND_DATETIME_ENABLE"
#define TEXT_PARAMETER_WRITE_DATA_TO_FILE_PATH				"PARAMETER_WRITE_DATA_TO_FILE_PATH"

 
#define TEXT_PARAMETER_SAMPLE_CONTROL_MODE 					"PARAMETER_SAMPLE_CONTROL_MODE"
#define TEXT_PARAMETER_SAMPLE_CONTROL_USE_MAX_ENABLE 		"PARAMETER_SAMPLE_CONTROL_USE_MAX_ENABLE"
#define TEXT_PARAMETER_SAMPLE_CONTROL_USE_MAX_VALUE 		"PARAMETER_SAMPLE_CONTROL_USE_MAX_VALUE"


#define TEXT_PARAMETER_PRE_TRIGGER_DELAY   					"PARAMETER_PRE_TRIGGER_DELAY"
#define TEXT_PARAMETER_RAW_SAMPLE_START_INDEX				"PARAMETER_RAW_SAMPLE_START_INDEX"
#define TEXT_PARAMETER_RAW_SAMPLE_LENGTH   					"PARAMETER_RAW_SAMPLE_LENGTH"

//#define TEXT_PARAMETER_CHANNEL_EXTERNAL_TRIGGER_ENABLE   	"PARAMETER_CHANNEL_EXTERNAL_TRIGGER_ENABLE"

//#define TEXT_PARAMETER_MAW_TEST_BUFFER_ENABLE_FLAG 			"PARAMETER_MAW_TEST_BUFFER_ENABLE_FLAG"
#define TEXT_PARAMETER_MAW_TEST_BUFFER_SELECT_ENERGY_FLAG 	"PARAMETER_MAW_TEST_BUFFER_SELECT_ENERGY_FLAG"
#define TEXT_PARAMETER_MAW_TEST_BUFFER_LENGTH   			"PARAMETER_MAW_TEST_BUFFER_LENGTH"
#define TEXT_PARAMETER_MAW_TEST_BUFFER_DELAY   				"PARAMETER_MAW_TEST_BUFFER_DELAY"
#define TEXT_PARAMETER_MAW_TEST_START_INDEX					"PARAMETER_MAW_TEST_START_INDEX"

#define TEXT_PARAMETER_FORMAT_ACCUM_ENABLE					"PARAMETER_FORMAT_ACCUM_ENABLE"
#define TEXT_PARAMETER_FORMAT_MAW_ENABLE					"PARAMETER_FORMAT_MAW_ENABLE"
#define TEXT_PARAMETER_FORMAT_ENERGY_ENABLE					"PARAMETER_FORMAT_ENERGY_ENABLE"


#define TEXT_PARAMETER_TRIGGER_COND_SOFTWARE_KEY			"PARAMETER_TRIGGER_COND_SOFTWARE_KEY"
#define TEXT_PARAMETER_TRIGGER_COND_VME_LEMO_TI				"PARAMETER_TRIGGER_COND_VME_LEMO_TI"
#define TEXT_PARAMETER_TRIGGER_COND_ADC_EXTERNAL			"PARAMETER_TRIGGER_COND_ADC_EXTERNAL"
#define TEXT_PARAMETER_TRIGGER_COND_ADC_INTERNAL			"PARAMETER_TRIGGER_COND_ADC_INTERNAL"
#define TEXT_PARAMETER_TRIGGER_COND_ADC_INTERNAL_SUM		"PARAMETER_TRIGGER_COND_ADC_INTERNAL_SUM"
#define TEXT_PARAMETER_TRIGGER_COND_ADC_INTERNAL_PILEUP		"PARAMETER_TRIGGER_COND_ADC_INTERNAL_PILEUP"


#define TEXT_PARAMETER_CHANNEL_POLARITY_INVERT   			"PARAMETER_CHANNEL_POLARITY_INVERT"
#define TEXT_PARAMETER_CHANNEL_RANGE_2V   					"PARAMETER_CHANNEL_RANGE_2V"
#define TEXT_PARAMETER_CHANNEL_50OHM_TERMINATION_DISABLE   	"PARAMETER_CHANNEL_50OHM_TERMINATION_DISABLE"
#define TEXT_PARAMETER_CHANNEL_ADC_OFFSET  					"PARAMETER_CHANNEL_ADC_OFFSET"



// --------
#define TEXT_PARAMETER_LEMO_OUT_CO_SELECT  					"PARAMETER_LEMO_OUT_CO_SELECT"
#define TEXT_PARAMETER_LEMO_OUT_TO_SELECT  					"PARAMETER_LEMO_OUT_TO_SELECT"
#define TEXT_PARAMETER_LEMO_OUT_UO_SELECT  					"PARAMETER_LEMO_OUT_UO_SELECT"

// --------


#define TEXT_PARAMETER_CHANNEL_TRIGGER_GENERATION_ENABLE   		"PARAMETER_CHANNEL_TRIGGER_GENERATION_ENABLE"
#define TEXT_PARAMETER_CHANNEL_TRIGGER_GENERATION_CFD_ENABLE    "PARAMETER_CHANNEL_TRIGGER_GENERATION_CFD_ENABLE "
#define TEXT_PARAMETER_CHANNEL_TRIGGER_GENERATION_THRESHOLD    	"PARAMETER_CHANNEL_TRIGGER_GENERATION_THRESHOLD "
#define TEXT_PARAMETER_CHANNEL_TRIGGER_GENERATION_PEAKING   	"PARAMETER_CHANNEL_TRIGGER_GENERATION_PEAKING"
#define TEXT_PARAMETER_CHANNEL_TRIGGER_GENERATION_GAP			"PARAMETER_CHANNEL_TRIGGER_GENERATION_GAP"
#define TEXT_PARAMETER_CHANNEL_TRIGGER_GENERATION_PULSE_LENGTH	"PARAMETER_CHANNEL_TRIGGER_GENERATION_PULSE_LENGTH"

#define TEXT_PARAMETER_CHANNEL_HE_TRIGGER_GENERATION_THRESHOLD  "PARAMETER_CHANNEL_HE_TRIGGER_GENERATION_THRESHOLD"
#define TEXT_PARAMETER_CHANNEL_HE_TRIGGER_GENERATION_SUPPRESS	"PARAMETER_CHANNEL_HE_TRIGGER_GENERATION_SUPPRESS"
#define TEXT_PARAMETER_CHANNEL_HE_TRIGGER_GENERATION_CFD_FUNCTION_IDX "PARAMETER_CHANNEL_HE_TRIGGER_GENERATION_CFD_FUNCTION_IDX"

#define TEXT_PARAMETER_SUM_TRIGGER_0_3		"PARAMETER_SUM_TRIGGER_0_3"
#define TEXT_PARAMETER_SUM_TRIGGER_4_7		"PARAMETER_SUM_TRIGGER_4_7"
#define TEXT_PARAMETER_SUM_TRIGGER_8_11		"PARAMETER_SUM_TRIGGER_8_11"
#define TEXT_PARAMETER_SUM_TRIGGER_12_15	"PARAMETER_SUM_TRIGGER_12_15"

//#define TEXT_PARAMETER_TRIGGER_GATE_WINDOW_LENGTH  			"PARAMETER_TRIGGER_GATE_WINDOW_LENGTH"
#define TEXT_PARAMETER_PILEUP_WINDOW_LENGTH   				"PARAMETER_PILEUP_WINDOW_LENGTH"
#define TEXT_PARAMETER_REPILEUP_WINDOW_LENGTH   			"PARAMETER_REPILEUP_WINDOW_LENGTH"


#define TEXT_PARAMETER_VME_TRIGGER_IDX		"PARAMETER_VME_TRIGGER_IDX"
#define TEXT_PARAMETER_VME_HE_TRIGGER_IDX	"PARAMETER_VME_HE_TRIGGER_IDX"

// --------

#define TEXT_PARAMETER_ENERGY_PEAKING			"PARAMETER_ENERGY_PEAKING"
#define TEXT_PARAMETER_ENERGY_GAP				"PARAMETER_ENERGY_GAP"
#define TEXT_PARAMETER_ENERGY_DECAY_TAU_TABLE	"PARAMETER_ENERGY_DECAY_TAU_TABLE"
#define TEXT_PARAMETER_ENERGY_DECAY_TAU_FACTOR	"PARAMETER_ENERGY_DECAY_TAU_FACTOR"
#define TEXT_PARAMETER_ENERGY_AVG_FACTOR		"PARAMETER_ENERGY_AVG_FACTOR"
#define TEXT_PARAMETER_ENERGY_PICKUP_IDX		"PARAMETER_ENERGY_PICKUP_IDX"

#define TEXT_PARAMETER_GATE1_START_INDEX	"PARAMETER_GATE1_START_INDEX"
#define TEXT_PARAMETER_GATE1_LENGTH			"PARAMETER_GATE1_LENGTH"
#define TEXT_PARAMETER_GATE2_START_INDEX	"PARAMETER_GATE2_START_INDEX"
#define TEXT_PARAMETER_GATE2_LENGTH			"PARAMETER_GATE2_LENGTH"
#define TEXT_PARAMETER_GATE3_START_INDEX	"PARAMETER_GATE3_START_INDEX"
#define TEXT_PARAMETER_GATE3_LENGTH			"PARAMETER_GATE3_LENGTH"
#define TEXT_PARAMETER_GATE4_START_INDEX	"PARAMETER_GATE4_START_INDEX"
#define TEXT_PARAMETER_GATE4_LENGTH			"PARAMETER_GATE4_LENGTH"
#define TEXT_PARAMETER_GATE5_START_INDEX	"PARAMETER_GATE5_START_INDEX"
#define TEXT_PARAMETER_GATE5_LENGTH			"PARAMETER_GATE5_LENGTH"
#define TEXT_PARAMETER_GATE6_START_INDEX	"PARAMETER_GATE6_START_INDEX"
#define TEXT_PARAMETER_GATE6_LENGTH			"PARAMETER_GATE6_LENGTH"

// --------
#define TEXT_PARAMETER_INTERNAL_SAMPLE_CLOCK_IDX	"PARAMETER_INTERNAL_SAMPLE_CLOCK_IDX"
#define TEXT_PARAMETER_INTERNAL_SAMPLE_CLOCK_FP_EN	"PARAMETER_INTERNAL_SAMPLE_CLOCK_FP_EN"
#define TEXT_PARAMETER_FP_CLOCK_IDX					"PARAMETER_FP_CLOCK_IDX"
#define TEXT_PARAMETER_SAMPLE_CLOCK_IDX				"PARAMETER_SAMPLE_CLOCK_IDX"
#define TEXT_PARAMETER_MULTIPLIER_IDX				"PARAMETER_MULTIPLIER_IDX"

// --------
#define TEXT_PARAMETER_LEMO_OUT_CO_SELECT	"PARAMETER_LEMO_OUT_CO_SELECT"
#define TEXT_PARAMETER_LEMO_OUT_TO_SELECT	"PARAMETER_LEMO_OUT_TO_SELECT"
#define TEXT_PARAMETER_LEMO_OUT_UO_SELECT	"PARAMETER_LEMO_OUT_UO_SELECT"

// --------
//#define TEXT_PARAMETER_ENERGY_P_VALUE   					"PARAMETER_ENERGY_P_VALUE"
//#define TEXT_PARAMETER_ENERGY_GAP_VALUE   					"PARAMETER_ENERGY_GAP_VALUE"
//#define TEXT_PARAMETER_ENERGY_TAU_VALUE   					"PARAMETER_ENERGY_TAU_VALUE"
//#define TEXT_PARAMETER_ENERGY_AVERAGE_VALUE   				"PARAMETER_ENERGY_AVERAGE_VALUE"
// --------



//#define TEXT_PARAMETER_ENERGY_HISTOGRAM_ENABLE_FLAG 		"PARAMETER_ENERGY_HISTOGRAM_ENABLE_FLAG"
//#define TEXT_PARAMETER_ENERGY_HISTOGRAM_ONLY_FLAG 			"PARAMETER_ENERGY_HISTOGRAM_ONLY_FLAG"
//#define TEXT_PARAMETER_ENERGY_HISTOGRAM_DIVIDER_VALUE 		"PARAMETER_ENERGY_HISTOGRAM_DIVIDER_VALUE"
//#define TEXT_PARAMETER_ENERGY_HISTOGRAM_OFFSET_VALUE 		"PARAMETER_ENERGY_HISTOGRAM_OFFSET_VALUE"

//#define TEXT_PARAMETER_BASELINE_AVERAGE_MODE   				"PARAMETER_BASELINE_AVERAGE_MODE"



//#define TEXT_PARAMETER_PC_SHAPE_HISTOGRAM_DIVIDER_X_VAL			"PARAMETER_PC_SHAPE_HISTOGRAM_DIVIDER_X_VAL"
//#define TEXT_PARAMETER_PC_SHAPE_HISTOGRAM_DIVIDER_Y_VAL			"PARAMETER_PC_SHAPE_HISTOGRAM_DIVIDER_Y_VAL"

//#define TEXT_PARAMETER_PC_TOF_SHAPE_HISTOGRAM_DIVIDER_X_VAL		"PARAMETER_PC_TOF_SHAPE_HISTOGRAM_DIVIDER_X_VAL"
//#define TEXT_PARAMETER_PC_TOF_SHAPE_HISTOGRAM_DIVIDER_Y_VAL		"PARAMETER_PC_TOF_SHAPE_HISTOGRAM_DIVIDER_Y_VAL"

//#define TEXT_PARAMETER_PC_TOF_HISTOGRAM_DIVIDER_VAL				"PARAMETER_PC_TOF_HISTOGRAM_DIVIDER_VAL"

//#define TEXT_PARAMETER_PC_CHARGE_HISTOGRAM_DIVIDER_VAL			"PARAMETER_PC_CHARGE_HISTOGRAM_DIVIDER_VAL"
//#define TEXT_PARAMETER_PC_CHARGE_HISTOGRAM_CHARGE_SELECT_FLAG	"PARAMETER_PC_CHARGE_HISTOGRAM_CHARGE_SELECT_FLAG"


//#define TEXT_PARAMETER_PC_HISTOGRAMMING_DISABLE_FOR_N_USEC_AFTER_RESTART_VAL	"PARAMETER_PC_HISTOGRAMMING_DISABLE_FOR_N_USEC_AFTER_RESTART_VAL"








class sis3316_get_configuration_parameters
{

private:
	int getNofKewWordLetters (char* line_buf, int max_length);
	int getFollowingParameter(char* line_buf, int max_length);
	int getFollowingChannelParameters(char* line_buf, int max_length, unsigned int* channel_parameters, char* parameter_string );

	bool isKeyWord (char c ) ;

	bool isUpperLetter (char c );
	bool isLowerLetter (char c );
	bool isDigit (char c );
	bool isControl (char c );
	bool isHexDigit (char c );
	//void calculateTriggerGateWindowLength (void);
	//void calculatePileupWindowLength (void);

public:

	//unsigned int uint_nof_events ;

	unsigned int uint_stop_after_nof_loops_enable ;
	unsigned int uint_stop_after_nof_loops_value ;

	unsigned int uint_WriteData_to_File_EnableFlag ;
	unsigned int uint_WriteData_to_MultipleFiles_Flag ;
	unsigned int uint_Append_DateTime_Flag ;
	char char_WriteData_to_File_path[512] ;

	unsigned int uint_sample_control_mode ;
	unsigned int uint_sample_control_use_max_enable ;
	unsigned int uint_sample_control_use_max_value ;


	unsigned int uint_pre_trigger_delay ;
	unsigned int uint_raw_sample_start_index;
	unsigned int uint_raw_sample_length ;


	//unsigned int uint_maw_test_buffer_enable_flag ;
	unsigned int uint_maw_test_buffer_select_energy_flag ;
	unsigned int uint_maw_test_buffer_length ;
	unsigned int uint_maw_test_buffer_delay ;
	unsigned int uint_maw_test_start_index;

	unsigned int uint_format_accum_enable_flag;
	unsigned int uint_format_maw_enable_flag;
	unsigned int uint_format_energy_enable_flag;

	unsigned int uint_trigger_cond_software_key_flag;
	unsigned int uint_trigger_cond_vme_lemo_ti_flag;
	unsigned int uint_trigger_cond_adc_external_flag;
	unsigned int uint_trigger_cond_adc_internal_flag;
	unsigned int uint_trigger_cond_adc_internal_sum_flag;
	unsigned int uint_trigger_cond_adc_internal_pileup_flag;

// -----------

	//unsigned int uint_channel_external_trigger_enable[16] ;
	unsigned int uint_channel_polarity_invert[16] ;

	unsigned int uint_channel_range_2V[16] ;
	unsigned int uint_channel_50ohm_termination_disable[16] ;
	unsigned int uint_channel_adc_offset[16] ;

// -----------



	unsigned int uint_channel_trigger_enable[16] ;
	unsigned int uint_channel_trigger_cfd_enable[16] ;
	unsigned int uint_channel_trigger_threshold[16] ;
	unsigned int uint_channel_trigger_peaking[16] ;
	unsigned int uint_channel_trigger_gap[16] ;
	unsigned int uint_channel_trigger_pulse_length[16] ;

	unsigned int uint_channel_he_trigger_threshold[16];
	unsigned int uint_channel_he_trigger_suppress;
	unsigned int uint_channel_he_trigger_generation_cfd_function_idx;

	unsigned int uint_sum_trigger_0_3;
	unsigned int uint_sum_trigger_4_7;
	unsigned int uint_sum_trigger_8_11;
	unsigned int uint_sum_trigger_12_15;

	//unsigned int uint_trigger_gate_window_length;
	unsigned int uint_pileup_window_length;
	unsigned int uint_re_pileup_window_length;

	unsigned int uint_vme_trigger_idx;
	unsigned int uint_vme_he_trigger_idx;
// -----------

	unsigned int uint_energy_peaking_value;
	unsigned int uint_energy_gap_value;
	unsigned int uint_energy_decay_tau_table;
	unsigned int uint_energy_decay_tau_factor;
	unsigned int uint_energy_average_factor;
	unsigned int uint_energy_pickup_idx;

	unsigned int uint_gate1_start_index;
	unsigned int uint_gate1_length;
	unsigned int uint_gate2_start_index;
	unsigned int uint_gate2_length;
	unsigned int uint_gate3_start_index;
	unsigned int uint_gate3_length;
	unsigned int uint_gate4_start_index;
	unsigned int uint_gate4_length;
	unsigned int uint_gate5_start_index;
	unsigned int uint_gate5_length;
	unsigned int uint_gate6_start_index;
	unsigned int uint_gate6_length;
// -----------
	unsigned int uint_internal_sample_clock_idx;
	unsigned int uint_internal_sample_clock_fp_en;
	unsigned int uint_fp_clock_idx;
	unsigned int uint_sample_clock_idx;
	unsigned int uint_multiplier_idx;
// -----------

// -----------
	unsigned int uint_lemo_out_CO_select ;
	unsigned int uint_lemo_out_TO_select ;
	unsigned int uint_lemo_out_UO_select ;
// -----------




	//unsigned int uint_energy_histogram_enable_flag ;
	//unsigned int uint_energy_histogram_only_flag ;
	//unsigned int uint_energy_histogram_divider_value ;
	//unsigned int uint_energy_histogram_offset_value ;



	//unsigned int uint_baseline_average_mode ;


	//unsigned int uint_PC_shapeHistogram_divider_x_val ;
	//unsigned int uint_PC_shapeHistogram_divider_y_val ;

	//unsigned int uint_PC_tof_shapeHistogram_divider_x_val ;
	//unsigned int uint_PC_tof_shapeHistogram_divider_y_val ;

	//unsigned int uint_PC_tofHistogram_divider_val ;

	//unsigned int uint_PC_chargeHistogram_divider_val ;
	//unsigned int uint_PC_chargeHistogram_charge_select_flag;

	//unsigned int uint_PC_histogramming_disable_for_N_usec_after_restart;




public:
	sis3316_get_configuration_parameters(void);

	int read_parameter_file(char *path);
	int write_parameter_file(char *path);

	~sis3316_get_configuration_parameters(void);
};

#endif /* GET_CONFIGURATION_PARAMETERS_H_ */
