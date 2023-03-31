# !/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Time     : 2023/3/30 11:34
# @Auther   :
# @File     : basic-tutorial-12.py
# 流式传输
import sys
import gi

gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
gi.require_version('Gst', '1.0')

from gi.repository import Gst, GObject, GLib


def cb_bus_message(_bus, new_msg, _custom_data):
    if new_msg:
        if new_msg.type == Gst.MessageType.ERROR:
            err, debug_info = new_msg.parse_error()
            print("cb_bus_message---> Error received from element %s:%s" % (new_msg.src.get_name(), err.message))
            _custom_data["pipeline"].set_state(Gst.State.READY)
            _custom_data["loop"].quit()
        elif new_msg.type == Gst.MessageType.EOS:
            _custom_data["pipeline"].set_state(Gst.State.READY)
            _custom_data["loop"].quit()
        elif new_msg.type == Gst.MessageType.BUFFERING:
            if _custom_data["is_live"]:
                return None
            percent = new_msg.parse_buffering()
            print("Buffering (%3d%%)" % (percent))
            # Wait until buffering is complete before start/resume playing
            if percent < 100:
                _custom_data["pipeline"].set_state(Gst.State.PAUSED)
            else:
                _custom_data["pipeline"].set_state(Gst.State.PLAYING)
        elif new_msg.type == Gst.MessageType.CLOCK_LOST:
            # Get a new clock
            print("CLOCK_LOST, Get a new clock")
            _custom_data["pipeline"].set_state(Gst.State.PAUSED)
            _custom_data["pipeline"].set_state(Gst.State.PLAYING)
        else:
            # Unhandled message
            pass
    pass


def run():
    pipeline = None
    bus = None
    message = None
    rtmp_url = "rtmp://103.229.149.171/myapp/GoProCut"

    # 初始化 GStreamer
    Gst.init(sys.argv[1:])

    # 创建elements
    pipeline = Gst.parse_launch("playbin uri=" + rtmp_url)
    # pipeline = Gst.parse_launch("playbin location=" )
    bus = pipeline.get_bus()

    custom_data = {"is_live": None, "pipeline": pipeline, "loop": None}
    ret = pipeline.set_state(Gst.State.PLAYING)
    if ret is Gst.StateChangeReturn.FAILURE:
        print("Unable to set the pipeline to the playing state.")
        Gst.Object.unref(pipeline)
        return -1
    elif ret is Gst.StateChangeReturn.NO_PREROLL:
        print("is live")
        custom_data["is_live"] = True
    else:
        custom_data["is_live"] = False
        # print("ret=",ret)
        pass

    print("is_live=", custom_data["is_live"])

    # main_loop = g_main_loop_new (NULL, FALSE);
    main_loop = GLib.MainLoop.new(None, False)
    custom_data["loop"] = main_loop
    bus.add_signal_watch()
    bus.connect("message", cb_bus_message, custom_data)
    main_loop.run()

    # Free resources
    main_loop.unref()
    Gst.Object.unref(bus)
    pipeline.set_state(Gst.State.NULL)


if __name__ == "__main__":
    run()
