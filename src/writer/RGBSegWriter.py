import csv
import json
import shutil
import os
import bpy

from PIL import Image

from src.main.Module import Module


class RGBSegWriter(Module):
    """ Writes RGB and Segmentation Annotations in to a file.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"
       "delete_temporary_files_afterwards", "True, if all temporary files should be deleted after merging."
       "rgb_output_key", "The output key with which the rgb images were registered. Should be the same as the output_key of the RgbRenderer module."
       "segmap_png_output_key", "The output key with which the segmentation images were registered. Should be the same as the output_key of the SegMapRenderer module."
    """

    def __init__(self, config):
        Module.__init__(self, config)

        self._avoid_rendering = config.get_bool("avoid_rendering", False)
        self.rgb_output_key = self.config.get_string("rgb_output_key", "colors")
        self.segmap_png_output_key = self.config.get_string("segmap_png_output_key", "segmap_png")
        self.ren_out_data_dir = os.path.join(self._determine_output_dir(False), 'image')
        self.seg_out_data_dir = os.path.join(self._determine_output_dir(False), 'segmentation')

        os.makedirs(self.ren_out_data_dir, exist_ok=True)
        os.makedirs(self.seg_out_data_dir, exist_ok=True)

    def run(self):
        if self._avoid_rendering:
            print("Avoid rendering is on, no output produced!")
            return

        # Find path pattern of segmentation images
        segmentation_map_output = self._find_registered_output_by_key(self.segmap_png_output_key)
        if segmentation_map_output is None:
            raise Exception("There is no output registered with key " + self.segmap_png_output_key + ". Are you sure you ran the SegMapPngRenderer module before?")
        
        # Find path pattern of rgb images
        rgb_output = self._find_registered_output_by_key(self.rgb_output_key)
        if rgb_output is None:
            raise Exception("There is no output registered with key " + self.rgb_output_key + ". Are you sure you ran the SimRgbRenderer module before?")
    
        # collect all segmaps
        segmentation_map_paths = []

        # collect all RGB paths
        new_out_paths = []
        # for each rendered frame
        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):

            # Segmentation
            source_path = segmentation_map_output["path"] % frame
            target_path = os.path.join(self.seg_out_data_dir, os.path.basename(segmentation_map_output["path"] % (frame)))

            shutil.copyfile(source_path, target_path)
            segmentation_map_paths.append(segmentation_map_output["path"] % frame)

            # RGB
            source_path = rgb_output["path"] % frame
            target_path = os.path.join(self.ren_out_data_dir, os.path.basename(rgb_output["path"] % (frame)))

            shutil.copyfile(source_path, target_path)
            new_out_paths.append(os.path.basename(target_path))

