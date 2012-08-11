class Runtime(object):
    def __init__(self, primitives):
        self.global_env = W_List(W_List(symbol("vau"), W_Vau(self.vau)), w_nil)
        self.global_env.comma(W_List(W_List(symbol("quote"), W_Vau(self.quote)), w_nil))
        primitives["eval"] = self.m_eval
        primitives["operate"] = self.operate
        primitives["lookup"] = self.lookup
        for name in primitives:
            prim = W_Primitive(primitives[name])
            self.global_env.comma(W_List(W_List(symbol(name), prim), w_nil))

    def bind(self, param, val):
        if param is w_nil and val is w_nil:
            return w_nil
        elif isinstance(param, W_Symbol):
            if param.name == "_":
                return w_nil
            else:
                return W_List(W_List(param, val), w_nil)
        elif isinstance(param, W_List) and isinstance(val, W_List):
            if param is w_nil:
                raise QuoppaException("too many arguments")
            elif val is w_nil:
                raise QuoppaException("too few arguments")
            return W_List(
                self.bind(param.car, val.car).comma(self.bind(param.cdr, val.cdr)),
                w_nil
            )
        else:
            raise QuoppaException("can't bind %s %s" % (param, val))

    def lookup(self, name, env):
        pair = env.car
        env = env.cdr
        while pair is not w_nil:
            if pair.car.equal(name):
                return pair
            if env is w_nil:
                break
            pair = env.car
            env = env.cdr
        raise QuoppaException("could not find %s" % name)

    def m_eval(self, env, exp):
        if env is w_nil:
            env = self.global_env
        if isinstance(exp, W_Symbol):
            return self.lookup(exp, env).cdr
        elif exp is w_nil:
            return w_nil
        elif isinstance(exp, W_List):
            return self.operate(env, self.m_eval(env, exp.car), exp.cdr)
        else:
            return exp

    def operate(self, env, fexpr, operands):
        return fexpr.call(self, env, operands)

    def vau(self, static_env, vau_operands):
        params = vau_operands.car
        env_param = vau_operands.cdr.car
        body = vau_operands.cdr.cdr.car
        return W_Fexpr(env_param, params, static_env, body)

    def quote(self, env, w_obj):
        if isinstance(w_obj, W_List):
            return w_obj.car
        else:
            return w_obj


### Runtime Classes
class QuoppaException(Exception):
    pass

class W_Object(object):
    __slots__ = []

    def to_string(self):
        return ''

    def to_repr(self):
        return "#<unknown>"

    def to_boolean(self):
        return True

    def __repr__(self):
        return "<" + self.__class__.__name__ + " " + self.to_string() + ">"

    def eq(self, w_obj):
        return self is w_obj

    eqv = eq
    equal = eqv

    def call(self, runtime, env, operative):
        raise QuoppaException("cannot call %s" % self.to_string())

class W_Undefined(W_Object):
    def to_repr(self):
        return "#<undefined>"

    to_string = to_repr

w_undefined = W_Undefined()

class W_Boolean(W_Object):
    def __new__(cls, val):
        if val:
            return w_true
        else:
            return w_false

    def __init__(self, val):
        pass

class W_True(W_Boolean):
    _w_true = None
    def __new__(cls, val):
        if cls._w_true is None:
            cls._w_true = W_Object.__new__(cls)
        return cls._w_true

    def __init__(self, val):
        assert val

    def to_repr(self):
        return "#t"
    to_string = to_repr

w_true = W_True(True)

class W_False(W_Boolean):
    _w_false = None
    def __new__(cls, val):
        if cls._w_false is None:
            cls._w_false = W_Object.__new__(cls)
        return cls._w_false

    def __init__(self, val):
        assert not val

    def to_repr(self):
        return "#f"
    to_string = to_repr

    def to_boolean(self):
        return False

w_false = W_False(False)

class W_String(W_Object):
    def __init__(self, val):
        self.strval = val

    def to_string(self):
        return self.strval

    def to_repr(self):
        str_lst = ["\""]
        for ch in self.strval:
            if ch in ["\"", "\\"]:
                str_lst.append("\\" + ch)
            else:
                str_lst.append(ch)

        str_lst.append("\"")
        return ''.join(str_lst)

    def __repr__(self):
        return "<W_String \"" + self.strval + "\">"

    def equal(self, w_obj):
        if not isinstance(w_obj, W_String):
            return False
        return self.strval == w_obj.strval

class W_Symbol(W_Object):
    #class dictionary for symbol storage
    obarray = {}

    def __init__(self, val):
        self.name = val

    def to_repr(self):
        return self.name

    to_string = to_repr

