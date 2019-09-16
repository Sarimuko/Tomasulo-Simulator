'''
用于将文本格式的NEL指令解析成列表格式
'''
from define import Op

def intToBin32(i):
    return (bin(((1 << 32) - 1) & i)[2:]).zfill(32)

def bin32ToInt(s):
    return int(s[1:], 2) - int(s[0]) * (1 << 31)


def parseLine(line):
    res = []
    line = line.split(",")
    if line[0] == "ADD":
        res.append(Op.ADD)
    elif line[0] == "MUL":
        res.append(Op.MUL)
    elif line[0] == "SUB":
        res.append(Op.SUB)
    elif line[0] == "DIV":
        res.append(Op.DIV)
    elif line[0] == "LD":
        res.append(Op.LD)
    elif line[0] == "JUMP":
        res.append(Op.JUMP)
    elif line[0] == "ADDONE":
        res.append(Op.ADDONE)
    elif line[0] == "ADDI":
        res.append(Op.ADDI)

    line = line[1:]
    for num in line:
        if num[0] == 'F':
            res.append(int(num[1:]) - 1)
        elif len(num) >= 3 and num[0:2] == "0x":
            t = int(num, 16)
            if t & (1 << 31) != 0:
                t = bin32ToInt(intToBin32(t))
    
            res.append(t)
        else:
            res.append(int(num))

    
    return res

def parse(filename):
    res = []
    insts = []
    f = open(filename)
    buffer = f.readline()
    while (buffer != ""):
        insts.append(buffer)
        inst = parseLine(buffer)
        if inst[0] == Op.ADDONE:
            res.append([Op.LD, 31, 1])
            res.append([Op.ADD, inst[1], inst[2], 31])
        elif inst[0] == Op.ADDI:
            res.append([Op.LD, 31, inst[3]])
            res.append([Op.ADD, inst[1], inst[2], 31])
        else:
            res.append(inst)
        buffer = f.readline()

    f.close()
    return insts, res

# print(parse('test.NEL'))