The compilation process starts with the following shell command:
```cmd
py -3.10 -m zs <file>
```

This command invokes the compiler in compilation mode with the given file
as the target source file.

The file will usually set up the compiler for general Z# compilation mode
and then compile the project files one by one.

Whenever a project is compiled, a new toolchain will be created specifically for
that project.


The default state is defined as:
```
CurrentContext = GlobalContext()

ModuleCache = Mapping<String, Module> {
    "core": CoreModule
}

Toolchain = Toolchain {
    Tokenizer = ()
    Parser = ()
    Interpreter = ()
}

ImportSystem = ImportSystem {
    Path = []
    Importers =  Mapping<String, Importer> {
    
    }
    DirectoryImporters = []
}
```


Whenever a document is executed, a new document context is created parented to the current context
```
CurrentContext = Document(parent=CurrentContext)
```

(then importing inside a scope will make the document parented to the scope it's in. not good)

When a module is created like this:
```
module MyModule;
```
its corresponding context is created in a similar way as document context

```
CurrentContext = Module(parent=CurrentContext)
```


A context is just a wrapper over a `dict[String, Object]`.


What I actually want is a context manager that has:
* A reference to the global context
* The document is currently being executed
* The module stack and the current module (i.e. the last declared module) (cause modules are recursive)
* The document stack (because documents can import other documents)
* The current state of the scope stack which may include:
  * Namespaces
  * Unnamed scopes
  * Types
  * Function body
  * Modules
  * Special scopes
* A way to look up an item by name in all the contexts and in the scopes
* The current context object (which is always the last context object that was added, which can be
a document, module, scope, class or whatever else)


Every top-level module gets its own toolchain.
