import bpy

from src.loader.Loader import Loader
from src.utility.Utility import Utility
import numpy as np


class SkyBoxLoader(Loader):
    """ Just imports the objects for the given file path & scale

    The import will load all materials into cycle nodes.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "path", "The path to the 3D data file to load. Can be either path or paths not both."
    """
    def __init__(self, config):
        Loader.__init__(self, config)

    def run(self):

        # file_path = Utility.resolve_path(self.config.get_string("path"))
        # loaded_object = Utility.import_objects(filepath=file_path)[0]
        # loaded_object.scale = self.config.get_vector("scale")

        bpy.ops.mesh.primitive_plane_add(size=30, location=self.config.get_vector('location'), rotation=self.config.get_vector('rotation'))
        obj = bpy.context.active_object
        obj.name = 'skybox'

        mat = bpy.data.materials.new('skybox_mtl')
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        obj.active_material = mat

        nodeOut = nodes.new(type='ShaderNodeOutputMaterial')
        nodeEmission = nodes.new(type='ShaderNodeEmission')
        nodeTexture = nodes.new(type='ShaderNodeTexImage')

        # Link them together
        links = mat.node_tree.links
        nodeEmission.inputs[1].default_value = self.config.get_float('strength')
        links.new(nodeEmission.outputs[0], nodeOut.inputs[0])
        links.new(nodeTexture.outputs[0], nodeEmission.inputs[0])

        # Configure Texture node
        img = bpy.data.images.load(self.config.get_string("path"))
        img.name = 'sky'
        nodeTexture.image = img

        # bsdf = mat.node_tree.nodes["Principled BSDF"]
        # texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
        # texImage.image = bpy.data.images.load(self.config.get_string("path"))
        # mat.node_tree.links.new(bsdf.inputs['Emission'], texImage.outputs['Color'])
        # bsdf.inputs['Emission'].alpha = self.config.get_float('strength')

        # # Assign it to object
        # if obj.data.materials:
        #     obj.data.materials[0] = mat
        # else:
        #     obj.data.materials.append(mat)