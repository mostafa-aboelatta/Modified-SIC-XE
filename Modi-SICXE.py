import sys
import re
from pathlib import Path


#  Team Names & Reg Numbers:
#  Kairm Magdy 231003685
#  Mustafa Aboelatta 231003175
#  Seif Soliman 231016024


OPTAB = {
    'ADD':   (0x18, 34), 'ADDF':  (0x58, 34), 'ADDR':  (0x90, 2),
    'AND':   (0x40, 34), 'CLEAR': (0xB4, 2),  'COMP':  (0x28, 34),
    'COMPF': (0x88, 34), 'COMPR': (0xA0, 2),  'DIV':   (0x24, 34),
    'DIVF':  (0x64, 34), 'DIVR':  (0x9C, 2),  'FIX':   (0xC4, 1),
    'FLOAT': (0xC0, 1),  'HIO':   (0xF4, 1),  'J':     (0x3C, 34),
    'JEQ':   (0x30, 34), 'JGT':   (0x34, 34), 'JLT':   (0x38, 34),
    'JSUB':  (0x48, 34), 'LDA':   (0x00, 34), 'LDB':   (0x68, 34),
    'LDCH':  (0x50, 34), 'LDF':   (0x70, 34), 'LDL':   (0x08, 34),
    'LDS':   (0x6C, 34), 'LDT':   (0x74, 34), 'LDX':   (0x04, 34),
    'LPS':   (0xD0, 34), 'MUL':   (0x20, 34), 'MULF':  (0x60, 34),
    'MULR':  (0x98, 2),  'NORM':  (0xC8, 1),  'OR':    (0x44, 34),
    'RD':    (0xD8, 34), 'RMO':   (0xAC, 2),  'RSUB':  (0x4C, 34),
    'SHIFTL':(0xA4, 2),  'SHIFTR':(0xA8, 2),  'SIO':   (0xF0, 1),
    'SSK':   (0xEC, 34), 'STA':   (0x0C, 34), 'STB':   (0x78, 34),
    'STCH':  (0x54, 34), 'STF':   (0x80, 34), 'STI':   (0xD4, 34),
    'STL':   (0x14, 34), 'STS':   (0x7C, 34), 'STSW':  (0xE8, 34),
    'STT':   (0x84, 34), 'STX':   (0x10, 34), 'SUB':   (0x1C, 34),
    'SUBF':  (0x5C, 34), 'SUBR':  (0x94, 2),  'SVC':   (0xB0, 2),
    'TD':    (0xE0, 34), 'TIO':   (0xF8, 1),  'TIX':   (0x2C, 34),
    'TIXR':  (0xB8, 2),  'WD':    (0xDC, 34),
}

REGTAB = {
    'A': 0, 'X': 1, 'L': 2, 'B': 3,
    'S': 4, 'T': 5, 'F': 6, 'PC': 8, 'SW': 9
}

VALID_BLOCK_NAMES = {'DEFAULT', 'DEFAULTB', 'CDATA', 'CBLKS'}

block_Table = {
    'DEFAULT': 0, 'DEFAULTB': 0,
    'CDATA':   0, 'CBLKS':    0, 'POOL': 0
}

# ── order_blocks: assigns order number to each block as it appears ──
def order_blocks():
    total = sum(block_Table.values())
    if   total == 0:  return 1
    elif total == 1:  return 2
    elif total == 3:  return 3
    elif total == 6:  return 4
    else:             return 5

DIRECTIVES = {'START', 'END', 'USE', 'BASE', 'RESW', 'RESB', 'WORD', 'BYTE', 'EQU'}

# ── Read input file ──
input_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('in.txt')
with open(input_file, 'r') as f:
    lines = f.readlines()

symbols      = []
instructions = []
references   = []

for line in lines:
    l = line.split()
    if len(l) == 0:
        symbols.append(' ')
        instructions.append(' ')
        references.append(' ')
    elif len(l) == 1:
        symbols.append(' ')
        instructions.append(l[0])
        references.append(' ')
    elif len(l) == 2:
        symbols.append(' ')
        instructions.append(l[0])
        references.append(l[1])
    else:
        symbols.append(l[0])
        instructions.append(l[1])
        references.append(l[2])

# ── Detect format of each instruction ──
instructions_format = []
for inst in instructions:
    mn = inst[1:] if inst.startswith('+') else inst
    mn = mn.upper()
    if mn in OPTAB:
        fmt = OPTAB[mn][1]
        if   fmt == 1:  instructions_format.append('1')
        elif fmt == 2:  instructions_format.append('2')
        elif fmt == 34: instructions_format.append('4' if inst.startswith('+') else '3')
    else:
        instructions_format.append(' ')

# ── Block LC trackers: [start, size] ──
D  = ['0x0000', '0x0000']   # DEFAULT
DB = ['0x0000', '0x0000']   # DEFAULTB
CD = ['0x0000', '0x0000']   # CDATA
CB = ['0x0000', '0x0000']   # CBLKS
P  = ['0x0000', '0x0000']   # POOL


#  PASS 1 — Location Counter + Symbol Table
 

location_counter = []   # block-relative LC per line
line_block       = []   # which block each line belongs to
track            = ' '  # current active block tracker string
check_blocks     = ' '  # last seen USE operand
program_name     = 'NONAME'
start_addr       = 0
pool_inserted    = False

