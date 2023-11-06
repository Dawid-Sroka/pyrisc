import sys

from consts import *
from isa import *
from components import *
from program import *
from sim import *
from snurisc import *

from threading import Timer

# -- snurisc main
filename = parse_args(sys.argv)
if not filename:
    show_usage(sys.argv[0])
    sys.exit()

cpu = SNURISC()
prog = Program()
entry_point = prog.load(cpu, filename)
if not entry_point:
    sys.exit()
# --

# -- cpu clock
def cpu_clock():
    print("clock interrupt!")

t = Timer(0.02, cpu_clock)
t.start()
# --

for i in range(5):
    cpu_ret = cpu.run(entry_point)
    print(EXC_MSG[cpu_ret])
    
    if (cpu_ret == EXC_EBREAK):
        continue


