# Installation

To install Z# on your machine, you need to install the source code and run it directly.

## Requirements
- Python 3.10 or above
- Git

## Steps
First, clone the github repo:
```sh
git clone https://github.com/xpodev/zs-py.git -b rewrite-core  # (1)!
```

1. The `rewrite-core` branch is the latest branch (currently).

Add the cloned repo to your PATH.

Then, create your first project:
```cmd
zsc new my_project
```

This will create a new directory `my_project` which will contain the generated project.

Open the generated directory in your favorite IDE and open the `main.zs` file located in `src/`.

Write the following lines and save the file:
```go title="main.zs"
print("Hello, World!");
```

Run the file:
```
zsc c my_project.main.zs
```

Expected output:
```
Hello, World!
```


<!-- ```cmd
pip install zs-py
```

```cmd
zs new my_project
cd my_project
```

```cmd
zs c my_project.main.zs
``` -->
