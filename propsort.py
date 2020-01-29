

import numpy as np

def sort_properly(path_list):
    
    list_numbers = []
    
    for pp in path_list:
       list_numbers.append(int(pp.split('.h5')[0].split('_')[-1]))  
    
    ind_sorted = np.argsort(list_numbers)
    list_path_sorted = list(np.take(path_list, ind_sorted))
    
    return(list_path_sorted)
    
