# Modi-SIC/XE Assembler

A two-pass assembly language processor for the Modified SIC/XE (Simple Instructional Computer with Extra Equipment) architecture. This project implements a complete assembler with support for multiple memory blocks, symbol resolution, and machine code generation.

## Overview

This assembler emulates a modified version of the SIC/XE machine, supporting both **Pass 1** (memory allocation and symbol table generation) and **Pass 2** (machine code generation). It processes assembly programs written in modi-SIC/XE language and generates executable object code in HTME format (Header, Text, Modification, End records).

### Key Features

- **Multi-Block Memory Architecture**: Supports up to 5 distinct memory blocks:
  - `DEFAULT`: Format 1 & 2 instructions
  - `DEFAULTB`: Format 3 & 4 instructions  
  - `CDATA`: Small data storage
  - `CBLKS`: Large memory blocks
  - `POOL`: Auto-managed literal pool for operands prefixed with `&`

- **Comprehensive Symbol Resolution**: Full symbol table management with absolute address calculation

- **Multiple Addressing Modes**: Supports all SIC/XE addressing modes:
  - Immediate (`#`)
  - Indirect (`@`)
  - Indexed (`,X`)
  - PC-relative and Base-relative addressing for Format 3
  - Extended (Format 4) addressing with modification records

- **Error Handling**: Robust error detection and reporting:
  - Unidentified block names
  - Undefined symbol references
  - Pool variable addressing errors
  - Invalid mnemonics

- **Object Code Generation**: Complete HTME record generation with modification records for relocatable code

- **Memory Visualization**: Interactive HTML-based memory map viewer (bonus feature)

## Installation

### Requirements
- Python 3.6+
- No external dependencies required

### Setup
```bash
git clone https://github.com/yourusername/modi-sicxe-assembler.git
cd modi-sicxe-assembler
```

## Usage

### Running the Assembler

```bash
python3 Modi-SICXE.py input_file.txt
```

Or with the default input file:
```bash
python3 Modi-SICXE.py in.txt
```

### Input File Format

Assembly source code in `in.txt`:
```assembly
COPY    START   0
        USE     DEFAULT
FIRST   LDA     #5
        +LDX    #300
        +JSUB   RDREC
        ...
        END     FIRST
```

## Output Files

### Generated Outputs

1. **intermediate.txt**: Pre-processing output with line-by-line location counters
   ```
   Location counter    Symbol    Instructions    Reference
   0000                FIRST     LDA             #5
   0003                          +LDX            #300
   ```

2. **symbTable.txt**: Symbol table with absolute addresses
   ```
   SYMBOL NAME    ADDRESS
   FIRST          000000
   LAST           000015
   ```

3. **blockTable.txt**: Memory block layout information
   ```
   BLOCK NAME    BLOCK NUMBER    ADDRESS    SIZE
   DEFAULT       0               000000     000020
   POOL          1               000020     000005
   ```

4. **PoolTable.txt**: Literal pool entries
   ```
   POOL NAME    ADDRESS    LENGTH    OBJECT CODE
   &X'10'       000020     01        10
   &C'EOF'      000021     03        454F46
   ```

5. **out_pass2.txt**: Object code for each instruction
   ```
   Location counter    Symbol    Instructions    Reference    Obj. code
   0000                FIRST     LDA             #5           000005
   0003                          +LDX            #300         040000300
   ```

6. **HTME.txt**: Executable object code in HTME format
   ```
   H.COPY....000000.000050
   T.000000.03.000005
   T.000003.04.040000300
   E.000000
   ```

7. **memory_viz.html**: Interactive memory visualization (requires browser to view)

### Error Handling

If an error occurs, an `error.txt` file is generated:
```
Error: Unidentified Symbol
PC: 000010
Line: 15
Detail: symbol 'UNDEFINED' is not defined
```

## Assembly Language Features

### Supported Instructions

All SIC/XE instructions are supported, including:
- **Arithmetic**: ADD, SUB, MUL, DIV, COMP
- **Floating-Point**: ADDF, SUBF, MULF, DIVF, COMPF
- **Load/Store**: LDA, LDX, STA, STX, LDCH, STCH, etc.
- **Control**: J, JEQ, JLT, JGT, JSUB, RSUB
- **Bit Operations**: AND, OR, SHIFTR, SHIFTL
- **I/O**: RD, WD, TD, TIX

### Directives

- `START [address]`: Program start
- `END [symbol]`: Program end
- `USE [block_name]`: Switch memory block
- `BASE symbol`: Set base register for addressing
- `NOBASE`: Clear base register
- `BYTE [value]`: Define byte data (C'...' or X'...')
- `WORD value`: Define 3-byte word
- `RESB length`: Reserve bytes
- `RESW count`: Reserve words

