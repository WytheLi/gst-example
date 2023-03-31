# !/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Time     : 2023/3/30 11:26
# @Auther   :
# @File     : basic-tutorial-05.py
# GUI工具包集成，未完成
import sys
import gi

gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '4.0')

from gi.repository import Gst, Gtk, GObject, GLib


# Gst.CLOCK_TIME_NONE= 18446744073709551615
# #define GST_CLOCK_TIME_IS_VALID(time)   (((GstClockTime)(time)) != GST_CLOCK_TIME_NONE)
def GST_CLOCK_TIME_IS_VALID(time):
    if time is not Gst.CLOCK_TIME_NONE:
        return True
    else:
        return False


# This function is called when new metadata is discovered in the stream
def tags_cb(play_bin, stream, _custom_data):
    # We are possibly in a GStreamer working thread, so we notify the main
    # thread of this event through a message in the bus
    play_bin.post_message(Gst.Message.new_application(play_bin, Gst.Structure.new_empty("tags-changed")))


# This function is called when an error message is posted on the bus
def error_cb(bus, msg, _custom_data):
    err = None
    debug_info = None

    # Print error details on the screen
    err, debug_info = msg.parse_error()
    print("Error received from element %s: %s" % (msg.src, err.message))
    print("Debugging information: %s" % (debug_info if debug_info else "none"))

    # Set the pipeline to READY (which stops playback)
    _custom_data["playbin"].set_state(Gst.State.READY)


# This function is called when an End-Of-Stream message is posted on the bus.
# We just set the pipeline to READY (which stops playback)
def eos_cb(bus, msg, _custom_data):
    print("End-Of-Stream reached.")
    _custom_data["playbin"].set_state(Gst.State.READY)


# This function is called periodically to refresh the GUI
def refresh_ui(_custom_data):
    current = -1

    # We do not want to update anything unless we are in the PAUSED or PLAYING states
    if _custom_data["state"] < Gst.State.PAUSED:
        return True

    # If we didn't know it yet, query the stream duration */
    if not GST_CLOCK_TIME_IS_VALID(_custom_data["duration"]):
        ret, _custom_data["duration"] = _custom_data["playbin"].query_duration(Gst.Format.TIME)
        if not ret:
            print("Could not query current duration.")
        else:
            # Set the range of the slider to the clip duration, in SECONDS
            _custom_data["slider"].set_range(0, _custom_data["duration"] / Gst.SECOND)

    ret, current = _custom_data["playbin"].query_position(Gst.Format.TIME)
    if ret:
        # Block the "value-changed" signal, so the slider_cb function is not called
        # (which would trigger a seek the user has not requested)
        GObject.signal_handler_block(_custom_data["slider"], _custom_data["slider_update_signal_id"])
        # Set the position of the slider to the current pipeline position, in SECONDS
        _custom_data["slider"].set_value(current / Gst.SECOND)
        # Re-enable the signal
        GObject.signal_handler_unblock(_custom_data["slider"], _custom_data["slider_update_signal_id"])
    return True


# This function is called when the pipeline changes states. We use it to
# keep track of the current state.
def state_changed_cb(bus, msg, _custom_data):
    old_state, new_state, pending_state = None
    old_state, new_state, pending_state = msg.parse_state_changed
    if msg.src == _custom_data["playbin"]:
        _custom_data["state"] = new_state
        print("State set to %s" % (Gst.Element.state_get_name(new_state)))
        if old_state == Gst.State.READY and new_state == Gst.State.PAUSED:
            # For extra responsiveness, we refresh the GUI as soon as we reach the PAUSED state
            refresh_ui(_custom_data)


# Extract metadata from all the streams and write it to the text widget in the GUI
def analyze_streams(_custom_data):
    # Clean current contents of the widget
    text = _custom_data["streams_list"].get_buffer()
    text.set_text("", -1)
    # Read some properties

    n_video = _custom_data["playbin"].get_property("n-video")
    n_audio = _custom_data["playbin"].get_property("n-audio")
    n_text = _custom_data["playbin"].get_property("n-text")

    for i in range(n_video):
        tages = None
        # Retrieve the stream's video tags
        GObject.signal_emitv()
        _custom_data["playbin"].emit("get-video-tags", i, tags)


