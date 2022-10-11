I have no idea what to write here

Modules can either be defined in the filesystem (module file)
or in the code itself (module declaration)

Setup scripts (when installing libraries) are responsible for
registering a module with a certain name (so it can be imported by name)

The reason importing a specific file from a module is almost useless is 
because it is also possible to import the object from the module itself -
unless the object is private, in which case, it shouldn't be used by external
code - unless the imported document is not included in the module.

---

Compilation hierarchy:
Each entry acts as the parent of the entry below it.

starred (*) entries are parented in order they were created.
1) Global Compiler Scope
2) Modules*
3) Document
4) Scopes*


Compile-time execution order:

1) Document body
   * Import statements (executes imported file/module file)
2) Reference resolve step (after build order)
