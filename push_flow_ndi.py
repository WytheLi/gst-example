# !/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Time     : 2023/3/30 11:41
# @Auther   :
# @File     : push_flow_ndi.py
"""
gst-launch-1.0 ndi-hwsrc name=ndi_src device=/dev/ndisrc0 width=1920 height=1080 interlaced=0 bitrate=10000 framerated=1000 frameraten=30*1000 shqtype=2 \
! video/SHQ0,format=SHQ0,width=1920,height=1080,frame_rate_N=30*1000,frame_rate_D=1000,frame_format_type=1 \
! queue ! channel-name=FULL group-name=public conn-type=multicast netprefix="239.255.0.0" netmask="255.255.0.0" ttl=127 ! ndisink name=main_ndi \
! queue ! shmsrc socket-path=/tmp/pcm do-timestamp=true is-live=true ! audio/x-raw, format=S16LE, rate=48000, channels=2 ! ndisink name=sub_dni
! ndi-hwsrc device=/dev/ndisrc1 width=640 height=360 interlaced=0 bitrate=10000 framerated=1000 frameraten=60*1000 shqtype=2 \
!
"""