# Error helper
def error_exit(error_name, pc, line_num, detail):
    with open('error.txt', 'w') as ef:
        ef.write(f"Error : {error_name}\n")
        ef.write(f"PC    : {pc:06X}\n")
        ef.write(f"Line  : line {line_num}\n")
        ef.write(f"Detail: {detail}\n")
    sys.exit(1)

# Get current absolute PC for error reporting
def get_abs_pc(track, D, DB, CD, CB):
    if   track == 'D':  return int(D[1],  16)
    elif track == 'DB': return int(DB[1], 16)
    elif track == 'CD': return int(CD[1], 16)
    elif track == 'CB': return int(CB[1], 16)
    return 0

for i, f in enumerate(instructions_format):
    line_num = i + 1

    # ── Pool operand detection: must happen BEFORE block assignment ──
    ref = references[i]
    if ref and ref[0] == '&' and not pool_inserted:
        block_Table['POOL'] = order_blocks()
        pool_inserted = True

    # ── Format 1/2/3/4: goes to the currently active block ──
    if f in ('1', '2', '3', '4'):
        sz = int(f)
        # Determine active block from check_blocks (last USE operand)
        cb = check_blocks.upper().strip() if check_blocks.strip() else 'DEFAULT'
        if cb not in ('DEFAULT', 'DEFAULTB', 'CDATA', 'CBLKS'):
            cb = 'DEFAULT'

        if cb == 'DEFAULT':
            if block_Table['DEFAULT'] == 0:
                block_Table['DEFAULT'] = order_blocks()
            location_counter.append(D[1])
            line_block.append('DEFAULT')
            D[1] = hex(int(D[1], 16) + sz)
            track = 'D'

        elif cb == 'DEFAULTB':
            if block_Table['DEFAULTB'] == 0:
                block_Table['DEFAULTB'] = order_blocks()
            location_counter.append(DB[1])
            line_block.append('DEFAULTB')
            DB[1] = hex(int(DB[1], 16) + sz)
            track = 'DB'

        elif cb == 'CDATA':
            if block_Table['CDATA'] == 0:
                block_Table['CDATA'] = order_blocks()
            location_counter.append(CD[1])
            line_block.append('CDATA')
            CD[1] = hex(int(CD[1], 16) + sz)
            track = 'CD'

        elif cb == 'CBLKS':
            if block_Table['CBLKS'] == 0:
                block_Table['CBLKS'] = order_blocks()
            location_counter.append(CB[1])
            line_block.append('CBLKS')
            CB[1] = hex(int(CB[1], 16) + sz)
            track = 'CB'

    # ── Directive ──
    else:
        directive = instructions[i].upper()

        if directive == 'START':
            program_name = symbols[i] if symbols[i].strip() else 'NONAME'
            start_addr   = int(references[i], 16) if references[i].strip() else 0
            location_counter.append('0x0000')
            line_block.append('DEFAULT')

        elif directive == 'USE':
            new_block = references[i].strip().upper() if references[i].strip() else 'DEFAULT'
            # Validate block name
            if new_block not in VALID_BLOCK_NAMES:
                abs_pc = get_abs_pc(track, D, DB, CD, CB)
                error_exit(
                    "Unidentified Block Name",
                    abs_pc, line_num,
                    f"unknown block name '{new_block}'; valid blocks are " +
                    ', '.join(sorted(VALID_BLOCK_NAMES))
                )
            check_blocks = new_block
            location_counter.append(' ')
            line_block.append(new_block)

        elif directive == 'BASE':
            # BASE/NOBASE: recorded at current block LC, no LC change
            if   track == 'D':  location_counter.append(D[1])
            elif track == 'DB': location_counter.append(DB[1])
            elif track == 'CD': location_counter.append(CD[1])
            elif track == 'CB': location_counter.append(CB[1])
            else:               location_counter.append(' ')
            line_block.append(check_blocks if check_blocks.strip() else 'DEFAULT')

        elif directive in ('RESW', 'RESB', 'WORD', 'BYTE'):
            cb = check_blocks.upper() if check_blocks.strip() else 'DEFAULT'

            if cb == 'CDATA':
                if block_Table['CDATA'] == 0:
                    block_Table['CDATA'] = order_blocks()
                track = 'CD'
                location_counter.append(CD[1])
                line_block.append('CDATA')
                if   directive == 'WORD': CD[1] = hex(int(CD[1], 16) + 3)
                elif directive == 'RESW': CD[1] = hex(int(CD[1], 16) + 3 * int(references[i]))
                elif directive == 'RESB': CD[1] = hex(int(CD[1], 16) + int(references[i]))  
                elif directive == 'BYTE':
                    r = references[i]
                    if r.upper().startswith('C'):
                        inner = re.match(r"C'([^']*)'", r, re.IGNORECASE)
                        sz = len(inner.group(1)) if inner else 0
                    else:
                        inner = re.match(r"X'([0-9A-Fa-f]*)'", r, re.IGNORECASE)
                        hx = inner.group(1) if inner else ''
                        if len(hx) % 2 != 0: hx = '0' + hx
                        sz = len(hx) // 2
                    CD[1] = hex(int(CD[1], 16) + sz)

            elif cb == 'CBLKS':
                if block_Table['CBLKS'] == 0:
                    block_Table['CBLKS'] = order_blocks()
                track = 'CB'
                location_counter.append(CB[1])
                line_block.append('CBLKS')
                if   directive == 'WORD': CB[1] = hex(int(CB[1], 16) + 3)
                elif directive == 'RESW': CB[1] = hex(int(CB[1], 16) + 3 * int(references[i])) 
                elif directive == 'RESB': CB[1] = hex(int(CB[1], 16) + int(references[i]))
                elif directive == 'BYTE':
                    r = references[i]
                    if r.upper().startswith('C'):
                        inner = re.match(r"C'([^']*)'", r, re.IGNORECASE)
                        sz = len(inner.group(1)) if inner else 0
                    else:
                        inner = re.match(r"X'([0-9A-Fa-f]*)'", r, re.IGNORECASE)
                        hx = inner.group(1) if inner else ''
                        if len(hx) % 2 != 0: hx = '0' + hx
                        sz = len(hx) // 2
                    CB[1] = hex(int(CB[1], 16) + sz)

            else:
                # WORD/BYTE in DEFAULT or DEFAULTB
                if cb == 'DEFAULTB':
                    if block_Table['DEFAULTB'] == 0:
                        block_Table['DEFAULTB'] = order_blocks()
                    track = 'DB'
                    location_counter.append(DB[1])
                    line_block.append('DEFAULTB')
                    if   directive == 'WORD': DB[1] = hex(int(DB[1], 16) + 3)
                    elif directive == 'RESW': DB[1] = hex(int(DB[1], 16) + 3 * int(references[i]))
                    elif directive == 'RESB': DB[1] = hex(int(DB[1], 16) + int(references[i]))
                    elif directive == 'BYTE':
                        r = references[i]
                        if r.upper().startswith('C'):
                            inner = re.match(r"C'([^']*)'", r, re.IGNORECASE)
                            sz = len(inner.group(1)) if inner else 0
                        else:
                            inner = re.match(r"X'([0-9A-Fa-f]*)'", r, re.IGNORECASE)
                            hx = inner.group(1) if inner else ''
                            if len(hx) % 2 != 0: hx = '0' + hx
                            sz = len(hx) // 2
                        DB[1] = hex(int(DB[1], 16) + sz)
                else:
                    if block_Table['DEFAULT'] == 0:
                        block_Table['DEFAULT'] = order_blocks()
                    track = 'D'
                    location_counter.append(D[1])
                    line_block.append('DEFAULT')
                    if   directive == 'WORD': D[1] = hex(int(D[1], 16) + 3)
                    elif directive == 'RESW': D[1] = hex(int(D[1], 16) + 3 * int(references[i]))
                    elif directive == 'RESB': D[1] = hex(int(D[1], 16) + int(references[i]))
                    elif directive == 'BYTE':
                        r = references[i]
                        if r.upper().startswith('C'):
                            inner = re.match(r"C'([^']*)'", r, re.IGNORECASE)
                            sz = len(inner.group(1)) if inner else 0
                        else:
                            inner = re.match(r"X'([0-9A-Fa-f]*)'", r, re.IGNORECASE)
                            hx = inner.group(1) if inner else ''
                            if len(hx) % 2 != 0: hx = '0' + hx
                            sz = len(hx) // 2
                        D[1] = hex(int(D[1], 16) + sz)

        elif directive == 'END':
            if   track == 'D':  location_counter.append(D[1])
            elif track == 'DB': location_counter.append(DB[1])
            elif track == 'CD': location_counter.append(CD[1])
            elif track == 'CB': location_counter.append(CB[1])
            else:               location_counter.append('0x0000')
            line_block.append(check_blocks if check_blocks.strip() else 'DEFAULT')

        else:
            location_counter.append(' ')
            line_block.append(check_blocks if check_blocks.strip() else 'DEFAULT')

