# !/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Time     : 2023/3/30 11:21
# @Auther   :
# @File     : play-srt.py
# 使用插件：
#                           video                   h264parse   capsfilter   avdec_h264    videoconvert   xvimagesink
# srtclientsrc   tsdemux            multiqueue
#                           audio                   aacparse    avdec_aac    audioconvert  autoaudiosink
"""
gst-launch-1.0 -v \
srtclientsrc uri="srt://192.168.35.194:10250" ! \
tsdemux name=demux \
demux. ! multiqueue name=queue ! h264parse ! capsfilter ! avdec_h264 ! videoconvert ! xvimagesink \
demux. ! queue. queue. ! aacparse ! avdec_aac ! audioconvert ! autoaudiosink

gst-launch-1.0 -v playbin uri=srt://192.168.35.194:10250 latency=100000000

tsdemux: 解复用 MPEG2 传输流
multiqueue:多队列
        默认队列大小限制为 5 个缓冲区、10MB 数据或 2 秒数据，以先达到者为准。请注意，缓冲区的数量将根据其他队列的填充级别动态增长。
h264parse:解析 H.264 流
capsfilter:
        该元素不会像这样修改数据，但可以对数据格式施加限制。
avdec_h264:libav h264 解码器
videoconvert:在多种视频格式之间转换视频帧。
xvimagesink:基于 Xv 的视频接收器
aacparse:高级音频编码解析器
        这是一个处理 ADIF 和 ADTS 流格式的 AAC 解析器。
        由于 ADIF 格式没有成帧，因此它不可搜索，也无法确定流持续时间。但是，可以搜索 ADTS 格式的 AAC 剪辑，并且解析器还可以估计播放位置和剪辑持续时间。

avdec_aac:libav aac解码器
audioconvert:将音频转换为不同的格式
            在各种可能的格式之间转换原始音频缓冲区。它支持整数到浮点数的转换、宽度/深度转换、符号和字节序转换和通道转换（即上混和下混），以及抖动和噪声整形。
autoaudiosink:用于自动检测到的音频接收器的包装器音频接收器
            是一种音频接收器，可自动检测要使用的适当音频接收器。它通过扫描注册表来查找在其元素信息的类字段中具有“Sink”和“Audio”并且还具有非零自动插入等级的所有元素。
"""
import sys
import gi
import datetime

gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
gi.require_version('Gst', '1.0')

from gi.repository import Gst, GObject, GLib


