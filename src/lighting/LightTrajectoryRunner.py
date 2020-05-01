import mathutils
import bpy
import random

import numpy.polynomial.polynomial as poly
from src.main.Module import Module
from src.utility.Utility import Utility
from mathutils import Vector, Euler


class LightTrajectoryRunner(Module):
    """ 
    Load a light source and run it along the predefined trajectory
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self.location_poly = self.config.get_list("poses/location_poly")
        self.rotation_poly = self.config.get_list("poses/rotation_poly")

    def run(self, n_frames):
        # Create light source
        light_data = bpy.data.lights.new(self.config.get_string('name'), type="POINT")
        light_obj = bpy.data.objects.new(self.config.get_string('name'), object_data=light_data)
        bpy.context.collection.objects.link(light_obj)

        light_data.type = self.config.get_string("light/type", 'POINT')
        light_data.energy = self.config.get_float("light/energy", 10)
        light_data.color = self.config.get_list("light/color", [1, 1, 1])
        light_data.distance = self.config.get_float("light/distance", 0)

        pts = [i/(n_frames-1) for i in range(n_frames)]
        locations_np = poly.polyval(pts, self.location_poly)
        rotations_np = poly.polyval(pts, self.rotation_poly)

        locations = locations_np.transpose(1, 0).astype(float).tolist()
        rotations = rotations_np.transpose(1, 0).astype(float).tolist()

        for i in range(n_frames):
            light_obj.location = Vector(locations[i])
            light_obj.rotation_euler = Euler(rotations[i])

            light_obj.keyframe_insert(data_path='location', frame=i)
            light_obj.keyframe_insert(data_path='rotation_euler', frame=i)
