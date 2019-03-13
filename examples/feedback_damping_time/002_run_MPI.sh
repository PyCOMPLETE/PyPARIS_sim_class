#!/usr/bin/bash

export PYTHONPATH=$PYTHONPATH:../../../

# Run MPI
mpiexec -n 4 ../../../PyPARIS/withmpi.py sim_class=PyPARIS_sim_class.Simulation.Simulation
