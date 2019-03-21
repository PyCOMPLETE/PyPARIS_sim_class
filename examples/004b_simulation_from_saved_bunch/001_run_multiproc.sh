#!/usr/bin/bash

export PYTHONPATH=$PYTHONPATH:../../../

rm simulation_status.sta

# Run Parallel without MPI
for i in 1 2 3
do
    echo "Run $i"
    ../../../PyPARIS/multiprocexec.py -n 3 sim_class=PyPARIS_sim_class.Simulation.Simulation
done