# ── Save block sizes (final LC = size) ──
for key in block_Table:
    if block_Table[key] != 0:
        block_Table[key] -= 1

block_sizes = {
    'DEFAULT':  int(D[1],  16),
    'DEFAULTB': int(DB[1], 16),
    'CDATA':    int(CD[1], 16),
    'CBLKS':    int(CB[1], 16),
}

# ── Compute POOL size from pool operands ──
pool_entries   = []   # list of (operand_str, data_bytes)
pool_seen      = set()
pool_lc        = 0

for ref in references:
    if ref and ref[0] == '&' and ref not in pool_seen:
        pool_seen.add(ref)
        rest = ref[1:]
        m = re.match(r"C'([^']*)'", rest, re.IGNORECASE)
        if m:
            data = bytes([ord(c) for c in m.group(1)])
        else:
            m = re.match(r"X'([0-9A-Fa-f]*)'", rest, re.IGNORECASE)
            hx = m.group(1) if m else ''
            if len(hx) % 2 != 0: hx = '0' + hx
            data = bytes.fromhex(hx)
        pool_entries.append((ref, pool_lc, data))
        pool_lc += len(data)

pool_sizes = pool_lc
P[1] = hex(pool_sizes)

# ── Build ordered block list based on block_Table order numbers ──
# block_Table values: order number (1=first, 2=second...) or 0=unused
# Convert back: subtract 1 already done above, now values are 0-indexed order
order_to_name = {}
for name, order in block_Table.items():
    if order >= 0 and (int(D[1],16) > 0 or int(DB[1],16) > 0 or
                       int(CD[1],16) > 0 or int(CB[1],16) > 0 or pool_sizes > 0):
        # Only include blocks that were actually used
        used = {
            'DEFAULT':  int(D[1],  16) > 0,
            'DEFAULTB': int(DB[1], 16) > 0,
            'CDATA':    int(CD[1], 16) > 0,
            'CBLKS':    int(CB[1], 16) > 0,
            'POOL':     pool_sizes > 0,
        }
        if used.get(name, False) or block_Table[name] > 0:
            order_to_name[block_Table[name]] = name

