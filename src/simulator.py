'''
定义模拟器状态和操作
'''
from define import Op, ResStationName, InstStatusName, LoadBuffer, FUName, ResultName, Op_map, Reserv_map, FU_map
import copy

class Simulator:
    def __init__(self):
        self.instStatus = []
        self.loadBuffer = [[False, False, False, -1, -1, [], 0, -1], [False, False, False, -1, -1, [], 0, -1], [False, False, False, -1, -1, [], 0, -1]]
        self.reservStation = [[False, False, False, -1, -1, [], 0, 0, 0, 0, 0, 0, -1] for i in range(9)] #保留站定义
        self.reservStation.extend(self.loadBuffer)
        # print(len(self.reservStation))
        
        self.FU = [[0, False, 0, 0, 0, 0, 0, 0, -1, -1] for i in range(7)] # 功能部件定义，记录该功能部件还需要多久完成计算，以及标记结果寄存器位置，和对应的保留站编号，和计算结果
        self.resultStatus = [[0, 0, 0, -1, -1] for i in range(32)] # 标记结果寄存器，标记自己的来源FU，状态，和监听该寄存器的保留站，和寄存器内容
        self.reg = [[0, 0, 0, -1, -1] for i in range(32)]


        self.reservAvail = [[], range(6), range(6, 9), range(6), range(6, 9), range(9, 12), range(6)] #标记每个OP可用的保留站编号
        self.FUAvail = [[], range(3), range(3, 5), range(3), range(3, 5), range(5, 7), range(3)] #标记可用的FU编号
        self.runSpan = [0, 3, 4, 3, 4, 3, 1]

        self.eip = 0 # 执行位置
        self.inst = None
        self.instrList = None # 待执行的指令列表

        self.stop = False
        self.clock = 0
        self.next = self.eip
        self.table = None
        self.pre = False #是否处于前瞻执行模式


        # 用于计算实际结果的函数
        self.functions = [lambda x, y: 0, lambda x, y: x + y, lambda x, y: x * y, lambda x, y: x - y, lambda x, y: int(x / y), lambda x, y: y, lambda x, y: x + y]

    def runInstr(self, instrList, inst):
        self.inst = inst
        self.instrList = instrList
        self.table = [[-1 for i in range(3)] for j in range(len(instrList))]
        

    def printTable(self):
        headers = ["Inst", "Issue", "Exec Complete", "Write Back"]
        for header in headers:
            print(header + '\t\t\t\t', end = '')
        print('\n')
        for i, r in enumerate(self.table):
            print(self.inst[i][:-1] + '\t\t\t\t' + str(r[InstStatusName.Issue]) + '\t\t\t\t' + str(r[InstStatusName.ExecComp]) + '\t\t\t\t' + str(r[InstStatusName.WriteRes]))
        

    def print_reserve(self):
        headers = ["", "Busy", "Running", "Op", "Vj", "Vk", "Qj", "Qk", "Waiting", "Listeners"]
        for header in headers:
            print(header + '\t', end = '')
        print('\n')
        for i, r in enumerate(self.reservStation):
            if i < len(self.reservStation) - len(self.loadBuffer):
                print(Reserv_map[i] + '\t' + str(r[ResStationName.Busy]) + '\t' + str(r[ResStationName.Running]) + '\t' + Op_map[r[ResStationName.Op]] + '\t' + str(r[ResStationName.Vj]) + '\t' + str(r[ResStationName.Vk]) + '\t' + str(r[ResStationName.Qj]) + '\t' + str(r[ResStationName.Qk]) + '\t' + str(r[ResStationName.Waiting]) + '\t' + str(r[ResStationName.Listeners]))
                
        print('\n')
        
    def print_loadBuffer(self):
        headers = ["", "Busy", "Address"]
        for header in headers:
            print(header + '\t', end = '')
        print('\n')
        for i, r in enumerate(self.loadBuffer):
            print(str(i) + '\t' + str(r[LoadBuffer.Busy]) + '\t' + str(r[LoadBuffer.Address]))

        print("\n")

    def print_FU(self):
        headers = ["", "Remaining"]
        pass
    


    def print_result(self):
        for j in range(4):
            for i in range(j * 8, (j + 1) * 8):
                print(str(i + 1) + '\t', end = "")
            print("\n")
            for i in range(j * 8, (j + 1) * 8):
                if self.resultStatus[i][ResultName.State] == 1:
                    print(Reserv_map[self.resultStatus[i][ResultName.Source]], end = " ")
                print(str(self.resultStatus[i][ResultName.Val]) + "\t", end = "")
            print('\n')

    def tick(self): #每次时钟信号发生
        print("CLOCK: " + str(self.clock))
        self.print_reserve()
        self.print_loadBuffer()
        self.print_result()
        # print(self.FU)
        # print(self.eip)
        self.clock += 1


        # print(str(self.clock) + ' ' + str(self.eip) + ' ' + str(self.next))



        # 首先进行功能部件计算，检测是否完成计算
        for i in range(len(self.FU)):
            # if self.FU[i][FUName.Op] == Op.JUMP:
            #     print(self.FU[i])
            if self.FU[i][FUName.Remaining] > 0:
                self.FU[i][FUName.Remaining] -= 1
                if self.FU[i][FUName.Remaining] == 0:
                    print("exec complete: " + str(self.clock))
                    if self.table[self.FU[i][FUName.Index]][InstStatusName.ExecComp] == -1:
                        self.table[self.FU[i][FUName.Index]][InstStatusName.ExecComp] = self.clock
            elif self.FU[i][FUName.Remaining] == 0 and self.FU[i][FUName.Busy]: # 进行写回
                self.FU[i][FUName.Busy] = False
                if self.table[self.FU[i][FUName.Index]][InstStatusName.WriteRes] == -1:
                    self.table[self.FU[i][FUName.Index]][InstStatusName.WriteRes] = self.clock
                print("write back: " + str(self.clock))
                stations = []
                if self.FU[i][FUName.Op] == Op.LD: #如果是load命令的话，那么需要写回的是loadBuffer
                    reserve = self.reservStation[self.FU[i][FUName.Reserve]]
                    reserve[LoadBuffer.Busy] = False
                    stations = reserve[LoadBuffer.Listeners]
                    reserve[LoadBuffer.Running] = False
        
                    if self.FU[i][FUName.RU][ResultName.Source] == self.FU[i][FUName.Reserve]:
                        self.FU[i][FUName.RU][ResultName.Val] = self.FU[i][FUName.Result]
                        self.FU[i][FUName.RU][ResultName.State] = 0
                    if self.FU[i][FUName.RU] in self.reg: #如果位于buffer中，那么修改一遍result status
                        result = self.resultStatus[self.reg.index(self.FU[i][FUName.RU])]
                        if result[ResultName.Source] == self.FU[i][FUName.Reserve]:
                            print(self.FU[i])
                            result[ResultName.Val] = self.FU[i][FUName.Result]
                            result[ResultName.State] = 0

                    reserve[LoadBuffer.Listeners] = []

                elif not self.FU[i][FUName.Op] == Op.JUMP and self.FU[i][FUName.RU] != -1: #如果有写回寄存器
                    # 写回寄存器
                    result = self.FU[i][FUName.RU]
                    reserve = self.reservStation[self.FU[i][FUName.Reserve]]
                    reserve[ResStationName.Busy] = False
                    reserve[ResStationName.Running] = False
                    
                    if result[ResultName.Source] == self.FU[i][FUName.Reserve]:
                        print(self.FU[i])
                        result[ResultName.Val] = self.FU[i][FUName.Result]
                        result[ResultName.State] = 0
                    if result in self.reg: #如果位于buffer中，那么修改一遍result status
                        result = self.resultStatus[self.reg.index(result)]
                        if result[ResultName.Source] == self.FU[i][FUName.Reserve]:
                            print(self.FU[i])
                            result[ResultName.Val] = self.FU[i][FUName.Result]
                            result[ResultName.State] = 0
                    
                    stations = self.reservStation[self.FU[i][FUName.Reserve]][ResStationName.Listeners] #通知所有监听这个结果的暂存站

                for station in stations:
                    for j in range(ResStationName.Vj, ResStationName.Vk + 1):
                        if self.reservStation[station][j] == self.FU[i][FUName.Reserve] + 1: #正在等待这个结果
                            if self.reservStation[station][ResStationName.Op] == Op.JUMP:
                                self.reservStation[station][j] = self.FU[i][FUName.RU][ResultName.Val]
                            else:
                                self.reservStation[station][j] = 0 # 已经接收到结果
                                self.reservStation[station][j + 2] = self.FU[i][FUName.Result]
                            self.reservStation[station][ResStationName.Waiting] -= 1
                # print(self.FU[i][FUName.Op])
                if self.FU[i][FUName.Op] == Op.JUMP: # 如果是跳转指令，直接跳转
                    reserv = self.reservStation[self.FU[i][FUName.Reserve]]
                    if reserv[ResStationName.Vj] == reserv[ResStationName.Vk]:
                        print("jump: ")
                        # print(self.FU[i])
                        print(self.reservStation[self.FU[i][FUName.Reserve]])
                        print(self.FU[i][FUName.Result])
                        self.eip = self.FU[i][FUName.Result]
                        self.stop = False
                        self.resultStatus = self.reg
                        self.pre = False

                    else:
                        print("not jump: ")
                        self.stop = False
                        self.pre = False
                        # print(self.FU[i])
                        for fu in self.FU:
                            if fu[FUName.RU] in self.reg:
                                fu[FUName.RU] = self.resultStatus[self.reg.index(fu[FUName.RU])]
                        print(self.reservStation[self.FU[i][FUName.Reserve]])


                self.FU[i][FUName.Busy] = False
                reserve = self.reservStation[self.FU[i][FUName.Reserve]]

                reserve[ResStationName.Busy] = False
                reserve[ResStationName.Running] = False
                reserve[ResStationName.Ready] = False
                
                # TODO: clear reservation station

        if self.eip < len(self.instrList) and not self.stop:
            # print(self.eip)
            res = self.readInst(self.instrList[self.eip][0], self.instrList[self.eip][1:])
            
            if res:
                if self.table[self.eip][InstStatusName.Issue] == -1:
                    self.table[self.eip][InstStatusName.Issue] = self.clock
                self.next = self.eip + 1
                print("issue: " + str(self.clock) + ": " + str(self.eip))
            else:
                self.next = self.eip

        # 遍历所有的保留站，看有没有可以就绪的
        for i in range(len(self.reservStation) - len(self.loadBuffer)):
            reserve = self.reservStation[i]
            if reserve[ResStationName.Waiting] == 0 and reserve[ResStationName.Running] == False and reserve[ResStationName.Busy] == True:
                op = reserve[ResStationName.Op]
                # print(op)
                # print(i)
                FUs = self.FUAvail[op]

                for fu in FUs:
                    if self.FU[fu][FUName.Remaining] == 0 and not self.FU[fu][FUName.Busy]:
                        self.FU[fu][FUName.Busy] = True
                        self.FU[fu][FUName.Remaining] = self.runSpan[op]

                        if reserve[ResStationName.Ready]:
                            self.FU[fu][FUName.Remaining] -= 1
                            # reserve[ResStationName.Ready] = False
                        # else:
                        reserve[ResStationName.Ready] = True

                        self.FU[fu][FUName.Reserve] = i
                        self.FU[fu][FUName.Qj] = self.reservStation[i][ResStationName.Qj]
                        self.FU[fu][FUName.Qk] = self.reservStation[i][ResStationName.Qk]
                        self.FU[fu][FUName.Op] = op
                        self.FU[fu][FUName.RU] = self.reservStation[i][ResStationName.Result]

                        self.FU[fu][FUName.Index] = self.reservStation[i][ResStationName.Index]
                        self.FU[fu][FUName.LastUpdate] = self.eip

                        if op == Op.DIV and self.FU[fu][FUName.Qk] == 0: #检测除法正确性
                            # print(self.FU[fu])
                            self.FU[fu][FUName.Remaining] = 1
                            self.FU[fu][FUName.Result] = self.FU[fu][FUName.Qj]
                        else:
                            self.FU[fu][FUName.Result] = self.functions[op](self.FU[fu][FUName.Qj], self.FU[fu][FUName.Qk])
                        reserve[ResStationName.Running] = True

                        print(self.FU[fu])

                        break
                reserve[ResStationName.Ready] = True

        # 扫描所有的LoadBuffer
        for i in range(len(self.loadBuffer)):
            loadBuffer = self.loadBuffer[i]
            op = Op.LD
            FUs = self.FUAvail[op]
            if loadBuffer[LoadBuffer.Busy] == True and loadBuffer[LoadBuffer.Running] == False:
                for fu in FUs:
                    if self.FU[fu][FUName.Remaining] == 0 and self.FU[fu][FUName.Busy] == False:
                        loadBuffer[LoadBuffer.Running] = True
                        self.FU[fu][FUName.Busy] = True
                        self.FU[fu][FUName.Remaining] = self.runSpan[op]

                        if loadBuffer[ResStationName.Ready]:
                            self.FU[fu][FUName.Remaining] -= 1
                        loadBuffer[ResStationName.Ready] = True

                        self.FU[fu][FUName.Reserve] = i + len(self.reservStation) - len(self.loadBuffer)
                        self.FU[fu][FUName.Qj] = self.loadBuffer[i][LoadBuffer.Address]
                        self.FU[fu][FUName.Qk] = self.loadBuffer[i][LoadBuffer.Address]

                        self.FU[fu][FUName.Result] = self.functions[op](self.FU[fu][FUName.Qj], self.FU[fu][FUName.Qk])
                        self.FU[fu][FUName.Op] = op

                        self.FU[fu][FUName.Index] = self.loadBuffer[i][LoadBuffer.Index]
                        self.FU[fu][FUName.LastUpdate] = self.eip

                        self.FU[fu][FUName.RU] = self.loadBuffer[i][LoadBuffer.Result]
                        print(self.FU[fu])

                        break
                loadBuffer[ResStationName.Ready] = True

        self.eip = self.next
 
                


    def readInst(self, index, args): #尝试issue
        if  index == Op.ADD:
            return self.ADD(args[0], args[1], args[2])
        elif index == Op.SUB:
            return self.SUB(args[0], args[1], args[2])
        elif index == Op.MUL:
            return self.MUL(args[0], args[1], args[2])
        elif index == Op.DIV:
            return self.DIV(args[0], args[1], args[2])
        elif index == Op.JUMP:
            return self.JUMP(args[0], args[1], args[2])
        elif index == Op.LD:
            return self.LD(args[0], args[1])

    def ADD(self, R1, R2, R3): #返回是否issue成功
        index = Op.ADD
        reservs = self.reservAvail[index]
        # FUs = self.FUAvail[index]
        # if self.resultStatus[R1][ResultName.Source] not in self.reservAvail[Op.LD]: # 结果寄存器被占用
        #     return False

        for r in reservs:
            if self.reservStation[r][ResStationName.Busy] == False:
                self.reservStation[r][ResStationName.Busy] = True
                if self.resultStatus[R2][ResultName.State] == 0:
                    self.reservStation[r][ResStationName.Qj] = self.resultStatus[R2][ResultName.Val]
                else:
                    # if self.resultStatus[R2][ResultName.Source] in self.reservAvail[Op.LD]:
                    self.reservStation[r][ResStationName.Vj] = self.resultStatus[R2][ResultName.Source] + 1
                    if self.resultStatus[R2][ResultName.Source] in self.reservAvail[Op.LD]: #如果等待的是LD的结果，监听的是LoadBuffer
                        self.reservStation[self.resultStatus[R2][ResultName.Source]][LoadBuffer.Listeners].append(r)
                    else:
                        self.reservStation[self.resultStatus[R2][ResultName.Source]][ResStationName.Listeners].append(r)
                    self.reservStation[r][ResStationName.Waiting] += 1
                
                if self.resultStatus[R3][ResultName.State] == 0:
                    self.reservStation[r][ResStationName.Qk] = self.resultStatus[R3][ResultName.Val]
                else:
                    self.reservStation[r][ResStationName.Vk] = self.resultStatus[R3][ResultName.Source] + 1

                    if self.resultStatus[R3][ResultName.Source] in self.reservAvail[Op.LD]: #如果等待的是LD的结果，监听的是LoadBuffer
                        self.reservStation[self.resultStatus[R3][ResultName.Source]][LoadBuffer.Listeners].append(r)
                    else:
                        self.reservStation[self.resultStatus[R3][ResultName.Source]][ResStationName.Listeners].append(r)

                    self.reservStation[r][ResStationName.Waiting] += 1

                self.resultStatus[R1][ResultName.Source] = r
                self.resultStatus[R1][ResultName.State] = 1 # 正在等待
                self.reservStation[self.resultStatus[R1][ResultName.Source]][ResStationName.Listeners] = []

                self.reservStation[r][ResStationName.Index] = self.eip
                self.reservStation[r][ResStationName.LastUpdate] = self.clock

                self.reservStation[r][ResStationName.Result] = self.resultStatus[R1]
                self.reservStation[r][ResStationName.Op] = index
                return True
        
        return False




    def SUB(self, R1, R2, R3):
        index = Op.SUB
        reservs = self.reservAvail[index]
        # FUs = self.FUAvail[index]
        # if self.resultStatus[R1][ResultName.Source] not in self.reservAvail[Op.LD]: # 结果寄存器被占用
        #     return False

        for r in reservs:
            if self.reservStation[r][ResStationName.Busy] == False:
                self.reservStation[r][ResStationName.Busy] = True
                if self.resultStatus[R2][ResultName.State] == 0:
                    
                    self.reservStation[r][ResStationName.Qj] = self.resultStatus[R2][ResultName.Val]
                else:
                    self.reservStation[r][ResStationName.Vj] = self.resultStatus[R2][ResultName.Source] + 1

                    if self.resultStatus[R2][ResultName.Source] in self.reservAvail[Op.LD]: #如果等待的是LD的结果，监听的是LoadBuffer
                        self.reservStation[self.resultStatus[R2][ResultName.Source]][LoadBuffer.Listeners].append(r)
                    else:
                        self.reservStation[self.resultStatus[R2][ResultName.Source]][ResStationName.Listeners].append(r)

                    self.reservStation[r][ResStationName.Waiting] += 1
                
                if self.resultStatus[R3][ResultName.State] == 0:
                    self.reservStation[r][ResStationName.Qk] = self.resultStatus[R3][ResultName.Val]
                else:
                    self.reservStation[r][ResStationName.Vk] = self.resultStatus[R3][ResultName.Source] + 1

                    if self.resultStatus[R3][ResultName.Source] in self.reservAvail[Op.LD]: #如果等待的是LD的结果，监听的是LoadBuffer
                        self.reservStation[self.resultStatus[R3][ResultName.Source]][LoadBuffer.Listeners].append(r)
                    else:
                        self.reservStation[self.resultStatus[R3][ResultName.Source]][ResStationName.Listeners].append(r)

                    self.reservStation[r][ResStationName.Waiting] += 1

                self.resultStatus[R1][ResultName.Source] = r
                self.resultStatus[R1][ResultName.State] = 1 # 正在等待
                self.reservStation[self.resultStatus[R1][ResultName.Source]][ResStationName.Listeners] = []

                self.reservStation[r][ResStationName.Index] = self.eip
                self.reservStation[r][ResStationName.LastUpdate] = self.clock

                self.reservStation[r][ResStationName.Result] = self.resultStatus[R1]
                self.reservStation[r][ResStationName.Op] = index
                return True
        
        return False

    def MUL(self, R1, R2, R3):
        index = Op.MUL
        reservs = self.reservAvail[index]
        # FUs = self.FUAvail[index]
        # if self.resultStatus[R1][ResultName.Source] not in self.reservAvail[Op.LD]: # 结果寄存器被占用
        #     return False

        for r in reservs:
            if self.reservStation[r][ResStationName.Busy] == False:
                self.reservStation[r][ResStationName.Busy] = True
                if self.resultStatus[R2][ResultName.State] == 0:
                    self.reservStation[r][ResStationName.Qj] = self.resultStatus[R2][ResultName.Val]
                else:
                    self.reservStation[r][ResStationName.Vj] = self.resultStatus[R2][ResultName.Source] + 1

                    if self.resultStatus[R2][ResultName.Source] in self.reservAvail[Op.LD]: #如果等待的是LD的结果，监听的是LoadBuffer
                        self.reservStation[self.resultStatus[R2][ResultName.Source]][LoadBuffer.Listeners].append(r)
                    else:
                        self.reservStation[self.resultStatus[R2][ResultName.Source]][ResStationName.Listeners].append(r)

                    self.reservStation[r][ResStationName.Waiting] += 1
                
                if self.resultStatus[R3][ResultName.State] == 0:
                    self.reservStation[r][ResStationName.Qk] = self.resultStatus[R3][ResultName.Val]
                else:
                    self.reservStation[r][ResStationName.Vk] = self.resultStatus[R3][ResultName.Source] + 1

                    if self.resultStatus[R3][ResultName.Source] in self.reservAvail[Op.LD]: #如果等待的是LD的结果，监听的是LoadBuffer
                        self.reservStation[self.resultStatus[R3][ResultName.Source]][LoadBuffer.Listeners].append(r)
                    else:
                        self.reservStation[self.resultStatus[R3][ResultName.Source]][ResStationName.Listeners].append(r)

                    self.reservStation[r][ResStationName.Waiting] += 1

                self.resultStatus[R1][ResultName.Source] = r
                self.resultStatus[R1][ResultName.State] = 1 # 正在等待
                self.reservStation[self.resultStatus[R1][ResultName.Source]][ResStationName.Listeners] = []

                self.reservStation[r][ResStationName.Index] = self.eip
                self.reservStation[r][ResStationName.LastUpdate] = self.clock

                self.reservStation[r][ResStationName.Result] = self.resultStatus[R1]
                self.reservStation[r][ResStationName.Op] = index
                return True
        
        return False

    def DIV(self, R1, R2, R3):
        index = Op.DIV
        reservs = self.reservAvail[index]
        # FUs = self.FUAvail[index]
        # if self.resultStatus[R1][ResultName.Source] not in self.reservAvail[Op.LD]: # 结果寄存器被占用，并且不是被LD占用的
        #     return False

        for r in reservs:
            if self.reservStation[r][ResStationName.Busy] == False:
                self.reservStation[r][ResStationName.Busy] = True
                if self.resultStatus[R2][ResultName.State] == 0:
                    self.reservStation[r][ResStationName.Qj] = self.resultStatus[R2][ResultName.Val]
                else:
                    self.reservStation[r][ResStationName.Vj] = self.resultStatus[R2][ResultName.Source] + 1

                    if self.resultStatus[R2][ResultName.Source] in self.reservAvail[Op.LD]: #如果等待的是LD的结果，监听的是LoadBuffer
                        self.reservStation[self.resultStatus[R2][ResultName.Source]][LoadBuffer.Listeners].append(r)
                    else:
                        self.reservStation[self.resultStatus[R2][ResultName.Source]][ResStationName.Listeners].append(r)

                    self.reservStation[r][ResStationName.Waiting] += 1
                
                if self.resultStatus[R3][ResultName.State] == 0:
                    self.reservStation[r][ResStationName.Qk] = self.resultStatus[R3][ResultName.Val]
                else:
                    self.reservStation[r][ResStationName.Vk] = self.resultStatus[R3][ResultName.Source] + 1

                    if self.resultStatus[R3][ResultName.Source] in self.reservAvail[Op.LD]: #如果等待的是LD的结果，监听的是LoadBuffer
                        self.reservStation[self.resultStatus[R3][ResultName.Source]][LoadBuffer.Listeners].append(r)
                    else:
                        self.reservStation[self.resultStatus[R3][ResultName.Source]][ResStationName.Listeners].append(r)

                    self.reservStation[r][ResStationName.Waiting] += 1

                self.resultStatus[R1][ResultName.Source] = r
                self.resultStatus[R1][ResultName.State] = 1 # 正在等待
                self.reservStation[self.resultStatus[R1][ResultName.Source]][ResStationName.Listeners] = []

                self.reservStation[r][ResStationName.Index] = self.eip
                self.reservStation[r][ResStationName.LastUpdate] = self.clock

                self.reservStation[r][ResStationName.Result] = self.resultStatus[R1]
                self.reservStation[r][ResStationName.Op] = index
                return True
        
        return False

    def LD(self, R1, I):
        # print("ld")
        index = Op.LD
        reservs = self.reservAvail[index]

        # print('ld')
        # if self.resultStatus[R1][ResultName.State] == 1 and self.resultStatus[R1][ResultName.Source] not in self.reservAvail[Op.LD]: # 结果寄存器被占用
        #     return False
        # print('ld result 1')
        for r in reservs:
            # print(r)
            # print(len(self.reservStation))
            if self.reservStation[r][LoadBuffer.Busy] == False:
                self.reservStation[r][LoadBuffer.Busy] = True

                self.reservStation[r][LoadBuffer.Address] = I

                # print(self.resultStatus)
                self.resultStatus[R1][ResultName.Source] = r

                self.resultStatus[R1][ResultName.State] = 1
                self.reservStation[self.resultStatus[R1][ResultName.Source]][ResStationName.Listeners] = []

                self.reservStation[r][LoadBuffer.Result] = self.resultStatus[R1]

                self.reservStation[r][ResStationName.Index] = self.eip
                self.reservStation[r][ResStationName.LastUpdate] = self.clock
                # print("ld reserve ok")
                # self.reservStation[r][ResStationName.Op] = index
                return True
        # print('ld')
        return False

    def JUMP(self, I, R, Offset):
        print("load jump")
        index = Op.JUMP
        reservs = self.reservAvail[index]
        # FUs = self.FUAvail[index]

