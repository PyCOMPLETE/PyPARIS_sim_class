#!/bin/bash

#BSUB -J inoct_0014
#BSUB -o %J.out
#BSUB -e %J.err
#BSUB -N
#BSUB -B
#BSUB -q hpc_inf
#B -a openmpi
#BSUB -n 8
#BSUB -R span[ptile=8]

source setup_env_cnaf

export PYTHONPATH=$PYTHONPATH:/home/HPC/giadarol/sim_workspace_8_11_2018


CURRDIR=/home/HPC/aromano/sim_workspace_cnaf/033_LHC_instab_dip_and_quad_edens_scan_6p5TeV_octupoles/simulations/edens_10.00e11_ecdipON_ecquadON
cd $CURRDIR
pwd

cd PyPARIS_sim_class
echo "Version:"          >  ../SimClass_git_info.txt
cat __version__.py       >> ../SimClass_git_info.txt
echo " "                 >> ../SimClass_git_info.txt
echo "git status:"       >> ../SimClass_git_info.txt
git status               >> ../SimClass_git_info.txt
echo "git log -n 1:"     >> ../SimClass_git_info.txt
git log -n 1             >> ../SimClass_git_info.txt

cp Simulation.py ../
cd ..

stdbuf -oL python ../../../PyPARIS/multiprocexec.py -n 8 sim_class=Simulation.Simulation >> opic.txt 2>> epic.txt
