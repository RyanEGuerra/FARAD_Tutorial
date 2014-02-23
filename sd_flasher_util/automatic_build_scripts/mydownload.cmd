#Thisisacomment
setmode -bscan
setCable -p usb1
identify 
assignfile -p 1 -file download_AP.bit
program -p 1
#verify -p 1 -file download_AP.bit
closeCable

setmode -bscan
setCable -p usb2
identify 
assignfile -p 1 -file download_STA.bit
program -p 1
#verify -p 1 -file download_STA.bit
closeCable

quit