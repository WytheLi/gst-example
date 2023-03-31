# !/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Time     : 2023/3/30 11:31
# @Auther   :
# @File     : basic-tutorial-08.py
# 缩短管道（push_data函数还未完成）
import sys
import gi
import struct

gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gst", "1.0")
gi.require_version("GstAudio", "1.0")

from gi.repository import Gst, GLib, GObject, GstAudio

CHUNK_SIZE = 1024   # Amount of bytes we are sending in each buffer
SAMPLE_RATE = 44100 # Samples per second we are sending


def int_to_bytes(x):
    if x >= 0:
        return x.to_bytes(2,'big')
    else:
        return x.to_bytes(2,'big',signed=True)

# This method is called by the idle GSource in the mainloop, to feed CHUNK_SIZE bytes into appsrc.
# The idle handler is added to the mainloop when appsrc requests us to start sending data (need-data signal)
# and is removed when appsrc has enough data (enough-data signal).
#此方法由mainloop中的空闲GSource调用，以将CHUNK\u大小的字节提供给appsrc。
#当appsrc请求我们开始发送数据（需要数据信号）时，空闲处理程序被添加到主循环中
#当appsrc有足够的数据（足够的数据信号）时，将删除。
def push_data(data):
    print("push_data")
    num_samples = int(CHUNK_SIZE / 2)  # Because each sample is 16 bits
    # Create a new empty buffer
    buffer = Gst.Buffer.new_allocate(None, CHUNK_SIZE, None)

    # Set its timestamp and duration
    buffer.dts      = Gst.util_uint64_scale(data["num_samples"],Gst.SECOND,SAMPLE_RATE)
    buffer.duration = Gst.util_uint64_scale(num_samples,Gst.SECOND,SAMPLE_RATE)

    # Generate some psychodelic waveform
    ret, map_info = buffer.map(Gst.MapFlags.WRITE)
    raw_data_list = list(map_info.data)

    # map_info.data:bytes  ---> raw:gint16:signed short
    data["c"] += data["d"]
    data["d"] -= data["c"] / 1000
    freq = 1100 + 1000 * data["d"]
    for i in range(num_samples):
        data["a"] += data["b"]
        data["b"] -= data["a"] / freq
        bytes_val_list = list( int_to_bytes( int(500 * data["a"]) ) )
        raw_data_list[i*2] = bytes_val_list[0]
        raw_data_list[i*2+1] = bytes_val_list[1]

    raw_bytes = bytes(raw_data_list)
    # map_info.data = raw_bytes                  #?????

    # Push the buffer into the appsrc
    # g_signal_emit_by_name (data->app_source, "push-buffer", buffer, &ret);
    ret = data["app_source"].emit("push-buffer",buffer)

    # Free the buffer now that we are done with it
    # buffer.unref()

    if ret != Gst.FlowReturn.OK:
        # We got some error, stop sending data
        return False
    return True



# This signal callback triggers when appsrc needs data. Here, we add an idle handler
# to the mainloop to start pushing data into the appsrc
def start_feed(source,size,data):
    print("start_feed")
    if data["sourceid"] == 0:
        print("Start feeding")
        # data["sourceid"] = GLib.idle_add(priority, push_data, data)
        data["sourceid"] = GLib.idle_add(push_data, data)


# This callback triggers when appsrc has enough data and we can stop sending.
# We remove the idle handler from the mainloop
def stop_feed(source, data):
    print("stop_feed")
    if data["sourceid"] != 0:
        print("Stop feeding")
        GLib.source_remove(data["sourceid"])
        data["sourceid"] = 0

# The appsink has received a buffer
def new_sample(sink,data):
    print("new_sample")
    # sample = Gst.Sample.new()
    # Retrieve the buffer 检索缓冲区
    # g_signal_emit_by_name (sink, "pull-sample", &sample);
    ret = sink.emit("pull-sample")
    if ret:
        # The only thing we do in this example is print a * to indicate a received buffer
        print ("*")
        return Gst.FlowReturn.OK
    return Gst.FlowReturn.ERROR



