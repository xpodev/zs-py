# ZSCompiler
Congratulations! You have successfully created a new Z# project.


To run the project, `cd` to the project directory and type in the following command:
```commandline
py -m zs c .
```

* At least Python version 3.10 must be installed


## Directory structure
If the project was created/initialized with the `--src` flag, 
the structure will look like this:

```
{project_dir}
  |--- env/
  |     |--- libraries/
  |     |       |--- builtins.zs
  |     |--- setup.zs
  |--- src/
  |     |--- main.zs
  |--- {project_dir}.main.zs
```

Otherwise, it'll look exactly the same except that the `main.zs` file will
be placed in the `{project_dir}` directory instead of in the `src` directory.

`env/` - This directory contains project specific items used for compilation
    such as libraries installed for the project and the setup file.

`env/setup.zs` - This file is the second to run when compiling the project and
    its purpose is to set up the compiler before compiling the rest of the project.
        
`env/libraries/` - Contains the libraries which were installed for this project.

`src/` (or `/` if created without `--src`) - The source directory. 
    This is where you should put the code files for your project.

`src/main.zs` - The main file. By default, this file contains the entry point
    of your program (i.e. the `Main` function).

`{project_dir}.main.zs` - Module file. This file runs first and is responsible
    for running the setup file and adding all of the source files to the compilation
    process.
