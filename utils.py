import re

from Program import *

t_seq = 1
l_seq = 1
lc_seq = 0
stack_trace_length = 8
env = 'x86'
# env = 'linux'

code_integrate = []

declared_type = {}

size_table = {
    'int': 4,
    'short': 2,
    'char': 1,
    'long': 8,
    'float': 4,
    'double': 8,
    '*': 4
}

instr_suffix = {
    'int': 'l'
}

int_type_list = ['int', 'short', 'char', 'long']
float_type_list = ['float', 'double']

instruction_table = {
    '=': 'mov',
    '+': 'add',
    '-': 'sub',
    '*': 'imul',
    '/': 'idiv',
    '++': 'inc',
    '--': 'dec'
}

float_instruction_table = {
    '+': 'faddp',
    '-': 'faddp',
    '*': 'fmulp',
    '/': 'fdivp'
}

prefix_instruction_table = {
    '-': 'neg'
}

conditional_jmp_table = {
    '==': 'je',
    '!=': 'jne',
    '>': 'jg',
    '>=': 'jge',
    '<': 'jl',
    '<=': 'jle'
}

relop_table = {
    '==': 'e',
    '!=': 'ne',
    '>': 'g',
    '>=': 'ge',
    '<': 'l',
    '<=': 'le'
}


class BaseNode:
    child_node_list = []
    val = None

    def __init__(self, sub_node_list: list):
        self.child_node_list = sub_node_list

    def __str__(self):
        msg: str = "<node" + ">"
        for node in self.child_node_list:
            msg = msg + "\n" + str(node)
        msg = msg + "\n</node>"
        return msg


class Node(BaseNode):
    optr = None
    storage_unit: StorageUnit

    def __init__(self, optr, sub_node_list: list):
        super(Node, self).__init__(sub_node_list)
        self.optr = optr
        self.nodeType = "Generic"
        self.fakeCode = []
        self.fakeCode_post = []
        self.targetCode = []
        self.targetCode_post = []
        self.asm_val = ''
        self.type = []

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        msg: str = "<" + self.nodeType + " optr='" + self.optr + "'>"
        for node in self.child_node_list:
            msg = msg + "\n" + str(node)
        msg = msg + "\n</" + self.nodeType + ">"
        return msg

    def set_program(self):
        pass

    def set_program_post(self):
        pass

    def start_program(self, su: StorageUnit):
        self.storage_unit = su
        self.set_program()
        for node in self.child_node_list:
            node.start_program(self.storage_unit)
        self.set_program_post()

    def get_fakeCode(self) -> list:
        return self.fakeCode

    def generate_fakeCode(self):
        global code_integrate
        fakeCode = self.get_fakeCode()
        if fakeCode is not None:
            code_integrate.extend(fakeCode)
        for node in self.child_node_list:
            node.generate_fakeCode()
        fakeCode = self.get_fakeCode_post()
        if fakeCode is not None:
            code_integrate.extend(fakeCode)
        return code_integrate

    def get_fakeCode_post(self) -> list:
        return self.fakeCode_post

    def get_targetCode_linux(self) -> list:
        return self.get_targetCode()

    def get_targetCode_post_linux(self) -> list:
        return self.get_targetCode_post()

    def get_targetCode(self) -> list:
        return self.targetCode

    def generate_targetCode(self):
        global code_integrate
        targetCode = self.get_targetCode()
        if targetCode is not None:
            code_integrate.extend(targetCode)
        for node in self.child_node_list:
            node.generate_targetCode()
        targetCode = self.get_targetCode_post()
        if targetCode is not None:
            code_integrate.extend(targetCode)
        return code_integrate

    def get_targetCode_post(self) -> list:
        return self.targetCode_post


