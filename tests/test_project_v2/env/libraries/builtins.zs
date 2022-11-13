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

var str = Object.__name__.__class__
var type = str.__class__
var dict = __srf__.context._cache.__class__
var list = __srf__.context._scopes.__class__
var tuple = dict.__bases__.__class__
