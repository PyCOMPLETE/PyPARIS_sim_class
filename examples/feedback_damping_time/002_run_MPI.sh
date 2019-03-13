#!/usr/bin/bash

export PYTHONPATH=$PYTHONPATH:../../../

# Run MPI
for i in 1 2 3
do
    echo "Run $i"
    mpiexec -n 3 ../../../PyPARIS/withmpi.py sim_class=PyPARIS_sim_class.Simulation.Simulation
done
