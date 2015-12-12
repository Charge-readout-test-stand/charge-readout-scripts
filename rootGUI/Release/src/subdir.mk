################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CPP_SRCS += \
../src/get_configuration_parameters.cpp \
../src/sis3316_class.cpp \
../src/sis3316_ethernet_access_class.cpp \
../src/sis3316_root_gui_flash.cpp \
../src/sis3316_root_gui_main.cpp \
../src/sis3316_root_gui_test1.cpp 

OBJS += \
./src/get_configuration_parameters.o \
./src/sis3316_class.o \
./src/sis3316_ethernet_access_class.o \
./src/sis3316_root_gui_flash.o \
./src/sis3316_root_gui_main.o \
./src/sis3316_root_gui_test1.o 

CPP_DEPS += \
./src/get_configuration_parameters.d \
./src/sis3316_class.d \
./src/sis3316_ethernet_access_class.d \
./src/sis3316_root_gui_flash.d \
./src/sis3316_root_gui_main.d \
./src/sis3316_root_gui_test1.d 


# Each subdirectory must supply rules for building sources it contributes
src/%.o: ../src/%.cpp
	@echo 'Building file: $<'
	@echo 'rootsys ${ROOTSYS}'
	@echo 'Invoking: GCC C++ Compiler'
	g++ -I ${ROOTSYS}/include -O3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o"$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