class ProgramNode(Node):
    def __init__(self, optr, sub_node_list: list):
        super().__init__(optr, sub_node_list)
        self.nodeType = "Program"
        self.constant_dict = {}

    def set_program(self):
        pass

    def get_fakeCode(self):
        pass

    def get_targetCode(self) -> list:
        global lc_seq
        if len(self.storage_unit.constant_list) == 0:
            self.targetCode.append(".section .text")
            return self.targetCode
        self.targetCode.append(".section .data")
        for const_field_id, const_field in self.storage_unit.constant_list.items():
            self.targetCode.append(const_field_id + ":")
            self.targetCode.append("\t." + str(const_field.type[0]) + " " + str(const_field.val))
        self.targetCode.append(".section .text")
        return self.targetCode


class ExtNode(Node):
    def __init__(self, optr, sub_node_list: list):
        super().__init__(optr, sub_node_list)
        self.nodeType = "Ext"
        self.type_leaf = None
        self.id_leaf = None

    def set_program(self):
        if self.optr == 'extdec':
            self.type_leaf = self.child_node_list[0]
            self.id_leaf = self.child_node_list[1]
            self.storage_unit.add_static(self.id_leaf.val, self.type_leaf.type, self.type_leaf.size)
        if self.optr == 'extdef_func':
            new_su = StorageUnit(self.storage_unit)
            self.storage_unit = new_su

    def set_program_post(self):
        if self.optr == 'extdef_func':
            self.storage_unit.add_static(self.child_node_list[0].val,
                                         self.child_node_list[0].ret_type_node.type,
                                         self.child_node_list[0].ret_type_node.size)

    def get_fakeCode(self) -> list:
        if self.optr == 'extdec':
            self.fakeCode.append('.globl ' + self.child_node_list[0].val)
        if self.optr == 'extdef_func':
            self.fakeCode.append('.globl ' + self.child_node_list[0].val)
        return self.fakeCode

    def get_targetCode(self) -> list:
        if self.optr == 'extdec':
            self.targetCode.append('.globl ' + self.child_node_list[0].val)
        if self.optr == 'extdef_func':
            self.targetCode.append('.globl _' + self.child_node_list[0].val)
        return self.targetCode

    def get_targetCode_post(self) -> list:
        post = []
        if self.child_node_list[1].child_node_list[-1].optr != 'return':
            post.append("leave")
            post.append("ret")
        post.extend(self.targetCode_post)
        self.targetCode_post = post
        return self.targetCode_post


