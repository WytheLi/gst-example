# !/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Time     : 2023/3/30 11:24
# @Auther   :
# @File     : basic-tutorial-03.py
import sys
import gi

gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gst", "1.0")

from gi.repository import Gst, GLib, GObject


def pad_added_handler(src, new_pad, data):
    sink_pad = data["convert"].get_static_pad("sink")
    ret = None
    new_pad_caps = None
    new_pad_struct = None
    new_pad_type = None

    print("Received new pad '%s' from '%s':" % (new_pad.name, src.name))
    # If our converter is already linked, we have nothing to do here
    if sink_pad.is_linked():
        print("We are already linked. Ignoring.")
        if new_pad_caps is not None:
            # new_pad_caps.unref()
            pass
        # sink_pad.unref()
        return None

    # Check the new pad's type
    new_pad_caps = new_pad.get_current_caps()
    new_pad_struct = new_pad_caps.get_structure(0)
    new_pad_type = new_pad_struct.get_name()
    if "audio/x-raw" not in new_pad_type:
        print("It has type '%s' which is not raw audio. Ignoring." % new_pad_type)
        if new_pad_caps is not None:
            # new_pad_caps.unref()
            pass
        # sink_pad.unref()
        return None

    # Attempt the link
    ret = new_pad.link(sink_pad)
    if ret is not Gst.PadLinkReturn.OK:
        # if ret == Gst.StateChangeReturn.FAILURE:
        # if GST_PAD_LINK_FAILED(ret):
        print("Type is '%s' but link failed." % new_pad_type)
    else:
        print("Link succeeded (type '%s')." % new_pad_type)

    # label.exit
    # Unreference the new pad's caps, if we got them
    if new_pad_caps is not None:
        # new_pad_caps.unref()
        pass
    # Unreference the sink pad
    # sink_pad.unref()
    return None


def run():
    # Structure to contain all our information, so we can pass it to callbacks
    custom_data = {
        "pipeline": None,
        "source": None,
        "convert": None,
        "resample": None,
        "sink": None
    }

    terminate = False
    # Initialize GStreamer
    Gst.init(sys.argv[1:])

    # Create the elements
    custom_data["source"] = Gst.ElementFactory.make("uridecodebin", "source")
    custom_data["convert"] = Gst.ElementFactory.make("audioconvert", "convert")
    custom_data["resample"] = Gst.ElementFactory.make("audioresample", "resample")
    custom_data["sink"] = Gst.ElementFactory.make("autoaudiosink", "sink")

    # Create the empty pipeline
    custom_data["pipeline"] = Gst.Pipeline.new("test-pipeline")

    if custom_data["pipeline"] is None or \
            custom_data["source"] is None or \
            custom_data["convert"] is None or \
            custom_data["resample"] is None or \
            custom_data["sink"] is None:
        print("Not all elements could be created.")
        return -1

    # Build the pipeline. Note that we are NOT linking the source at this
    # point. We will do it later.
    custom_data["pipeline"].add(custom_data["source"])
    custom_data["pipeline"].add(custom_data["convert"])
    custom_data["pipeline"].add(custom_data["resample"])
    custom_data["pipeline"].add(custom_data["sink"])

    if custom_data["convert"].link(custom_data["resample"]) is False or \
            custom_data["resample"].link(custom_data["sink"]) is False:
        print("Elements could not be linked.")
        custom_data["pipeline"].unref()
        return -1

    # Set the URI to play
    custom_data["source"].set_property("uri",
                                       "https://www.freedesktop.org/software/gstreamer-sdk/data/media/sintel_trailer-480p.webm")

    # Connect to the pad-added signal
    custom_data["source"].connect("pad-added", pad_added_handler, custom_data)

    # Start playing
    ret = custom_data["pipeline"].set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        print("Unable to set the pipeline to the playing state.")
        # custom_data["pipeline"].unref()
        return -1

    # Listen to the bus
    bus = custom_data["pipeline"].get_bus()

    terminate = True
    while terminate == True:
        msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE,
                                     Gst.MessageType.STATE_CHANGED | Gst.MessageType.ERROR | Gst.MessageType.EOS)
        # Parse message
        if msg is not None:
            if msg.type == Gst.MessageType.ERROR:
                err, dbg_info = msg.parse_error()
                print("Error received from element %s: %s" % (msg.src.name, err.message))
                print("Debugging information: %s" % (dbg_info if dbg_info is not None else "None"))
                terminate = False
            elif msg.type == Gst.MessageType.EOS:
                print("End-Of-Stream reached.")
                terminate = False
            elif msg.type == Gst.MessageType.STATE_CHANGED:
                # We are only interested in state-changed messages from the pipeline
                if msg.src == custom_data["pipeline"]:
                    old_state, new_state, pending = msg.parse_state_changed()
                    print("Pipeline state changed from %s to %s:" % (
                    Gst.Element.state_get_name(old_state), Gst.Element.state_get_name(new_state)))
            else:
                # We should not reach here
                print("Unexpected message received.")

    # Free resources
    bus.unref()
    custom_data["pipeline"].set_state(Gst.State.NULL)
    # custom_data["pipeline"].unref()

    return None


if __name__ == "__main__":
    run()
