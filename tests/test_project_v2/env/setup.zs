let compiler = get Compiler;

compiler.Context.Add("__srf__", compiler);

compiler.Context.Add("__file__", get fun() => __srf__.CurrentFile);

compiler.Context.Add("__module__", get fun() => __srf__.Modules.Top());

import * from "env/libraries/builtins.zs"