class CalcNode(Node):
    def __init__(self, optr, sub_node_list: list):
        super().__init__(optr, sub_node_list)
        self.nodeType = "Calc"

    def set_program(self):
        global t_seq
        self.val = 'T' + str(t_seq)
        t_seq = t_seq + 1
        self.asm_val = '%eax'

    def set_program_post(self):
        if self.type:
            return
        if self.child_node_list[0].type[0] in int_type_list and self.child_node_list[1].type[0] in int_type_list:
            self.type = self.child_node_list[0].type.copy()
        if not self.child_node_list[0].type or not self.child_node_list[1].type:
            print("CalcNode Error")
            raise ValueError("Calc Error")
        if self.child_node_list[0].type not in int_type_list:
            self.type = self.child_node_list[0].type
        else:
            self.type = self.child_node_list[1].type
        if not self.type:
            print("Compiler Error: Type Not Specified")
            raise ValueError("Type not Specified")

    def get_targetCode(self) -> list:
        if self.child_node_list[0].optr == '*':
            self.child_node_list[0].asm_val = '%edx'
        if self.child_node_list[0].optr == '/':
            self.child_node_list[0].asm_val = '%ecx'
        return self.targetCode

    def get_targetCode_post(self) -> list:
        if self.type[0] in int_type_list:
            return self.get_targetCode_post_int()
        elif self.type[0] in float_type_list:
            return self.get_targetCode_post_float()

    @classmethod
    def load_float(cls, node: Node) -> list:
        if node.type[0] in int_type_list:
            inst = []
            temp_storage = str(node.storage_unit.func_calling_space)+'(%esp)'
            if node.asm_val == '%eax':
                inst.append("mov{} {},{}".format(instr_suffix[node.type[0]],node.asm_val,temp_storage))
                inst.append("fild{} {}".format(instr_suffix[node.type[0]],temp_storage))
            else:
                inst.append("fild{} {}".format(instr_suffix[node.type[0]], node.asm_val))
            return inst
        elif node.asm_val != '#':
            return ['flds {}'.format(node.asm_val)]

    @classmethod
    def save_float(cls, node_dest: Node):
        if node_dest.type in int_type_list:
            return ['fist {}'.format(node_dest.asm_val)]
        else:
            return ['fsts {}'.format(node_dest.asm_val)]

    def get_targetCode_post_float(self) -> list:
        post = []
        self.asm_val = '#'
        try:
            if self.optr == '=':
                post.extend(self.load_float(self.child_node_list[1]))
                post.extend(self.save_float(self.child_node_list[0]))
                self.asm_val = self.child_node_list[0].asm_val
            else:
                if self.optr in ['+', '-', '*', '/', '>', '<', '>=', '<=', '==']:
                    if self.optr in ['+', '-', '*']:
                        post.extend(self.load_float(self.child_node_list[1]))
                        if self.optr == '-':
                            post.append("fchs")
                        post.extend(self.load_float(self.child_node_list[0]))
                        if self.child_node_list[0].asm_val == '#':
                            post.append("{} %st(1),%st(0)".format(float_instruction_table[self.optr]))
                        else:
                            post.append("{} %st(0),%st(1)".format(float_instruction_table[self.optr]))
                    else:
                        self.asm_val = '%eax'
                        post.extend(self.load_float(self.child_node_list[1]))
                        post.extend(self.load_float(self.child_node_list[0]))
                        post.append("fcomip %st(0),%st(1)")
                        post.append("set{} %al".format(relop_table[self.optr]))
                        if self.asm_val != '%eax':
                            post.append("movzbl %al,{}".format(self.asm_val))
        except KeyError as e:
            print("Compiler Error: Key Error in Calc: {}".format(str(self)))
            traceback.print_exc()
        post.extend(self.targetCode_post)
        self.targetCode_post = post
        return self.targetCode_post

    def get_targetCode_post_int(self) -> list:
        post = []
        temp_res = '%eax'
        try:
            if self.optr == '=':
                post.append("mov{} {},{}".format(instr_suffix[self.type[0]],
                                                 self.child_node_list[1].asm_val, self.child_node_list[0].asm_val))
                self.asm_val = self.child_node_list[0].asm_val
            else:
                if self.optr in ['+', '-', '*', '>', '<', '>=', '<=', '==']:
                    post.append(
                        "mov{} {},%eax".format(instr_suffix[self.type[0]], self.child_node_list[1].asm_val))
                    if self.optr in ['+', '-', '*']:
                        post.append(
                            "{}{} {},%eax".format(instruction_table[self.optr], instr_suffix[self.type[0]],
                                                  self.child_node_list[0].asm_val))
                    else:
                        post.append("cmp{} {},%eax".format(instr_suffix[self.type[0]], self.child_node_list[0].asm_val))
                        post.append("set{} %al".format(relop_table[self.optr], instr_suffix[self.type[0]]))
                        if self.asm_val != '%eax':
                            post.append("movzbl %al,{}".format(self.asm_val))
                if self.optr in ['/', '%']:
                    div_num = self.child_node_list[1].asm_val
                    if self.child_node_list[0].asm_val != '%eax':
                        post.append("mov{} {},%eax".format(instr_suffix[self.type[0]], self.child_node_list[0].asm_val))
                    if self.child_node_list[1].nodeType == 'NUM':
                        post.append("mov{} {},%ebx".format(instr_suffix[self.type[0]], self.child_node_list[1].asm_val))
                        div_num = '%ebx'
                    post.append('cltd')
                    post.append('idiv{} {}'.format(instr_suffix[self.type[0]], div_num))
                    if self.optr in ['%']:
                        temp_res = '%edx'
                if temp_res != self.asm_val:
                    post.append("mov{} {},{}".format(instr_suffix[self.child_node_list[0].type[0]],
                                                     temp_res, self.asm_val))
        except KeyError as e:
            print("Compiler Error: Key Error in Calc: {}".format(str(self)))
            traceback.print_exc()
        post.extend(self.targetCode_post)
        self.targetCode_post = post
        return self.targetCode_post

    def get_fakeCode_post(self) -> list:
        post = []
        self.type = self.child_node_list[0].type  # Simple implicit type convert
        try:
            post.append(
                "{} = {} {} {}".format(self.val, self.child_node_list[0].val, self.optr, self.child_node_list[1].val))
            '''if self.optr in ['+', '-', '*']:
                self.fakeCode.append("{}{} {},{}".format(
                    instruction_table[self.optr], instr_suffix[self.child_node_list[0].type],
                    self.child_node_list[0].val, self.child_node_list[1].val
                ))'''
        except KeyError as e:
            print("Compiler Error: Key Error in Calc\n\toptr: {}, type: {}".format(
                self.optr, self.child_node_list[0].type
            ))
            traceback.print_exc()
        post.extend(self.fakeCode_post)
        self.fakeCode_post = post
        return self.fakeCode_post


