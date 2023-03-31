# !/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Time     : 2023/3/30 11:25
# @Auther   :
# @File     : basic-tutorial-04.py
# 时间管理
import sys
import gi

gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
gi.require_version('Gst', '1.0')

from gi.repository import Gst, GObject, GLib

'''
本教程展示了如何使用 GStreamer 与时间相关的工具。尤其是：
    如何查询管道以获取流位置或持续时间等信息。
    如何在流中寻找（跳转）到不同的位置（时间）。

GstQuery是一种机制,允许向元素或垫询问一条信息。
在此示例中，我们询问管道是否允许搜索（某些来源，如直播流，不允许搜索）。
如果允许，那么，一旦电影运行了十秒钟，我们就会使用搜索跳到不同的位置。
在之前的教程中，一旦我们设置并运行了管道，我们的 main 函数就只是坐着等待 通过总线接收一个ERROR或一个。
EOS在这里,我们修改这个函数来周期性地唤醒和查询流水线位置，这样我们就可以在屏幕上打印出来了。这类似于媒体播放器所做的，定期更新用户界面。
最后，只要流持续时间发生变化，就会查询和更新流持续时间。
'''


# #define GST_STIME_ARGS(t)                        \
#   ((t) == GST_CLOCK_STIME_NONE || (t) >= 0) ? '+' : '-',        \
#     GST_CLOCK_STIME_IS_VALID (t) ?                    \
#     (guint) (((GstClockTime)(ABS(t))) / (GST_SECOND * 60 * 60)) : 99,    \
#     GST_CLOCK_STIME_IS_VALID (t) ?                    \
#     (guint) ((((GstClockTime)(ABS(t))) / (GST_SECOND * 60)) % 60) : 99,    \
#     GST_CLOCK_STIME_IS_VALID (t) ?                    \
#     (guint) ((((GstClockTime)(ABS(t))) / GST_SECOND) % 60) : 99,    \
#     GST_CLOCK_STIME_IS_VALID (t) ?                    \
#     (guint) (((GstClockTime)(ABS(t))) % GST_SECOND) : 999999999
def GST_TIME_ARGS(time):
    if time == Gst.CLOCK_TIME_NONE:
        return "CLOCK_TIME_NONE"
    return "%u:%02u:%02u.%09u" % (time / (Gst.SECOND * 60 * 60),
                                  (time / (Gst.SECOND * 60)) % 60,
                                  (time / Gst.SECOND) % 60,
                                  time % Gst.SECOND)


# Gst.CLOCK_TIME_NONE= 18446744073709551615
# #define GST_CLOCK_TIME_IS_VALID(time)   (((GstClockTime)(time)) != GST_CLOCK_TIME_NONE)
def GST_CLOCK_TIME_IS_VALID(time):
    if time is not Gst.CLOCK_TIME_NONE:
        return True
    else:
        return False


# Forward definition of the message processing function
def handle_message(_custom_data, _msg):
    # Parse message
    if _msg:
        if _msg.type == Gst.MessageType.ERROR:
            err, debug_info = _msg.parse_error()
            print(f"Error received from element {_msg.src.get_name()}: {err.message}")
            print(f"Debugging information: {debug_info if debug_info else 'none'}")
            _custom_data["terminate"] = True
            pass
        elif _msg.type == Gst.MessageType.EOS:
            print("\nEnd-Of-Stream reached.\n")
            _custom_data["terminate"] = True
            pass
        elif _msg.type == Gst.MessageType.DURATION_CHANGED:
            # The duration has changed, mark the current one as invalid
            _custom_data["duration"] = Gst.CLOCK_TIME_NONE
            print("The duration has changed, mark the current one as invalid")
            pass
        elif _msg.type == Gst.MessageType.STATE_CHANGED:
            old_state, new_state, pending = _msg.parse_state_changed()
            # if (GST_MESSAGE_SRC (msg) == GST_OBJECT (data->playbin))
            if _msg.src == _custom_data["playbin"]:
                print("Pipeline state changed from %s to %s:\n" % (
                Gst.Element.state_get_name(old_state), Gst.Element.state_get_name(new_state)))
                # Remember whether we are in the PLAYING state or not
                if new_state == Gst.State.PLAYING:
                    _custom_data["playing"] = True
                else:
                    _custom_data["playing"] = False

                if _custom_data["playing"]:
                    print("_custom_data[\"playing\"] is True")
                    # We just moved to PLAYING. Check if seeking is possible
                    query = Gst.Query.new_seeking(Gst.Format.TIME)
                    if _custom_data["playbin"].query(query):
                        print("---->query")
                        _format, _custom_data["seek_enabled"], start, end = query.parse_seeking()
                        if _custom_data["seek_enabled"]:
                            print("Seeking is ENABLED from %s to %s " % (GST_TIME_ARGS(start), GST_TIME_ARGS(end)))
                        else:
                            print("Seeking is DISABLED for this stream.")
                    else:
                        print("Seeking query failed.")
                    # query.unref()
                else:
                    print("_custom_data[\"playing\"] is False")
        else:
            # We should not reach here
            print("Unexpected message received.")
        # _msg.unref()
    pass


