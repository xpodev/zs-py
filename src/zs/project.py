from pathlib import Path

from zs.cli.options import InitOptions


def init(options: InitOptions):
    name = options.project_name

    if name is None:
        raise ValueError(f"'zs init' is not implemented yet")

    cwd = Path.cwd()

    if (cwd / name).exists():
        raise FileExistsError(f"Directory '{cwd / name}' already exists")

    project_dir = (cwd / name)
    project_dir.mkdir()

    source_dir = project_dir / "src"
    source_dir.mkdir()

    env_dir = project_dir / "env"
    env_dir.mkdir()

    with (env_dir / "setup-env.zs").open("w") as setup_env:
        ...

    with (project_dir / f"{name}.main.zs").open("w") as project_file:
        project_file.write('\n'.join([
            "import \"env/setup-env.zs\";",
            "import \"src/main.zs\";", ''
        ]))

    with (source_dir / "main.zs").open("w") as main_file:
        ...

    with (project_dir / "readme.md").open("w") as readme_file:
        readme_file.write('\n'.join([
            f"# {name}", "",
            "To run the project, `cd` to the project folder and execute the following command:",
            "```cmd", "./run.bat", "```",
            '',
            "You can learn more about Z# in our [documentation](https://xpodev.github.io/zs-py/)."
        ]))

    with (project_dir / "run.bat").open("w") as compile_script:
        compile_script.write(f"py -m zs c ./{name}.main.zs\n")
