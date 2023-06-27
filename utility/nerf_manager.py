import bpy

from pathlib import Path

from turbo_nerf.constants import NERF_ITEM_IDENTIFIER_ID
from .dotdict import dotdict
from .pylib import PyTurboNeRF as tn

class NeRFManager():
    n_items = 0

    items = {}

    _bridge = None
    _manager = None
    _runtime_check_result = None

    @classmethod
    def pylib_version(cls):
        return tn.__version__
    
    @classmethod
    def required_pylib_version(cls):
        return "0.0.13"

    @classmethod
    def is_pylib_compatible(cls):
        return cls.pylib_version() == cls.required_pylib_version()
    
    @classmethod
    def check_runtime(cls):
        if cls._runtime_check_result is not None:
            return cls._runtime_check_result
        
        rm = tn.RuntimeManager()
        cls._runtime_check_result = rm.check_runtime()
        return cls._runtime_check_result

    @classmethod
    def mgr(cls):
        if cls._manager is None:
            cls._manager = tn.NeRFManager()

        return cls._manager
    
    @classmethod
    def bridge(cls):
        if cls._bridge is None:
            cls._bridge = tn.BlenderBridge()

        return cls._bridge
    
    @classmethod
    def add_nerf(cls, nerf: tn.NeRF):
        item_id = cls.n_items
        item = dotdict({
            "nerf": nerf
        })

        cls.items[item_id] = item

        cls.n_items += 1

        return item_id

    @classmethod
    def import_dataset(cls, dataset_path):
        dataset = tn.Dataset(file_path=dataset_path)
        dataset.load_transforms()

        nerf = cls.mgr().create()
        nerf.attach_dataset(dataset)

        return cls.add_nerf(nerf)

    @classmethod
    def clone(cls, nerf):
        cloned_nerf = cls.mgr().clone(nerf)
        return cls.add_nerf(cloned_nerf)
    
    @classmethod
    def destroy(cls, item_id):
        cls.mgr().destroy(cls.items[item_id].nerf)
        del cls.items[item_id]

    @classmethod
    def load_snapshot(cls, path: Path):
        nerf = cls.mgr.load(str(path.absolute()))
        return cls.add_nerf(nerf)

    @classmethod
    def save_snapshot(cls, item_id, path: Path):
        nerf = cls.items[item_id].nerf
        cls.mgr().save(nerf, str(path.absolute()))

    @classmethod
    def get_all_nerfs(cls):
        nerfs =  [item.nerf for item in cls.items.values()]
        return nerfs
    
    @classmethod
    def is_training(cls):
        return cls.bridge().is_training()

    @classmethod
    def get_training_step(cls):
        return cls.bridge().get_training_step()

    @classmethod
    def is_ready_to_train(cls):
        return cls.bridge().is_ready_to_train()
    
    @classmethod
    def is_image_data_loaded(cls):
        return cls.bridge().is_image_data_loaded()
    
    @classmethod
    def can_load_images(cls):
        # TODO: need a better way to check if a dataset is loadable
        # return cls.bridge().can_load_images()

        return cls.n_items > 0 and not cls.is_image_data_loaded()
    
    @classmethod
    def load_training_images(cls, item: int|tn.NeRF):
        nerf: tn.NeRF
        if isinstance(item, int):
            nerf = cls.get_nerf_by_id(item)
        elif isinstance(item, bpy.types.Object):
            nerf = cls.get_nerf_for_obj(item)
        else:
            nerf = item
        
        cls.bridge().load_training_images(
            proxy=nerf,
            batch_size=2<<20
        )
    
    @classmethod
    def unload_training_images(cls):
        cls.bridge().unload_training_images()

    @classmethod
    def start_training(cls):
        cls.bridge().start_training()
    
    @classmethod
    def stop_training(cls):
        cls.bridge().stop_training()

    @classmethod
    def toggle_training(cls):
        if cls.is_training():
            cls.stop_training()
        else:
            cls.start_training()
    
    @classmethod
    def reset_training(cls):
        cls.bridge().reset_training()

    @classmethod
    def get_nerf_by_id(cls, nerf_id: int) -> tn.NeRF:
        return cls.items[nerf_id].nerf
    
    @classmethod
    def get_nerf_for_obj(cls, nerf_obj: bpy.types.Object) -> tn.NeRF:
        nerf_id = nerf_obj[NERF_ITEM_IDENTIFIER_ID]
        return cls.get_nerf_by_id(nerf_id)
    
    @classmethod
    def set_bridge_object_property(cls, object_name, property_name, value):
        obj = getattr(cls.bridge(), object_name, None)
        if obj is None:
            return

        setattr(obj, property_name, value)
    
    @classmethod
    def get_bridge_object_property(cls, object_name, property_name, default=None):
        obj = getattr(cls.bridge(), object_name, None)
        if obj is None:
            return default

        return getattr(obj, property_name, default)
    
    @classmethod
    def bridge_obj_prop_setter(cls, obj_name, prop_name):
        def setter(self, value):
            cls.set_bridge_object_property(obj_name, prop_name, value)
        
        return setter
    
    @classmethod
    def bridge_obj_prop_getter(cls, obj_name, prop_name, default):
        def getter(self):
            return cls.get_bridge_object_property(obj_name, prop_name, default)
        
        return getter

