let compiler = get Compiler;

// compiler.Toolchain.Parser.ExpressionParser.Prefix("get", 50, MOD_Get);

compiler.Context.Add(compiler, "__srf__");

__srf__.Context.Add(get fun() => __srf__.CurrentFile, "__file__");

__srf__.Context.Add(get fun() => __srf__.Modules.Top(), "__module__");

fun export(stream) {
    __srf__.Toolchain.Parser.NextExpression()
}

compiler.Toolchain.Parser.ExpressionParser.Prefix("export", 50, export);

compiler.Context.ImportSystem.AddDirectory("env/libraries");

if (true) import * from "builtins.zs"

