#!/usr/bin/bash

export PYTHONPATH=$PYTHONPATH:../../../

# Run Parallel without MPI
../../../PyPARIS/multiprocexec.py -n 3 sim_class=PyPARIS_sim_class.Simulation.Simulation