class PrefixCalcNode(CalcNode):
    def __init__(self, optr, sub_node_list: list):
        super().__init__(optr, sub_node_list)
        self.nodeType = "PrefixCalc"

    def set_program_post(self):
        if self.optr == '*':
            if self.child_node_list[0].type[0] == '*':
                self.type = self.child_node_list[0].type[1:]

    def get_fakeCode_post(self):
        post = []
        self.type = self.child_node_list[0].type  # Simple implicit type convert
        if self.optr == '+' or self.optr == '-':
            post.append("{} = {}{}".format(self.val, self.optr, self.child_node_list[0].val))
        self.fakeCode_post.extend(post)
        return self.fakeCode_post

    def get_targetCode_post(self) -> list:
        post = []
        self.type = self.child_node_list[0].type  # Simple implicit type convert
        if self.optr == '-':
            post.append("neg{} {}".format(instr_suffix[self.type], self.child_node_list[0].asm_val))
        elif self.optr == 'force_convert':
            self.type = self.child_node_list[0].type
        else:
            post.append("{}{} {}".format(instruction_table[self.optr], instr_suffix[self.type], self.asm_val))
        post.extend(self.fakeCode_post)
        self.fakeCode_post = post
        return self.fakeCode_post


class MemNode(Node):
    def __init__(self, optr, sub_node_list: list):
        super().__init__(optr, sub_node_list)
        self.nodeType = "MemNode"

    def set_program(self):
        pass


class FunDefNode(Node):
    def __init__(self, ret_type_node, fundec):
        super().__init__('funhead_def', [ret_type_node, fundec])
        self.nodeType = "FunDef"
        self.ret_type_node = ret_type_node
        self.id_node = fundec
        self.val = fundec.val
        self.params = []

    def set_program(self):
        self.ret_type_node = self.child_node_list[0]
        self.id_node = self.child_node_list[1]
        self.val = self.id_node.val
        self.params = self.child_node_list[2:]
        self.storage_unit.add_func(self.id_node.val, self.ret_type_node.type, self.params)

    def get_fakeCode(self):
        self.fakeCode.append("{}:".format(self.val))
        return self.fakeCode

    def get_targetCode_post(self) -> list:
        post = []
        post.append("_{}:".format(self.val))
        post.append("pushl %ebp")
        post.append("movl %esp,%ebp")
        alloc = self.storage_unit.get_total_space()
        if alloc != 0:
            post.append("subl ${},%esp".format(alloc))
        post.extend(self.targetCode_post)
        self.targetCode_post = post
        return self.targetCode_post