def run():
    # Structure to contain all our information, so we can pass it around
    custom_data = {
        "playbin": None,
        "playing": False,
        "terminate": False,
        "seek_enabled": False,
        "seek_done": False,
        "duration": Gst.CLOCK_TIME_NONE
    }

    # rtmp_url = "rtmp://103.229.149.171/myapp/GoProCut"
    rtmp_url = "rtsp://192.168.42.244:554/ch01"
    file_uri = "./data/gnzw.mp4"

    # 初始化 GStreamer
    Gst.init(sys.argv[1:])

    # 创建elements
    custom_data["playbin"] = Gst.ElementFactory.make("playbin", "playbin")
    if custom_data["playbin"] is None:
        print("Not all elements could be created.")
        return -1

    # Set the URI to play
    # custom_data["playbin"].set_property("uri", "https://www.freedesktop.org/software/gstreamer-sdk/data/media/sintel_trailer-480p.webm")
    custom_data["playbin"].set_property("uri", rtmp_url)
    # custom_data["playbin"].set_property("uri", "file:///home/chenqiang/Desktop/worksapce/gstreamer-python-dev/python-basic-tutorial/data/gnzw.mp4")
    # Start playing
    ret = custom_data["playbin"].set_state(Gst.State.PLAYING)
    if ret is Gst.StateChangeReturn.FAILURE:
        print("Unable to set the pipeline to the playing state.")
        return -1

    # Listen to the bus
    bus = custom_data["playbin"].get_bus()

    while custom_data["terminate"] is False:
        msg = bus.timed_pop_filtered(1000 * Gst.MSECOND,
                                     Gst.MessageType.STATE_CHANGED | Gst.MessageType.ERROR | Gst.MessageType.EOS | Gst.MessageType.DURATION_CHANGED)
        # Parse message
        if msg is not None:
            handle_message(custom_data, msg)
        else:
            # print("We got no message, this means the timeout expired")
            # We got no message, this means the timeout expired
            if custom_data["playing"]:
                print("playing=", custom_data["playing"])
                current = -1
                # Query the current position of the stream
                ret, current = custom_data["playbin"].query_position(Gst.Format.TIME)
                if not ret:
                    print("Could not query current position.\n")

                # If we didn't know it yet, query the stream duration
                if not GST_CLOCK_TIME_IS_VALID(custom_data["duration"]):
                    ret, custom_data["duration"] = custom_data["playbin"].query_duration(Gst.Format.TIME)
                    if not ret:
                        print("Could not query current duration.\n")

                # Print current position and total duration
                print("Position %s %s" % (GST_TIME_ARGS(current), GST_TIME_ARGS(custom_data["duration"])))

                # If seeking is enabled, we have not done it yet, and the time is right, seek
                if custom_data["seek_enabled"] and (not custom_data["seek_done"]) and (current > 10 * Gst.SECOND):
                    print("\nReached 10s, performing seek...\n")
                    custom_data["playbin"].seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                                       30 * Gst.SECOND)
                    custom_data["seek_done"] = True
            else:
                print("playing=", custom_data["playing"])
                pass

    print("Free resource")
    # Free resource
    # Gst.Object.unref(bus)
    custom_data["playbin"].set_state(Gst.State.NULL)
    # Gst.Object.unref(custom_data["playbin"])
    return 0


if __name__ == "__main__":
    run()