# This function is called when an error message is posted on the bus
def error_cb(bus, msg, data):
    print("error_cb")
    # Print error details on the screen
    err ,debug_info = msg.parse_error()
    print("Error received from element %s: %s\n" % (msg.src.name, err.message))
    print("Debugging information: %s\n", debug_info if debug_info else "None")
    data["main_loop"].quit()


def run():
    # Structure to contain all our information, so we can pass it to callbacks
    custom_data = {
        "pipeline"       : None,
        "app_source"     : None,
        "tee"            : None,
        "audio_queue"    : None,
        "audio_convert1" : None,
        "audio_resample" : None,
        "audio_sink"     : None,
        "video_queue"    : None,
        "audio_convert2" : None,
        "visual"         : None,
        "video_convert"  : None,
        "video_sink"     : None,
        "app_queue"      : None,
        "app_sink"       : None,
        "num_samples"    : 0, # Number of samples generated so far (for timestamp generation)
                                #For waveform generation
        "a"              : 0,
        "b"              : 0,
        "c"              : 0,
        "d"              : 0,
        "sourceid"       : 0, # To control the GSource
        "main_loop"      : None, # GLib's Main Loop
    }

    custom_data["b"] = 1 # For waveform generation
    custom_data["d"] = 1

    # Initialize GStreamer
    Gst.init(sys.argv[1:])

    # Create the empty pipeline
    custom_data["pipeline"] = Gst.Pipeline.new("test-pipeline")

    # Create the elements
    custom_data["app_source"]     = Gst.ElementFactory.make("appsrc", "audio_source")
    custom_data["tee"]            = Gst.ElementFactory.make("tee", "tee")
    custom_data["audio_queue"]    = Gst.ElementFactory.make("queue", "audio_queue")
    custom_data["audio_convert1"] = Gst.ElementFactory.make("audioconvert", "audio_convert")
    custom_data["audio_resample"] = Gst.ElementFactory.make("audioresample", "audio_resample")
    custom_data["audio_sink"]     = Gst.ElementFactory.make("autoaudiosink", "audio_sink")
    custom_data["video_queue"]    = Gst.ElementFactory.make("queue", "video_queue")
    custom_data["audio_convert2"] = Gst.ElementFactory.make("audioconvert", "audio_convert2")
    custom_data["visual"]         = Gst.ElementFactory.make("wavescope", "visual")
    custom_data["video_convert"]  = Gst.ElementFactory.make("videoconvert", "video_convert")
    custom_data["video_sink"]     = Gst.ElementFactory.make("autovideosink", "video_sink")
    custom_data["app_queue"]      = Gst.ElementFactory.make("queue", "app_queue")
    custom_data["app_sink"]       = Gst.ElementFactory.make("appsink", "app_sink")

    if not custom_data["pipeline"] or not custom_data["app_source"] or not custom_data["tee"] or \
       not custom_data["audio_queue"] or not custom_data["audio_convert1"] or not custom_data["audio_resample"] or \
       not custom_data["audio_sink"] or not custom_data["video_queue"] or not custom_data["audio_convert2"] or \
       not custom_data["visual"] or not custom_data["video_convert"] or not custom_data["video_sink"] or \
       not custom_data["app_queue"] or not custom_data["app_sink"] :
       print("Not all elements could be created.")
       return -1

    # Configure wavescope
    custom_data["visual"].set_property("shader",0)
    custom_data["visual"].set_property("style",0)

    # Configure appsrc
    info = GstAudio.AudioInfo.new()
    info.set_format(GstAudio.AudioFormat.S16, SAMPLE_RATE, 1, None)
    audio_caps = info.to_caps()
    custom_data["app_source"].set_property("caps",audio_caps)
    custom_data["app_source"].set_property("format",Gst.Format.TIME)
    custom_data["app_source"].connect("need-data",start_feed,custom_data)
    custom_data["app_source"].connect("enough-data",stop_feed,custom_data)

    # Configure appsink
    custom_data["app_sink"].set_property("emit-signals",True)
    custom_data["app_sink"].set_property("caps",audio_caps)
    custom_data["app_sink"].connect("new-sample",new_sample,custom_data)

    # Link all elements that can be automatically linked because they have "Always" pads

    add_list = [
                custom_data["app_source"],custom_data["tee"],custom_data["audio_queue"],custom_data["audio_convert1"],
                custom_data["audio_resample"],custom_data["audio_sink"],custom_data["video_queue"],custom_data["audio_convert2"],
                custom_data["visual"],custom_data["video_convert"],custom_data["video_sink"],custom_data["app_queue"],custom_data["app_sink"]
                ]

    for element in add_list:
        custom_data["pipeline"].add(element)

    if custom_data["app_source"].link(custom_data["tee"]) != True or \
       custom_data["audio_queue"].link(custom_data["audio_convert1"]) != True or \
       custom_data["audio_convert1"].link(custom_data["audio_resample"]) != True or \
       custom_data["audio_resample"].link(custom_data["audio_sink"]) != True or \
       custom_data["video_queue"].link(custom_data["audio_convert2"]) != True or \
       custom_data["audio_convert2"].link(custom_data["visual"]) != True or \
       custom_data["visual"].link(custom_data["video_convert"]) != True or \
       custom_data["video_convert"].link(custom_data["video_sink"]) != True or \
       custom_data["app_queue"].link(custom_data["app_sink"]) != True:

       print("Elements could not be linked.")

       # custom_data["pipeline"].unref()
       return -1


    # Manually link the Tee, which has "Request" pads
    # tee_audio_pad = gst_element_request_pad_simple (data.tee, "src_%u")
    tee_audio_pad = custom_data["tee"].get_request_pad("src_%u")
    # g_print ("Obtained request pad %s for audio branch.\n", gst_pad_get_name (tee_audio_pad))
    print("Obtained request pad %s for audio branch.\n", tee_audio_pad.get_pad_template().name_template)
    queue_audio_pad = custom_data["audio_queue"].get_static_pad("sink")
    tee_video_pad =  custom_data["tee"].get_request_pad("src_%u")
    print ("Obtained request pad %s for video branch.\n", tee_video_pad.get_pad_template().name_template)
    queue_video_pad = custom_data["video_queue"].get_static_pad("sink")
    tee_app_pad = custom_data["tee"].get_request_pad("src_%u")
    print ("Obtained request pad %s for app branch.\n", tee_app_pad.get_pad_template().name_template)
    queue_app_pad = custom_data["app_queue"].get_static_pad("sink")


    if tee_audio_pad.link(queue_audio_pad) != Gst.PadLinkReturn.OK or \
        tee_video_pad.link(queue_video_pad) != Gst.PadLinkReturn.OK or \
        tee_app_pad.link(queue_app_pad) != Gst.PadLinkReturn.OK:
        print("Tee could not be linked\n")
        # custom_data["pipeline"].unref()
        return -1

    # queue_audio_pad.unref()
    # queue_video_pad.unref()
    # queue_app_pad.unref()

    # Instruct the bus to emit signals for each received message, and connect to the interesting signals
    bus = custom_data["pipeline"].get_bus()
    bus.add_signal_watch()
    bus.connect("message::error",error_cb,custom_data)
    # bus.unref()

    # Start playing the pipeline
    custom_data["pipeline"].set_state(Gst.State.PLAYING)

    # Create a GLib Main Loop and set it to run
    custom_data["main_loop"] = GLib.MainLoop.new(None,False)
    custom_data["main_loop"].run()

    # Release the request pads from the Tee, and unref them

    custom_data["tee"].release_request_pad(tee_audio_pad)
    custom_data["tee"].release_request_pad(tee_video_pad)
    custom_data["tee"].release_request_pad(tee_app_pad)

    # tee_audio_pad.unref()
    # tee_video_pad.unref()
    # tee_app_pad.unref()

    # Free resources
    custom_data["pipeline"].set_state(Gst.State.NULL)
    # custom_data["pipeline"].unref()

    return 0


if __name__ == "__main__":
    run()