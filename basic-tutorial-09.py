# !/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Time     : 2023/3/30 11:32
# @Auther   :
# @File     : basic-tutorial-09.py
import sys
import gi

gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gst", "1.0")
gi.require_version("GstPbutils", "1.0")


from gi.repository import Gst, GLib, GObject,GstPbutils



def GST_TIME_ARGS(time):
    if time == Gst.CLOCK_TIME_NONE:
        return "CLOCK_TIME_NONE"
    return "%u:%02u:%02u.%09u" % (time / (Gst.SECOND * 60 * 60),
                                  (time / (Gst.SECOND * 60)) % 60,
                                  (time / Gst.SECOND) % 60,
                                  time % Gst.SECOND)



# Print a tag in a human-readable format (name: value)
def print_tag_foreach ( tags, tag, user_data)
    pass
#   GValue val = { 0, };
#   gchar *str;
#   gint depth = GPOINTER_TO_INT (user_data);

#   gst_tag_list_copy_value (&val, tags, tag);

#   if (G_VALUE_HOLDS_STRING (&val))
#     str = g_value_dup_string (&val);
#   else
#     str = gst_value_serialize (&val);

#   g_print ("%*s%s: %s\n", 2 * depth, " ", gst_tag_get_nick (tag), str);
#   g_free (str);

#   g_value_unset (&val);




# Print information regarding a stream and its substreams, if any
def print_topology (info, depth):
    if not info:
        return
    print_stream_info(info, depth)

    next = info.get_next()
    if next:
        print_topology (next, depth + 1)
    elif:
        pass


'''
#define GST_IS_DISCOVERER_CONTAINER_INFO(obj) \   (G_TYPE_CHECK_INSTANCE_TYPE((obj),GST_TYPE_DISCOVERER_CONTAINER_INFO))
'''
"""

  GstDiscovererStreamInfo *next;
  if (!info)
    return;

  print_stream_info (info, depth);

  next = gst_discoverer_stream_info_get_next (info);
  if (next) {
    print_topology (next, depth + 1);
    gst_discoverer_stream_info_unref (next);
  } else if (GST_IS_DISCOVERER_CONTAINER_INFO (info)) {
    GList *tmp, *streams;

    streams = gst_discoverer_container_info_get_streams (GST_DISCOVERER_CONTAINER_INFO (info));
    for (tmp = streams; tmp; tmp = tmp->next) {
      GstDiscovererStreamInfo *tmpinf = (GstDiscovererStreamInfo *) tmp->data;
      print_topology (tmpinf, depth + 1);
    }
    gst_discoverer_stream_info_list_free (streams);
  }
}
"""



# This function is called every time the discoverer has information regarding
# one of the URIs we provided.
def on_discovered_cb(discoverer,info,err,data):

    uri    = info.get_uri(info)
    result = info.get_result(info)

    if result == GstPbutils.DiscovererResult.URI_INVALID:
        print("Invalid URI '%s'\n", uri)
    elif result == GstPbutils.DiscovererResult.ERROR:
        print ("Discoverer error: %s\n", err.message)
    elif result == GstPbutils.DiscovererResult.TIMEOUT:
        print ("Timeout\n")
    elif result == GstPbutils.DiscovererResult.MISSING_PLUGINS:
        str = info.get_misc().to_string()
        print ("Missing plugins: %s\n", str)
    elif result == GstPbutils.DiscovererResult.OK:
        print ("Discovered '%s'\n", uri)
    else:
        pass

    if result != GstPbutils.DiscovererResult.OK:
        print("This URI cannot be played\n")
        return

    # If we got no error, show the retrieved information
    print ("\nDuration: %s Gst.TIME_FORMAT \n" % ( GST_TIME_ARGS ( info.get_duration() ) ) );

    tags = info.get_tags()
    if tags:
        print("Tags:")
        tags.foreach(print_tag_foreach,None)

    print ("Seekable: %s\n", ("yes" if info.get_seekable() else "no"));

    sinfo = info.get_stream_info()
    if not sinfo:
        return

    print("Stream information:\n")
    print_topology (sinfo, 1);



# This function is called when the discoverer has finished examining
# all the URIs we provided.
def on_finished_cb (discoverer, data):
    print("Finished discovering\n")
    data["loop"].quit()



def run():

    # Structure to contain all our information, so we can pass it around
    custom_data = {
        "discoverer":None,
        "loop":None
    }

    uri = "https://www.freedesktop.org/software/gstreamer-sdk/data/media/sintel_trailer-480p.webm";

    # if a URI was provided, use it instead of the default one
    if len(sys.argv) > 1:
        uri = sys.argv[1]

    # Initialize GStreamer
    Gst.init(sys.argv[1:])

    # Instantiate the Discoverer
    custom_data["discoverer"] = GstPbutils.Discoverer.new(5 * Gst.SECOND)
    if not custom_data["discoverer"] :
        print("Error creating discoverer instance\n")
        return -1

    # Connect to the interesting signals
    custom_data["discoverer"].connect("discovered",on_discovered_cb,custom_data)
    custom_data["discoverer"].connect("finished",on_finished_cb,custom_data)

    # Start the discoverer process (nothing to do yet)
    custom_data["discoverer"].start()

    # Add a request to process asynchronously the URI passed through the command line

    if not custom_data["discoverer"].discover_uri_async(uri):
        print("Failed to start discovering URI '%s'\n" % uri )
        return -1

    # Create a GLib Main Loop and set it to run, so we can wait for the signals
    custom_data["loop"] = GLib.MainLoop.new(None, False)
    custom_data["loop"].run()

    # Stop the discoverer process
    custom_data["discoverer"].stop()

    # Free resources
    # data["loop"].unref()
    return 0

if __name__ == "__main__":
    run()