class LocalDecNode(Node):
    def __init__(self, type_node, id_node, is_param=False, sub_dec_list=None):
        if is_param:
            super().__init__('param_dec', [])
        else:
            super().__init__('dec', [])
        self.child_node_list = [type_node, id_node]
        if sub_dec_list is not None:
            self.child_node_list.append(sub_dec_list)
        self.nodeType = "LocalDec"
        self.type_node = self.child_node_list[0]

    def set_program(self):
        if type(self.child_node_list[0]) == TypeLeaf and type(self.child_node_list[1]) == TypeLeaf:
            self.child_node_list.insert(0, TypeLeaf.getType(self.child_node_list[0].val, self.child_node_list[1]))
            self.child_node_list.pop(1)
            self.child_node_list.pop(1)
        self.type_node = self.child_node_list[0]
        self.type = self.type_node.type
        self.id_node = self.child_node_list[1]
        self.id_node.type = self.child_node_list[0]
        if self.optr == 'param_dec':
            self.storage_unit.add_param(self.id_node.val, self.type_node.type,
                                        self.type_node.size)
        else:
            self.storage_unit.add_local(self.id_node.val, self.type_node.type,
                                        self.type_node.size)
        if len(self.child_node_list) == 3:
            self.child_node_list[2].child_node_list.pop(0)
            self.child_node_list[2].child_node_list.insert(0, IdLeaf(self.id_node.val))


class FunDecNode(Node):
    def __init__(self, optr, sub_node_list: list):
        super().__init__(optr, sub_node_list)
        self.nodeType = "FunDec"


class CompStmtNode(Node):
    def __init__(self, optr, sub_node_list: list):
        super().__init__(optr, sub_node_list)
        self.nodeType = "CompStmt"

    def set_program(self):
        new_su = StorageUnit(self.storage_unit)
        self.storage_unit = new_su


class StmtNode(Node):
    def __init__(self, optr, sub_node_list: list):
        super().__init__(optr, sub_node_list)
        self.nodeType = "Stmt"

    def set_program(self):
        pass

    def get_fakeCode_post(self):
        post = []
        if self.optr == 'return':
            if self.child_node_list[0] is not None:
                post.append('retVal = {}'.format(self.child_node_list[0].val))
            post.append('ret')
        post.extend(self.fakeCode_post)
        self.fakeCode_post = post
        return self.fakeCode_post

    def get_targetCode_post_linux(self) -> list:
        post = []
        if self.optr == 'return':
            if self.child_node_list[0] is not None:
                if self.child_node_list[0].type[0] in float_type_list and self.child_node_list[0].asm_val != '#':
                    CalcNode.load_float(self.child_node_list[0])
                if self.child_node_list[0].type[0] in int_type_list and self.child_node_list[0].asm_val != '%eax':
                    post.append('movl {},%eax'.format(self.child_node_list[0].asm_val))
            post.append('leave')
            post.append('ret')
        if self.optr == 'print':
            post.append("movl ${},%edx".format(self.child_node_list[0].field.size))
            post.append("movl {},%ecx".format(self.child_node_list[0].asm_val))
            post.append("movl $1,%ebx")
            post.append("movl $4,%eax")
            post.append("int $0x80")
        post.extend(self.fakeCode_post)
        self.fakeCode_post = post
        return self.fakeCode_post

    def get_targetCode_post(self) -> list:
        post = []
        if self.optr == 'return':
            if self.child_node_list[0] is not None:
                if self.child_node_list[0].type[0] in float_type_list and self.child_node_list[0].asm_val != '#':
                    CalcNode.load_float(self.child_node_list[0])
                if self.child_node_list[0].type[0] in int_type_list and self.child_node_list[0].asm_val != '%eax':
                    post.append('movl {},%eax'.format(self.child_node_list[0].asm_val))
            post.append('leave')
            post.append('ret')
        if self.optr == 'print':
            post.append("movb {},%dl".format(self.child_node_list[0].asm_val))
            post.append("movb $2,%ah")
            post.append("int $0x21")
        post.extend(self.fakeCode_post)
        self.fakeCode_post = post
        return self.fakeCode_post