class SRTPlay:
    def __init__(self, uri=None):
        self.uri = uri
        # 初始化 GStreamer
        Gst.init(sys.argv[1:])

        # 创建elements
        self.pipeline = Gst.Pipeline.new("SRT-Play")
        self.src = Gst.ElementFactory.make("srtclientsrc", "src")
        self.demux = Gst.ElementFactory.make("tsdemux", "demux")
        self.queue = Gst.ElementFactory.make("multiqueue", "queue")
        self.parsev = Gst.ElementFactory.make("h264parse", "parsev")
        self.filter = Gst.ElementFactory.make("capsfilter", "filter")
        self.avdec_v = Gst.ElementFactory.make("avdec_h264", "avdec_v")
        self.convv = Gst.ElementFactory.make("videoconvert", "convv")  # 视频转换元素
        self.sinkv = Gst.ElementFactory.make("xvimagesink", "sinkv")  # 图像接收器
        self.parsea = Gst.ElementFactory.make("aacparse", "parsea")
        self.avdec_a = Gst.ElementFactory.make("avdec_aac", "avdec_a")
        self.conva = Gst.ElementFactory.make("audioconvert", "conva")  # 视频转换元素
        self.sinka = Gst.ElementFactory.make("autoaudiosink", "sinka")  # 自动音频接收器 autoaudiosink

        # Request video pad
        self.multiqueue_video_sink_pad = self.queue.get_request_pad("sink_%u")
        multiqueue_video_sink_pad_name = self.multiqueue_video_sink_pad.get_property("template").name_template
        print("Obtained request pad %s for video branch from multiqueue element.\n" % (multiqueue_video_sink_pad_name))

        # Request audio pad
        self.multiqueue_audio_sink_pad = self.queue.get_request_pad("sink_%u")
        multiqueue_audio_sink_pad_name = self.multiqueue_audio_sink_pad.get_property("template").name_template
        print("Obtained request pad %s for audio branch from multiqueue element.\n" % (multiqueue_audio_sink_pad_name))

        # 向管道中添加元件
        elements_list = [self.src, self.demux, self.queue, self.parsev, self.filter, self.avdec_v, self.convv,
                         self.sinkv, self.parsea, self.avdec_a, self.conva, self.sinka]
        if not self.add_elements_to_pipeline(elements_list):
            return False
        print("pipeline add elements ok.")

        # 连接elements
        if not self.src.link(self.demux):
            print("src link demux failed.")
            return False
        if not self.link_elements([self.queue, self.parsev, self.filter, self.avdec_v, self.convv, self.sinkv]):
            return False
        else:
            print("video Elements linked.")

        if not self.link_elements([self.queue, self.parsea, self.avdec_a, self.conva, self.sinka]):
            return False
        else:
            print("audio Elements linked.")

        self.demux.connect("pad-added", self.cb_demux_newpad)

        self.set_elements_property()

        self.add_keyboard()

    def play(self):
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret is Gst.StateChangeReturn.FAILURE:
            print("Unable to set the pipeline to the playing state.")
            return False
        elif ret is Gst.StateChangeReturn.NO_PREROLL:
            print("is_live")
        else:
            print("pipeline set state playing. ret=", ret)

        # self.loop = GLib.MainLoop()
        self.loop = GLib.MainLoop.new(None, False)
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.cb_bus_message)
        self.loop.run()

    def free(self):
        # Release the request pads from the Tee, and unref them
        self.queue.release_request_pad(self.multiqueue_video_sink_pad)
        self.queue.release_request_pad(self.multiqueue_audio_sink_pad)

        # Free resources
        self.pipeline.set_state(Gst.State.NULL)

    def cb_bus_message(self, bus, new_msg):
        if new_msg:
            msg_src_name = new_msg.src.get_name()
            msg_type = new_msg.type
            # print(msg_src_name, msg_type)
            if msg_type == Gst.MessageType.ERROR:
                err, debug_info = new_msg.parse_error()
                print("Error received from element %s:%s" % (msg_src_name, err.message))
                self.pipeline.set_state(Gst.State.READY)
                self.loop.quit()
            elif msg_type == Gst.MessageType.EOS:
                print("End-Of-Stream reached.")
                self.pipeline.set_state(Gst.State.READY)
                self.loop.quit()
            elif msg_type == Gst.MessageType.BUFFERING:
                percent = new_msg.parse_buffering()
                print("Gst.MessageType.BUFFERING. Buffering (%3d%%)" % (percent))
                # Wait until buffering is complete before start/resume playing
                if percent < 100:
                    self.pipeline.set_state(Gst.State.PAUSED)
                else:
                    self.pipeline.set_state(Gst.State.PLAYING)
                pass
            elif msg_type == Gst.MessageType.CLOCK_LOST:
                # Get a new clock
                self.pipeline.set_state(Gst.State.PAUSED)
                self.pipeline.set_state(Gst.State.PLAYING)
                print("clock lost, Get a new clock")
                pass
            elif msg_type == Gst.MessageType.STATE_CHANGED:
                # oldstate, newstate, pending = new_msg.parse_state_changed()
                # print("oldstate=",oldstate," newstate=",newstate," pending=",pending)
                pass
            else:
                # print("Unhandled message")
                pass
        else:
            print("Error new_msg=", new_msg)

    def cb_demux_newpad(self, demux, new_pad):
        pad_name = new_pad.get_property("template").name_template
        pad_current_caps = new_pad.get_current_caps()
        src_name = pad_current_caps.get_structure(0).get_name()
        # print("pad_name=",pad_name,"src_name=",src_name)

        if pad_name == "video_%01x_%05x":
            ret = new_pad.link(self.multiqueue_video_sink_pad)
            print("decode src", pad_name, "link multiqueue sink. ret=", ret)
        elif pad_name == "audio_%01x_%05x":
            ret = new_pad.link(self.multiqueue_audio_sink_pad)
            print("decode src", pad_name, "link multiqueue sink. ret=", ret)
        else:
            print("add a unknown new pad:", pad_name, "src_name:", src_name)
            pass

    def set_elements_property(self):
        delay = 100000000
        # 设置播放地址
        self.src.set_property("uri", self.uri)
        self.pipeline.set_latency(delay)  # 100ms 设置管道的延时，单位为ns
        print("set uri=%s" % self.uri)
        print("set pipeline latency=%dns" % delay)

    def add_elements_to_pipeline(self, elements_list):
        if self.pipeline:
            for element in elements_list:
                if not self.pipeline.add(element):
                    print("add element failed.")
                    return False
            return True
        else:
            print("pipeline is none.")
            return False

    def link_elements(self, elements_list):
        length = len(elements_list)
        if length < 2:
            print("length of list is < 2 .")
            return False

        element_link = elements_list[0]
        for element in elements_list[1:]:
            if element_link.link(element):
                element_link = element
            else:
                print("link element failed.")
                return False
        return True

    def add_keyboard(self):
        # Add a keyboard watch so we get notified of keystrokes
        io_stdin = GLib.IOChannel.unix_new(sys.stdin.fileno())
        # io_stdin.add_watch(GLib.IOCondition.IN,handle_keyboard) 方法已经弃用
        GLib.io_add_watch(io_stdin, GLib.PRIORITY_DEFAULT, GLib.IOCondition.IN, self.handle_keyboard)

        # Process keyboard input

    def handle_keyboard(self, source, cond):
        status, str, length, terminator_pos = source.read_line()
        if status != GLib.IOStatus.NORMAL:
            return True
        unichar_tolower_data = GLib.unichar_tolower(str[0])
        if 'q' == unichar_tolower_data:
            self.loop.quit()
        elif 'f' == unichar_tolower_data:
            print("get f from keyboard.")
            return True


if __name__ == "__main__":
    uri = "srt://192.168.35.194:10250"
    srt = SRTPlay(uri)
    srt.play()
    srt.free()
