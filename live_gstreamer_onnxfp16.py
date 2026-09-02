import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib

import numpy as np
import onnxruntime as ort
from datetime import datetime

from cameras import cameras


Gst.init(None)


# =========================
# ONNX
# =========================

session = ort.InferenceSession(
    "./models/27knmodel.onnx",
    providers=["CPUExecutionProvider"]
)

input_name = session.get_inputs()[0].name

print("ONNX input:", session.get_inputs()[0].shape)
print("ONNX output:", session.get_outputs()[0].shape)


# =========================
# FRAME CALLBACK
# =========================

def on_frame(sink, name):

    sample = sink.emit("pull-sample")

    if sample is None:
        return Gst.FlowReturn.ERROR

    buffer = sample.get_buffer()

    success, map_info = buffer.map(Gst.MapFlags.READ)

    if not success:
        return Gst.FlowReturn.ERROR

    try:

        # GStreamer gives us 640x640 BGR
        frame = np.frombuffer(
            map_info.data,
            dtype=np.uint8
        ).reshape(640, 640, 3)


        # HWC -> CHW
        frame = frame.transpose(2, 0, 1)


        # uint8 -> float32
        frame = frame.astype(np.float32) / 255.0


        # Add batch dimension
        # [3,640,640] -> [1,3,640,640]
        frame = np.expand_dims(frame, axis=0)


        # =========================
        # ONNX INFERENCE
        # =========================

        output = session.run(
            None,
            {input_name: frame}
        )


        # =========================
        # DETECTION
        # =========================

        detections = output[0][0]

        # Expected format:
        # [6, number_of_predictions]
        #
        # 0-3 = box
        # 4   = class 0 score
        # 5   = class 1 score

        for detection in detections.T:

            class_scores = detection[4:]

            class_id = np.argmax(class_scores)

            confidence = class_scores[class_id]


            if class_id == 1 and confidence > 0.5:

                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] "
                    f"- {name} - Human detected"
                )

                break


    finally:

        buffer.unmap(map_info)


    return Gst.FlowReturn.OK


# =========================
# RUN CAMERAS
# =========================

def run():

    pipelines = []


    for name, config in cameras.items():

        url = config["url"]
        codec = config["codec"]


        # =========================
        # DECODER
        # =========================

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

            print(f"Unknown codec: {codec}")
            continue


        print(f"Starting {name} ({codec})")


        # =========================
        # GSTREAMER PIPELINE
        # =========================

        pipeline = Gst.parse_launch(
            f'''
            rtspsrc location="{url}" latency=100 !
            {decoder}

            videoscale !
            video/x-raw,width=640,height=640 !

            videorate !
            video/x-raw,framerate=1/1 !

            videoconvert !
            video/x-raw,format=BGR !

            appsink name=sink_{name}
            emit-signals=true
            sync=false
            max-buffers=1
            drop=true
            '''
        )


        # Get appsink
        sink = pipeline.get_by_name(
            f"sink_{name}"
        )


        # Connect callback
        sink.connect(
            "new-sample",
            on_frame,
            name
        )


        # Start pipeline
        pipeline.set_state(
            Gst.State.PLAYING
        )


        pipelines.append(pipeline)


    # =========================
    # MAIN LOOP
    # =========================

    loop = GLib.MainLoop()


    try:

        loop.run()

    except KeyboardInterrupt:

        print("Stopping...")


    finally:

        for pipeline in pipelines:

            pipeline.set_state(
                Gst.State.NULL
            )


# =========================
# START
# =========================

run()