block_order = [order_to_name[k] for k in sorted(order_to_name.keys()) if k >= 0]

# ── Compute absolute start addresses ──
abs_starts = {}
addr = 0
for bname in block_order:
    abs_starts[bname] = addr
    if   bname == 'DEFAULT':  addr += int(D[1],  16)
    elif bname == 'DEFAULTB': addr += int(DB[1], 16)
    elif bname == 'CDATA':    addr += int(CD[1], 16)
    elif bname == 'CBLKS':    addr += int(CB[1], 16)
    elif bname == 'POOL':     addr += pool_sizes

total_length = addr


#  BUILD SYMBOL TABLE
#  symbol -> absolute address

sym_table = {}

for i, sym in enumerate(symbols):
    if sym.strip() and sym.strip().upper() not in (program_name.upper(),):
        lc_str = location_counter[i]
        if lc_str.strip():
            blk   = line_block[i] if i < len(line_block) else 'DEFAULT'
            lc_val = int(lc_str, 16) if lc_str.strip() else 0
            abs_addr = abs_starts.get(blk, 0) + lc_val
            sym_table[sym.strip().upper()] = abs_addr
 
#  BUILD POOL TABLE
#  pool_entry -> (absolute address, length, hex data)

pool_abs_start = abs_starts.get('POOL', 0)
pool_table = {}    # operand_str -> (abs_addr, data_bytes)
for (op_str, rel_lc, data) in pool_entries:
    pool_table[op_str] = (pool_abs_start + rel_lc, data)


#  RESOLVE END OPERAND
#  If END COPY (program name not in symtable), resolve to FIRST

end_operand = ''
for i, inst in enumerate(instructions):
    if inst.upper() == 'END':
        end_operand = references[i].strip().upper()
        break

if end_operand == program_name.upper() and end_operand not in sym_table:
    # Find first symbol in DEFAULT at lc=0
    for sym, addr in sym_table.items():
        if addr == abs_starts.get('DEFAULT', 0):
            end_operand = sym
            # Update references list too
            for i, inst in enumerate(instructions):
                if inst.upper() == 'END':
                    references[i] = sym
            break


#  WRITE intermediate.txt

def write_intermediate():
    with open('intermediate.txt', 'w') as f:
        f.write(f"{'Location counter':<18}{'Symbol':<9}{'Instructions':<14}{'Reference'}\n")
        f.write(f"{'----------------':<18}{'-------':<9}{'------------':<14}{'----------'}\n")
        for i in range(len(instructions)):
            if instructions[i].strip() == ' ' or instructions[i].strip() == '':
                continue
            lc  = location_counter[i] if i < len(location_counter) else ' '
            sym = symbols[i].strip()
            mn  = instructions[i].strip()
            ref = references[i].strip()

            lc_str = ''
            if lc.strip():
                try:
                    lc_str = f"{int(lc, 16):04X}"
                except:
                    lc_str = ''

            f.write(f"{lc_str:<18}{sym:<9}{mn:<14}{ref}\n")


#  WRITE symbTable.txt

def write_symtable():
    with open('symbTable.txt', 'w') as f:
        f.write(f"{'SYMBOL NAME':<13}{'ADDRESS'}\n")
        for sym, addr in sym_table.items():
            f.write(f"{sym:<13}{addr:04X}\n")


#  WRITE blockTable.txt

def write_blocktable():
    with open('blockTable.txt', 'w') as f:
        f.write(f"{'BLOCK NAME':<12}{'BLOCK NUMBER':<14}{'ADDRESS':<9}{'SIZE'}\n")
        for idx, bname in enumerate(block_order):
            bstart = abs_starts[bname]
            if   bname == 'DEFAULT':  bsize = int(D[1],  16)
            elif bname == 'DEFAULTB': bsize = int(DB[1], 16)
            elif bname == 'CDATA':    bsize = int(CD[1], 16)
            elif bname == 'CBLKS':    bsize = int(CB[1], 16)
            elif bname == 'POOL':     bsize = pool_sizes
            else: bsize = 0
            f.write(f"{bname:<12}{idx:<14}{bstart:04X}     {bsize:04X}\n")
        f.write(f"\nTotal program length: {total_length:X}\n")


#  WRITE PoolTable.txt

def write_pooltable():
    with open('PoolTable.txt', 'w') as f:
        f.write(f"{'POOL NAME':<11}{'ADDRESS':<9}{'LENGTH':<8}{'OBJECT CODE'}\n")
        for (op_str, rel_lc, data) in pool_entries:
            abs_addr = pool_table[op_str][0]
            f.write(f"{op_str:<11}{abs_addr:04X}     {len(data):<8}{data.hex().upper()}\n")


#  PASS 2 — Object Code Generation

base_reg_val = None   # absolute address in BASE register
pass2_lines  = []     # list of dicts: lc, sym, mn, ref, obj_code, abs_lc
mod_records  = []     # (abs_addr, nibble_length) for M records

