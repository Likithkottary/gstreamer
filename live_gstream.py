import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib
from cameras import cameras

Gst.init(None)

def run_cpu(display=True):

    pipelines = []

    for name, url in cameras.items():

        print(f"Starting CPU: {name}")

        if display:
            sink = "videoconvert ! autovideosink sync=false"
        else:
            sink = "fakesink"

        pipeline = Gst.parse_launch(
            f'''
            rtspsrc location="{url}" latency=100 !
            rtph265depay !
            h265parse !
            avdec_h265 !
            videoscale !
            video/x-raw,width=640,height=480 !
            {sink}
            '''
        )

        pipeline.set_name(name)
        pipeline.set_state(Gst.State.PLAYING)

        pipelines.append(pipeline)

    loop = GLib.MainLoop()

    try:
        loop.run()

    except KeyboardInterrupt:
        print("Stopping CPU streams...")

    finally:
        for pipeline in pipelines:
            pipeline.set_state(Gst.State.NULL)


run_cpu(display=True)