class FuncCallNode(CalcNode):
    def __init__(self, optr, sub_node_list: list):
        super().__init__(optr, sub_node_list)
        self.nodeType = 'FuncCall'

    def set_program(self):
        self.val = self.child_node_list[0].val
        self.func = self.storage_unit.getFunc(self.val)
        self.type = self.func.type
        self.size = size_table[self.type[0]]
        self.params = self.func.param_list
        if self.type[0] in int_type_list:
            self.asm_val = '%eax'
        elif self.type[0] in float_type_list:
            self.asm_val = '#'

    def set_program_post(self):
        space = 0
        type_space = 0
        i = 0
        des = "(%esp)"
        offset = 0
        while i < len(self.child_node_list) - 1:
            arg = self.child_node_list[i + 1]
            param = self.params[i]
            space = space + size_table[arg.type[0]]
            if param.type[0] in float_type_list and arg.type[0] in int_type_list or param.type[0] in int_type_list and \
                    arg.type[0] in float_type_list:
                type_space = max(size_table[param.type[0]], size_table[arg.type[0]])
            param.asm_val = des
            offset = size_table[arg.type[0]] + offset
            des = str(offset) + "(%esp)"
            i = i + 1
        self.storage_unit.type_convert_space = max(self.storage_unit.type_convert_space, type_space)
        self.storage_unit.func_calling_space = max(self.storage_unit.func_calling_space, space)

    def get_targetCode(self) -> list:
        i = 0
        while i < len(self.child_node_list) - 1:
            arg = self.child_node_list[i + 1]
            param = self.params[i]
            if arg.type[0] in float_type_list or param.type[0] in float_type_list:
                self.targetCode_post.extend(CalcNode.load_float(arg))
                self.targetCode_post.extend(CalcNode.save_float(param))
            else:
                if arg.asm_val != '%eax':
                    self.targetCode_post.append("mov{} {},%eax".format(instr_suffix[arg.type[0]], arg.asm_val))
                self.targetCode_post.append("mov{} %eax,{}".format(instr_suffix[arg.type[0]], param.asm_val))
            i = i + 1
        self.targetCode_post.append("{} _{}".format("call", self.child_node_list[0].val))
        return self.targetCode

    def get_fakeCode_post(self) -> list:
        post = []
        if len(self.child_node_list) == 2:
            for arg in self.child_node_list[1].child_node_list:
                post.append("add arg {}".format(arg.val))
        post.append("call {}".format(self.child_node_list[0].val))
        post.extend(self.fakeCode_post)
        self.fakeCode_post = post
        return self.fakeCode_post


