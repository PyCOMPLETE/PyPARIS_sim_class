import numpy as np
import Simulation as sim_mod
import time

ring = sim_mod.get_serial_CPUring()

list_slice_objects = ring.pieces_to_be_treated # Head is the last element
list_machine_elements = ring.sim_content.mypart

# Truck the beam to the first ecloud (excluded)
for ee in list_machine_elements:
    if ee in ring.sim_content.my_list_eclouds:
        first_ecloud = ee
        break
    for ss in list_slice_objects[::-1]:
        ee.track(ss)

# Record pinch info
first_ecloud.save_ele_distributions_last_track = True
first_ecloud.save_ele_field = True
first_ecloud.save_ele_potential = True

N_slices = len(list_slice_objects)

t_start = time.mktime(time.localtime())
for i_ss, ss in enumerate(list_slice_objects[::-1]):
    if np.mod(i_ss, 20)==0:
        print("%d / %d"%(i_ss, N_slices))
    first_ecloud.track(ss)
t_end = time.mktime(time.localtime())

print('Track time %.2f s' % (t_end - t_start))

# Save pich to file
import scipy.io as sio
sio.savemat('pinch_pic_data.mat', {
    'xg': xg,
    'yg': yg,
    'zg': slices.z_centers,
    'rho': first_ecloud.rho_ele_last_track,
    'phi': first_ecloud.phi_ele_last_track,
    'Ex': first_ecloud.Ex_ele_last_track,
    'Ey': first_ecloud.Ey_ele_last_track,
    'sigma_x_beam': bunch.sigma_x(),
    'sigma_y_beam': bunch.sigma_y(),
    'sigma_z_beam': bunch.sigma_z(),
    }, oned_as = 'row')