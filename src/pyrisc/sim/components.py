#==========================================================================
#
#   The PyRISC Project
#
#   SNURISC: A RISC-V ISA Simulator
#
#   Classes for hardware components: RegisterFile, Register, and Memory.
#
#   Jin-Soo Kim
#   Systems Software and Architecture Laboratory
#   Seoul National University
#   http://csl.snu.ac.kr
#
#==========================================================================


from pyrisc.sim.consts import *
from pyrisc.sim.isa import *


#--------------------------------------------------------------------------
#   Constants
#--------------------------------------------------------------------------

# Symbolic register names
rname =  [
            'zero', 'ra',  'sp',  'gp',  'tp',  't0',  't1',  't2',
            's0',   's1',  'a0',  'a1',  'a2',  'a3',  'a4',  'a5',
            'a6',   'a7',  's2',  's3',  's4',  's5',  's6',  's7',
            's8',   's9',  's10', 's11', 't3',  't4',  't5',  't6'
        ]


#--------------------------------------------------------------------------
#   RegisterFile: models 32-bit RISC-V register file
#--------------------------------------------------------------------------

class RegisterFile(object):

    def __init__(self):
        self.reg = WORD([0] * NUM_REGS)

    def read(self, regno):

        if regno == 0:
            return 0
        elif regno > 0 and regno < NUM_REGS:
            return self.reg[regno]
        else:
            raise ValueError

    def write(self, regno, value):

        if regno == 0:
            return
        elif regno > 0 and regno < NUM_REGS:
            self.reg[regno] = WORD(value)
        else:
            raise ValueError

    def dump(self, columns = 4):

        print("Registers")
        print("=" * 9)
        for c in range (0, NUM_REGS, columns):
            str = ""
            for r in range (c, min(NUM_REGS, c + columns)):
                name = rname[r]
                val = self.reg[r]
                str += "%-11s0x%08x    " % ("%s ($%d):" % (name, r), val)
            print(str)


#--------------------------------------------------------------------------
#   Register: models a single 32-bit register
#--------------------------------------------------------------------------

class Register(object):

    def __init__(self, initval = 0):
        self.r = WORD(initval)

    def read(self):
        return self.r

    def write(self, val):
        self.r = WORD(val)


#--------------------------------------------------------------------------
#   Memory: models a memory
#--------------------------------------------------------------------------

class Memory(object):

    def __init__(self, mem_start, mem_size, word_size):

        self.word_size  = word_size
        self.mem_words  = mem_size // word_size
        self.mem_start  = mem_start
        self.mem_end    = mem_start + mem_size
        self.mem        = WORD([0] * self.mem_words)

    def access(self, valid, addr, data, fcn):

        if (not valid):
            res = ( WORD(0), True )
        elif (addr < self.mem_start) or (addr >= self.mem_end) or \
            addr % self.word_size != 0:
            res = ( WORD(0) , False )
        elif fcn == M_XRD:
            val = self.mem[(addr - self.mem_start) // self.word_size]
            res = ( val, True )
        elif fcn == M_XWR:
            self.mem[(addr - self.mem_start) // self.word_size] = WORD(data)
            res = ( WORD(0), True )
        else:
            res = ( WORD(0), False )
        return res

    def dump(self, skipzero = False):

        print("Memory 0x%08x - 0x%08x" % (self.mem_start, self.mem_end - 1))
        print("=" * 30)
        for a in range(self.mem_start, self.mem_end, self.word_size):
            val, status = self.access(True, a, 0, M_XRD)
            if not status:
                continue
            if (not skipzero) or (val != 0):
                print("0x%08x: " % a, ' '.join("%02x" % ((val >> i) & 0xff) for i in [0, 8, 16, 24]), " (0x%08x)" % val)


VPO_LENTGH = 12
PAGE_SIZE = 2 ** VPO_LENTGH

class PageTableEntry:
    def __init__(self, vpn):
        self.vpn = vpn
        words_in_page  = PAGE_SIZE // WORD_SIZE
        self.physical_page     = WORD([0] * words_in_page)

class PageTable:
    def __init__(self):
        self.table = {}

    def access(self, valid, va, data, function):
        if not valid:
            return ( WORD(0), True )
        vpn = va >> VPO_LENTGH
        VPO_MASK = 2**VPO_LENTGH - 1
        vpo = (va & VPO_MASK) // WORD_SIZE
        if function == M_XRD:
            # check permissions, validity etc
            if vpn not in self.table.keys():
                return ( WORD(0), False )
            pte = self.table[vpn]
            page = pte.physical_page
            ppo = vpo
            return ( page[ppo], True )
        elif function == M_XWR:
            # check permissions, validity etc
            if vpn not in self.table.keys():
                self.table[vpn] = PageTableEntry(vpn)
            pte = self.table[vpn]
            page = pte.physical_page
            ppo = vpo
            page[ppo] = data
            return ( WORD(0), True )
        else:
            return ( WORD(0), False )

    def get_byte(self, va: int):
        word, _ = self.access(True, va, 0, M_XRD)
        remainder = va % 4
        byte = (word >> (remainder * 8)) & 0xFF
        return byte


#--------------------------------------------------------------------------
#   Clock: models a cpu clock
#--------------------------------------------------------------------------

class Clock(object):

    def __init__(self):
        self.cycles = 0
        ## period - how often clock interrupt occurs
        self.period = 500
