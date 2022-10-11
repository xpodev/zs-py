# Library: Core

The `core` library is a native library provided by the compiler which contain
the very basic building blocks of the rest of the standard library.

The `core` library can be imported like follow:
```zs
import "core";
```

This library defines the following types:
* Type
* Function
* Method
* ZSCompiler

It also defines the native types:
* Integral types
  - i8
  - u8
  - i16
  - u16
  - i32
  - u32
  - i64
  - u64
  - I (native int)
  - U (native unsigned int)
  - f32 (single, float)
  - f64 (double)
  - bool
  - string (not a primitive, but has built-in support)
