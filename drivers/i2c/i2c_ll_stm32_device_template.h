<%inherit file="device_declare.txt"/>
#ifndef _I2C_LL_STM32_DEVICE_H_
#define _I2C_LL_STM32_DEVICE_H_

<% 
  irq_flag      = 'CONFIG_I2C_STM32_INTERRUPT'
  config_struct = 'i2c_stm32_config'
  data_struct   = 'i2c_stm32_data'
  api_struct    = 'api_funcs'
  init_function = 'i2c_stm32_init'
%>

<% def name="irq_config_function_body(device_name, config_struct_name, data_struct_name, irq_config_config_function_name, device_lable)">

<%/def>


{{ self.device(data, ['st,stm32-i2c-v1', 'st,stm32-i2c-v2']) }}

#endif
