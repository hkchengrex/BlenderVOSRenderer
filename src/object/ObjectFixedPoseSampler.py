import bpy

from src.utility.BlenderUtility import get_all_mesh_objects
from src.main.Module import Module
from src.utility.ItemCollection import ItemCollection

import mathutils
from mathutils import Vector, Euler
import bmesh
import sys
import numbers
from collections import defaultdict

class ObjectFixedPoseSampler(Module):
    """ Samples positions and rotations of selected object inside the sampling volume while performing mesh and bounding box collision checks.

    .. csv-table::
       :header: "Parameter", "Description"

       "objects_to_sample", "Here call an appropriate Provider (Getter) in order to select objects."
       "max_tries", "Amount of tries before giving up on an object and moving to the next one. Optional. Type: int. Default value: 1000."
       "pos_sampler", "Here call an appropriate Provider (Sampler) in order to sample position (XYZ 3d vector) for each object."
       "rot_sampler", "Here call an appropriate Provider (Sampler )in order to sample rotation (Euler angles 3d vector) for each object."
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self.bvh_tree = None

    def run(self, frame_id):
        objects = self.config.get_list("objects_to_sample", get_all_mesh_objects())

        src_poses = self.config.get_list("poses")
        for obj in objects:
            if obj.type == "MESH":
                position = obj.location
                rotation = obj.rotation_euler

                frame_id = frame_id % len(src_poses)

                position = position + Vector(src_poses[frame_id]['location'])
                rotation.rotate(Euler(src_poses[frame_id]['rotation']))

                obj.location = position
                obj.rotation_euler = rotation
                bpy.context.view_layer.update()


    def insert_key_frames(self, obj, frame_id):
        """ Insert key frames for given object pose

        :param obj: Loaded object
        :param frame_id: The frame number where key frames should be inserted.
        """

        obj.keyframe_insert(data_path='location', frame=frame_id)
        obj.keyframe_insert(data_path='rotation_euler', frame=frame_id)
