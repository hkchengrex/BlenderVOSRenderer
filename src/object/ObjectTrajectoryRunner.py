import bpy

from src.utility.BlenderUtility import get_mesh_objects_with_name
from src.main.Module import Module
from src.utility.ItemCollection import ItemCollection

import mathutils
from mathutils import Vector, Euler
import bmesh
import sys
import numbers
from collections import defaultdict

class ObjectTrajectoryRunner(Module):
    """ Run a set of objects along the predefined trajectory

    .. csv-table::
       :header: "Parameter", "Description"

       "target_name", "Name of the object to be controlled."
       "poses", "Poses to be used in each time frame."
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self.poses = self.config.get_list("poses")

    def run(self, frame_id):
        objects = get_mesh_objects_with_name(self.config.get_list('target_names'))

        for obj in objects:
            obj.location = Vector(self.poses[frame_id]['location'])
            obj.rotation_euler = Euler(self.poses[frame_id]['rotation'])


    def insert_key_frames(self, obj, frame_id):
        """ Insert key frames for given object pose

        :param obj: Loaded object
        :param frame_id: The frame number where key frames should be inserted.
        """

        obj.keyframe_insert(data_path='location', frame=frame_id)
        obj.keyframe_insert(data_path='rotation_euler', frame=frame_id)
