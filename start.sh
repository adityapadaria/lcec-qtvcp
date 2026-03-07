#!/bin/bash

#---------------------------------------------------------------------------------------------------------------------------------

date=$(date '+%d/%m/%Y %H:%M:%S');

echo "---------------------------------------------------------------------------------------------------------------------------------"
echo "  Bharat CNC Controller: $date"
echo "---------------------------------------------------------------------------------------------------------------------------------"

#---------------------------------------------------------------------------------------------------------------------------------

# echo " >  Stopping EtherCAT master"

# if lsmod | grep -wq ec_genet; then
#   sudo rmmod ec_genet
# fi

# if lsmod | grep -wq ec_generic; then
#   sudo rmmod ec_generic
# fi

# if lsmod | grep -wq ec_master; then
#   sudo /etc/init.d/ethercat stop
# fi

#---------------------------------------------------------------------------------------------------------------------------------

# echo " >  Loading EtherCAT modules"

# sudo modprobe ec_master main_devices=2c:cf:67:8e:ad:a5
# sudo modprobe ec_generic

#---------------------------------------------------------------------------------------------------------------------------------

# echo " >  Binding Ethernet driver to EtherCAT master"

# echo fd580000.ethernet > sudo /sys/bus/platform/drivers/bcmgenet/unbind
# echo fd580000.ethernet > sudo /sys/bus/platform/drivers/ec_bcmgenet/bind

# sudo chmod 666 /dev/EtherCAT0

#---------------------------------------------------------------------------------------------------------------------------------

echo " >  Starting LinuxCNC with EtherCAT configuration"
echo " "

# sleep 2

# export DISPLAY=:0
linuxcnc /home/cnc/linuxcnc/configs/lcec-qtvcp/config.ini

echo " "

#---------------------------------------------------------------------------------------------------------------------------------

# echo " >  Stopping EtherCAT master"

# if lsmod | grep -wq ec_generic; then
#   sudo rmmod ec_generic
# fi

# if lsmod | grep -wq ec_master; then
#   sudo /etc/init.d/ethercat stop
# fi

#---------------------------------------------------------------------------------------------------------------------------------

echo " >  Exit"

#---------------------------------------------------------------------------------------------------------------------------------

# sudo reboot
