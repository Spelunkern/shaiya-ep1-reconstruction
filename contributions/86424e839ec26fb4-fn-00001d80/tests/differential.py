#!/usr/bin/env python3
"""Compare Windows x86 COFF built from source with the actual original instructions."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import random
import shutil
import struct
import subprocess
import sys

try:
    import unicorn
    from unicorn import Uc, UcError, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_HOOK_MEM_READ, UC_HOOK_MEM_INVALID
    from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP, UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_EFLAGS
except ImportError:
    raise SystemExit('Install tests/requirements.txt in a virtual environment; see docs/FIRST_BLOCK.md')

ROOT = Path(__file__).resolve().parents[3]
DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import reverse as reverse

BLOCK_ID = DIRECTORY.name
SYMBOL = '_ep1_86424e839ec26fb4_00001d80'
CODE = 0x00401D80
STOP = 0x00200000
DATA = 0x01000000
STACK = 0x70000000
SP = STACK + 0xF000
SAVED = {UC_X86_REG_EBX:0x12345678, UC_X86_REG_ESI:0x3456789A, UC_X86_REG_EDI:0x56789ABC, UC_X86_REG_EBP:0x789ABCDE}


def coff_text(path, wanted):
    """Load i386 COFF .text, applying only same-section REL32 relocations."""
    data = path.read_bytes()
    machine, nsections, _, symbol_pointer, symbol_count, optional_size, _ = struct.unpack_from('<HHIIIHH', data)
    assert machine == 0x14C and optional_size == 0, 'Expected an i386 COFF object'
    sections = []
    for i in range(nsections):
        off = 20 + i * 40
        name = data[off:off+8].split(b'\0')[0].decode()
        _, _, raw_size, raw_pointer, reloc_pointer, _, reloc_count, _, _ = struct.unpack_from('<IIIIIIHHI', data, off+8)
        sections.append((name, raw_size, raw_pointer, reloc_pointer, reloc_count))
    text_index = next(i+1 for i,s in enumerate(sections) if s[0] == '.text')
    _, size, pointer, reloc_pointer, reloc_count = sections[text_index-1]
    text = bytearray(data[pointer:pointer+size])
    strings = symbol_pointer + symbol_count * 18
    symbols = {}
    index = 0
    while index < symbol_count:
        off = symbol_pointer + index * 18
        name_bytes = data[off:off+8]
        if name_bytes[:4] == b'\0'*4:
            str_off = strings + struct.unpack_from('<I',name_bytes,4)[0]
            name = data[str_off:data.index(b'\0',str_off)].decode()
        else:
            name = name_bytes.split(b'\0')[0].decode()
        value, section, _, _, auxiliary = struct.unpack_from('<IhHBB',data,off+8)
        symbols[index] = (name,value,section)
        index += 1 + auxiliary
    for i in range(reloc_count):
        offset, symbol, kind = struct.unpack_from('<IIH',data,reloc_pointer+i*10)
        name, value, section = symbols[symbol]
        assert section == text_index and kind == 0x14, f'Unexpected dependency/relocation: {name}, section={section}, type={kind}'
        addend = struct.unpack_from('<i',text,offset)[0]
        struct.pack_into('<I',text,offset,(value + addend - offset - 4) & 0xFFFFFFFF)
    entry = next(value for name,value,section in symbols.values() if name == wanted and section == text_index)
    return bytes(text), entry


def run(code, entry, payload=b'\0\0', odd=False, guard=False, null=False, parameter=None, initial_eax=0):
    guest = Uc(UC_ARCH_X86, UC_MODE_32)
    guest.mem_map(CODE & ~4095,0x10000)
    guest.mem_write(CODE,code)
    guest.mem_map(STOP,4096)
    guest.mem_map(STACK,0x10000)
    data_size = max(4096, ((len(payload)+32+4095)//4096)*4096)
    if guard:
        data_size = max(4096, ((len(payload)+4095)//4096)*4096)
    guest.mem_map(DATA,data_size)
    guest.mem_write(DATA,b'\xa5'*data_size)
    pointer = DATA + (data_size-len(payload) if guard else 8+int(odd))
    guest.mem_write(pointer,payload)
    guest.mem_protect(DATA,data_size,UC_PROT_READ)
    argument = parameter if parameter is not None else (0 if null else pointer)
    guest.mem_write(SP,struct.pack('<II',STOP,argument))
    guest.reg_write(UC_X86_REG_ESP,SP)
    guest.reg_write(UC_X86_REG_EFLAGS,0x202)
    guest.reg_write(UC_X86_REG_EAX,initial_eax)
    guest.reg_write(UC_X86_REG_ECX,0xA1B2C3D4)
    guest.reg_write(UC_X86_REG_EDX,0xB2C3D4E5)
    for reg,value in SAVED.items():guest.reg_write(reg,value)
    reads = []
    faults = []
    def on_read(uc,access,address,size,value,user):
        if DATA <= address < DATA+data_size:
            reads.append((address-pointer,size))
    def on_fault(uc,access,address,size,value,user):
        faults.append((access,address,size))
        return False
    guest.hook_add(UC_HOOK_MEM_READ,on_read)
    guest.hook_add(UC_HOOK_MEM_INVALID,on_fault)
    error = None
    try:
        guest.emu_start(CODE+entry,STOP,timeout=1000000,count=1000000)
    except UcError as exc:
        error = exc.errno
    if error is None:
        assert guest.reg_read(UC_X86_REG_EIP) == STOP, 'Execution did not return (limit reached)'
        assert guest.reg_read(UC_X86_REG_ESP) == SP+4, 'Incorrect cdecl stack cleanup'
        assert bytes(guest.mem_read(SP+4,4)) == struct.pack('<I',argument), 'Argument changed'
        for reg,value in SAVED.items():
            assert guest.reg_read(reg) == value, 'Callee-saved register changed'
    assert bytes(guest.mem_read(pointer,len(payload))) == payload, 'Input memory changed'
    return dict(eax=guest.reg_read(UC_X86_REG_EAX), reads=reads, error=error, faults=faults)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'work/first-block-test')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True,exist_ok=True)
    clang = shutil.which('clang')
    assert clang, 'Install Clang (Ubuntu: sudo apt-get install clang)'
    assert unicorn.__version__ == '2.1.4', 'Use the pinned Unicorn version'
    block = reverse.choose_block(BLOCK_ID)
    binary = reverse.choose_binary(block['binary_id'])
    original_path = ROOT/binary['paths'][0]
    assert reverse.sha(original_path) == block['binary_sha256'], 'Wrong original binary'
    original = b''.join(reverse.mapped_bytes(original_path.read_bytes(),binary['pe'],a,z) for a,z in block['ranges'])
    assert hashlib.sha256(original).hexdigest() == block['body_sha256']
    assert block['ranges'] == [[0x1D80,0x1D96]], 'Unexpected function boundary'
    build_lines = [subprocess.check_output([clang,'--version'],text=True).strip()]
    randomizer = random.Random(0x1D80)
    units_cases = [[],[65],[0xFFFF],[0xD800,0xDC00],[65,0,66],list(range(1,65)),[0x1234]*4095]
    for _ in range(500):
        units_cases.append([randomizer.randrange(1,65536) for _ in range(randomizer.randrange(0,257))])
    comparisons = 0
    fault_comparisons = 0
    arithmetic_comparisons = 0
    results = []
    for optimization in ('-O0','-O2'):
        compiled = []
        for source,symbol,label in [(DIRECTORY/'src/function.c',SYMBOL,'function'),(DIRECTORY/'tests/arithmetic_probe.c','_test_finish_byte_delta','arithmetic')]:
            obj = out/(label+optimization+'.obj')
            command = [clang,'--target=i686-pc-windows-msvc','-std=c11','-ffreestanding','-fno-stack-protector','-Wall','-Wextra','-Werror',optimization,'-c',str(source),'-o',str(obj)]
            process = subprocess.run(command,capture_output=True,text=True)
            build_lines.extend([' '.join(command).replace(str(ROOT),'<repo>'),process.stdout,process.stderr])
            assert process.returncode == 0, process.stderr
            compiled.append(coff_text(obj,symbol))
        reconstructed, entry = compiled[0]
        for case_number,units in enumerate(units_cases):
            payload = struct.pack('<'+'H'*(len(units)+1),*units,0)
            first_zero = units.index(0) if 0 in units else len(units)
            for layout in ('aligned','unaligned','guard'):
                kwargs = dict(odd=layout=='unaligned',guard=layout=='guard')
                expected = run(original,0,payload,**kwargs)
                actual = run(reconstructed,entry,payload,**kwargs)
                assert expected['error'] is None and expected['eax'] == first_zero
                assert expected == actual, (optimization,case_number,layout,expected,actual)
                assert expected['reads'] == [(2*i,2) for i in range(first_zero+1)], 'Read past terminator or wrong width'
                comparisons += 1
        for name,kwargs in [('null',dict(null=True)),('no_terminator',dict(payload=b'\xff'*4096,guard=True))]:
            expected = run(original,0,**kwargs)
            actual = run(reconstructed,entry,**kwargs)
            assert expected['error'] is not None
            for field in ('error','faults','reads'):
                assert expected[field] == actual[field],(optimization,name,field,expected,actual)
            fault_comparisons += 1
        arithmetic, arithmetic_entry = compiled[1]
        deltas = [0,1,2,3,0x7FFFFFFC,0x7FFFFFFE,0x7FFFFFFF,0x80000000,0x80000001,0xFFFFFFFE,0xFFFFFFFF]
        deltas += [randomizer.randrange(0x100000000) for _ in range(500)]
        for delta in deltas:
            # Enter the original SUB/SAR/DEC/RET tail with a synthetic post-loop EAX.
            expected = run(original,14,parameter=DATA,initial_eax=(DATA+delta)&0xFFFFFFFF)
            actual = run(arithmetic,arithmetic_entry,parameter=delta)
            assert expected['error'] is None and actual['error'] is None and expected['eax'] == actual['eax'],(optimization,hex(delta),expected,actual)
            assert not expected['reads'] and not actual['reads']
            arithmetic_comparisons += 1
        results.append(dict(optimization=optimization,source_text_sha256=hashlib.sha256(reconstructed).hexdigest(),code_bytes=len(reconstructed),symbol_offset=entry))
    (out/'build.log').write_text('\n'.join(build_lines)+'\nPASS Windows x86 COFF builds, no external relocations\n')
    summary = dict(block_id=BLOCK_ID,original_sha256=block['binary_sha256'],body_sha256=block['body_sha256'],
                   target='i686-pc-windows-msvc',unicorn=unicorn.__version__,host=platform.platform(),
                   scan_comparisons=comparisons,fault_comparisons=fault_comparisons,arithmetic_comparisons=arithmetic_comparisons,builds=results,
                   assertions=['EAX return','cdecl ESP and argument preservation','EBX/ESI/EDI/EBP preservation',
                               'input unchanged','exact input read addresses and widths','null and unterminated faults','synthetic arithmetic overflow boundaries'],
                   limitations=['CPU emulation, not whole CONFIG.exe on Windows','No compiler/linker identity claim',
                                'Huge strings modeled only through the arithmetic tail, not allocated or fully scanned',
                                'No MMIO, concurrent mutation, or alignment-check exception comparison'])
    (out/'comparison.json').write_text(json.dumps(summary,indent=2)+'\n')
    message=f'PASS {comparisons} scan + {fault_comparisons} fault + {arithmetic_comparisons} arithmetic comparisons against original x86 instructions'
    (out/'comparison.log').write_text(message+'\n'+json.dumps(summary,indent=2)+'\n')
    print(message)
    print(out)

if __name__ == '__main__':
    main()
