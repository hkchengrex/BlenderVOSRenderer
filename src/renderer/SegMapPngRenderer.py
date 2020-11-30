import csv
import os

import bpy
import numpy as np
from PIL import Image

from src.renderer.Renderer import Renderer
from src.utility.Utility import Utility
from src.utility.BlenderUtility import load_image

def get_color_map(N=256):
    def bitget(byteval, idx):
        return ((byteval & (1 << idx)) != 0)

    cmap = np.zeros((N, 3), dtype=np.uint8)
    for i in range(N):
        r = g = b = 0
        c = i
        for j in range(8):
            r = r | (bitget(c, 0) << 7-j)
            g = g | (bitget(c, 1) << 7-j)
            b = b | (bitget(c, 2) << 7-j)
            c = c >> 3

        cmap[i] = np.array([r, g, b])

    return cmap

cache_color_map = get_color_map()
def pal_color_map():
    return cache_color_map


class SegMapPngRenderer(Renderer):
    """
    Renders segmentation maps for each registered keypoint.

    The rendering is stored using the .exr file type and a color depth of 16bit to achieve high precision.

    .. csv-table::
       :header: "Parameter", "Description"

       "map_by", "Method to be used for color mapping. Allowed values: instance, class"
       "segcolormap_output_key": "The key which should be used for storing the class instance to color mapping in a merged file."
       "segcolormap_output_file_prefix": "The file prefix that should be used when writing the class instance to color mapping to file."
    """

    def __init__(self, config):
        Renderer.__init__(self, config, False)
        # As we use float16 for storing the rendering, the interval of integers which can be precisely stored is [-2048, 2048].
        # As blender does not allow negative values for colors, we use [0, 2048] ** 3 as our color space which allows ~8 billion different colors/labels. This should be enough.
        self.render_colorspace_size_per_dimension = 256

    def _colorize_object(self, obj, color):
        """ Adjusts the materials of the given object, s.t. they are ready for rendering the seg map.

        This is done by replacing all nodes just with an emission node, which emits the color corresponding to the category of the object.

        :param obj: The object to use.
        :param color: RGB array of a color.
        """
        # Create new material emitting the given color
        new_mat = bpy.data.materials.new(name="segmentation")
        new_mat.use_nodes = True
        nodes = new_mat.node_tree.nodes
        links = new_mat.node_tree.links
        emission_node = nodes.new(type='ShaderNodeEmission')
        output = Utility.get_nodes_with_type(nodes, 'OutputMaterial')
        if output and len(output) == 1:
            output = output[0]
        else:
            raise Exception("This material: {} has not one material output!".format(new_mat.name))

        emission_node.inputs['Color'].default_value[:3] = color
        links.new(emission_node.outputs['Emission'], output.inputs['Surface'])

        # Set material to be used for coloring all faces of the given object
        if len(obj.material_slots) > 0:
            for i in range(len(obj.material_slots)):
                if self._use_alpha_channel:
                    obj.data.materials[i] = self.add_alpha_texture_node(obj.material_slots[i].material, new_mat)
                else:
                    obj.data.materials[i] = new_mat
        else:
            obj.data.materials.append(new_mat)

    def _set_world_background_color(self, color):
        """ Set the background color of the blender world obejct.

        :param color: A 3-dim array containing the background color in range [0, 255]
        """
        nodes = bpy.context.scene.world.node_tree.nodes
        nodes.get("Background").inputs['Color'].default_value = color + [1]

    def _colorize_objects_for_instance_segmentation(self, objects):
        """ Sets a different color to each object.

        :param objects: A list of objects.
        :return: The num_splits_per_dimension of the spanned color space, the color map
        """
        colors, num_splits_per_dimension = Utility.generate_equidistant_values(len(objects)+1, self.render_colorspace_size_per_dimension)

        # Set world background label
        self._set_world_background_color(colors[0])

        idx = 1
        for obj in objects:
            if 'skybox' in obj.name:
                self._colorize_object(obj, colors[0])
            else:
                self._colorize_object(obj, colors[idx])
            idx += 1

        return colors, num_splits_per_dimension

    def run(self):
        with Utility.UndoAfterExecution():
            self._configure_renderer(default_samples=1)

            # get current method for color mapping, instance or class
            method = self.config.get_string("map_by", "class")

            # Get objects with materials (i.e. not lights or cameras)
            objs_with_mats = [obj for obj in bpy.context.scene.objects if hasattr(obj.data, 'materials')]

            colors, num_splits_per_dimension = self._colorize_objects_for_instance_segmentation(objs_with_mats)

            bpy.context.scene.render.image_settings.file_format = "OPEN_EXR"
            bpy.context.scene.render.image_settings.color_depth = "16"
            bpy.context.view_layer.cycles.use_denoising = False
            bpy.context.scene.cycles.filter_width = 0.0

            if self._use_alpha_channel:
                self.add_alpha_channel_to_textures(blurry_edges=False)

            # Determine path for temporary and for final output
            temporary_segmentation_file_path = os.path.join(self._temp_dir, "segpng_")
            final_segmentation_file_path = os.path.join(self._determine_output_dir(), self.config.get_string("output_file_prefix", ""))

            # Render the temporary output
            self._render("seg_", custom_file_path=temporary_segmentation_file_path)

            # Find optimal dtype of output based on max index
            for dtype in [np.uint8, np.uint16, np.uint32]:
                optimal_dtype = dtype
                if np.iinfo(optimal_dtype).max >= len(colors) - 1:
                    break

            # After rendering
            if not self._avoid_rendering:
                for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):  # for each rendered frame
                    file_path = temporary_segmentation_file_path + "%04d" % frame + ".exr"
                    segmentation = load_image(file_path)

                    segmap = Utility.map_back_from_equally_spaced_equidistant_values(segmentation, num_splits_per_dimension, self.render_colorspace_size_per_dimension)
                    segmap = segmap.astype(optimal_dtype)

                    fname = final_segmentation_file_path + "%04d.png" % frame
                    # np.save(fname, segmap)
                    seg = Image.fromarray(segmap, mode='P')
                    seg.putpalette(pal_color_map())
                    seg.save(fname)


        self._register_output("", "segmap_png", ".png", "1.0.0")