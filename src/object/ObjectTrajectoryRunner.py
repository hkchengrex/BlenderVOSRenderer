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

    def run(self, n_frames):
        objects = get_mesh_objects_with_name(self.config.get_list('target_names'))

        for i in range(n_frames):
            for obj in objects:
                obj.location = Vector(self.poses[i]['location'])
                obj.rotation_euler = Euler(self.poses[i]['rotation'])

                obj.keyframe_insert(data_path='location', frame=i)
                obj.keyframe_insert(data_path='rotation_euler', frame=i)
