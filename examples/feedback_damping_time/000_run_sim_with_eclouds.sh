#!/usr/bin/bash

export PYTHONPATH=$PYTHONPATH:../../../

# Run Parallel without MPI
# ../../../PyPARIS/multiprocexec.py -n 3 sim_class=PyPARIS_sim_class.Simulation.Simulation

# Run Serial
# ../../serialexec.py sim_class=PyPARIS_sim_class.Simulation.Simulation

# Run MPI
mpiexec -n 4 ../../../PyPARIS/withmpi.py sim_class=PyPARIS_sim_class.Simulation.Simulation
