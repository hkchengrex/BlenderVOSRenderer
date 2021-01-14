import bpy
import os
import numpy as np

from src.renderer.Renderer import Renderer
from src.utility.Utility import Utility
from src.utility.BlenderUtility import load_image


class SimFlowRenderer(Renderer):
    """ Renders optical flow between consecutive keypoints.

    .. csv-table::
        :header: "Parameter", "Description"

        "forward_flow_output_key", "The key which should be used for storing forward optical flow values. Type: str, default: 'forward_flow'."
        "backward_flow_output_key", "The key which should be used for storing backward optical flow values. Type: str, default: 'backward_flow'."
        "forward_flow", "Whether to render forward optical flow. Type: bool, default: True."
        "backward_flow", "Whether to render backward optical flow. Type: bool, default: True."
        "blender_image_coordinate_style", "Whether to specify the image coordinate system at the bottom left (blender default; True) or top left (standard convention; False). Type: bool, default: False."
    """

    def __init__(self, config):
        Renderer.__init__(self, config, False)

    def _output_vector_field(self):
        """ Configures compositor to output speed vectors. """

        # Flow settings (is called "vector" in blender)
        bpy.context.scene.render.use_compositing = True
        bpy.context.scene.use_nodes = True
        bpy.context.scene.view_layers["View Layer"].use_pass_vector = True

        # Adapt compositor to output vector field
        tree = bpy.context.scene.node_tree
        links = tree.links

        # Use existing render layer
        render_layer_node = tree.nodes.get('Render Layers')

        separate_rgba = tree.nodes.new('CompositorNodeSepRGBA')
        links.new(render_layer_node.outputs['Vector'], separate_rgba.inputs['Image'])

        if self.config.get_bool('forward_flow', False):
            combine_fwd_flow = tree.nodes.new('CompositorNodeCombRGBA')
            links.new(separate_rgba.outputs['B'], combine_fwd_flow.inputs['R'])
            links.new(separate_rgba.outputs['A'], combine_fwd_flow.inputs['G'])
            fwd_flow_output_file = tree.nodes.new('CompositorNodeOutputFile')
            fwd_flow_output_file.base_path = self._determine_output_dir()
            fwd_flow_output_file.format.file_format = "OPEN_EXR"
            fwd_flow_output_file.file_slots.values()[0].path = "fwd_flow_"
            links.new(combine_fwd_flow.outputs['Image'], fwd_flow_output_file.inputs['Image'])

        if self.config.get_bool('backward_flow', False):
            # actually need to split - otherwise the A channel of the image is getting weird, no idea why
            combine_bwd_flow = tree.nodes.new('CompositorNodeCombRGBA')
            links.new(separate_rgba.outputs['R'], combine_bwd_flow.inputs['R'])
            links.new(separate_rgba.outputs['G'], combine_bwd_flow.inputs['G'])
            bwd_flow_output_file = tree.nodes.new('CompositorNodeOutputFile')
            bwd_flow_output_file.base_path = self._determine_output_dir()
            bwd_flow_output_file.format.file_format = "OPEN_EXR"
            bwd_flow_output_file.file_slots.values()[0].path = "bwd_flow_"
            links.new(combine_bwd_flow.outputs['Image'], bwd_flow_output_file.inputs['Image'])

    def run(self):
        # determine whether to get optical flow or scene flow - get scene flow per default
        get_forward_flow = self.config.get_bool('forward_flow', False)
        get_backward_flow = self.config.get_bool('backward_flow', False)

        if get_forward_flow is False and get_backward_flow is False:
            raise Exception("Take the FlowRenderer Module out of the config if both forward and backward flow are set to False!")

        with Utility.UndoAfterExecution():
            self._configure_renderer(default_samples=self.config.get_int("samples", 1))

            self._output_vector_field()

            # only need to render once; both fwd and bwd flow will be saved
            temporary_fwd_flow_file_path = os.path.join(self._temp_dir, 'fwd_flow_')
            temporary_bwd_flow_file_path = os.path.join(self._temp_dir, 'bwd_flow_')
            self._render("bwd_flow_", custom_file_path=temporary_bwd_flow_file_path)

            final_fwd_file_path = os.path.join(self._determine_output_dir(), self.config.get_string("forward_flow_output_file_prefix", ""))
            final_bwd_file_path = os.path.join(self._determine_output_dir(), self.config.get_string("backward_flow_output_file_prefix", ""))

            # After rendering: convert to optical flow or calculate hsv visualization, if desired
            if not self._avoid_rendering:
                for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
                    # temporarily save respective vector fields
                    if get_forward_flow:

                        file_path = temporary_fwd_flow_file_path + "%04d" % frame + ".exr"
                        fwd_flow_field = load_image(file_path, num_channels=4).astype(np.float32)

                        if not self.config.get_bool('blender_image_coordinate_style', False):
                            fwd_flow_field[:, :, 1] = fwd_flow_field[:, :, 1] * -1

                        fname = final_fwd_file_path + '%04d_fw.npy' % frame
                        forward_flow = fwd_flow_field * -1  # invert forward flow to point at next frame
                        np.save(fname, forward_flow[:, :, :2])

                    if get_backward_flow:
                        file_path = temporary_bwd_flow_file_path + "%04d" % frame + ".exr"
                        bwd_flow_field = load_image(file_path, num_channels=4).astype(np.float32)

                        if not self.config.get_bool('y_origin_bot', False):
                            bwd_flow_field[:, :, 1] = bwd_flow_field[:, :, 1] * -1

                        fname = final_bwd_file_path + '%04d_bw.npy' % frame
                        np.save(fname, bwd_flow_field[:, :, :2])

        # register desired outputs
        if get_forward_flow:
            self._register_output("", default_key="forward_flow",
                                  suffix='_fw.npy', version='2.0.0')
        if get_backward_flow:
            self._register_output("", default_key="backward_flow",
                                  suffix='_bw.npy', version='2.0.0')

