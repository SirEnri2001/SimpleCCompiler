import traceback
from typing import Optional

addr_offset = 0
su_id = 0


class Field:
    id: str
    size: int
    type: str

    def __init__(self, id, type_list:list, size):
        self.id = id
        self.size = size
        self.type = type_list
        self.fieldType = "Field"

    def __repr__(self):
        return "<"+self.fieldType+" id='" + self.id + "' type='" + str(self.type) + "'/>"


class LocalField(Field):
    def __init__(self, id, type_list:list, size, offset):
        super().__init__(id, type_list, size)
        self.fieldType='Local'
        self.offset = offset


class ParamField(LocalField):
    def __init__(self, id, type_list:list, size, offset):
        super().__init__(id, type_list, size,offset)
        self.fieldType='Param'


class StaticField(Field):
    def __init__(self, id, type_list:list, size):
        super().__init__(id, type_list, size)
        self.fieldType='Static'

class ConstantField(Field):
    def __init__(self, id, type_list:list,val, size):
        super().__init__(id, type_list, size)
        self.fieldType='Constant'
        self.val = val


class FuncField(Field):
    def __init__(self, id, type_list:list,param_list):
        super().__init__(id, type_list, 4)
        self.fieldType='Func'
        self.param_list = param_list


class StorageUnit:
    field_table = {}
    static_list = {}
    constant_list = {}
    func_list = {}
    def __repr__(self):
        sub = ""
        for su in self.sub_storageUnit:
            sub+=str(su)
        return "<Storage id=\""+str(self._su_id)+"\" size=\""+str(self.size)+"\">"+sub+"</Storage>"

    def __init__(self, caller: Optional):
        global su_id
        self.caller = caller
        self._su_id = su_id
        self.field_table = {}
        self.size = 0
        self.func_calling_space = 0
        self.type_convert_space = 0
        self.sub_storageUnit = []
        self.param_offset = 0
        if caller is not None:
            self.static_list = caller.static_list
            self.constant_list = caller.constant_list
            caller.sub_storageUnit.append(self)
        su_id = su_id + 1

    def get_total_space(self):
        return self.size+ self.get_type_convert_space()+self.get_func_calling_space()

    def add_field(self, field: Field):
        try:
            if self.field_table[field.id] is not None:
                print(str(field) + " already been declared")
            else:
                self.field_table[field.id] = field
        except KeyError:
            self.field_table[field.id] = field

    def add_size(self, size: int):
        self.size = self.size+size
        if self.caller is not None:
            self.caller.add_size(size)

    def add_local(self, id, type, size):
        field = LocalField(id, type, size, self.size)
        self.add_size(size)
        self.add_field(field)

    def add_param(self, id, type, size):
        field = ParamField(id, type, size, self.param_offset)
        self.param_offset = self.param_offset + size
        self.add_field(field)

    def add_func(self, id, type_list, params_node_list: list):
        if self.caller is not None:
            self.caller.add_func(id, type_list, params_node_list)
        else:
            try:
                if self.func_list[id]:
                    print("Redeclare of constant variable: {}".format(id))
                return self.func_list[id]
            except KeyError:
                field = FuncField(id, type_list, params_node_list)
                self.func_list[id] = field
                return field

    def getFunc(self, id: str) -> FuncField:
        field = None
        try:
            field = self.func_list[id]
        except KeyError:
                print("Error: Undefined Function of " + str(id))
                traceback.print_exc()
                self.add_func(id,["int"],[])
                field = self.get(id)
        return field

    def get(self, id: str) -> Field:
        field = None
        try:
            field = self.field_table[id]
        except KeyError:
            if self.caller is not None:
                field = self.caller.get(id)
        try:
            if field is None:
                field = self.constant_list[id]
        except KeyError:
            try:
                if field is None:
                    field = self.static_list[id]
            except KeyError:
                if field is None:
                    print("Error: Undefined Identifier of " + str(id))
                    traceback.print_exc()
                    self.add_local(id,["int"],8)
                    field = self.get(id)
        return field

    def add_constant(self, id: str, type_list: list,const_val, size: int):
        if self.caller is not None:
            self.caller.add_constant(id, type_list, const_val,size)
        else:
            try:
                if self.constant_list[id]:
                    print("Redeclare of constant variable: {}".format(id))
                return self.constant_list[id]
            except KeyError:
                field = ConstantField(id, type_list,const_val, size)
                self.constant_list[id]=field
                return field


    def add_static(self, id: str, type_list, size: int):
        try:
            return self.static_list[id]
        except KeyError:
            field = StaticField(id, type_list, size)
            self.static_list[id] = field
            if self.caller is not None:
                self.caller.add_static(id, type_list, size)
        return field

    def get_func_calling_space(self):
        space = self.func_calling_space
        for su in self.sub_storageUnit:
            space = max(space,su.func_calling_space)
        return space

    def get_type_convert_space(self):
        space = self.type_convert_space
        for su in self.sub_storageUnit:
            space = max(space,su.type_convert_space)
        return space