class FlowCtrlNode(StmtNode):
    def __init__(self, optr, sub_node_list: list):
        super().__init__(optr, sub_node_list)
        self.nodeType = "FlowCtrl"
        self.label1 = ''
        self.label2 = ''

    def set_program(self):
        global l_seq
        self.label1 = "L{}".format(l_seq)
        self.label2 = "L{}".format(l_seq + 1)
        l_seq = l_seq + 2

    def get_targetCode_post(self) -> list:
        post = []
        if self.optr == 'if':
            post.append("{}:".format(self.label1))
        if self.optr == 'if_else':
            post.append("{}:".format(self.label2))
        if self.optr == 'while':
            post.append("jmp {}".format(self.label1))
            post.append("{}:".format(self.label2))
        post.extend(self.targetCode_post)
        self.targetCode_post = post
        return self.targetCode_post

    def get_targetCode(self) -> list:
        global l_seq
        if self.optr == 'if':
            self.child_node_list[1].targetCode.append("cmpl $0,{}".format(self.child_node_list[0].asm_val))
            self.child_node_list[1].targetCode.append("je {}".format(self.label1))
        if self.optr == 'if_else':
            self.child_node_list[1].targetCode.append("cmpl $0,{}".format(self.child_node_list[0].asm_val))
            self.child_node_list[1].targetCode.append("je {}".format(self.label1))
            self.child_node_list[2].targetCode.append("jmp {}".format(self.label2))
            self.child_node_list[2].targetCode.append("{}:".format(self.label1))
        if self.optr == 'while':
            self.child_node_list[1].targetCode.append("{}:".format(self.label1))
            self.child_node_list[1].targetCode.append("cmpl $0,{}".format(self.child_node_list[0].asm_val))
            self.child_node_list[1].targetCode.append("je {}".format(self.label2))
        return self.targetCode

    def get_fakeCode(self):
        global l_seq
        if self.optr == 'if':
            label = "L{}".format(l_seq)
            l_seq = l_seq + 1
            self.child_node_list[1].fakeCode.append("cmp {},$0".format(self.child_node_list[0].val))
            self.child_node_list[1].fakeCode.append("je {}".format(label))
            self.fakeCode_post.append("{}:".format(label))
        if self.optr == 'if_else':
            label1 = "L{}".format(l_seq)
            label2 = "L{}".format(l_seq + 1)
            l_seq = l_seq + 2
            self.child_node_list[1].fakeCode.append("cmp {},$0".format(self.child_node_list[0].val))
            self.child_node_list[1].fakeCode.append("je {}".format(label1))
            self.child_node_list[2].fakeCode.append("jmp {}".format(label2))
            self.child_node_list[2].fakeCode.append("{}:".format(label1))
            self.fakeCode_post.append("{}:".format(label2))
        if self.optr == 'while':
            label1 = "L{}".format(l_seq)
            label2 = "L{}".format(l_seq + 1)
            l_seq = l_seq + 2
            self.child_node_list[1].fakeCode.append("{}:".format(label1))
            self.child_node_list[1].fakeCode.append("cmp {},$0".format(self.child_node_list[0].val))
            self.child_node_list[1].fakeCode.append("je {}".format(label2))
            self.fakeCode_post.append("jmp {}".format(label1))
            self.fakeCode_post.append("{}:".format(label2))
        return self.fakeCode


class Leaf(Node):
    def __init__(self, type, val):
        super(Leaf, self).__init__('', [])
        self.nodeType = type
        self.val = val
        if self.nodeType == 'NUM':
            self.asm_val = '$' + str(self.val)

    def __str__(self):
        return "<" + str(self.nodeType) + " val='" + str(self.val) + "'/>"


class NoneLeaf(Leaf):
    inst = None

    def __init__(self):
        super().__init__('none', None)
        self.type = []

    @classmethod
    def getInstance(cls):
        if cls.inst is None:
            cls.inst = NoneLeaf()
        return cls.inst

    def __str__(self):
        return "<Empty/>"


class LiteralLeaf(Leaf):
    def __init__(self, type_list, val):
        super().__init__('Literal', val)
        self.val = val
        self.type = type_list
        self.type_str = TypeLeaf.get_str(type_list)
        if type_list[0] in size_table.keys():
            self.size = size_table[type_list[0]]

    def set_program(self):
        global lc_seq
        self.asm_val = 'LC{}'.format(str(lc_seq))
        lc_seq = lc_seq + 1
        if self.type_str == 'char *':
            self.storage_unit.add_constant(self.asm_val, ['asciz'], self.val, self.size)
        else:
            self.storage_unit.add_constant(self.asm_val, self.type, self.val, self.size)


class ValLeaf(Leaf):
    def __init__(self, type, val):
        super().__init__('Val', val)
        self.type = TypeLeaf.getTypeList(type)
        if self.type[0] in int_type_list:
            self.asm_val = '$' + str(self.val)
            self.asm_val = '$' + str(self.val)
            self.size = size_table[self.type[0]]


