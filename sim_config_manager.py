
class SimConfig(object):
    def __init__(self, param_file):

        import importlib
        spec = importlib.util.spec_from_file_location('temp.mod',
            param_file)
        mod_params =  importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod_params)

        for nn in dir(mod_params):
            if nn.startswith('__') and nn.endswith('__'):
                continue
            setattr(self, nn, getattr(mod_params, nn))
