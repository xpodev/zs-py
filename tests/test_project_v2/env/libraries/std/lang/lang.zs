import * from "env/libraries/builtins.zs";


fun codegen(fn) {
    setattr(fn, "__class__", CodeGenFunction);
    fn
}


var Call = codegen(id)(fun(){}()).__class__
var Name = codegen(id)(id).__class__


fun create_type(name) {
    Python.type(name, Python.tuple(), Python.dict())
}


fun create_closure(function) {
    fun(delegate, closure) {
        setattr(delegate, "__call__", partial(function, closure));
        setattr(delegate, "refer", partial(fun(delegate, closure, name, object) {
            setattr(closure, name, object);
            delegate
        }, delegate, closure));
        delegate
    }(Object(), Object())
}


var with_scope = codegen(fun(index_from_end, body) {
    fun enter(context) {
        fun(cm) {
            cm.__enter__()
        }(__srf__.toolchain.interpreter.execute(context))
    };
    fun exit(cm) {
        cm.__exit__(Python.None, Python.None, Python.None)
    };
    fun execute() {
        __srf__.toolchain.interpreter.execute(body)
    };
    fun(enter_args, exit_args) {
        fun(context) {
            enter_args.append(context);
            exit_args.append(context);
            execute.body.insert(0, Call(enter, enter_args));
            execute.body.append(Call(exit, exit_args));
            execute()
        }(__srf__.toolchain.interpreter.x.scope(__srf__.toolchain.interpreter.x.frames.__getitem__(__srf__.toolchain.interpreter.execute(index_from_end).__neg__())))
    }(Python.list(), Python.list())
})


var __impl_if = codegen(fun(condition, true_, false_) {
    fun(cases) {
        cases.__setitem__(true, true_);
        cases.__setitem__(false, false_);
        __srf__.toolchain.interpreter.execute(
            cases.__getitem__(
                Python.bool(__srf__.toolchain.interpreter.execute(condition))
            )
        )
    }(Python.dict())
})


var __impl_if__ctx = codegen(fun(ctx, condition, true_, false_) {
    fun(cases) {
        cases.__setitem__(true, true_);
        cases.__setitem__(false, false_);
        __srf__.toolchain.interpreter.execute(cases.__getitem__(Python.bool(condition)))
    }(Python.dict())
})


var __impl_with = codegen(fun(context, body) {
    fun(cm) {
        cm.__enter__();
        __srf__.toolchain.interpreter.execute(body);
        cm.__exit__(Python.None, Python.None, Python.None)
    }(__srf__.toolchain.interpreter.execute(context));
})


// print(__srf__.toolchain.interpreter.x.local_scope)
// __impl_with(__srf__.toolchain.interpreter.x.scope(), print(__srf__.toolchain.interpreter.x.local_scope))


// Python.builtins.exit()


fun equals(x, y) {
    fun(res) {
        __impl_if(res.__eq__(Python.builtins.NotImplemented), y.__eq__(x), res)
    }(x.__eq__(y))
}


fun empty() {}


var __exec__ = fun(node) {
    __srf__.toolchain.interpreter.execute(
        __srf__.toolchain.preprocessor.preprocess(
            node
        )
    )
}

fun __pexec__(node) {
    __srf__.toolchain.interpreter.execute(node)
}
