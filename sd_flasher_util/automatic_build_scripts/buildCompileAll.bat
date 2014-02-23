:: This build script has been customized for the Mango 802.11 Reference Design. It MUST be modified to automate
:: the generation of different project. You can run it by just double-clicking the script in the window browser.
:: It must be placed in the SDK_Workspace project associated with the FPGA Hardware configuration (the project
:: that both Board Support Packages are built from).
::
:: It also depends on the file "mydownload.cmd", which is an impact batch file.
::
:: This batch script does three important things: 
:: 1. It automatically grabs the system.bit FPGA programming file generated by XPS and overwrites the flash memory of
::    the embedded MicroBlaze microcontrollers with the appropriate compiled ELF file. It will do this for both the
::    802.11 AP and the 802.11 STA projects separately and place the finished, complete FPGA bit files in the local
::    directory called "download_AP.bit" and "download_AP.bit"
::
:: 2. It then tries to program two attached WARPv3 boards with the two FPGA images via the Digilent JTAG programmers.
::    It chooses which board is AP and which is STA based on the order that their USB programmer enumerates in the
::    Windows 7 OS. Thus, you shold unplug both programmers ***from your computer***, then plug in the programmer
::    intended for the AP WARPv3 and then the programmer intended for the STA WARPv3. You will see messages about the
::    success or failure of this process in the terminal.
::
:: 3. Finally, after the first two steps have completed (step 2 is allowed to fail, in case you just want to generate
::    the SD flash images without programming attached FPGAs), the script converts with FPGA .bit images into flash
::    images "download_AP.bin" and "download_STA.bin", which can be programmed to SD Flash cards for programming WARPv3:
::    
::		A. In the SDK, choose Xilinx Tools -> Launch Shell.
::      B. The new command prompt will start in the SDK workspace directory. CD to the hardware project directory.
::		   For example, if you're using the WARP template project, you would run "cd WARPv3_TemplateProject_v0_hw_platform".
::		C. Confirm the hardware project directory contains system.bit and download.bit.
::		D. Run: promgen -u 0 download.bit -p bin -spi -w
::		E. Confirm promgen created/updated the file "download.bin"
::
:: Written by:   Narendra Anand (nanand@rice.edu)
:: Commented by: Ryan E. Guerra (me@ryaneguerra.com)
:: Covered by the MIT License: http://opensource.org/licenses/MIT

data2mem -bm system_bd.bmm -bt system.bit -bd ../wlan_mac_low_dcf/Debug/wlan_mac_low_dcf.elf tag mb_low -bd ../wlan_mac_high_ap/Debug/wlan_mac_high_ap.elf tag mb_high -o b download_AP.bit 

data2mem -bm system_bd.bmm -bt system.bit -bd ../wlan_mac_low_dcf/Debug/wlan_mac_low_dcf.elf tag mb_low -bd ../wlan_mac_high_sta/Debug/wlan_mac_high_sta.elf tag mb_high -o b download_STA.bit 

impact -batch mydownload.cmd

promgen -u 0 download_AP.bit -p bin -spi -w

promgen -u 0 download_STA.bit -p bin -spi -w