from src.main.Module import Module
import mathutils

class Loader(Module):
    """
    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"
       "add_properties", "properties in form of a dict, which should be add to all loaded objects."
    """
    def __init__(self, config, mk_dir=True):
        Module.__init__(self, config, mk_dir)

    def _set_properties(self, objects):
        """ Sets all custom properties of all given objects according to the configuration.

        :parameter objects: A list of objects which should receive the custom properties
        """

        properties = self.config.get_raw_dict("add_properties", {})

        for obj in objects:
            for key, value in properties.items():
                obj[key] = value