def symbol(name):
    #use this to create new symbols, it stores all symbols
    #in W_Symbol.obarray dict
    #if already in obarray return it 
    name = name.lower()
    w_symb = W_Symbol.obarray.get(name, None)
    if w_symb is None:
        w_symb = W_Symbol(name)
        W_Symbol.obarray[name] = w_symb

    assert isinstance(w_symb, W_Symbol)
    return w_symb

class W_Real(W_Object):
    def __init__(self, val):
        self.exact = False
        self.realval = val

    def to_string(self):
        return str(self.realval)

    def to_repr(self):
        # return repr(self.realval)
        return str(float(self.realval))

    def to_number(self):
        return self.to_float()

    def to_fixnum(self):
        return int(self.realval)

    def to_float(self):
        return self.realval

    def round(self):
        int_part = int(self.realval)
        if self.realval > 0:
            if self.realval >= (int_part + 0.5):
                return int_part + 1

            return int_part

        else:
            if self.realval <= (int_part - 0.5):
                return int_part - 1

            return int_part

    def is_integer(self):
        return self.realval == self.round()

    def eqv(self, w_obj):
        return isinstance(w_obj, W_Real) \
            and self.exact is w_obj.exact \
            and self.realval == w_obj.realval
    equal = eqv

W_Number = W_Real

class W_Integer(W_Real):
    def __init__(self, val):
        self.intval = val
        self.realval = val
        self.exact = True

    def to_string(self):
        return str(self.intval)

    def to_repr(self):
        #return repr(self.intval)
        return str(int(self.intval))

    def to_number(self):
        return self.to_fixnum()

    def to_fixnum(self):
        return self.intval

    def to_float(self):
        return float(self.intval)

class W_List(W_Object):
    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr

    def to_string(self):
        return "(" + self.to_lstring() + ")"

    def to_lstring(self):
        car = self.car.to_string()
        cdr = self.cdr
        if cdr is w_nil:
            return car
        elif isinstance(cdr, W_List): #still proper list
            return car + " " + cdr.to_lstring()
        else: #end proper list with dotted
            return car + " . " + cdr.to_string()

    def to_repr(self):
        return "(" + self.to_lrepr() + ")"

    def to_lrepr(self):
        car = self.car.to_repr()
        cdr = self.cdr
        if cdr is w_nil: #end of proper list
            return car
        elif isinstance(cdr, W_List): #still proper list
            return car + " " + cdr.to_lrepr()
        else: #end proper list with dotted
            return car + " . " + cdr.to_repr()

    def __repr__(self):
        return "<W_List " + self.to_repr() + ">"

    def equal(self, w_obj):
        return isinstance(w_obj, W_List) and \
            self.car.equal(w_obj.car) and \
            self.cdr.equal(w_obj.cdr)

    def cons(self, w_pair):
        if self.cdr is w_nil:
            return W_List(self.car, w_pair)
        else:
            return W_List(self.car, self.cdr.cons(w_pair))

    def comma(self, w_pair):
        if self.cdr is w_nil:
            self.cdr = w_pair
            return self
        else:
            self.cdr.comma(w_pair)
            return self

class W_Nil(W_List):
    _w_nil = None
    def __new__(cls):
        if cls._w_nil is None:
            cls._w_nil = W_Object.__new__(cls)
        return cls._w_nil

    def __init__(self):
        pass

    def __repr__(self):
        return "<W_Nil ()>"

    def to_repr(self):
        return "()"

    to_string = to_repr

    def comma(self, w_pair):
        return w_pair

    cons = comma

w_nil = W_Nil()

class W_Fexpr(W_Object):
    def __init__(self, env_param, params, static_env, body):
        self.env_param = env_param
        self.params = params
        self.static_env = static_env
        self.body = body

    def to_string(self):
        return '#<an fexpr>'

    to_repr = to_string

    def call(self, runtime, dynamic_env, operands):
        local_names = W_List(self.env_param, self.params)
        local_values = dynamic_env.comma(operands)
        local_env = runtime.bind(local_names, local_values).comma(self.static_env)
        return runtime.m_eval(local_env, body)

class W_Primitive(W_Fexpr):
    def __init__(self, fun):
        self.fun = fun

    def to_string(self):
        return "#<a primitive>"

    to_repr = to_string

    def call(self, runtime, env, operands):
        operands_w = []
        while operands is not w_nil:
            operands_w.append(runtime.m_eval(env, operands.car))
            operands = operands.cdr
        return self.fun(*operands_w)

class W_Vau(W_Primitive):
    def call(self, runtime, env, operands):
        return self.fun(env, operands)