# 如果已经处于前瞻执行那么issue失败
        if self.pre:
            return False

        for r in reservs:
            if self.reservStation[r][ResStationName.Busy] == False:
                self.reservStation[r][ResStationName.Busy] = True

                print("self.eip")
                print(self.eip)
                self.reservStation[r][ResStationName.Qj] = self.eip
                self.reservStation[r][ResStationName.Qk] = Offset
                self.reservStation[r][ResStationName.Op] = index
    

                if self.resultStatus[R][ResultName.State] == 1:
                    self.reservStation[r][ResStationName.Vj] = self.resultStatus[R][ResultName.Source] + 1#等待R
                    self.reservStation[r][ResStationName.Waiting] += 1

                    if self.resultStatus[R][ResultName.Source] in self.reservAvail[Op.LD]: #如果等待的是LD的结果，监听的是LoadBuffer
                        self.reservStation[self.resultStatus[R][ResultName.Source]][LoadBuffer.Listeners].append(r)
                    else:
                        self.reservStation[self.resultStatus[R][ResultName.Source]][ResStationName.Listeners].append(r)

                else:
                    self.reservStation[r][ResStationName.Vj] = self.resultStatus[R][ResultName.Val] # 否则直接载入
                
                self.reservStation[r][ResStationName.Vk] = I

                self.reservStation[r][ResStationName.Index] = self.eip
                self.reservStation[r][ResStationName.LastUpdate] = self.clock

                self.pre = True
                self.reg = self.resultStatus
                self.resultStatus = copy.deepcopy(self.reg)
                # self.stop = True
                return True
        
        return False