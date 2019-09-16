# from enum import Enum

class Op:
    UNDEFINED = 0
    ADD = 1
    MUL = 2
    SUB = 3
    DIV = 4
    LD = 5
    JUMP = 6
    ADDONE = 7
    ADDI = 8

Op_map = {0: "None", 1:"ADD", 2: "MUL", 3: "SUB", 4: "DIV", 5: "LD", 6: "JUMP"}
Reserv_map = {0: "Ars1", 1: "Ars2", 2: "Ars3", 3: "Ars4", 4: "Ars5", 5: "Ars6", 6: "Mrs1", 7: "Mrs2", 8: "Mrs3", 9: "Load1", 10: "Load2", 11: "Load3"}
FU_map = {0: "Add1", 1: "Add2", 2: "Add3", 3: "Mult1", 4: "Mult2", 5: "Load1", 6: "Load2"}
class ResStationName:
    Busy = 0
    Running = 1
    Ready = 2
    LastUpdate = 3
    Index = 4
    Listeners = 5
    Op = 6
    Vj = 7
    Vk = 8
    Qj = 9
    Qk = 10
    Waiting = 11
    Result = 12

class InstStatusName:
    Issue = 0
    ExecComp = 1
    WriteRes = 2

class LoadBuffer:
    Busy = 0
    Running = 1
    Ready = 2
    LastUpdate = 3
    Index = 4
    Listeners = 5
    Address = 6
    Result = 7
    # Listeners = 8 #注册的等待这个loadBuffer的ReserveStation

class ResultName:
    Source = 0
    State = 1
    Val = 2
    LastUpdate = 3
    Index = 4

class FUName:
    Remaining = 0
    Busy = 1
    Op = 2
    Qj = 3
    Qk = 4
    RU = 5
    Reserve = 6
    Result = 7
    LastUpdate = 8
    Index = 9


