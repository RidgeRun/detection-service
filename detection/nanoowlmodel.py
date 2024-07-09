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
NanoOwl model
"""

from typing import List, Optional

import numpy as np
from nanoowl.owl_predictor import OwlPredictor
from PIL import Image
from sahi.models.base import DetectionModel
from sahi.prediction import ObjectPrediction


class NanoOwlModel(DetectionModel):
    """
    NanoOwl detection model for SAHI
    """

    def __init__(self, model_name: str, model_engine: str = None, **kwargs):
        self.model_name = model_name
        self.model = None
        self.objects = None
        self.objects_encoding = None
        self.objects_threshold = None
        self._original_predictions = None
        self._object_prediction_list_per_image = None
        super().__init__(model_path=model_engine, **kwargs)

    def set_detection_objects(self, objects, thresholds):
        """
        Set detection objects and thresholds.

        Args:
          objects: array of objects to detect
          threshold: score threshold's array corresponding to the objects
        """
        self.objects = objects
        self.objects_encoding = self.model.encode_text(objects)
        self.objects_threshold = thresholds

    def load_model(self):
        """
        NanoOwl model is initialized and set to self.model
        """
        try:
            self.model = OwlPredictor(
                self.model_name,
                image_encoder_engine=self.model_path
            )

        except Exception as e:
            raise TypeError("Load model failed.", e) from e

    def perform_inference(self, image):
        """
        Object detection is performed over image and the prediction
        result is set to self._original_predictions.

        Args:
            image(Union[np.ndarray, PIL.Image]
                A numpy array or PIL.Image that contains the image to be predicted.

        """

        if isinstance(image, np.ndarray):
            if image.shape[0] < 5:  # image in CHW
                image = image[:, :, ::-1]
            image_pil = Image.fromarray(image)
        else:
            image_pil = image

        # Run model prediction
        output = self.model.predict(
            image=image_pil,
            text=self.objects,
            text_encodings=self.objects_encoding,
            threshold=self.objects_threshold,
            pad_square=True
        )
        self._original_predictions = output

    def _create_object_prediction_list_from_original_predictions(
            self,
            shift_amount_list: Optional[List[List[int]]] = None,
            full_shape_list: Optional[List[List[int]]] = None):

        predictions = self._original_predictions
        labels = predictions.labels
        bboxes = predictions.boxes
        scores = predictions.scores

        if shift_amount_list is None:
            shift_amount_list = [[0, 0]]

        object_prediction_list_per_image = []
        object_prediction_list = []
        for i, label in enumerate(labels):
            object_prediction = ObjectPrediction(
                bbox=bboxes[i].cpu(),
                category_id=int(label),
                category_name=self.objects[label],
                shift_amount=shift_amount_list,
                score=scores[i],
                full_shape=full_shape_list,
            )
            object_prediction_list.append(object_prediction)

        object_prediction_list_per_image.append(object_prediction_list)
        self._object_prediction_list_per_image = object_prediction_list_per_image
