import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib

from cameras import cameras

Gst.init(None)


def run_cpu(display=True):

    pipelines = []

    for name, config in cameras.items():

        url = config["url"]
        codec = config["codec"]

        print(f"Starting CPU: {name} ({codec})")

        if codec == "h264":
            decoder = """
                rtph264depay !
                h264parse !
                avdec_h264 !
            """

        elif codec == "h265":
            decoder = """
                rtph265depay !
                h265parse !
                avdec_h265 !
            """

        else:
            print(f"Unknown codec for {name}: {codec}")
            continue

        if display:
            sink = "videoconvert ! autovideosink sync=false"
        else:
            sink = "fakesink"

        pipeline = Gst.parse_launch(
            f'''
            rtspsrc location="{url}" latency=100 !
            {decoder}
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