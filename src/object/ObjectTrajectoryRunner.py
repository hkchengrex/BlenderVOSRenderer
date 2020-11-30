import bpy

from src.utility.BlenderUtility import get_mesh_objects_with_name
from src.main.Module import Module
from src.utility.Utility import Utility
from src.object.MeshDeformer import MeshModeler

from mathutils import Vector, Euler
import numpy as np
import numpy.polynomial.polynomial as polynomial
import bmesh
import sys
import numbers
from collections import defaultdict

class ObjectTrajectoryRunner(Module):
    """ 
    Load an object and run it along the predefined trajectory
    """

    def __init__(self, config):
        Module.__init__(self, config, False)
        self.location_poly = self.config.get_list("poses/location_poly")
        self.rotation_poly = self.config.get_list("poses/rotation_poly")
        self.scale_poly = self.config.get_list("poses/scale_poly")

    # I have no idea why it gives me 3 arguments
    # Maybe it just wants to argue with me
    def mesh_deform_handler(self, scene, sth):
        frame = scene.frame_current

        if frame == 0:
            self.obj = get_mesh_objects_with_name([self.name])[0]
            self.modeler.mesh = self.obj.data

        self.modeler.update_animation(frame)
        self.modeler.apply_transformation()

    def run(self, n_frames):

        file_path = Utility.resolve_path(self.config.get_string("path"))
        self.obj = Utility.import_objects(filepath=file_path)[0]

        seed = self.config.get_int("seed")

        # Load addition texture if there is any
        texture_path = self.config.get_string('texture', '')
        if texture_path != '':
            # Remove old UV maps
            uv_layers = self.obj.data.uv_layers
            if len(uv_layers) > 0:
                uv_layers.remove(uv_layers[0])

            # Build new UV layer automatically via warpping
            # https://blender.stackexchange.com/questions/120805/smart-unwrap-using-script
            bpy.context.view_layer.objects.active = self.obj
            self.obj.select_set(True)
            lm =  self.obj.data.uv_layers.get("LightMap")
            if not lm:
                lm = self.obj.data.uv_layers.new(name="LightMap")
            lm.active = True
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT') # for all faces
            if len(self.obj.data.polygons) < 1000:
                bpy.ops.uv.smart_project()
            else:
                bpy.ops.uv.cylinder_project() # Smart is better but it is too slow
            bpy.ops.object.editmode_toggle()
            self.obj.select_set(False)

            # Remove obsolete texture
            self.obj.data.materials.clear()
                
            # Create new texture and link them
            mat = bpy.data.materials.new(self.obj.name + '_mtl')
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes['Principled BSDF']
            texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
            texImage.image = bpy.data.images.load(texture_path)
            mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])

            # Bring in the new material
            self.obj.data.materials.append(mat)
            for poly in self.obj.data.polygons:
                poly.material_index = len(bpy.data.materials)-1

            print('Texture map loaded!')
        else:
            print('Original texture retained!')

        # Try deformation -- no every model can pass it
        np.random.seed(seed)

        self.name = self.obj.name

        pts = [i/(n_frames-1) for i in range(n_frames)]
        locations_np = polynomial.polyval(pts, self.location_poly)
        rotations_np = polynomial.polyval(pts, self.rotation_poly)
        scales_np = polynomial.polyval(pts, self.scale_poly)

        locations = locations_np.transpose(1, 0).astype(float).tolist()
        rotations = rotations_np.transpose(1, 0).astype(float).tolist()
        scales = scales_np.transpose(1, 0).astype(float).tolist()

        for i in range(n_frames):
            self.obj.location = Vector(locations[i])
            self.obj.rotation_euler = Euler(rotations[i])
            self.obj.scale = Vector(scales[i])

            self.obj.keyframe_insert(data_path='location', frame=i)
            self.obj.keyframe_insert(data_path='rotation_euler', frame=i)
            self.obj.keyframe_insert(data_path='scale', frame=i)