### Pool Literals

Operands prefixed with `&` are automatically stored in the POOL block:
```assembly
LDA     &X'10'      ; Pool entry: 10
LDCH    &C'A'       ; Pool entry: 41
```

## Technical Details

### Two-Pass Assembly Process

**Pass 1: Memory Allocation**
- Processes input line-by-line
- Calculates location counters for each block
- Identifies all symbols and their addresses
- Builds pool table for literal operands
- Validates block names and syntax

**Pass 2: Code Generation**
- Generates machine code for each instruction
- Resolves symbol addresses
- Applies addressing modes (PC-relative, Base-relative)
- Creates modification records for relocatable code
- Generates HTME records

### Addressing Mode Resolution (Format 3)

For Format 3 instructions, addresses are resolved using:
1. **Immediate addressing** (`#value`): Direct value embedding
2. **PC-relative** (default): Displacement = target - (current_address + 3)
3. **Base-relative** (if BASE set): Displacement = target - base_register_value

Displacement must fit in 12 bits for PC-relative or 12 bits for Base-relative.

### Format 4 Extended Addressing

Format 4 instructions (prefixed with `+`) use full 20-bit addressing:
```assembly
+LDA     SYMBOL      ; Extended addressing, creates modification record
```

## Example Program

```assembly
COPY    START   0
*       First Pass: compute locations
        USE     DEFAULT
FIRST   LDA     #5
        STA     ALPHA
        LDX     #300
        +JSUB   RDREC
        ...
*       Pool literals
        USE     DEFAULT
ALPHA   RESW    1
*       End with entry point
        END     FIRST
```

## Memory Layout Example

```
Address: 0 1 2 3 4 5 6 7 8 9 A B C D E F
000000:  17 10 00 48 65 6C 6C 6F 00 00 00 00 00 00 00 00
000010:  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
```

Interactive visualization available in `memory_viz.html`

## Team Members

- Kairm Magdy (231003685)
- Mustafa Aboelatta (231003175)  
- Seif Soliman (231016024)

## Submission Details

**Course**: CC410 - ECE3502 Systems Programming  
**Institution**: Arab Academy for Science & Technology & Maritime Transport  
**Deadline**: May 9, 2026

## Bonus Features

### Memory Visualization Interface
- Hexadecimal memory display with 16 columns per row
- Jump-to-address functionality
- Interactive tooltips showing memory addresses
- Color-coded memory usage (loaded vs. empty)
- Statistics panel with program size and usage metrics

## Error Types

The assembler detects and reports:

| Error | Description |
|-------|-------------|
| **Unidentified Block Name** | Reference to undefined block (valid: DEFAULT, DEFAULTB, CDATA, CBLKS) |
| **Unidentified Symbol** | Symbol used but not defined or out of scope |
| **POOLVAR error** | Pool operand cannot be addressed with PC or Base-relative addressing |
| **Addressing Error** | General addressing mode conflict or out-of-range displacement |
| **Unidentified Mnemonic** | Unknown instruction mnemonic |

## Architecture Details

### Instruction Formats

- **Format 1** (1 byte): HIO, SIO, TIO, FIX, FLOAT, NORM
- **Format 2** (2 bytes): Register-to-register operations (ADDR, SUBR, MULR, DIVR, etc.)
- **Format 3** (3 bytes): Standard instructions with addressing modes
- **Format 4** (4 bytes): Extended format with full 20-bit addressing

### Registers

Standard SIC/XE register set:
- A (0): Accumulator
- X (1): Index register
- L (2): Linkage register
- B (3): Base register
- S (4): General
- T (5): General
- F (6): Floating-point
- PC (8): Program counter
- SW (9): Status word

## Performance

- Processes typical programs (1000+ lines) in milliseconds
- Memory efficient with streaming output generation
- Supports programs up to 2^20 bytes (maximum addressing range)

## Known Limitations

- Pool operands must be addressable within PC or Base-relative range
- Symbol names limited to 8 characters (standard SIC/XE)
- Maximum 5 memory blocks per program
- Floating-point instructions validated but not executed

## Testing

Standard test cases included for:
- Multi-block program assembly
- Symbol resolution across blocks
- Pool literal generation and addressing
- Extended format (Format 4) code generation
- Error detection and reporting

## License

Academic project for coursework - Arab Academy for Science & Technology & Maritime Transport

## References

- SIC/XE Architecture Documentation
- System Programming course materials (CC410 - ECE3502)
- HTME Object Code Format Specification
