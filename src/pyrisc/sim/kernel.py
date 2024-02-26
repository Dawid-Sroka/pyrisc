import sys

from consts import *
from isa import *
from components import *
from program import *
from sim import *
from snurisc import *


# -- snurisc main
filename = parse_args(sys.argv)
if not filename:
    show_usage(sys.argv[0])
    sys.exit()

cpu = SNURISC()
prog = Program()
entry_point = prog.load(cpu, filename) # tu będziemy ładować init
if not entry_point:
    sys.exit()
# --

for i in range(5):
#while(1):
    print(i)
    # zamiast wywoływać run pewnie chcemy najpierw wywołać jakieś set_context.
    # I ta metoda będzie dopiero wywołać cpu.run
    # Oprócz tego pewnie get_context i create_context
    cpu_status = cpu.run(entry_point)
    print(EXC_MSG[cpu_status])

    if (cpu_status == EXC_EBREAK):
        # Najpierw chcemy dodać proste syscalle. Najpierw exit
        # Potem jakiś prosty read i write na standarwe wyjście i wejście
        # zareaguj na syscalla
        continue
    elif (cpu_status == EXC_CLOCK):
        # Patrzymy czy minął kwant czasu, czy zwykle przerwanie
        # jakaś akcja schedulera
        continue
