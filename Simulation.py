import os
import Simulation_parameters as pp

import PyPARIS.communication_helpers as ch
import numpy as np
import PyPARIS.share_segments as shs
import time
import pickle
import h5py

from PyHEADTAIL.particles.slicing import UniformBinSlicer


class Simulation(object):
    def __init__(self):
        self.N_turns = pp.N_turns
        self.pp = pp

    def init_all(self):

        self.n_slices = pp.n_slices
    
        
        # read the optics if needed
        if pp.optics_pickle_file is not None:
            with open(pp.optics_pickle_file) as fid:
                optics = pickle.load(fid)
                self.n_kick_smooth = np.sum(['_kick_smooth_' in nn for nn in optics['name']])
        else:
            optics=None
            self.n_kick_smooth = pp.n_segments

        # define the machine
        from LHC_custom import LHC
        self.machine = LHC(
                        n_segments=pp.n_segments,
                        machine_configuration=pp.machine_configuration,
                        beta_x=pp.beta_x, beta_y=pp.beta_y,
                        accQ_x=pp.Q_x, accQ_y=pp.Q_y,
                        Qp_x=pp.Qp_x, Qp_y=pp.Qp_y,
                        octupole_knob=pp.octupole_knob, 
                        optics_dict=optics,
                        V_RF=pp.V_RF
                        )
        self.n_segments = self.machine.transverse_map.n_segments
        
        # compute sigma
        inj_opt = self.machine.transverse_map.get_injection_optics()
        sigma_x_inj = np.sqrt(inj_opt['beta_x']*pp.epsn_x/self.machine.betagamma)
        sigma_y_inj = np.sqrt(inj_opt['beta_y']*pp.epsn_y/self.machine.betagamma)
        
        
        if pp.optics_pickle_file is None:
            sigma_x_smooth = sigma_x_inj
            sigma_y_smooth = sigma_y_inj
        else:
            beta_x_smooth = None
            beta_y_smooth = None
            for ele in self.machine.one_turn_map:
                if ele in self.machine.transverse_map:
                    if '_kick_smooth_' in ele.name1:
                        if beta_x_smooth is None:
                            beta_x_smooth = ele.beta_x1
                            beta_y_smooth = ele.beta_y1
                        else:
                            if beta_x_smooth != ele.beta_x1 or beta_y_smooth != ele.beta_y1:
                                raise ValueError('Smooth kicks must have all the same beta')
             
            if beta_x_smooth is None:
                sigma_x_smooth = None
                sigma_y_smooth = None
            else:
                sigma_x_smooth = np.sqrt(beta_x_smooth*pp.epsn_x/self.machine.betagamma)
                sigma_y_smooth = np.sqrt(beta_y_smooth*pp.epsn_y/self.machine.betagamma)

        # define MP size
        nel_mp_ref_0 = pp.init_unif_edens_dip*4*pp.x_aper*pp.y_aper/pp.N_MP_ele_init_dip
        
        # prepare e-cloud
        import PyECLOUD.PyEC4PyHT as PyEC4PyHT
        
        if pp.custom_target_grid_arcs is not None:
            target_grid_arcs = pp.custom_target_grid_arcs
        else:
            target_grid_arcs = {
                    'x_min_target':-pp.target_size_internal_grid_sigma*sigma_x_smooth,
                    'x_max_target':pp.target_size_internal_grid_sigma*sigma_x_smooth,
                    'y_min_target':-pp.target_size_internal_grid_sigma*sigma_y_smooth, 
                    'y_max_target':pp.target_size_internal_grid_sigma*sigma_y_smooth,
                    'Dh_target':pp.target_Dh_internal_grid_sigma*sigma_x_smooth}
        self.target_grid_arcs = target_grid_arcs

        if pp.enable_arc_dip:
            ecloud_dip = PyEC4PyHT.Ecloud(slice_by_slice_mode=True,
                            L_ecloud=self.machine.circumference/self.n_kick_smooth*pp.fraction_device_dip, slicer=None, 
                            Dt_ref=pp.Dt_ref, pyecl_input_folder=pp.pyecl_input_folder,
                            chamb_type = pp.chamb_type,
                            x_aper=pp.x_aper, y_aper=pp.y_aper,
                            filename_chm=pp.filename_chm, 
                            PyPICmode = pp.PyPICmode,
                            Dh_sc=pp.Dh_sc_ext,
                            N_min_Dh_main = pp.N_min_Dh_main,
                            f_telescope = pp.f_telescope,
                            N_nodes_discard = pp.N_nodes_discard, 
                            target_grid = target_grid_arcs,                          
                            init_unif_edens_flag=pp.init_unif_edens_flag_dip,
                            init_unif_edens=pp.init_unif_edens_dip, 
                            N_mp_max=pp.N_mp_max_dip,
                            nel_mp_ref_0=nel_mp_ref_0,
                            B_multip=pp.B_multip_dip,
                            enable_kick_x = pp.enable_kick_x,
                            enable_kick_y = pp.enable_kick_y)
                        
        if pp.enable_arc_quad:               
            ecloud_quad = PyEC4PyHT.Ecloud(slice_by_slice_mode=True,
                            L_ecloud=self.machine.circumference/self.n_kick_smooth*pp.fraction_device_quad, slicer=None, 
                            Dt_ref=pp.Dt_ref, pyecl_input_folder=pp.pyecl_input_folder,
                            chamb_type = pp.chamb_type,
                            x_aper=pp.x_aper, y_aper=pp.y_aper,
                            filename_chm=pp.filename_chm,
                            PyPICmode = pp.PyPICmode,
                            Dh_sc=pp.Dh_sc_ext,
                            N_min_Dh_main = pp.N_min_Dh_main,
                            f_telescope = pp.f_telescope,
                            N_nodes_discard = pp.N_nodes_discard,  
                            target_grid = target_grid_arcs,
                            N_mp_max=pp.N_mp_max_quad,
                            nel_mp_ref_0=nel_mp_ref_0,
                            B_multip=pp.B_multip_quad,
                            filename_init_MP_state=pp.filename_init_MP_state_quad,
                            enable_kick_x = pp.enable_kick_x,
                            enable_kick_y = pp.enable_kick_y)


                        
        if self.ring_of_CPUs.I_am_the_master and pp.enable_arc_dip:
            with open('multigrid_config_dip.txt', 'w') as fid:
                if hasattr(ecloud_dip.spacech_ele.PyPICobj, 'grids'):
                    fid.write(repr(ecloud_dip.spacech_ele.PyPICobj.grids))
                else:
                    fid.write("Single grid.")
            
            with open('multigrid_config_dip.pkl', 'w') as fid:
                if hasattr(ecloud_dip.spacech_ele.PyPICobj, 'grids'):
                    pickle.dump(ecloud_dip.spacech_ele.PyPICobj.grids, fid)
                else:
                    pickle.dump('Single grid.', fid)
                
        if self.ring_of_CPUs.I_am_the_master and pp.enable_arc_quad:
            with open('multigrid_config_quad.txt', 'w') as fid:
                if hasattr(ecloud_quad.spacech_ele.PyPICobj, 'grids'):
                    fid.write(repr(ecloud_quad.spacech_ele.PyPICobj.grids))
                else:
                    fid.write("Single grid.")

            with open('multigrid_config_quad.pkl', 'w') as fid:
                if hasattr(ecloud_quad.spacech_ele.PyPICobj, 'grids'):
                    pickle.dump(ecloud_quad.spacech_ele.PyPICobj.grids, fid)
                else:
                    pickle.dump('Single grid.', fid)
                

        # setup transverse losses (to "protect" the ecloud)
        import PyHEADTAIL.aperture.aperture as aperture
        apt_xy = aperture.EllipticalApertureXY(x_aper=pp.target_size_internal_grid_sigma*sigma_x_inj, 
                                               y_aper=pp.target_size_internal_grid_sigma*sigma_y_inj)
        self.machine.one_turn_map.append(apt_xy)
        
        
        if pp.enable_transverse_damper:
            # setup transverse damper
            from PyHEADTAIL.feedback.transverse_damper import TransverseDamper
            damper = TransverseDamper(dampingrate_x=pp.dampingrate_x, dampingrate_y=pp.dampingrate_y)
            self.machine.one_turn_map.append(damper)



        # We suppose that all the object that cannot be slice parallelized are at the end of the ring
        i_end_parallel = len(self.machine.one_turn_map)-pp.n_non_parallelizable

        # split the machine
        sharing = shs.ShareSegments(i_end_parallel, self.ring_of_CPUs.N_nodes)
        myid = self.ring_of_CPUs.myid
        i_start_part, i_end_part = sharing.my_part(myid)
        self.mypart = self.machine.one_turn_map[i_start_part:i_end_part]
        if self.ring_of_CPUs.I_am_a_worker:
            print 'I am id=%d/%d (worker) and my part is %d long'%(myid, self.ring_of_CPUs.N_nodes, len(self.mypart))
        elif self.ring_of_CPUs.I_am_the_master:
            self.non_parallel_part = self.machine.one_turn_map[i_end_parallel:]
            print 'I am id=%d/%d (master) and my part is %d long'%(myid, self.ring_of_CPUs.N_nodes, len(self.mypart))

        #install eclouds in my part
        my_new_part = []
        self.my_list_eclouds = []
        for ele in self.mypart:
            my_new_part.append(ele)
            if ele in self.machine.transverse_map:
                if pp.optics_pickle_file is None or '_kick_smooth_' in ele.name1:
                    if pp.enable_arc_dip:
                        ecloud_dip_new = ecloud_dip.generate_twin_ecloud_with_shared_space_charge()
                        my_new_part.append(ecloud_dip_new)
                        self.my_list_eclouds.append(ecloud_dip_new)
                    if pp.enable_arc_quad:
                        ecloud_quad_new = ecloud_quad.generate_twin_ecloud_with_shared_space_charge()
                        my_new_part.append(ecloud_quad_new)
                        self.my_list_eclouds.append(ecloud_quad_new)
                elif '_kick_element_' in ele.name1 and pp.enable_eclouds_at_kick_elements:
                    
                    i_in_optics = list(optics['name']).index(ele.name1)
                    kick_name = optics['name'][i_in_optics]
                    element_name = kick_name.split('_kick_element_')[-1]
                    L_curr = optics['L_interaction'][i_in_optics]
                    
                    buildup_folder = pp.path_buildup_simulations_kick_elements.replace('!!!NAME!!!', element_name)
                    chamber_fname = '%s_chamber.mat'%(element_name)
                    
                    B_multip_curr = [0., optics['gradB'][i_in_optics]]
                    
                    x_beam_offset = optics['x'][i_in_optics]*pp.orbit_factor
                    y_beam_offset = optics['y'][i_in_optics]*pp.orbit_factor
                    
                    sigma_x_local = np.sqrt(optics['beta_x'][i_in_optics]*pp.epsn_x/self.machine.betagamma)
                    sigma_y_local = np.sqrt(optics['beta_y'][i_in_optics]*pp.epsn_y/self.machine.betagamma)
                    
                    ecloud_ele = PyEC4PyHT.Ecloud(slice_by_slice_mode=True,
                            L_ecloud=L_curr, slicer=None, 
                            Dt_ref=pp.Dt_ref, pyecl_input_folder=pp.pyecl_input_folder,
                            chamb_type = 'polyg',
                            x_aper=None, y_aper=None,
                            filename_chm=buildup_folder+'/'+chamber_fname, 
                            PyPICmode = pp.PyPICmode,
                            Dh_sc=pp.Dh_sc_ext,
                            N_min_Dh_main = pp.N_min_Dh_main,
                            f_telescope = pp.f_telescope,
                            N_nodes_discard = pp.N_nodes_discard,                             
                            target_grid = {'x_min_target':-pp.target_size_internal_grid_sigma*sigma_x_local+x_beam_offset, 'x_max_target':pp.target_size_internal_grid_sigma*sigma_x_local+x_beam_offset,
                                           'y_min_target':-pp.target_size_internal_grid_sigma*sigma_y_local+y_beam_offset, 'y_max_target':pp.target_size_internal_grid_sigma*sigma_y_local+y_beam_offset,
                                           'Dh_target':pp.target_Dh_internal_grid_sigma*sigma_y_local},
                            N_mp_max=pp.N_mp_max_quad,
                            nel_mp_ref_0=nel_mp_ref_0,
                            B_multip=B_multip_curr,
                            filename_init_MP_state=buildup_folder+'/'+pp.name_MP_state_file_kick_elements, 
                            x_beam_offset=x_beam_offset,
                            y_beam_offset=y_beam_offset,
                            enable_kick_x = pp.enable_kick_x,
                            enable_kick_y = pp.enable_kick_y)

                    my_new_part.append(ecloud_ele)
                    self.my_list_eclouds.append(ecloud_ele)                          
                
        self.mypart = my_new_part

        if pp.footprint_mode:
            print 'Proc. %d computing maps'%myid
            # generate a bunch 
            bunch_for_map=self.machine.generate_6D_Gaussian_bunch_matched(
                        n_macroparticles=pp.n_macroparticles_for_footprint_map, intensity=pp.intensity, 
                        epsn_x=pp.epsn_x, epsn_y=pp.epsn_y, sigma_z=pp.sigma_z)

            # Slice the bunch
            slicer_for_map = UniformBinSlicer(n_slices = pp.n_slices, z_cuts=(-pp.z_cut, pp.z_cut))
            slices_list_for_map = bunch_for_map.extract_slices(slicer_for_map)
            
            
            #Track the previous part of the machine
            for ele in self.machine.one_turn_map[:i_start_part]:
                for ss in slices_list_for_map:
                    ele.track(ss)            

            # Measure optics, track and replace clouds with maps
            list_ele_type = []
            list_meas_beta_x = []
            list_meas_alpha_x = []
            list_meas_beta_y = []
            list_meas_alpha_y = []
            for ele in self.mypart:
                list_ele_type.append(str(type(ele)))
                # Measure optics
                bbb = sum(slices_list_for_map) 
                list_meas_beta_x.append(bbb.beta_Twiss_x())
                list_meas_alpha_x.append(bbb.alpha_Twiss_x())
                list_meas_beta_y.append(bbb.beta_Twiss_y())
                list_meas_alpha_y.append(bbb.alpha_Twiss_y())
                
                if ele in self.my_list_eclouds:
                    ele.track_once_and_replace_with_recorded_field_map(slices_list_for_map)
                else:
                    for ss in slices_list_for_map:
                        ele.track(ss)       
            print 'Proc. %d done with maps'%myid

            with open('measured_optics_%d.pkl'%myid, 'wb') as fid:
                pickle.dump({
                        'ele_type':list_ele_type,
                        'beta_x':list_meas_beta_x,
                        'alpha_x':list_meas_alpha_x,
                        'beta_y':list_meas_beta_y,
                        'alpha_y':list_meas_alpha_y,
                    }, fid)
            
            #remove RF
            if self.ring_of_CPUs.I_am_the_master:
                self.non_parallel_part.remove(self.machine.longitudinal_map)
                    
    def init_master(self):
        
        # Manage multi-job operation
        if pp.footprint_mode:
            if pp.N_turns!=pp.N_turns_target:
                raise ValueError('In footprint mode you need to set N_turns_target=N_turns_per_run!')
        
        import PyPARIS_sim_class.Save_Load_Status as SLS
        SimSt = SLS.SimulationStatus(N_turns_per_run=pp.N_turns, check_for_resubmit = True, N_turns_target=pp.N_turns_target)
        SimSt.before_simulation()
        self.SimSt = SimSt

        # generate a bunch 
        if pp.footprint_mode:
            self.bunch = self.machine.generate_6D_Gaussian_bunch_matched(
                n_macroparticles=pp.n_macroparticles_for_footprint_track, intensity=pp.intensity, 
                epsn_x=pp.epsn_x, epsn_y=pp.epsn_y, sigma_z=pp.sigma_z)
        elif SimSt.first_run:

            if pp.bunch_from_file is not None:
                print 'Loading bunch from file %s ...'%pp.bunch_from_file
                with h5py.File(pp.bunch_from_file, 'r') as fid:
                    self.bunch = self.buffer_to_piece(np.array(fid['bunch']).copy())
                print 'Bunch loaded from file.\n'

            else:
                self.bunch = self.machine.generate_6D_Gaussian_bunch_matched(
                                n_macroparticles=pp.n_macroparticles, intensity=pp.intensity, 
                                epsn_x=pp.epsn_x, epsn_y=pp.epsn_y, sigma_z=pp.sigma_z)
                
                # compute initial displacements
                inj_opt = self.machine.transverse_map.get_injection_optics()
                sigma_x = np.sqrt(inj_opt['beta_x']*pp.epsn_x/self.machine.betagamma)
                sigma_y = np.sqrt(inj_opt['beta_y']*pp.epsn_y/self.machine.betagamma)
                x_kick = pp.x_kick_in_sigmas*sigma_x
                y_kick = pp.y_kick_in_sigmas*sigma_y
                
                # apply initial displacement
                if not pp.footprint_mode:
                    self.bunch.x += x_kick
                    self.bunch.y += y_kick
                
                print 'Bunch initialized.'
        else:
            print 'Loading bunch from file...'
            with h5py.File('bunch_status_part%02d.h5'%(SimSt.present_simulation_part-1), 'r') as fid:
                self.bunch = self.buffer_to_piece(np.array(fid['bunch']).copy())
            print 'Bunch loaded from file.'

        # initial slicing
        self.slicer = UniformBinSlicer(n_slices = pp.n_slices, z_cuts=(-pp.z_cut, pp.z_cut))

        # define a bunch monitor 
        from PyHEADTAIL.monitors.monitors import BunchMonitor
        self.bunch_monitor = BunchMonitor('bunch_evolution_%02d'%self.SimSt.present_simulation_part,
                            pp.N_turns, {'Comment':'PyHDTL simulation'}, 
                            write_buffer_every = 3)
        
        # define a slice monitor 
        from PyHEADTAIL.monitors.monitors import SliceMonitor
        self.slice_monitor = SliceMonitor('slice_evolution_%02d'%self.SimSt.present_simulation_part,
                            pp.N_turns, self.slicer,  {'Comment':'PyHDTL simulation'}, 
                            write_buffer_every = 3)
        
        #slice for the first turn
        slice_obj_list = self.bunch.extract_slices(self.slicer)

        pieces_to_be_treated = slice_obj_list
        
        print 'N_turns', self.N_turns
        
        if pp.footprint_mode:
            self.recorded_particles = ParticleTrajectories(pp.n_macroparticles_for_footprint_track, self.N_turns)

        return pieces_to_be_treated

    def init_worker(self):
        pass

    def treat_piece(self, piece):
        for ele in self.mypart: 
                ele.track(piece)

    def finalize_turn_on_master(self, pieces_treated):
        
        # re-merge bunch
        self.bunch = sum(pieces_treated)

        #finalize present turn (with non parallel part, e.g. synchrotron motion)
        for ele in self.non_parallel_part:
            ele.track(self.bunch)
            
        # save results		
        #print '%s Turn %d'%(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()), i_turn)
        self.bunch_monitor.dump(self.bunch)
        self.slice_monitor.dump(self.bunch)
        
        # prepare next turn (re-slice)
        new_pieces_to_be_treated = self.bunch.extract_slices(self.slicer)
        
        # order reset of all clouds
        orders_to_pass = ['reset_clouds']
        
        if pp.footprint_mode:
            self.recorded_particles.dump(self.bunch)
        
        # check if simulation has to be stopped
        # 1. for beam losses
        if not pp.footprint_mode and self.bunch.macroparticlenumber < pp.sim_stop_frac * pp.n_macroparticles:
            orders_to_pass.append('stop')
            self.SimSt.check_for_resubmit = False
            print 'Stop simulation due to beam losses.'
        
        # 2. for the emittance growth
        if pp.flag_check_emittance_growth:
            epsn_x_max = (pp.epsn_x)*(1 + pp.epsn_x_max_growth_fraction)
            epsn_y_max = (pp.epsn_y)*(1 + pp.epsn_y_max_growth_fraction)
            if not pp.footprint_mode and (self.bunch.epsn_x() > epsn_x_max or self.bunch.epsn_y() > epsn_y_max):
                orders_to_pass.append('stop')
                self.SimSt.check_for_resubmit = False
                print 'Stop simulation due to emittance growth.'
        
        return orders_to_pass, new_pieces_to_be_treated


    def execute_orders_from_master(self, orders_from_master):
        if 'reset_clouds' in orders_from_master:
            for ec in self.my_list_eclouds: ec.finalize_and_reinitialize()


        
    def finalize_simulation(self):
        if pp.footprint_mode:
            # Tunes

            import NAFFlib
            print 'NAFFlib spectral analysis...'
            qx_i = np.empty_like(self.recorded_particles.x_i[:,0])
            qy_i = np.empty_like(self.recorded_particles.x_i[:,0])
            for ii in range(len(qx_i)):
                qx_i[ii] = NAFFlib.get_tune(self.recorded_particles.x_i[ii] + 1j*self.recorded_particles.xp_i[ii])
                qy_i[ii] = NAFFlib.get_tune(self.recorded_particles.y_i[ii] + 1j*self.recorded_particles.yp_i[ii])
            print 'NAFFlib spectral analysis done.'

            # Save
            import h5py
            dict_beam_status = {\
            'x_init': np.squeeze(self.recorded_particles.x_i[:,0]),
            'xp_init': np.squeeze(self.recorded_particles.xp_i[:,0]),
            'y_init': np.squeeze(self.recorded_particles.y_i[:,0]),
            'yp_init': np.squeeze(self.recorded_particles.yp_i[:,0]),
            'z_init': np.squeeze(self.recorded_particles.z_i[:,0]),
            'qx_i': qx_i,
            'qy_i': qy_i,
            'x_centroid': np.mean(self.recorded_particles.x_i, axis=1),
            'y_centroid': np.mean(self.recorded_particles.y_i, axis=1)}
                
            with h5py.File('footprint.h5', 'w') as fid:
                for kk in dict_beam_status.keys():
                    fid[kk] = dict_beam_status[kk]
        else:
            #save data for multijob operation and launch new job
            import h5py
            with h5py.File('bunch_status_part%02d.h5'%(self.SimSt.present_simulation_part), 'w') as fid:
                fid['bunch'] = self.piece_to_buffer(self.bunch)
            if not self.SimSt.first_run:
                os.system('rm bunch_status_part%02d.h5'%(self.SimSt.present_simulation_part-1))
            self.SimSt.after_simulation()

        
    def piece_to_buffer(self, piece):
        buf = ch.beam_2_buffer(piece)
        return buf

    def buffer_to_piece(self, buf):
        piece = ch.buffer_2_beam(buf)
        return piece