for i in range(len(instructions)):
    mn  = instructions[i].strip().upper()
    sym = symbols[i].strip().upper()
    ref = references[i].strip()
    lc  = location_counter[i]
    blk = line_block[i] if i < len(line_block) else 'DEFAULT'

    force4 = mn.startswith('+')
    if force4:
        mn = mn[1:]

    # Absolute LC of this instruction
    if lc.strip():
        try:
            abs_lc = abs_starts.get(blk, 0) + int(lc, 16)
        except:
            abs_lc = 0
    else:
        abs_lc = None

    obj_code = None

    # ── Directives with no object code ──
    if mn in ('START', 'USE', 'END', 'RESW', 'RESB', 'EQU', ''):
        pass2_lines.append({
            'lc': lc, 'sym': sym, 'mn': ('+' if force4 else '') + mn,
            'ref': ref, 'obj_code': None, 'abs_lc': abs_lc
        })
        continue

    if mn == 'BASE':
        sym_up = ref.upper()
        if sym_up in sym_table:
            base_reg_val = sym_table[sym_up]
        elif ref.strip().lstrip('-').isdigit():
            base_reg_val = int(ref)
        pass2_lines.append({
            'lc': lc, 'sym': sym, 'mn': mn,
            'ref': ref, 'obj_code': None, 'abs_lc': abs_lc
        })
        continue

    if mn == 'NOBASE':
        base_reg_val = None
        pass2_lines.append({
            'lc': lc, 'sym': sym, 'mn': mn,
            'ref': ref, 'obj_code': None, 'abs_lc': abs_lc
        })
        continue

    # ── WORD ──
    if mn == 'WORD':
        val = int(ref) if ref.lstrip('-').isdigit() else 0
        obj_code = f"{val & 0xFFFFFF:06X}"
        pass2_lines.append({
            'lc': lc, 'sym': sym, 'mn': mn,
            'ref': ref, 'obj_code': obj_code, 'abs_lc': abs_lc
        })
        continue

    # ── BYTE ──
    if mn == 'BYTE':
        m = re.match(r"C'([^']*)'", ref, re.IGNORECASE)
        if m:
            data = bytes([ord(c) for c in m.group(1)])
        else:
            m = re.match(r"X'([0-9A-Fa-f]*)'", ref, re.IGNORECASE)
            hx = m.group(1) if m else ''
            if len(hx) % 2 != 0: hx = '0' + hx
            data = bytes.fromhex(hx)
        obj_code = data.hex().upper()
        pass2_lines.append({
            'lc': lc, 'sym': sym, 'mn': mn,
            'ref': ref, 'obj_code': obj_code, 'abs_lc': abs_lc
        })
        continue

    # ── Must be a real instruction ──
    if mn not in OPTAB:
        pc_err = abs_lc if abs_lc else 0
        error_exit("Unidentified Mnemonic", pc_err, i+1,
                   f"unknown mnemonic '{mn}'")

    opcode, base_fmt = OPTAB[mn]
    fmt = 4 if force4 else (3 if base_fmt == 34 else base_fmt)

    # ── Format 1 ──
    if fmt == 1:
        obj_code = f"{opcode:02X}"

    # ── Format 2 ──
    elif fmt == 2:
        regs = [r.strip() for r in ref.split(',')] if ref.strip() else []
        r1   = REGTAB.get(regs[0].upper(), 0) if len(regs) > 0 else 0
        r2   = REGTAB.get(regs[1].upper(), 0) if len(regs) > 1 else 0
        obj_code = f"{opcode:02X}{r1:X}{r2:X}"

    # ── Format 3 ──
    elif fmt == 3:
        n, i_bit, x = 1, 1, 0
        raw = ref

        if raw.startswith('#'):
            n = 0; i_bit = 1
            raw = raw[1:]
        elif raw.startswith('@'):
            n = 1; i_bit = 0
            raw = raw[1:]

        if raw.upper().endswith(',X'):
            x = 1
            raw = raw[:-2]

        is_pool = raw.startswith('&')

        # Get target address
        ta = None
        is_numeric = False

        if not raw.strip():
            # No operand (e.g. RSUB) -> force object code with disp=0, no flags
            byte1 = (opcode & 0xFC) | ((n & 1) << 1) | (i_bit & 1)
            byte2 = 0x00
            byte3 = 0x00
            obj_code = f"{byte1:02X}{byte2:02X}{byte3:02X}"
            pass2_lines.append({
                'lc': lc, 'sym': sym, 'mn': ('+' if force4 else '') + mn,
                'ref': ref, 'obj_code': obj_code, 'abs_lc': abs_lc
            })
            continue
        elif is_pool:
            entry = pool_table.get(ref)
            if entry is None:
                error_exit("POOLVAR error", abs_lc or 0, i+1,
                           f"pool operand '{ref}' not found")
            ta = entry[0]
        elif raw.strip().lstrip('-').isdigit():
            ta = int(raw)
            is_numeric = True
        else:
            ta = sym_table.get(raw.upper())
            if ta is None:
                error_exit("Unidentified Symbol", abs_lc or 0, i+1,
                           f"symbol '{raw}' is not defined")

        # Calculate displacement
        b = 0; p = 0; disp = 0

        if is_numeric and n == 0 and i_bit == 1:
            # Pure immediate number → embed directly
            disp = ta & 0xFFF
        else:
            pc   = abs_lc + 3
            pc_d = ta - pc
            b_d  = (ta - base_reg_val) if base_reg_val is not None else None

            if -2048 <= pc_d <= 2047:
                p    = 1
                disp = pc_d & 0xFFF
            elif b_d is not None and 0 <= b_d <= 4095:
                b    = 1
                disp = b_d
            else:
                if is_pool:
                    error_exit(
                        "POOLVAR error",
                        abs_lc or 0, i+1,
                        f"pool operand '{ref}' cannot be addressed using PC-relative or Base-relative addressing"
                    )
                else:
                    error_exit(
                        "Addressing Error",
                        abs_lc or 0, i+1,
                        f"cannot address '{ref}' using PC or Base relative"
                    )

        byte1 = (opcode & 0xFC) | ((n & 1) << 1) | (i_bit & 1)
        byte2 = ((x&1)<<7)|((b&1)<<6)|((p&1)<<5)|((disp>>8)&0xF)
        byte3 = disp & 0xFF
        obj_code = f"{byte1:02X}{byte2:02X}{byte3:02X}"

    # ── Format 4 ──
    elif fmt == 4:
        n, i_bit, x = 1, 1, 0
        raw = ref

        if raw.startswith('#'):
            n = 0; i_bit = 1
            raw = raw[1:]
        elif raw.startswith('@'):
            n = 1; i_bit = 0
            raw = raw[1:]

        if raw.upper().endswith(',X'):
            x = 1
            raw = raw[:-2]

        ta = sym_table.get(raw.upper())
        if ta is None:
            try:    ta = int(raw, 0)
            except: error_exit("Unidentified Symbol", abs_lc or 0, i+1,
                                f"symbol '{raw}' is not defined")

        byte1 = (opcode & 0xFC) | ((n & 1) << 1) | (i_bit & 1)
        byte2 = ((x&1)<<7) | (0<<6) | (0<<5) | (1<<4) | ((ta>>16)&0xF)
        byte3 = (ta >> 8) & 0xFF
        byte4 = ta & 0xFF
        obj_code = f"{byte1:02X}{byte2:02X}{byte3:02X}{byte4:02X}"

        # Modification record: abs_lc+1, length=5 nibbles
        if abs_lc is not None:
            mod_records.append((abs_lc + 1, 5))

    pass2_lines.append({
        'lc': lc, 'sym': sym, 'mn': ('+' if force4 else '') + mn,
        'ref': ref, 'obj_code': obj_code, 'abs_lc': abs_lc
    })


