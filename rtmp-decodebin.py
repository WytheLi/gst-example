# !/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Time     : 2023/3/30 11:14
# @Auther   :
# @File     : rtmp-decodebin.py
# 使用插件：rtmpsrc、decodebin
"""
# 输出视频
gst-launch-1.0 --gst-debug-level=3 rtmpsrc location=rtmp://103.229.149.171/myapp/GoProCut ! decodebin ! videoconvert ! autovideosink
gst-launch-1.0 --gst-debug-level=3 rtmpsrc location=rtmp://103.229.149.171/myapp/GoProCut ! decodebin ! videoconvert ! xvimagesink

# 输出音频
gst-launch-1.0 rtmpsrc location=rtmp://103.229.149.171/myapp/GoProCut ! decodebin ! queue ! audioconvert ! autoaudiosink

# 输出音视频
gst-launch-1.0 --gst-debug-level=3 rtmpsrc location=rtmp://103.229.149.171/myapp/GoProCut ! decodebin name=decode \
decode. ! queue max-size-buffers=0 max-size-bytes=0 max-size-time=0 ! videoconvert ! xvimagesink \
decode. ! queue max-size-buffers=0 max-size-bytes=0 max-size-time=0 ! audioconvert ! autoaudiosink
"""
import sys
import gi
import datetime

gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
gi.require_version('Gst', '1.0')

from gi.repository import Gst, GObject, GLib


def cb_decode_newpad(decode, new_pad, _convv, _queuea):
    __FUN__ = sys._getframe().f_code.co_name
    pad_name = new_pad.get_property("template").name_template
    pad_current_caps = new_pad.get_current_caps()
    src_name = pad_current_caps.get_structure(0).get_name()
    print("src_name=", src_name)

    # ---->src_pad_name video/x-raw
    # ---->src_pad_name audio/x-raw

    if src_name == "video/x-raw":
        convv_pad = _convv.get_static_pad("sink")
        ret = new_pad.link(convv_pad)
        print(__FUN__, sys._getframe().f_lineno, "decode src", pad_name, "link convv sink. ret=", ret)
        pass
    elif src_name == "audio/x-raw":
        queuea_pad = _queuea.get_static_pad("sink")
        ret = new_pad.link(queuea_pad)
        print(__FUN__, sys._getframe().f_lineno, "decode src", pad_name, "link queuev sink. ret=", ret)
        pass
    else:
        print(__FUN__, sys._getframe().f_lineno, "add a unknown new pad:", pad_name, "src_name:", src_name)
        pass


def cb_bus_message(_bus, new_msg, _custom_data):
    __FUN__ = sys._getframe().f_code.co_name
    if new_msg:
        msg_src_name = new_msg.src.get_name()
        msg_type = new_msg.type
        # print(__FUN__,sys._getframe().f_lineno,msg_src_name, msg_type)
        if msg_type == Gst.MessageType.ERROR:
            err, debug_info = new_msg.parse_error()
            print(__FUN__, sys._getframe().f_lineno, "Error received from element %s:%s" % (msg_src_name, err.message))
            _custom_data["pipeline"].set_state(Gst.State.READY)
            _custom_data["loop"].quit()
        elif msg_type == Gst.MessageType.EOS:
            print(__FUN__, sys._getframe().f_lineno, "End-Of-Stream reached.")
            _custom_data["pipeline"].set_state(Gst.State.READY)
            _custom_data["loop"].quit()
        elif msg_type == Gst.MessageType.BUFFERING:
            print("----------------------Gst.MessageType.BUFFERING-------------------------------------")
            pass
        elif msg_type == Gst.MessageType.CLOCK_LOST:
            print("----------------------Gst.MessageType.CLOCK_LOST-------------------------------------")
            pass
        elif msg_type == Gst.MessageType.STATE_CHANGED:
            pass
        else:
            # Unhandled message
            pass
    else:
        print(__FUN__, sys._getframe().f_lineno, "Error new_msg=", new_msg)


def run():
    __FUN__ = sys._getframe().f_code.co_name
    rtmp_url = "rtmp://103.229.149.171/myapp/GoProCut"

    # 初始化 GStreamer
    Gst.init(sys.argv[1:])

    # 创建elements
    pipeline = Gst.Pipeline.new("RTMP-Play")
    src = Gst.ElementFactory.make("rtmpsrc", "src")
    decode = Gst.ElementFactory.make("decodebin", "decode")

    queuev = Gst.ElementFactory.make("queue", "queuev")
    convv = Gst.ElementFactory.make("videoconvert", "convv")  # 视频转换元素
    sinkv = Gst.ElementFactory.make("xvimagesink", "sinkv")  # 图像接收器

    queuea = Gst.ElementFactory.make("queue", "queuea")
    conva = Gst.ElementFactory.make("audioconvert", "conva")  # 视频转换元素
    sinka = Gst.ElementFactory.make("autoaudiosink", "sinka")  # 自动音频接收器 autoaudiosink

    # 设置播放地址
    src.set_property("location", rtmp_url)

    # 设置queuev、queuea，禁用queue的大小限制，也可以设置为最大值
    queuev.set_property("max-size-buffers", 0)  # Default: 200
    queuev.set_property("max-size-bytes", 0)  # Default: 10485760
    queuev.set_property("max-size-time", 0)  # Default: 1000000000 ns
    queuea.set_property("max-size-buffers", 0)  # Default: 200
    queuea.set_property("max-size-bytes", 0)  # Default: 10485760
    queuea.set_property("max-size-time", 0)  # Default: 1000000000 ns

    # 向管道中添加元件
    pipeline.add(src)
    pipeline.add(decode)
    pipeline.add(convv)
    pipeline.add(sinkv)
    pipeline.add(queuea)
    pipeline.add(conva)
    pipeline.add(sinka)

    # 连接elements
    src.link(decode)
    decode.connect("pad-added", cb_decode_newpad, convv, queuea)
    convv.link(sinkv)
    queuea.link(queuea)
    queuea.link(conva)
    conva.link(sinka)

    ret = pipeline.set_state(Gst.State.PLAYING)
    if ret is Gst.StateChangeReturn.FAILURE:
        print(__FUN__, sys._getframe().f_lineno, "Unable to set the pipeline to the playing state.")
        return
    elif ret is Gst.StateChangeReturn.NO_PREROLL:
        print(__FUN__, sys._getframe().f_lineno, "is_live")
    else:
        print(__FUN__, sys._getframe().f_lineno, "pipeline set state playing. ret=", ret)

    main_loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()

    custom_data = {
        "pipeline": pipeline,
        "loop": main_loop
    }

    bus.connect("message", cb_bus_message, custom_data)
    main_loop.run()

    # Free resources
    main_loop.unref()
    Gst.Object.unref(bus)
    pipeline.set_state(Gst.State.NULL)


if __name__ == "__main__":
    run()