"""
  for (i = 0; i < n_video; i++) {
    tags = NULL;
    /* Retrieve the stream's video tags */
    g_signal_emit_by_name (data->playbin, "get-video-tags", i, &tags);
    if (tags) {
      total_str = g_strdup_printf ("video stream %d:\n", i);
      gtk_text_buffer_insert_at_cursor (text, total_str, -1);
      g_free (total_str);
      gst_tag_list_get_string (tags, GST_TAG_VIDEO_CODEC, &str);
      total_str = g_strdup_printf ("  codec: %s\n", str ? str : "unknown");
      gtk_text_buffer_insert_at_cursor (text, total_str, -1);
      g_free (total_str);
      g_free (str);
      gst_tag_list_free (tags);
    }
  }

  for (i = 0; i < n_audio; i++) {
    tags = NULL;
    /* Retrieve the stream's audio tags */
    g_signal_emit_by_name (data->playbin, "get-audio-tags", i, &tags);
    if (tags) {
      total_str = g_strdup_printf ("\naudio stream %d:\n", i);
      gtk_text_buffer_insert_at_cursor (text, total_str, -1);
      g_free (total_str);
      if (gst_tag_list_get_string (tags, GST_TAG_AUDIO_CODEC, &str)) {
        total_str = g_strdup_printf ("  codec: %s\n", str);
        gtk_text_buffer_insert_at_cursor (text, total_str, -1);
        g_free (total_str);
        g_free (str);
      }
      if (gst_tag_list_get_string (tags, GST_TAG_LANGUAGE_CODE, &str)) {
        total_str = g_strdup_printf ("  language: %s\n", str);
        gtk_text_buffer_insert_at_cursor (text, total_str, -1);
        g_free (total_str);
        g_free (str);
      }
      if (gst_tag_list_get_uint (tags, GST_TAG_BITRATE, &rate)) {
        total_str = g_strdup_printf ("  bitrate: %d\n", rate);
        gtk_text_buffer_insert_at_cursor (text, total_str, -1);
        g_free (total_str);
      }
      gst_tag_list_free (tags);
    }
  }

  for (i = 0; i < n_text; i++) {
    tags = NULL;
    /* Retrieve the stream's subtitle tags */
    g_signal_emit_by_name (data->playbin, "get-text-tags", i, &tags);
    if (tags) {
      total_str = g_strdup_printf ("\nsubtitle stream %d:\n", i);
      gtk_text_buffer_insert_at_cursor (text, total_str, -1);
      g_free (total_str);
      if (gst_tag_list_get_string (tags, GST_TAG_LANGUAGE_CODE, &str)) {
        total_str = g_strdup_printf ("  language: %s\n", str);
        gtk_text_buffer_insert_at_cursor (text, total_str, -1);
        g_free (total_str);
        g_free (str);
      }
      gst_tag_list_free (tags);
    }
  }
}
"""


# This function is called when the PLAY button is clicked
def play_cb(button, _custom_data):
    _custom_data["playbin"].set_state(Gst.State.PLAYING)


# This function is called when the PAUSE button is clicked
def pause_cb(button, _custom_data):
    _custom_data["playbin"].set_state(Gst.State.PAUSED)


# This function is called when the STOP button is clicked
def stop_cb(button, _custom_data):
    _custom_data["playbin"].set_state(Gst.State.READY)


# This function is called when the main window is closed
def delete_event_cb(widget, event, _custom_data):
    stop_cb(None, _custom_data)
    Gtk.quit()


# This function is called when the slider changes its position. We perform a seek to the
# new position here.
def slider_cb(range, _custom_data):
    value = _custom_data["slider"].get_value()
    _custom_data["playbin"].seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                        value * Gst.SECOND)


