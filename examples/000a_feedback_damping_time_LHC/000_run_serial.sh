#!/usr/bin/bash

export PYTHONPATH=$PYTHONPATH:../../../

rm simulation_status.sta

# Run Serial
for i in 1 2 3
do
    echo "Run $i"
    ../../../PyPARIS/serialexec.py sim_class=PyPARIS_sim_class.Simulation.Simulation
done
