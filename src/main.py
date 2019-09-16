from parser import parse
from simulator import Simulator

sim = Simulator()
inst, inst_list= parse("test.NEL")
sim.runInstr(inst_list, inst)

for i in range(60):
    sim.tick()

sim.printTable()