#  WRITE out_pass2.txt

def write_pass2():
    with open('out_pass2.txt', 'w') as f:
        f.write(f"{'Location counter':<18}{'Symbol':<9}{'Instructions':<14}{'Reference':<12}{'Obj. code'}\n")
        f.write(f"{'----------------':<18}{'-------':<9}{'------------':<14}{'----------':<12}{'-------------- '}\n")
        for entry in pass2_lines:
            lc  = entry['lc']
            sym = entry['sym']
            mn  = entry['mn']
            ref = entry['ref']
            obj = entry['obj_code']

            lc_str = ''
            if lc.strip():
                try:    lc_str = f"{int(lc, 16):04X}"
                except: lc_str = ''

            mn_clean = mn.lstrip('+').upper()
            if mn_clean in ('RESW', 'RESB') or obj is None:
                obj_str = 'No object code'
            else:
                obj_str = obj

            f.write(f"{lc_str:<18}{sym:<9}{mn:<14}{ref:<12}{obj_str}\n")


#  GENERATE HTME RECORDS

def generate_htme():
    records = []

    # ── H record ──
    prog = (program_name + 'XX')[:8]
    records.append(f"H.{prog}.{start_addr:06X}.{total_length:06X}")

    # ── Collect (abs_addr, hex_string) for all object code ──
    segments = []

    for entry in pass2_lines:
        obj    = entry['obj_code']
        abs_lc = entry['abs_lc']
        mn     = entry['mn'].lstrip('+').upper()
        if obj and abs_lc is not None and mn not in ('RESW', 'RESB'):
            segments.append((abs_lc, obj))

    # Add pool entries
    for (op_str, rel_lc, data) in pool_entries:
        abs_addr = pool_table[op_str][0]
        segments.append((abs_addr, data.hex().upper()))

    # Sort segments by block order then by address
    def block_sort_key(seg):
        addr = seg[0]
        for idx, bname in enumerate(block_order):
            bstart = abs_starts[bname]
            bsize  = {'DEFAULT': int(D[1],16), 'DEFAULTB': int(DB[1],16),
                      'CDATA': int(CD[1],16), 'CBLKS': int(CB[1],16),
                      'POOL': pool_sizes}.get(bname, 0)
            if bstart <= addr < bstart + bsize:
                return (idx, addr)
        return (99, addr)

    # Group by block
    block_segs = {bname: [] for bname in block_order}
    for abs_addr, hex_str in segments:
        for bname in block_order:
            bstart = abs_starts[bname]
            bsize  = {'DEFAULT': int(D[1],16), 'DEFAULTB': int(DB[1],16),
                      'CDATA': int(CD[1],16), 'CBLKS': int(CB[1],16),
                      'POOL': pool_sizes}.get(bname, 0)
            if bstart <= abs_addr < bstart + bsize:
                block_segs[bname].append((abs_addr, hex_str))
                break

    # Generate T records per block (non-POOL first, then POOL)
    def gen_t_records(segs):
        recs = []
        if not segs:
            return recs
        segs = sorted(segs, key=lambda x: x[0])
        cur_start      = None
        cur_hex_list   = []
        cur_byte_count = 0

        def flush():
            nonlocal cur_start, cur_hex_list, cur_byte_count
            if cur_hex_list:
                recs.append(
                    f"T.{cur_start:06X}.{cur_byte_count:02X}." +
                    '.'.join(cur_hex_list)
                )
            cur_start = None; cur_hex_list = []; cur_byte_count = 0

        for abs_addr, hex_str in segs:
            blen     = len(hex_str) // 2
            expected = (cur_start + cur_byte_count) if cur_start is not None else None

            if cur_start is None:
                cur_start = abs_addr; cur_hex_list = [hex_str]; cur_byte_count = blen
            elif abs_addr == expected and cur_byte_count + blen <= 30:
                cur_hex_list.append(hex_str); cur_byte_count += blen
            else:
                flush()
                cur_start = abs_addr; cur_hex_list = [hex_str]; cur_byte_count = blen

        flush()
        return recs

    non_pool = [b for b in block_order if b != 'POOL']
    for bname in non_pool:
        records.extend(gen_t_records(block_segs[bname]))

    if 'POOL' in block_order:
        records.extend(gen_t_records(block_segs['POOL']))

    # ── M records ──
    for abs_addr, length in mod_records:
        records.append(f"M.{abs_addr:06X}.{length:02X}")

    # ── E record ──
    end_addr = sym_table.get(end_operand, start_addr)
    records.append(f"E.{end_addr:06X}")

    return records

