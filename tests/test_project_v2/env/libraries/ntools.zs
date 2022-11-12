import * from "env/libraries/builtins.zs";


var Function_call = partialmethod(__srf__.toolchain.interpreter.execute)
Function_call.keywords.__setitem__("execute", true)
setattr(Function, "__call__", Function_call)