class IdLeaf(Leaf):
    def __init__(self, val):
        super().__init__("Identifier", val)
        self.name = val
        self.field = None

    def set_program(self):
        self.field = self.storage_unit.get(self.name)
        self.type = self.field.type
        self.size = self.field.size

    def set_program_post(self):
        global stack_trace_length
        if type(self.field) == LocalField:
            self.asm_val = str(-self.field.offset - self.field.size) + "(%ebp)"
        elif type(self.field) == ParamField:
            self.asm_val = str(self.field.offset + stack_trace_length) + "(%ebp)"
        elif type(self.field) == StaticField:
            self.asm_val = self.field.id
        else:
            self.asm_val = "unknown symbol: {}".format(self)


class TypeLeaf(Leaf):
    size: int

    def __str__(self):
        return "<" + str(self.nodeType) + " list=\"" + str(self.type) + "'\"/>"

    @classmethod
    def get_str(cls, type: list) -> str:
        val = ''
        i = 0
        while i < len(type):
            _type = type[i]
            if _type == '*':
                val = '*' + val
            elif re.match(r'\[\d*]', _type):
                if re.match(r'\(.*?\)', _type):
                    print("Type Error: no such type {}".format(val + _type))
                elif i > 0 and type[i - 1] == '*':
                    val = "(" + val + ")" + _type
                else:
                    val = val + _type
            elif re.match(r'\(.*?\)', _type):
                if i > 0:
                    val = '(' + val + ')' + _type
            else:
                if i == 0:
                    val = str(_type)
                else:
                    val = str(_type) + " " + val
            i = i + 1
        return val

    def __init__(self, val, subtype):
        super().__init__("Type", val)
        global declared_type
        if re.match(r"\(.*?\)", val):
            self.size = 0
        else:
            self.size = size_table[val]
        if subtype.nodeType != 'none':
            self.type = subtype.type.copy()
            self.type.append(val)
        else:
            self.type = [val]
        self.val = TypeLeaf.get_str(self.type)

    def set_program(self):
        pass

    @classmethod
    def getType(cls, val, subtype=NoneLeaf.getInstance()):
        global declared_type
        str_list = []
        if subtype.nodeType != 'none':
            str_list = subtype.type.copy()
        str_list.append(val)
        str = TypeLeaf.get_str(str_list)
        try:
            typeObj = declared_type[str]
        except KeyError:
            typeObj = TypeLeaf(val, subtype)
            declared_type[str] = typeObj
        return typeObj

    @classmethod
    def getTypeList(cls, val, subtype=NoneLeaf.getInstance()):
        return TypeLeaf.getType(val, subtype).type


class TreeOptimizer:
    def DeleteNone(self, root: Node):
        for node in root.child_node_list:
            if type(node) == NoneLeaf:
                root.child_node_list.remove(node)
        for node in root.child_node_list:
            self.DeleteNone(node)

    def PromotionNodes(self, root: Node):
        is_clean = False
        while not is_clean:
            is_clean = True
            for node in root.child_node_list:
                if type(node) == Node and node.optr == 'append':
                    is_clean = False
                    idx = root.child_node_list.index(node)
                    for node2 in node.child_node_list:
                        root.child_node_list.insert(idx, node2)
                        idx = idx + 1
                    root.child_node_list.remove(node)
        for node in root.child_node_list:
            self.PromotionNodes(node)

    def PromotionNodesSpecified(self, root: Node, spec: list):
        is_clean = False
        while not is_clean:
            is_clean = True
            for node in root.child_node_list:
                if not type(node) == Leaf and node.optr in spec:
                    for node2 in node.child_node_list:
                        if not type(node2) == Leaf and node2.optr in spec:
                            root.child_node_list.insert(root.child_node_list.index(node), node2)
                            node.child_node_list.remove(node2)
                            is_clean = False
                            break
        for node in root.child_node_list:
            self.PromotionNodesSpecified(node, spec)
