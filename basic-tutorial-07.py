# !/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Time     : 2023/3/30 11:29
# @Auther   :
# @File     : basic-tutorial-07.py
# 多线程和PAD可用
import sys
import gi

gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gst", "1.0")

from gi.repository import Gst, GLib, GObject


def run():
    # Initialize GStreamer
    Gst.init(sys.argv[1:])

    # Create the empty pipeline
    pipeline = Gst.Pipeline.new("test-pipeline")

    # Create the elements
    audio_source   = Gst.ElementFactory.make("audiotestsrc", "audio_source")
    tee            = Gst.ElementFactory.make("tee", "tee")
    audio_queue    = Gst.ElementFactory.make("queue", "audio_queue")
    audio_convert  = Gst.ElementFactory.make("audioconvert", "audio_convert")
    audio_resample = Gst.ElementFactory.make("audioresample", "audio_resample")
    audio_sink     = Gst.ElementFactory.make("autoaudiosink", "audio_sink")
    video_queue    = Gst.ElementFactory.make("queue", "video_queue")
    visual         = Gst.ElementFactory.make("wavescope", "visual")
    video_convert  = Gst.ElementFactory.make("videoconvert", "csp")
    video_sink     = Gst.ElementFactory.make("autovideosink", "video_sink")

    if not pipeline or not audio_source or not tee or \
       not audio_queue or not audio_convert or not audio_resample or \
       not audio_sink or not video_queue or not visual or \
       not video_convert or not video_sink:
       print("Not all elements could be created.")
       return -1

    # Configure elements

    audio_source.set_property("freq", 215.0)
    visual.set_property("shader", 0)
    visual.set_property("style", 1)

    # Link all elements that can be automatically linked because they have "Always" pads
    element_list = [audio_source, tee, audio_queue, audio_convert, audio_resample, audio_sink, video_queue, visual, video_convert, video_sink]
    for element in element_list:
        pipeline.add(element)

    if not audio_source.link(tee) or not audio_queue.link(audio_convert) or not audio_convert.link(audio_resample) or \
       not audio_resample.link(audio_sink) or not video_queue.link(visual) or not visual.link(video_convert) or \
       not video_convert.link(video_sink):
       print("Elements could not be linked.")
       return -1

    # Manually link the Tee, which has "Request" pads
    tee_audio_pad = tee.get_request_pad("src_%u")
    # name_template = tee_audio_pad.get_pad_template().name_template
    audio_name_template = tee_audio_pad.get_property("template").name_template
    print("Obtained request pad %s for audio branch.\n" % (audio_name_template ))
    queue_audio_pad = audio_queue.get_static_pad("sink")
    tee_video_pad = tee.get_request_pad("src_%u")
    video_name_template = tee_video_pad.get_property("template").name_template
    print("Obtained request pad %s for video branch.\n" % (video_name_template))
    queue_video_pad = video_queue.get_static_pad("sink")
    if tee_audio_pad.link(queue_audio_pad) != Gst.PadLinkReturn.OK or \
        tee_video_pad.link(queue_video_pad) != Gst.PadLinkReturn.OK:
        print("Tee could not be linked.")
        return -1

    # Start playing the pipeline
    ret = pipeline.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        print("Unable to set the pipeline to the playing state.")
        return -1

    # Wait until error or EOS
    bus = pipeline.get_bus()
    msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)

    # Release the request pads from the Tee, and unref them
    tee.release_request_pad(tee_audio_pad)
    tee.release_request_pad(tee_video_pad)

    # Free resources
    pipeline.set_state(Gst.State.GST_STATE_NULL)
    return 0


if __name__ == "__main__":
    run()
