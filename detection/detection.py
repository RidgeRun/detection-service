#  Copyright (C) 2024 RidgeRun, LLC (http://www.ridgerun.com)
#  All Rights Reserved.
#
#  The contents of this software are proprietary and confidential to RidgeRun,
#  LLC.  No part of this program may be photocopied, reproduced or translated
#  into another programming language without prior written consent of
#  RidgeRun, LLC.  The user is free to modify the source code after obtaining
#  a software license from RidgeRun.  All source code changes must be provided
#  back to RidgeRun without any encumbrance.

"""
Object detection from vst video
"""

import logging

import numpy as np
from jetson_utils import videoSource
from mmj_utils.vst import VST
from rrmsutils.schemagenerator import SchemaGenerator
from sahi.predict import get_sliced_prediction

from detection.nanoowlmodel import NanoOwlModel

logger = logging.getLogger("detection")


class Detection:
    """
    Detection class
    """

    def __init__(self, search_queue, source_queue,
                 vst_uri="http://0.0.0.0:81", redis_host="0.0.0.0",
                 redis_port=6379, redis_stream="detection", objects=None, thresholds=None,
                 vertical_slices=1, horizontal_slices=1):
        if objects is None:
            objects = ["a person"]

        if thresholds is None:
            thresholds = [0.2] * len(objects)

        self._search_queue = search_queue
        self._source_queue = source_queue
        self._vst_uri = vst_uri
        self._default_objects = objects
        self._default_thresholds = thresholds
        self._redis_host = redis_host
        self._redis_port = redis_port
        self._redis_stream = redis_stream
        self._image_size = [0, 0]
        self._vertical_slices = vertical_slices
        self._horizontal_slices = horizontal_slices
        self._use_sahi = not (vertical_slices == 1 and horizontal_slices == 1)

    def get_input_stream(self, input_stream=None):
        """
        Determine VST input stream

        Args:
           input_stream (str, optional): name of the RTSP source stream or empty to use the first stream available through VST

        Returns:
           str: The uri for the requested stream
        """
        vst = VST(self._vst_uri)
        vst_rtsp_streams = vst.get_rtsp_streams()

        logger.info(f"VST input streams: {vst_rtsp_streams}")
        if len(vst_rtsp_streams) == 0:
            raise RuntimeError("No valid input source in VST")

        stream = None
        if input_stream:
            for rtsp_stream in vst_rtsp_streams:
                if rtsp_stream['name'] == input_stream:
                    stream = rtsp_stream
                    break

            if not stream:
                logger.warning(f"{input_stream} not found in VST")

        if not stream:
            stream = vst_rtsp_streams[0]

        return stream

    def process_search(self, search):
        """
        Process a search to get the list of requested objects
        with the corresponding thresholds. If only one threshold
        is provided it is used for all the objects

        Args:
          search(Search): model Search with the requested objects and thresholds

        Returns:
          Tuple[List(str), List(float)]: A tuple with two list: a list of extracted
          objects and a list of the corresponding thresholds
        """
        str_objects = search.objects[0]
        objects = str_objects.split(",")
        objects = [x.strip() for x in objects]

        str_thresholds = search.thresholds[0]
        thresholds = str_thresholds.split(",")
        thresholds = [float(x.strip()) for x in thresholds]

        if len(thresholds) == 1:
            thresholds = [thresholds[0]] * len(objects)

        return objects, thresholds

    def create_video_stream(self, stream_name=None):
        """
        Create video source stream for the given sensor name
        or use the first VST source available

        Args:
           stream_name(str): VST sensor name

        Returns:
           Tuple[videoSource, str]: A tuple of videoSource to
           capture frames and its corresponding sensor id
        """

        # Get input stream from vst
        input_stream = self.get_input_stream(stream_name)
        sensor_id = input_stream['streamID']

        logger.info(f"Get video from stream {input_stream}")

        # Create video input using jetson-utils
        v_source = videoSource(input_stream['url'], options={
            "latency": 50, "codec": "h264"})

        return v_source, sensor_id

    def prepare(self):
        """
        Prepare detection resources

        Returns:
           Tuple[videoSource, OwlPredictor, SchemaGenerator]: A tuple with a videoSource object to
           capture frames from vst stream, a predictor object to process detection
           prompt and SchemaGenerator to post messages to redis

        """

        # Load GenAI model
        model_name = "google/owlvit-base-patch32"
        model_engine = "/opt/nanoowl/data/owl_image_encoder_patch32.engine"
        predictor = NanoOwlModel(model_name=model_name,
                                 model_engine=model_engine)
        predictor.load_model()

        # Get first VST stream source
        v_input, sensor_id = self.create_video_stream()

        image_size = [v_input.GetWidth(), v_input.GetHeight()]
        self._image_size = image_size
        # Get schema format generator and connect to redis
        schema_gen = SchemaGenerator(sensor_id=sensor_id,
                                     image_size=image_size)
        schema_gen.connect_redis(
            self._redis_host, self._redis_port, self._redis_stream)

        return v_input, predictor, schema_gen

    def _calculate_slice_size(self, image_size):
        width = image_size[0]
        height = image_size[1]

        slice_width = int((width/self._horizontal_slices) * 1.2)
        slice_height = int((height/self._vertical_slices) * 1.2)

        logger.info(f"Using slices of {slice_width} x {slice_height}")

        return slice_width, slice_height

    def loop(self):
        """
        Get buffers from RTSP stream and detect requested objects
        """

        # Prepare resources
        v_input, predictor, schema_gen = self.prepare()

        # Initial prompt
        objects = self._default_objects
        thresholds = self._default_thresholds
        predictor.set_detection_objects(objects, thresholds)

        logger.info(
            f"Initial prompt objects={objects} thresholds={thresholds}")

        if self._use_sahi:
            slice_width, slice_height = self._calculate_slice_size(
                self._image_size)

        while True:
            # Get source updates
            if not self._source_queue.empty():
                input_name = self._source_queue.get()
                v_input, _ = self.create_video_stream(input_name)
                self._image_size = [0, 0]

            # Get search updates
            if not self._search_queue.empty():
                objects, thresholds = self.process_search(
                    self._search_queue.get())
                predictor.set_detection_objects(objects, thresholds)

            # Capture next image
            image = v_input.Capture()
            if image is None:
                logger.warning("Capture timeout")
                continue

            if self._image_size == [0, 0]:
                image_size = [v_input.GetWidth(), v_input.GetHeight()]
                self._image_size = image_size
                schema_gen.image_size = image_size

                if self._use_sahi:
                    slice_width, slice_height = self._calculate_slice_size(
                        self._image_size)

            # Run model prediction
            if not self._use_sahi:
                predictor.perform_inference(image)
                output = predictor.original_predictions
                text_labels = [objects[x] for x in output.labels]
                bboxes = output.boxes.tolist()
            else:
                output = get_sliced_prediction(
                    np.ascontiguousarray(image),
                    predictor,
                    slice_height=slice_height,
                    slice_width=slice_width,
                    overlap_height_ratio=0.2,
                    overlap_width_ratio=0.2)

                bboxes = []
                text_labels = []
                predictions = output.object_prediction_list
                for prediction in predictions:
                    bboxes.append(prediction.bbox.to_xyxy())
                    text_labels.append(prediction.category.name)

            if text_labels:
                logger.debug(f"labels {text_labels} bboxes {bboxes}")
                schema_gen(text_labels, bboxes)
