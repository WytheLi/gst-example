# !/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Time     : 2023/3/30 11:35
# @Auther   :
# @File     : basic-tutorial-13.py
# 播放速度
import sys
import gi

gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
gi.require_version('Gst', '1.0')

from gi.repository import Gst, GObject, GLib

custom_data = {
    "pipeline": None,
    "video_sink": None,
    "loop": None,
    "playing": False,  # Playing or Paused
    "rate": 0  # Current playback rate (can be negative)
}


def ABS(n):
    -n if n < 0 else n


# Send seek event to change rate
def send_seek_event(data):
    # Obtain the current position, needed for the seek event
    ret, position = data["pipeline"].query_position(Gst.Format.TIME)
    if not ret:
        print("Unable to retrieve current position.\n")
        return

        # Create the seek event
    if data["rate"] > 0:
        seek_event = Gst.Event.new_seek(data["rate"],
                                        Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
                                        Gst.SeekType.SET,
                                        position,
                                        Gst.SeekType.END,
                                        0)
    else:
        seek_event = Gst.Event.new_seek(data["rate"],
                                        Gst.Format.TIME,
                                        Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
                                        Gst.SeekType.SET,
                                        0,
                                        Gst.SeekType.SET,
                                        position)

    if data["video_sink"] == None:
        #  If we have not done so, obtain the sink through which we will send the seek events
        data["video_sink"] = data["pipeline"].get_property("video-sink")

    # Send the event
    data["video_sink"].send_event(seek_event)

    print("Current rate: %g\n" % data["rate"])


# Process keyboard input
def handle_keyboard(source, cond, data):
    status, str, length, terminator_pos = source.read_line()

    if status != GLib.IOStatus.NORMAL:
        return True
    unichar_tolower_data = GLib.unichar_tolower(str[0])
    if 'p' == unichar_tolower_data:
        data["playing"] = not data["playing"]
        data["pipeline"].set_state(Gst.State.PLAYING if data["playing"] else Gst.State.PAUSED)
        print("Setting state to %s\n" % ("PLAYING" if data["playing"] else "PAUSE"))

    elif 's' == unichar_tolower_data:
        if GLib.unichar_isupper(str[0]):
            data["rate"] *= 2.0
        else:
            data["rate"] /= 2.0
        send_seek_event(data)
    elif 'd' == unichar_tolower_data:
        data["rate"] *= -1.0
        send_seek_event(data)
    elif 'n' == unichar_tolower_data:
        if data["video_sink"] == None:
            # If we have not done so, obtain the sink through which we will send the step events
            data["video_sink"] = data["pipeline"].get_property("video-sink")

        data["video_sink"].send_event(Gst.Event.new_step(Gst.Format.BUFFERS, 1, ABS(data["rate"]), True, False))
        print("Stepping one frame\n")
    elif 'q' == unichar_tolower_data:
        data["loop"].quit()

    return True


def run():
    # 初始化 GStreamer
    Gst.init(sys.argv[1:])

    # Print usage map
    print("USAGE: Choose one of the following options, then press enter:\n"
          " 'P' to toggle between PAUSE and PLAY\n"
          " 'S' to increase playback speed, 's' to decrease playback speed\n"
          " 'D' to toggle playback direction\n"
          " 'N' to move to next frame (in the current direction, better in PAUSE)\n"
          " 'Q' to quit\n")

    # Build the pipeline
    # custom_data["pipeline"] = Gst.parse_launch("playbin uri=https://www.freedesktop.org/software/gstreamer-sdk/data/media/sintel_trailer-480p.webm")
    custom_data["pipeline"] = Gst.parse_launch(
        "playbin uri=file:///home/chenqiang/Desktop/worksapce/gstreamer-python-dev/python-basic-tutorial/data/gnzw.mp4")
    # Add a keyboard watch so we get notified of keystrokes
    io_stdin = GLib.IOChannel.unix_new(sys.stdin.fileno())
    # io_stdin.add_watch(GLib.IOCondition.IN,handle_keyboard,custom_data) 方法已经弃用
    GLib.io_add_watch(io_stdin, GLib.PRIORITY_DEFAULT, GLib.IOCondition.IN, handle_keyboard, custom_data)

    # Start playing
    ret = custom_data["pipeline"].set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        print("Unable to set the pipeline to the playing state.\n");
        return -1
    custom_data["playing"] = True
    custom_data["rate"] = 1.0

    # Create a GLib Main Loop and set it to run
    custom_data["loop"] = GLib.MainLoop.new(None, False)
    custom_data["loop"].run()

    # Free resources
    custom_data["loop"].unref()
    io_stdin.unref()
    custom_data["pipeline"].set_state(Gst.State.NULL)
    if custom_data["video_sink"] != None:
        custom_data["video_sink"].unref()
    custom_data["pipeline"].unref()

    return 0


if __name__ == "__main__":
    run()