def write_htme(records):
    with open('HTME.txt', 'w') as f:
        f.write('\n'.join(records) + '\n')




#  Memory Visualization

def write_memory_viz():
    # Ensure memory map covers at least the program length
    mem_size = max(total_length, 0x100)
    memory = ['--'] * mem_size

    def place(addr, hex_str):
        data = bytes.fromhex(hex_str)
        for j, b in enumerate(data):
            if addr + j < mem_size:
                memory[addr + j] = f"{b:02X}"

    # Populate memory from Pass 2 lines
    for entry in pass2_lines:
        obj = entry['obj_code']
        abs_lc = entry['abs_lc']
        mn = entry['mn'].lstrip('+').upper()
        if obj and abs_lc is not None and mn not in ('RESW', 'RESB'):
            place(abs_lc, obj)

    # Populate memory from literals pool
    for (op_str, rel_lc, data) in pool_entries:
        place(pool_table[op_str][0], data.hex().upper())

    # Generate Dynamic Column Headers (+0 to +F)
    col_headers = "".join([f'<th class="col-header">+{i:X}</th>' for i in range(16)])

    # Generate Rows
    rows = []
    for row in range((mem_size + 15) // 16):
        base = row * 16
        cells = ""
        for col in range(16):
            addr = base + col
            val = memory[addr] if addr < mem_size else '--'
            cls = 'used' if val != '--' else 'empty'
            # Add title for tooltip (address)
            cells += f'<td class="{cls}" title="{addr:06X}h">{val}</td>'
        rows.append(f'<tr><td class="addr">{base:06X}</td>{cells}</tr>')

    rows_str = '\n'.join(rows)

    # The New HTML Template
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Modi-SIC/XE Memory Map</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #F5F0E8; --surface: #EDE7D9; --surface2: #E3DBCB; --border: #C8BAA0;
    --border-dark: #A8967A; --text: #2E2A22; --text-muted: #7A6E5F; --addr-col: #5C4F3A;
    --used-bg: #2D5A3D; --used-text: #D4EDD9; --used-border: #1E3D29;
    --empty-bg: #EDE7D9; --empty-text: #C4B49A;
    --highlight-bg: #8B4513; --highlight-text: #FFF8EE;
    --header-bg: #2E2A22; --header-text: #D4C9B0;
    --btn-bg: #2D5A3D; --btn-text: #D4EDD9; --btn-hover: #1E3D29;
    --stat-accent: #5C8A3C; --shadow: rgba(46,42,34,0.12);
  }}

  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: var(--bg); color: var(--text); font-family: 'DM Mono', monospace;
    min-height: 100vh; padding: 32px 24px;
  }}

  .page-header {{ margin-bottom: 28px; padding-bottom: 20px; border-bottom: 2px solid var(--border-dark); }}
  .page-header h1 {{ font-family: 'DM Serif Display', serif; font-size: 2.2rem; margin-bottom: 6px; }}
  .page-header h1 em {{ font-style: italic; color: var(--used-bg); }}
  .page-header p {{ font-size: 0.78rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; }}

  .stats {{ display: flex; gap: 20px; margin-bottom: 24px; flex-wrap: wrap; }}
  .stat {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px 20px; box-shadow: 0 1px 4px var(--shadow); }}
  .stat-label {{ font-size: 0.68rem; text-transform: uppercase; color: var(--text-muted); margin-bottom: 4px; }}
  .stat-value {{ font-size: 1.1rem; font-weight: 500; color: var(--stat-accent); }}

  .controls {{ display: flex; gap: 10px; margin-bottom: 20px; align-items: center; }}
  .controls input {{ background: var(--surface); border: 1px solid var(--border-dark); color: var(--text); padding: 7px 12px; font-family: 'DM Mono', monospace; border-radius: 6px; width: 130px; }}
  .btn {{ background: var(--btn-bg); border: none; color: var(--btn-text); padding: 7px 18px; cursor: pointer; border-radius: 6px; }}
  .btn.secondary {{ background: transparent; border: 1px solid var(--border-dark); color: var(--text-muted); }}

  .mem-wrapper {{ border: 1px solid var(--border-dark); border-radius: 10px; overflow: hidden; box-shadow: 0 4px 16px var(--shadow); }}
  .mem-container {{ overflow-x: auto; max-height: 70vh; overflow-y: auto; }}
  table {{ border-collapse: collapse; font-size: 0.76rem; width: 100%; }}
  thead tr {{ position: sticky; top: 0; z-index: 2; }}
  .col-header {{ background: var(--header-bg); color: var(--header-text); padding: 9px 6px; text-align: center; border-right: 1px solid rgba(255,255,255,0.06); }}
  
  td {{ padding: 5px 3px; text-align: center; min-width: 34px; border-right: 1px solid var(--border); border-bottom: 1px solid var(--border); transition: background 0.12s; }}
  td.addr {{ color: var(--addr-col); text-align: right; padding-right: 14px; border-right: 2px solid var(--border-dark); background: var(--surface) !important; }}
  td.used {{ background: var(--used-bg) !important; color: var(--used-text) !important; font-weight: 500; }}
  td.empty {{ background: var(--empty-bg); color: var(--empty-text); }}
  td.highlight {{ background: var(--highlight-bg) !important; color: var(--highlight-text) !important; outline: 2px solid #6B3410; }}

  .legend {{ display: flex; gap: 24px; margin-top: 16px; align-items: center; }}
  .legend-item {{ display: flex; align-items: center; gap: 8px; font-size: 0.75rem; color: var(--text-muted); }}
  .legend-swatch {{ width: 16px; height: 16px; border-radius: 3px; border: 1px solid var(--border-dark); }}
  .legend-swatch.used {{ background: var(--used-bg); }}
  .legend-swatch.empty {{ background: var(--empty-bg); }}
  .legend-swatch.highlight {{ background: var(--highlight-bg); }}

  #tooltip {{ position: fixed; background: var(--header-bg); color: var(--header-text); font-size: 0.72rem; padding: 5px 10px; border-radius: 5px; pointer-events: none; opacity: 0; z-index: 100; }}
</style>
</head>
<body>
<div class="page-header">
  <h1>Modi-SIC/XE <em>Memory Map</em></h1>
  <p>Byte-addressable hexadecimal display &nbsp;·&nbsp; 16 columns per row</p>
</div>
<div class="stats">
  <div class="stat">
    <div class="stat-label">Program Size</div>
    <div class="stat-value">{total_length:06X}h</div>
  </div>
  <div class="stat">
    <div class="stat-label">Loaded Bytes</div>
    <div class="stat-value" id="usedCount">—</div>
  </div>
  <div class="stat">
    <div class="stat-label">Empty Bytes</div>
    <div class="stat-value" id="emptyCount">—</div>
  </div>
  <div class="stat">
    <div class="stat-label">Start Address</div>
    <div class="stat-value">{start_addr:06X}h</div>
  </div>
</div>
<div class="controls">
  <input type="text" id="jAddr" placeholder="Jump to e.g. 000004">
  <button class="btn" onclick="jump()">Go</button>
  <button class="btn secondary" onclick="resetHighlight()">Clear</button>
</div>
<div class="mem-wrapper">
  <div class="mem-container">
    <table id="mt">
      <thead><tr><th class="col-header">Address</th>{col_headers}</tr></thead>
      <tbody>{rows_str}</tbody>
    </table>
  </div>
</div>
<div class="legend">
  <div class="legend-item"><div class="legend-swatch used"></div><span>Loaded</span></div>
  <div class="legend-item"><div class="legend-swatch empty"></div><span>Empty</span></div>
  <div class="legend-item"><div class="legend-swatch highlight"></div><span>Target</span></div>
</div>
<div id="tooltip"></div>
<script>
  document.getElementById('usedCount').textContent = document.querySelectorAll('td.used').length + ' bytes';
  document.getElementById('emptyCount').textContent = document.querySelectorAll('td.empty').length + ' bytes';
  function jump() {{
    var val = document.getElementById('jAddr').value.trim();
    var a = parseInt(val, 16);
    if (isNaN(a)) return;
    var rows = document.querySelectorAll('#mt tbody tr');
    var r = Math.floor(a / 16), c = a % 16;
    if (r < rows.length) {{
      rows[r].scrollIntoView({{ behavior: 'smooth', block: 'center' }});
      resetHighlight();
      var tds = rows[r].querySelectorAll('td');
      if (tds[c + 1]) tds[c + 1].classList.add('highlight');
    }}
  }}
  function resetHighlight() {{ document.querySelectorAll('.highlight').forEach(el => el.classList.remove('highlight')); }}
  var tip = document.getElementById('tooltip');
  document.querySelectorAll('td').forEach(td => {{
    td.addEventListener('mousemove', e => {{
      if(td.classList.contains('addr')) return;
      tip.textContent = td.getAttribute('title') + ' -> ' + td.textContent;
      tip.style.left = (e.clientX + 15) + 'px'; tip.style.top = (e.clientY - 25) + 'px';
      tip.style.opacity = '1';
    }});
    td.addEventListener('mouseleave', () => tip.style.opacity = '0');
  }});
</script>
</body></html>"""

    with open('memory_viz.html', 'w') as f:
        f.write(html)


write_intermediate()
write_symtable()
write_blocktable()
write_pooltable()
write_pass2()
htme = generate_htme()
write_htme(htme)
write_memory_viz()

print("Assembly complete. Output files generated:")
print("  intermediate.txt, out_pass2.txt, symbTable.txt,")
print("  blockTable.txt, PoolTable.txt, HTME.txt, memory_viz.html")
