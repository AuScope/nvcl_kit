
from types import SimpleNamespace
from nvcl_kit.constants import Scalar

'''
For Reader class:

def setFilter(reader, nvcl_id=nvcl_id, name=name)
'''

def gen_scalar_by_depth(reader, *, nvcl_id_list=None, resolution=20.0, scalar_class=Scalar.ANY, log_type=None, top_n=5):
    if nvcl_id_list is None:
        nvcl_id_list = reader.get_nvcl_id_list() 
        if not nvcl_id_list:
            raise StopIteration()
    
    for n_id in nvcl_id_list:
        imagelog_data_list = reader.get_imagelog_data(n_id)
        if imagelog_data_list:
            for ild in imagelog_data_list:
                if (log_type is None or ild.log_type == log_type) and \
                   (ild.log_name == scalar_class or scalar_class == Scalar.ANY):
                    bh_data = reader.get_borehole_data(ild.log_id, resolution, ild.log_name, top_n=top_n)
                    yield n_id, ild.log_id, bh_data