# This creates all the GTK+ widgets that compose our application, and registers the callbacks
def create_ui(_custom_data):
    main_window = None  # The uppermost window, containing all other windows
    video_window = None  # The drawing area where the video will be shown
    main_box = None  # VBox to hold main_hbox and the controls
    main_hbox = None  # HBox to hold the video_window and the stream info text widget
    controls = None  # HBox to hold the buttons and the slider
    play_button = None  # Buttons
    pause_button = None
    stop_button = None

    main_window = Gtk.Window.new(GTK_WINDOW_TOPLEVEL)
    main_window.connect("delete-event", delete_event_cb, _custom_data)

    video_window = Gtk.DrawingArea.new()
    video_window.set_double_buffered(False)
    video_window.connect("realize", realize_cb, _custom_data)
    video_window.connect("draw", draw_cb, _custom_data)

    play_button = Gtk.Button.new_from_icon_name("media-playback-start", Gtk.IconSize.SMALL_TOOLBAR)
    play_button.connect("clicked", play_cb, _custom_data)

    pause_button = Gtk.Button.new_from_icon_name("media-playback-pause", Gtk.IconSize.SMALL_TOOLBAR)
    pause_button.connect("clicked", pause_cb, _custom_data)

    stop_button = Gtk.Button.new_from_icon_name("media-playback-stop", Gtk.IconSize.SMALL_TOOLBAR)
    stop_button.connect("clicked", stop_cb, _custom_data)

    _custom_data["slider"] = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
    _custom_data["slider"].set_draw_value(0)
    _custom_data["slider_update_signal_id"] = _custom_data["slider"].connect("value-changed", slider_cb, _custom_data)

    _custom_data["streams_list"] = Gtk.TextView.new()
    _custom_data["streams_list"].set_editable(Fasle)

    controls = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
    controls.pack_start(play_button, False, False, 2)
    controls.pack_start(pause_button, False, False, 2)
    controls.pack_start(stop_button, False, False, 2)
    controls.pack_start(_custom_data["slider"], True, True, 2)

    main_hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
    main_hbox.pack_start(video_window, True, True, 0)
    main_hbox.pack_start(_custom_data["streams_list"], False, False, 2)

    main_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
    main_box.pack_start(main_hbox, True, True, 0)
    main_box.pack_start(controls, False, False, 0)
    main_window.add(main_box)
    main_window.set_default_size(640, 480)
    main_window.show_all()


# This function is called when an "application" message is posted on the bus.
# Here we retrieve the message posted by the tags_cb callback
def application_cb(bus, msg, _custom_data):
    if GLib.strcmp0(msg.get_structure().get_name(), "tags-changed") == 0:
        # If the message is the "tags-changed" (only one we are currently issuing), update
        # the stream info GUI
        analyze_streams(_custom_data)


def run():
    # Initialize GTK
    Gtk.init(sys.argv[1:])

    # 初始化 GStreamer
    Gst.init(sys.argv[1:])

    custom_data = {
        "playbin": None,  # Our one and only pipeline
        "slider": None,  # Slider widget to keep track of current position
        "streams_list": None,  # Text widget to display info about the streams
        "slider_update_signal_id": None,  # Signal ID for the slider update signal
        "state": None,  # Current state of the pipeline
        "duration": None  # Duration of the clip, in nanoseconds
    }

    custom_data["playbin"] = Gst.ElementFactory.make("playbin", "playbin")
    if custom_data["playbin"] is None:
        print("Not all elements could be created.")
        return -1
    custom_data["playbin"].set_property("uri",
                                        "https://www.freedesktop.org/software/gstreamer-sdk/data/media/sintel_trailer-480p.webm")

    # Connect to interesting signals in playbin
    custom_data["playbin"].connect("video-tags-changed", tags_cb, custom_data)
    custom_data["playbin"].connect("audio-tags-changed", tags_cb, custom_data)
    custom_data["playbin"].connect("text-tags-changed", tags_cb, custom_data)

    # Create the GUI
    create_ui(custom_data)

    # Instruct the bus to emit signals for each received message, and connect to the interesting signals
    bus = custom_data["playbin"].get_bus()
    bus.add_signal_watch()
    bus.connect("message::error", error_cb, custom_data)
    bus.connect("message::eos", eos_cb, custom_data)
    bus.connect("message::state-changed", state_changed_cb, custom_data)
    bus.connect("message::application", application_cb, custom_data)
    bus.unref()
    pass


if __name__ == "__main__":
    run()
