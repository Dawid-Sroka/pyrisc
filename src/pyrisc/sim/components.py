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

from abc import ABC, abstractmethod

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
VPO_MASK = 2**VPO_LENTGH - 1
VPN_MASK = 2**32 - 1 - VPO_MASK

class PageTableEntry:
    def __init__(self, vpn, prot):
        self.vpn = vpn
        self.perms = prot
        self.physical_page     = bytes(PAGE_SIZE)
    

class TranslatesAddresses(ABC):
    
    @abstractmethod
    # returns pte or None (when there is no such page)
    def translate(self, vpn: int) -> PageTableEntry | None:
        raise NotImplementedError


class MMU():
    def __init__(self, translates_addresses: TranslatesAddresses):
        self.page_table = translates_addresses

    # def mem_store(self, va, data) -> (WORD, int):
    #     NotImplementedError

    # def mem_load(self,va) -> (WORD, int):
    #     NotImplementedError

    def mem_access(self, valid, va, data, function) -> (WORD, int):
        # if not valid:
        #     return ( WORD(0), True )
        vpn = va >> VPO_LENTGH
        vpo = (va & VPO_MASK)
        pte = self.page_table.translate(vpn)
        if pte == None:
            # there's no such page in pt
            # kernel must do something
            return ( WORD(0), EXC_PAGE_FAULT_MISS )
        elif function == M_XRD:
            # check pte permissions, validity etc
            if pte.perms == M_READ_ONLY or pte.perms == M_READ_WRITE:
                page = pte.physical_page
                ppo = vpo
                word_value = int.from_bytes(page[ppo:ppo+WORD_SIZE], "little")
                return ( WORD(word_value), EXC_NONE )
            else:
                # fault
                return ( WORD(0), EXC_PAGE_FAULT_PERMS )
        elif function == M_XWR:
            # check permissions, validity etc
            if pte.perms == M_READ_WRITE:
                page = pte.physical_page
                ppo = vpo
                word_as_bytes = int(data).to_bytes(WORD_SIZE, "little")
                page[ppo:ppo+WORD_SIZE] = word_as_bytes
                return ( WORD(0), EXC_NONE )
            else:
                # fault
                return ( WORD(0), EXC_PAGE_FAULT_PERMS )
        else:
            return ( WORD(0), EXC_ILLEGAL_INST )


#--------------------------------------------------------------------------
#   Clock: models a cpu clock
#--------------------------------------------------------------------------

class Clock(object):

    def __init__(self):
        self.cycles = 0
        ## period - how often clock interrupt occurs
        self.period = 500
