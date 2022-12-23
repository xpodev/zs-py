import {
    CodeGenFunction,
    Function,
    Object,
    getattr,
    setattr,
    print,
    partial,
    partialmethod
} from __srf__.builtins;

// make Z# functions Python callables
var Function_call = partialmethod(__srf__.toolchain.interpreter.execute)
Function_call.keywords.__setitem__("execute", true)
setattr(Function, "__call__", Function_call)

// add closures to Z# functions
var Function_refer = partialmethod(fun(func, name, value) {
    setattr(func.__closure__, name, value);
    func
})
setattr(Function, "refer", Function_refer)


var INTERPRETER = __srf__.toolchain.interpreter

// Setup the "_._" operator again
fun GET_ATTR(left, right) {
    getattr(INTERPRETER.execute(left), right)
}

//INTERPRETER.x.local("_._", GET_ATTR)

// setup the Python backend interface

fun id(x) { x }

// namespace Python
var Python = Object()

setattr(Python, "builtins", getattr._native.__globals__.__getitem__("__builtins__"))
setattr(Python, "str", Object.__name__.__class__)
setattr(Python, "int", id(0).__class__)
setattr(Python, "type", Python.str.__class__)
setattr(Python, "object", Object.__bases__.__getitem__(0))
setattr(Python, "dict", __srf__.context._cache.__class__)
setattr(Python, "list", __srf__.context._scopes.__class__)
setattr(Python, "tuple", Python.object.__bases__.__class__)
setattr(Python, "bool", true.__class__)
setattr(Python, "None", Python.list().append(Python))

// tests

fun __test_module__builtins(test) {
    test("builtins");
    test("str");
    test("int");
    test("type");
    test("object");
    test("dict");
    test("list");
    test("tuple");
    test("None")
}
__test_module__builtins(fun(name) { print(name, getattr(Python, name)) })
