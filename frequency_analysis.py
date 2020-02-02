import NAFFlib

def get_tunes(recorded_particles, filename_output=None):

    print("NAFFlib spectral analysis...")
    qx_i = np.empty_like(self.recorded_particles.x_i[:, 0])
    qy_i = np.empty_like(self.recorded_particles.x_i[:, 0])
    for ii in range(len(qx_i)):
        qx_i[ii] = NAFFlib.get_tune(
            self.recorded_particles.x_i[ii]
            + 1j * self.recorded_particles.xp_i[ii]
        )
        qy_i[ii] = NAFFlib.get_tune(
            self.recorded_particles.y_i[ii]
            + 1j * self.recorded_particles.yp_i[ii]
        )
    print("NAFFlib spectral analysis done.")

    # Save

    dict_beam_status = {
        "x_init": np.squeeze(self.recorded_particles.x_i[:, 0]),
        "xp_init": np.squeeze(self.recorded_particles.xp_i[:, 0]),
        "y_init": np.squeeze(self.recorded_particles.y_i[:, 0]),
        "yp_init": np.squeeze(self.recorded_particles.yp_i[:, 0]),
        "z_init": np.squeeze(self.recorded_particles.z_i[:, 0]),
        "qx_i": qx_i,
        "qy_i": qy_i,
        "x_centroid": np.mean(self.recorded_particles.x_i, axis=1),
        "y_centroid": np.mean(self.recorded_particles.y_i, axis=1),
    }

    if filename_output is not None:
        import h5py
        with h5py.File(filename_output, "w") as fid:
            for kk in list(dict_beam_status.keys()):
                fid[kk] = dict_beam_status[kk]