class DummyComm(object):

    def __init__(self, N_cores_pretend, pretend_proc_id):
        self.N_cores_pretend = N_cores_pretend
        self.pretend_proc_id = pretend_proc_id

    def Get_size(self):
        return self.N_cores_pretend

    def Get_rank(self):
        return self.pretend_proc_id

    def Barrier(self):
        pass

def get_sim_instance(N_cores_pretend, id_pretend, 
        init_sim_objects_auto=True):

    from PyPARIS.ring_of_CPUs import RingOfCPUs
    myCPUring = RingOfCPUs(Simulation(),
            comm=DummyComm(N_cores_pretend, id_pretend), 
                init_sim_objects_auto=init_sim_objects_auto)
    return myCPUring.sim_content

def get_serial_CPUring(init_sim_objects_auto=True):
    from PyPARIS.ring_of_CPUs import RingOfCPUs
    myCPUring = RingOfCPUs(Simulation(), force_serial=True, 
                init_sim_objects_auto=init_sim_objects_auto)
    return myCPUring

    


class ParticleTrajectories(object):
    def __init__(self, n_record, n_turns):

        # prepare storage for particles coordinates
        self.x_i = np.empty((n_record, n_turns))
        self.xp_i = np.empty((n_record, n_turns))
        self.y_i = np.empty((n_record, n_turns))
        self.yp_i = np.empty((n_record, n_turns))
        self.z_i = np.empty((n_record, n_turns))
        self.i_turn = 0
        
    def dump(self, bunch):
        
        # id and momenta after track
        id_after = bunch.id
        x_after = bunch.x
        y_after = bunch.y
        z_after = bunch.z
        xp_after = bunch.xp
        yp_after = bunch.yp

        # sort id and momenta after track
        indsort = np.argsort(id_after)
        id_after = np.take(id_after, indsort)
        x_after = np.take(x_after, indsort)
        y_after = np.take(y_after, indsort)
        z_after = np.take(z_after, indsort)
        xp_after = np.take(xp_after, indsort)
        yp_after = np.take(yp_after, indsort)

        self.x_i[:,self.i_turn] = x_after
        self.xp_i[:,self.i_turn] = xp_after
        self.y_i[:,self.i_turn] = y_after
        self.yp_i[:,self.i_turn] = yp_after
        self.z_i[:,self.i_turn] = z_after    
            
        self.i_turn += 1


