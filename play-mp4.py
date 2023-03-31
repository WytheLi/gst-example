# !/usr/bin/env python3
# GStreamer播放MP4文件
# 使用插件：filesrc、qtdemux
# GStreamer播放mp4的命令行如下：
"""
gst-launch-1.0 --gst-debug-level=3 \
filesrc location="01.mp4" ! qtdemux name=demux \
demux.audio_0 ! queue ! faad ! audioconvert ! autoaudiosink \
demux.video_0 ! queue ! avdec_h264 ! videoconvert ! xvimagesink
"""

import logging
import sys
import gi

gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GLib

logging.basicConfig(level=logging.DEBUG, format="[%(name)s] [%(levelname)8s] - %(message)s")
logger = logging.getLogger(__name__)


def cb_demuxer_newpad(demux, new_pad, queue_v, queue_a):
    """
        demux创建新pad时，指定其与某个pad连接
    :param demux:
    :param new_pad:
    :param queue_v:
    :param queue_a:
    :return:
    """
    if new_pad.get_property("template").name_template == "video_%u":
        v_pad = queue_v.get_static_pad("sink")
        new_pad.link(v_pad)
    elif new_pad.get_property("template").name_template == "audio_%u":
        a_pad = queue_a.get_static_pad("sink")
        new_pad.link(a_pad)
    else:
        pass


def run():
    pipeline = None
    bus = None
    message = None

    # initialize GStreamer
    Gst.init(sys.argv[1:])
    # 创建elements
    pipeline = Gst.Pipeline.new("MP4-Play")
    src = Gst.ElementFactory.make("filesrc", "src")
    demuxer = Gst.ElementFactory.make("qtdemux", "demux")  # 将QuickTime格式文件（如mp4）分解成音频和视频流
    # 创建视频队列element视频缓存
    queuev = Gst.ElementFactory.make("queue", "queuev")
    decodev = Gst.ElementFactory.make("avdec_h264", "decodev")  # ffmpeg插件avdec_h264
    convv = Gst.ElementFactory.make("videoconvert", "convv")  # 视频转换插件
    sinkv = Gst.ElementFactory.make("ximagesink", "sinkv")  # 图像接收器，xvimagesink、ximagesink有啥区别？
    # 创建音频队列element
    queuea = Gst.ElementFactory.make("queue", "queuea")
    decodea = Gst.ElementFactory.make("faad", "decodea")  # ffmpeg插件faad
    conva = Gst.ElementFactory.make("audioconvert", "conva")  # 视频转换元素
    sinka = Gst.ElementFactory.make("autoaudiosink", "sinka")  # 自动音频接收器
    # 播放地址（这里location表示视频和代码在同一个目录）
    src.set_property("location", "01.mp4")
    # 添加pad时回调
    demuxer.connect("pad-added", cb_demuxer_newpad, queuev, queuea)

    # 向管道中添加插件
    pipeline.add(src)
    pipeline.add(demuxer)

    pipeline.add(queuev)
    pipeline.add(decodev)
    pipeline.add(convv)
    pipeline.add(sinkv)

    pipeline.add(queuea)
    pipeline.add(decodea)
    pipeline.add(conva)
    pipeline.add(sinka)

    # link elements
    src.link(demuxer)

    queuev.link(decodev)
    decodev.link(convv)
    convv.link(sinkv)

    queuea.link(decodea)
    decodea.link(conva)
    conva.link(sinka)

    pipeline.set_state(Gst.State.PLAYING)
    print(Gst.StateChangeReturn)

    # Listen to the bus
    bus = pipeline.get_bus()
    msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)

    # Parse message
    if msg:
        if msg.type == Gst.MessageType.ERROR:
            err, debug_info = msg.parse_error()
            print(f"Error received from element {msg.src.get_name()}: {err.message}")
            print(f"Debugging information: {debug_info if debug_info else 'none'}")
        elif msg.type == Gst.MessageType.EOS:
            logger.info("End-Of-Stream reached.")
        else:
            # This should not happen as we only asked for ERRORs and EOS
            print("Unexpected message received.")
    # free resources
    pipeline.set_state(Gst.State.NULL)

    return None


if __name__ == "__main__":
    run()
