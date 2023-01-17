When compiling a project, there are a few systems in play:

* Global context
* Import system
* Parser
* Package manager

Each one can be modified to fill the compilation needs of the project

The global context is actually shared between the project and all the imported
libraries/projects/files, so it can be used for conditional compiling.

The import system defines some settings such as:
* Library search path
* Default special file format (default `{dir_name}.{type}.zs`)
    - module (executed when importing the directory)
    - main (executed when running the directory)
    - setup (executed when installing the directory as a package)
    - package (executed when packaging the directory to a package)
* Custom importers
* Directory importer

The import system is defined per project.

The parser is responsible for parsing the stream of tokens of a document
It can be modified to add:
* Custom operators (i.e. define a symbol and precedence for the operator)
* Custom modifiers (an AST modifier function)
* Parsers (a parser that can be accessed by name)

The parser is defined per project.

The package manager is responsible for managing the packages of the current environment

The PM can be used to temporarily install packages and detect missing dependencies


