# !/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Time     : 2023/3/30 11:17
# @Auther   :
# @File     : rtmp-flvdemux-queue.py
# 使用插件：rtmpsrc、flvdemux、queue
"""
gst-launch-1.0 --gst-debug-level=3 \
rtmpsrc location=rtmp://103.229.149.171/myapp/GoProCut ! \
flvdemux name=demux \
demux.audio ! queue max-size-time=0 max-size-bytes=0 max-size-buffers=0 ! faad ! audioconvert ! autoaudiosink \
demux.video ! queue max-size-time=0 max-size-bytes=0 max-size-buffers=0 ! h264parse ! avdec_h264 ! videoconvert ! xvimagesink

gst-launch-1.0 --gst-debug-level=3 \
rtmpsrc location=rtmp://103.229.149.171/myapp/GoProCut ! \
flvdemux name=demux \
demux.audio ! queue max-size-buffers=4294967295 max-size-bytes=4294967295 max-size-time=18446744073709551615 ! faad ! audioconvert ! autoaudiosink \
demux.video ! queue max-size-buffers=4294967295 max-size-bytes=4294967295 max-size-time=18446744073709551615 ! h264parse ! avdec_h264 ! videoconvert ! xvimagesink
"""
import sys
import gi
import datetime

gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
gi.require_version('Gst', '1.0')

from gi.repository import Gst, GObject, GLib


# demuxer.connect("pad-added",cb_demuxer_newpad,queuev,queuea)
def cb_demuxer_newpad(_demuxer, new_pad, _queuev, _queuea):
    __FUN__ = sys._getframe().f_code.co_name
    pad_name = new_pad.get_property("template").name_template
    ret = new_pad.get_pad_template()
    # print("ret=",ret)

    if pad_name == "video":
        queuev_pad = _queuev.get_static_pad("sink")
        ret = new_pad.link(queuev_pad)
        print(__FUN__, sys._getframe().f_lineno, "demuxer src", pad_name, "link queuev sink. ret=", ret)
    elif pad_name == "audio":
        queuea_pad = _queuea.get_static_pad("sink")
        ret = new_pad.link(queuea_pad)
        print(__FUN__, sys._getframe().f_lineno, "demuxer src", pad_name, "link queuev sink. ret=", ret)
    else:
        print(__FUN__, sys._getframe().f_lineno, "add a unknown new pad:", pad_name)


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


def cb_queuev_underrun(_queuev):
    print(datetime.datetime.now(), "---------------cb_queuev_underrun")
    # _queuev.set_state(Gst.State.PAUSED)
    ret = _queuev.get_state(Gst.CLOCK_TIME_NONE)
    print("ret =", ret)


def cb_queuev_overrun(_queuev):
    print(datetime.datetime.now(), "---------------cb_queuev_overrun")
    # _queuev.set_state(Gst.State.PLAYING)
    ret = _queuev.get_state(Gst.CLOCK_TIME_NONE)
    print("ret =", ret)


def cb_queuev_running(_queuev):
    print(datetime.datetime.now(), "---------------cb_queuev_running")
    # _queuev.set_state(Gst.State.PLAYING)
    ret = _queuev.get_state(Gst.CLOCK_TIME_NONE)
    print("ret =", ret)


def cb_queuev_pushing(_queuev):
    print(datetime.datetime.now(), "---------------cb_queuev_pushing")
    ret = _queuev.get_state(Gst.CLOCK_TIME_NONE)
    print("ret =", ret)


def cb_queuea_underrun(_queuea):
    print(datetime.datetime.now(), "---------------cb_queuea_underrun")
    # _queuea.set_state(Gst.State.PAUSED)
    ret = _queuea.get_state(Gst.CLOCK_TIME_NONE)
    print("ret =", ret)


def cb_queuea_overrun(_queuea):
    print(datetime.datetime.now(), "---------------cb_queuea_overrun")
    # _queuea.set_state(Gst.State.PLAYING)
    ret = _queuea.get_state(Gst.CLOCK_TIME_NONE)
    print("ret =", ret)


def cb_queuea_running(_queuea):
    print(datetime.datetime.now(), "---------------cb_queuea_running")
    # _queuea.set_state(Gst.State.PLAYING)
    ret = _queuea.get_state(Gst.CLOCK_TIME_NONE)
    print("ret =", ret)


def cb_queuea_pushing(_queuea):
    print(datetime.datetime.now(), "---------------cb_queuea_pushing")
    ret = _queuea.get_state(Gst.CLOCK_TIME_NONE)
    print("ret =", ret)


def run():
    __FUN__ = sys._getframe().f_code.co_name
    rtmp_url = "rtmp://103.229.149.171/myapp/GoProCut"

    # 初始化 GStreamer
    Gst.init(sys.argv[1:])

    # 创建elements
    pipeline = Gst.Pipeline.new("RTMP-Play")
    src = Gst.ElementFactory.make("rtmpsrc", "src")
    demuxer = Gst.ElementFactory.make("flvdemux", "demux")

    queuev = Gst.ElementFactory.make("queue", "queuev")
    h264parse = Gst.ElementFactory.make("h264parse", "parsev")
    decodebinv = Gst.ElementFactory.make("avdec_h264", "decodev")  # ffmpeg插件avdec_h264
    convv = Gst.ElementFactory.make("videoconvert", "convv")  # 视频转换元素
    sinkv = Gst.ElementFactory.make("xvimagesink", "sinkv")  # 图像接收器

    queuea = Gst.ElementFactory.make("queue", "queuea")
    decodebina = Gst.ElementFactory.make("faad", "decodea")  # ffmpeg插件faad
    conva = Gst.ElementFactory.make("audioconvert", "conva")  # 视频转换元素
    sinka = Gst.ElementFactory.make("autoaudiosink", "sinka")  # 自动音频接收器 autoaudiosink

    # 设置播放地址
    src.set_property("location", rtmp_url)

    # 设置queuev、queuea，禁用queue的大小限制，也可以设置为最大值
    queuev.set_property("max-size-buffers", 0)  # Default: 200
    queuev.set_property("max-size-bytes", 0)  # Default: 10485760
    queuev.set_property("max-size-time", 0)  # 1s Default: 1000000000 ns

    queuea.set_property("max-size-buffers", 0)  # Default: 200
    queuea.set_property("max-size-bytes", 0)  # Default: 10485760
    queuea.set_property("max-size-time", 0)  # 1s Default: 1000000000 ns

    # 向管道中添加元件
    pipeline.add(src)
    pipeline.add(demuxer)
    pipeline.add(queuev)
    pipeline.add(h264parse)
    pipeline.add(decodebinv)
    pipeline.add(convv)
    pipeline.add(sinkv)
    pipeline.add(queuea)
    pipeline.add(decodebina)
    pipeline.add(conva)
    pipeline.add(sinka)

    # 连接elements
    src.link(demuxer)
    demuxer.connect("pad-added", cb_demuxer_newpad, queuev, queuea)
    queuev.link(h264parse)
    h264parse.link(decodebinv)
    decodebinv.link(convv)
    convv.link(sinkv)
    queuea.link(decodebina)
    decodebina.link(conva)
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
