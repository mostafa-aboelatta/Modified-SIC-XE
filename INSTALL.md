# Installation & Quick Start Guide

## System Requirements

- **Python**: 3.6 or higher
- **OS**: Windows, macOS, or Linux
- **Disk Space**: < 1 MB
- **Memory**: Minimal (< 50 MB)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/modi-sicxe-assembler.git
cd modi-sicxe-assembler
```

### 2. Verify Python Installation

```bash
python3 --version
```

Expected output: `Python 3.6.x` or higher

### 3. No Dependencies Required

This project uses only Python standard library:
- `sys`: Command-line arguments
- `re`: Regular expressions for parsing
- `pathlib`: File path handling

No external packages need to be installed!

## Quick Start

### Basic Usage

1. **Prepare your assembly file** as `in.txt`:

```assembly
COPY    START   0
        USE     DEFAULT
FIRST   LDA     #5
        STA     ALPHA
        END     FIRST
ALPHA   RESW    1
```

2. **Run the assembler**:

```bash
python3 Modi-SICXE.py in.txt
```

3. **Check output files**:

- `symbTable.txt` - Symbol definitions
- `HTME.txt` - Executable object code
- `memory_viz.html` - Visual memory layout

### Output Files Generated

After successful assembly:

```
✓ intermediate.txt    - Pass 1 intermediate output
✓ symbTable.txt       - Symbol table with addresses
✓ blockTable.txt      - Memory block layout
✓ PoolTable.txt       - Literal pool entries
✓ out_pass2.txt       - Pass 2 machine code
✓ HTME.txt            - Object code in HTME format
✓ memory_viz.html     - Interactive memory viewer
```

### Viewing Results

#### Text Output Files
Open in any text editor:
```bash
# On Windows
notepad symbTable.txt

# On macOS/Linux
cat symbTable.txt
```

#### Memory Visualization
Open in web browser:
```bash
# On Windows
start memory_viz.html

# On macOS
open memory_viz.html

# On Linux
firefox memory_viz.html
```

## Example Programs

### Minimal Program

**in.txt**:
```assembly
HELLO   START   0
        LDA     #10
        END     HELLO
```

**Run**:
```bash
python3 Modi-SICXE.py in.txt
```

**Output** (`HTME.txt`):
```
H.HELLO.000000.000003
T.000000.03.000A00
E.000000
```

### Program with Multiple Blocks

**in.txt**:
```assembly
PROG    START   0
        USE     DEFAULT
START   LDA     #5
        +JSUB   COMPUTE
        USE     CDATA
DATA    RESW    1
        USE     DEFAULT
        END     START
```

### Program with Pool Literals

**in.txt**:
```assembly
PROG    START   0
        LDA     &X'0A'
        LDCH    &C'A'
        END     PROG
```

The assembler automatically manages the POOL block for `&` operands.

## Troubleshooting

### Python Not Found

**Error**: `python3: command not found`

**Solution**:
- Install Python from [python.org](https://www.python.org)
- Or use `python` instead of `python3` (Windows)
- Or add Python to PATH

### File Not Found

**Error**: `FileNotFoundError: [Errno 2] No such file or directory: 'in.txt'`

**Solution**:
- Create `in.txt` in the same directory as Modi-SICXE.py
- Or specify the input file path:
  ```bash
  python3 Modi-SICXE.py /path/to/my/assembly.txt
  ```

### Assembly Errors

**Error**: `Unidentified Symbol` or other errors

**Solution**:
- Check `error.txt` for details
- Verify symbol is defined before use
- Check syntax of directives
- Ensure block names are valid (DEFAULT, DEFAULTB, CDATA, CBLKS)

**error.txt example**:
```
Error: Unidentified Symbol
PC: 000010
Line: line 15
Detail: symbol 'UNDEFINED' is not defined
```

### Empty Output Files

**Problem**: Output files created but empty

**Solution**:
- Check for errors in `error.txt`
- Verify input file has valid assembly
- Ensure in.txt is in the same directory

## Development Setup

### For Contributors

1. **Fork the repository**

2. **Clone your fork**:
```bash
git clone https://github.com/yourname/modi-sicxe-assembler.git
cd modi-sicxe-assembler
```

3. **Create feature branch**:
```bash
git checkout -b feature/my-feature
```

4. **Make changes** to Modi-SICXE.py

5. **Test changes**:
```bash
python3 Modi-SICXE.py in.txt
# Verify output files
```

6. **Commit and push**:
```bash
git add .
git commit -m "Add: description of changes"
git push origin feature/my-feature
```

7. **Create Pull Request** on GitHub

## Testing Your Installation

### Test 1: Basic Assembly

**Create test.txt**:
```assembly
TEST    START   0
        LDA     #123
        END     TEST
```

**Run**:
```bash
python3 Modi-SICXE.py test.txt
```

**Verify**: Check that HTME.txt contains object code

### Test 2: Error Handling

**Create error_test.txt**:
```assembly
BAD     START   0
        LDA     UNDEFINED
        END     BAD
```

**Run**:
```bash
python3 Modi-SICXE.py error_test.txt
```

**Verify**: error.txt should be created with error details

### Test 3: Multi-Block Program

**Create blocks.txt**:
```assembly
PROG    START   0
        USE     DEFAULT
        LDA     #1
        USE     CDATA
VALUE   RESW    1
        USE     DEFAULT
        END     PROG
```

**Run**:
```bash
python3 Modi-SICXE.py blocks.txt
```

**Verify**: blockTable.txt shows multiple blocks

## Command Reference

### Basic Syntax

```bash
python3 Modi-SICXE.py [input_file]
```

### Arguments

- `input_file` (optional): Path to assembly source file
  - Default: `in.txt` (current directory)
  - Can be absolute or relative path

### Examples

```bash
# Use default input file
python3 Modi-SICXE.py

# Use specific input file
python3 Modi-SICXE.py my_program.txt

# Use file in different directory
python3 Modi-SICXE.py /path/to/assembly/file.asm

# On Windows with relative path
python3 Modi-SICXE.py .\programs\test.txt
```

## File Locations

### Input
- Default: `in.txt` (current working directory)
- Custom: Any path specified as argument

### Outputs
- All generated files go to current working directory:
  - `intermediate.txt`
  - `symbTable.txt`
  - `blockTable.txt`
  - `PoolTable.txt`
  - `out_pass2.txt`
  - `HTME.txt`
  - `memory_viz.html`
  - `error.txt` (if errors occur)

## Performance Tips

- **Large programs**: May take a few seconds for 10,000+ lines
- **Memory usage**: Proportional to number of symbols
- **File I/O**: Sequential reading/writing optimized

## Updating Python

### Windows
```bash
# Check for updates
python3 -m pip install --upgrade pip
```

### macOS
```bash
brew upgrade python3
```

### Linux
```bash
sudo apt update && sudo apt upgrade python3
```

## Next Steps

1. **Read the README** for full feature documentation
2. **Check examples** in PROJECT_STRUCTURE.md
3. **Review supported instructions** in README.md
4. **Create your own programs** using SIC/XE syntax

## Getting Help

- **Questions**: Check README.md and PROJECT_STRUCTURE.md
- **Bugs**: Create an issue on GitHub with assembly code
- **Features**: Submit feature request with use case
- **Documentation**: Suggest improvements

## Additional Resources

- **Project Structure**: See `PROJECT_STRUCTURE.md`
- **Contributing**: See `CONTRIBUTING.md`
- **Full Documentation**: See `README.md`

## License

Academic project for educational purposes.

---

**Happy assembling!** 🚀

For more information, see [README.md](README.md)
