sudo ip link show dev can0

sudo ip link set can0 type can help

sudo ip link set can0 type can bitrate 500000 listen-only on

sudo ip link set can0 up

#sudo candump -cae can0,0:0,#FFFFFFFF
