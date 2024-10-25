# Copyright 2021, Breakaway Consulting Pty. Ltd.
# SPDX-License-Identifier: BSD-2-Clause

"""The SDK build script.

# Why Python (and not make, or something else)?

We call out to Make, but having this top-level driver script
is useful.

There are just a lot of things that are much easier in Python
than in make.

"""
from argparse import ArgumentParser
from os import popen, system, environ
from shutil import copy
from pathlib import Path
from dataclasses import dataclass
from sys import executable
from tarfile import open as tar_open, TarInfo
import platform as host_platform
from enum import IntEnum
import json

from typing import Any, Dict, Union, List, Tuple, Optional

NAME = "microkit"
VERSION = "1.4.1"

ENV_BIN_DIR = Path(executable).parent

MICROKIT_EPOCH = 1616367257

TOOLCHAIN_AARCH64 = "aarch64-none-elf"
TOOLCHAIN_RISCV = "riscv64-unknown-elf"

KERNEL_CONFIG_TYPE = Union[bool, str]
KERNEL_OPTIONS = Dict[str, Union[bool, str]]


class KernelArch(IntEnum):
    AARCH64 = 1
    RISCV64 = 2

    def c_toolchain(self) -> str:
        if self == KernelArch.AARCH64:
            return TOOLCHAIN_AARCH64
        elif self == KernelArch.RISCV64:
            return TOOLCHAIN_RISCV
        else:
            raise Exception(f"Unsupported toolchain architecture '{self}'")

    def is_riscv(self) -> bool:
        return self == KernelArch.RISCV64

    def is_arm(self) -> bool:
        return self == KernelArch.AARCH64

    def to_str(self) -> str:
        if self == KernelArch.AARCH64:
            return "aarch64"
        elif self == KernelArch.RISCV64:
            return "riscv64"
        else:
            raise Exception(f"Unsupported arch {self}")


@dataclass
class BoardInfo:
    name: str
    arch: KernelArch
    gcc_cpu: Optional[str]
    loader_link_address: int
    kernel_options: KERNEL_OPTIONS
    examples: Dict[str, Path]


@dataclass
class ConfigInfo:
    name: str
    debug: bool
    kernel_options: KERNEL_OPTIONS


SUPPORTED_BOARDS = (
    BoardInfo(
        name="tqma8xqp1gb",
        arch=KernelArch.AARCH64,
        gcc_cpu="cortex-a35",
        loader_link_address=0x80280000,
        kernel_options={
            "KernelPlatform": "tqma8xqp1gb",
            "KernelIsMCS": True,
            "KernelArmExportPCNTUser": True,
            "KernelArmHypervisorSupport": True,
            "KernelArmVtimerUpdateVOffset": False,
        },
        examples={
            "ethernet": Path("example/tqma8xqp1gb/ethernet")
        }
    ),
    BoardInfo(
        name="zcu102",
        arch=KernelArch.AARCH64,
        gcc_cpu="cortex-a53",
        loader_link_address=0x40000000,
        kernel_options={
            "KernelPlatform": "zynqmp",
            "KernelARMPlatform": "zcu102",
            "KernelIsMCS": True,
            "KernelArmExportPCNTUser": True,
            "KernelArmHypervisorSupport": True,
            "KernelArmVtimerUpdateVOffset": False,
        },
        examples={
            "hello": Path("example/zcu102/hello")
        }
    ),
    BoardInfo(
        name="maaxboard",
        arch=KernelArch.AARCH64,
        gcc_cpu="cortex-a53",
        loader_link_address=0x50000000,
        kernel_options={
            "KernelPlatform": "maaxboard",
            "KernelIsMCS": True,
            "KernelArmExportPCNTUser": True,
            "KernelArmHypervisorSupport": True,
            "KernelArmVtimerUpdateVOffset": False,
        },
        examples={
            "hello": Path("example/maaxboard/hello")
        }
    ),
    BoardInfo(
        name="imx8mm_evk",
        arch=KernelArch.AARCH64,
        gcc_cpu="cortex-a53",
        loader_link_address=0x41000000,
        kernel_options={
            "KernelPlatform": "imx8mm-evk",
            "KernelIsMCS": True,
            "KernelArmExportPCNTUser": True,
            "KernelArmHypervisorSupport": True,
            "KernelArmVtimerUpdateVOffset": False,
        },
        examples={
            "passive_server": Path("example/imx8mm_evk/passive_server")
        }
    ),
    BoardInfo(
        name="imx8mp_evk",
        arch=KernelArch.AARCH64,
        gcc_cpu="cortex-a53",
        loader_link_address=0x41000000,
        kernel_options={
            "KernelPlatform": "imx8mp-evk",
            "KernelIsMCS": True,
            "KernelArmExportPCNTUser": True,
            "KernelArmHypervisorSupport": True,
            "KernelArmVtimerUpdateVOffset": False,
        },
        examples={
            "hello": Path("example/imx8mp_evk/hello")
        }
    ),
    BoardInfo(
        name="imx8mq_evk",
        arch=KernelArch.AARCH64,
        gcc_cpu="cortex-a53",
        loader_link_address=0x41000000,
        kernel_options={
            "KernelPlatform": "imx8mq-evk",
            "KernelIsMCS": True,
            "KernelArmExportPCNTUser": True,
            "KernelArmHypervisorSupport": True,
            "KernelArmVtimerUpdateVOffset": False,
        },
        examples={
            "hello": Path("example/imx8mq_evk/hello")
        }
    ),
    BoardInfo(
        name="odroidc2",
        arch=KernelArch.AARCH64,
        gcc_cpu="cortex-a53",
        loader_link_address=0x20000000,
        kernel_options={
            "KernelPlatform": "odroidc2",
            "KernelIsMCS": True,
            "KernelArmExportPCNTUser": True,
            "KernelArmHypervisorSupport": True,
            "KernelArmVtimerUpdateVOffset": False,
        },
        examples={
            "hello": Path("example/odroidc2/hello")
        }
    ),
    BoardInfo(
        name="odroidc4",
        arch=KernelArch.AARCH64,
        gcc_cpu="cortex-a55",
        loader_link_address=0x20000000,
        kernel_options={
            "KernelPlatform": "odroidc4",
            "KernelIsMCS": True,
            "KernelArmExportPCNTUser": True,
            "KernelArmHypervisorSupport": True,
            "KernelArmVtimerUpdateVOffset": False,
        },
        examples={
            "timer": Path("example/odroidc4/timer")
        }
    ),
    BoardInfo(
        name="qemu_virt_aarch64",
        arch=KernelArch.AARCH64,
        gcc_cpu="cortex-a53",
        loader_link_address=0x70000000,
        kernel_options={
            "KernelPlatform": "qemu-arm-virt",
            "KernelIsMCS": True,
            "KernelArmExportPCNTUser": True,
            "QEMU_MEMORY": "2048",
            "KernelArmHypervisorSupport": True,
            "KernelArmExportPCNTUser": True,
            "KernelArmExportPTMRUser": True,
            "KernelArmVtimerUpdateVOffset": False,
        },
        examples={
            "hello": Path("example/qemu_virt_aarch64/hello"),
            "hierarchy": Path("example/qemu_virt_aarch64/hierarchy")
        }
    ),
    BoardInfo(
        name="qemu_virt_riscv64",
        arch=KernelArch.RISCV64,
        gcc_cpu=None,
        loader_link_address=0x80200000,
        kernel_options={
            "KernelPlatform": "qemu-riscv-virt",
            "KernelIsMCS": True,
            "QEMU_MEMORY": "2048",
            "KernelRiscvExtD": True,
            "KernelRiscvExtF": True,
        },
        examples={
            "hello": Path("example/qemu_virt_riscv64/hello"),
        }
    ),
    BoardInfo(
        name="rockpro64",
        arch=KernelArch.AARCH64,
        gcc_cpu="cortex-a53",
        loader_link_address=0x30000000,
        kernel_options={
            "KernelPlatform": "rockpro64",
            "KernelIsMCS": True,
            "KernelArmExportPCNTUser": True,
            "KernelArmHypervisorSupport": True,
            "KernelArmVtimerUpdateVOffset": False,
        },
        examples={
            "hello": Path("example/rockpro64/hello")
        }
    ),
    BoardInfo(
        name="star64",
        arch=KernelArch.RISCV64,
        gcc_cpu=None,
        loader_link_address=0x60000000,
        kernel_options={
            "KernelIsMCS": True,
            "KernelPlatform": "star64",
            "KernelRiscvExtD": True,
            "KernelRiscvExtF": True,
        },
        examples={
            "hello": Path("example/star64/hello")
        }
    ),
)

SUPPORTED_CONFIGS = (
    ConfigInfo(
        name="release",
        debug=False,
        kernel_options={},
    ),
    ConfigInfo(
        name="debug",
        debug=True,
        kernel_options={
            "KernelDebugBuild": True,
            "KernelPrinting": True,
            "KernelVerificationBuild": False
        }
    ),
    ConfigInfo(
        name="benchmark",
        debug=False,
        kernel_options={
            "KernelArmExportPMUUser": True,
            "KernelDebugBuild": False,
            "KernelVerificationBuild": False,
            "KernelBenchmarks": "track_utilisation"
        },
    ),
)


def tar_filter(tarinfo: TarInfo) -> TarInfo:
    """This is used to change the tarinfo when created the .tar.gz archive.

    This ensures the tar file does not leak information from the build environment.
    """
    # Force uid/gid
    tarinfo.uid = tarinfo.gid = 0
    tarinfo.uname = tarinfo.gname = "microkit"
    # This is unlikely to be set, but force it anyway
    tarinfo.pax_headers = {}
    tarinfo.mtime = MICROKIT_EPOCH
    assert tarinfo.isfile() or tarinfo.isdir()
    # Set the permissions properly
    if tarinfo.isdir():
        tarinfo.mode = tarinfo.mode & ~0o777 | 0o744
    if tarinfo.isfile():
        if "/bin/" in tarinfo.name:
            # Assume everything in bin should be executable.
            tarinfo.mode = tarinfo.mode & ~0o777 | 0o755
        else:
            tarinfo.mode = tarinfo.mode & ~0o777 | 0o644
    return tarinfo


def get_tool_target_triple() -> str:
    host_system = host_platform.system()
    if host_system == "Linux":
        return "x86_64-unknown-linux-musl"
    elif host_system == "Darwin":
        host_arch = host_platform.machine()
        if host_arch == "x86_64":
            return "x86_64-apple-darwin"
        elif host_arch == "arm64":
            return "aarch64-apple-darwin"
        else:
            raise Exception(f"Unexpected Darwin architecture: {host_arch}")
    else:
        raise Exception(f"The platform \"{host_system}\" is not supported")


def test_tool() -> None:
    r = system(
        f"cd tool/microkit && cargo test"
    )
    assert r == 0


def build_tool(tool_target: Path, target_triple: str) -> None:
    r = system(
        f"cd tool/microkit && cargo build --release --target {target_triple}"
    )
    assert r == 0

    tool_output = f"./tool/microkit/target/{target_triple}/release/microkit"

    copy(tool_output, tool_target)

    tool_target.chmod(0o755)


def build_sel4(
    sel4_dir: Path,
    root_dir: Path,
    build_dir: Path,
    board: BoardInfo,
    config: ConfigInfo,
) -> Dict[str, Any]:
    """Build seL4"""
    build_dir = build_dir / board.name / config.name / "sel4"
    build_dir.mkdir(exist_ok=True, parents=True)

    sel4_install_dir = build_dir / "install"
    sel4_build_dir = build_dir / "build"

    sel4_install_dir.mkdir(exist_ok=True, parents=True)
    sel4_build_dir.mkdir(exist_ok=True, parents=True)

    print(f"Building sel4: {sel4_dir=} {root_dir=} {build_dir=} {board=} {config=}")

    config_args = list(board.kernel_options.items()) + list(config.kernel_options.items())
    config_strs = []
    for arg, val in sorted(config_args):
        if isinstance(val, bool):
            str_val = "ON" if val else "OFF"
        else:
            str_val = str(val)
        s = f"-D{arg}={str_val}"
        config_strs.append(s)
    config_str = " ".join(config_strs)

    toolchain = f"{board.arch.c_toolchain()}-"
    cmd = (
        f"cmake -GNinja -DCMAKE_INSTALL_PREFIX={sel4_install_dir.absolute()} "
        f" -DPYTHON3={executable} "
        f" -DCROSS_COMPILER_PREFIX={toolchain}"
        f" {config_str} "
        f"-S {sel4_dir.absolute()} -B {sel4_build_dir.absolute()}")

    r = system(cmd)
    if r != 0:
        raise Exception(f"Error configuring sel4: cmd={cmd}")

    cmd = f"cmake --build {sel4_build_dir.absolute()}"
    r = system(cmd)
    if r != 0:
        raise Exception(f"Error building sel4: cmd={cmd}")

    cmd = f"cmake --install {sel4_build_dir.absolute()}"
    r = system(cmd)
    if r != 0:
        raise Exception(f"Error installing sel4: cmd={cmd}")

    elf = sel4_install_dir / "bin" / "kernel.elf"
    dest = (
        root_dir / "board" / board.name / config.name / "elf" / "sel4.elf"
    )
    dest.unlink(missing_ok=True)
    copy(elf, dest)
    # Make output read-only
    dest.chmod(0o744)

    invocations_all = sel4_build_dir / "generated" / "invocations_all.json"
    dest = (root_dir / "board" / board.name / config.name / "invocations_all.json")
    dest.unlink(missing_ok=True)
    copy(invocations_all, dest)
    dest.chmod(0o744)

    include_dir = root_dir / "board" / board.name / config.name / "include"
    for source in ("kernel_Config", "libsel4", "libsel4/sel4_Config", "libsel4/autoconf"):
        source_dir = sel4_install_dir / source / "include"
        for p in source_dir.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(source_dir)
            dest = include_dir / rel
            dest.parent.mkdir(exist_ok=True, parents=True)
            dest.unlink(missing_ok=True)
            copy(p, dest)
            dest.chmod(0o744)

    gen_config_path = sel4_install_dir / "libsel4/include/kernel/gen_config.json"
    with open(gen_config_path, "r") as f:
        gen_config = json.load(f)
        return gen_config


def build_elf_component(
    component_name: str,
    root_dir: Path,
    build_dir: Path,
    board: BoardInfo,
    config: ConfigInfo,
    defines: List[Tuple[str, str]]
) -> None:
    """Build a specific ELF component.

    Right now this is either the loader or the monitor
    """
    sel4_dir = root_dir / "board" / board.name / config.name
    build_dir = build_dir / board.name / config.name / component_name
    build_dir.mkdir(exist_ok=True, parents=True)
    toolchain = f"{board.arch.c_toolchain()}-"
    defines_str = " ".join(f"{k}={v}" for k, v in defines)
    defines_str += f" ARCH={board.arch.to_str()} BOARD={board.name} BUILD_DIR={build_dir.absolute()} SEL4_SDK={sel4_dir.absolute()} TOOLCHAIN={toolchain}"

    if board.gcc_cpu is not None:
        defines_str += f" GCC_CPU={board.gcc_cpu}"

    r = system(
        f"{defines_str} make -C {component_name}"
    )
    if r != 0:
        raise Exception(
            f"Error building: {component_name} for board: {board.name} config: {config.name}"
        )
    elf = build_dir / f"{component_name}.elf"
    dest = (
        root_dir / "board" / board.name / config.name / "elf" / f"{component_name}.elf"
    )
    dest.unlink(missing_ok=True)
    copy(elf, dest)
    # Make output read-only
    dest.chmod(0o744)


def build_doc(root_dir: Path):
    output = root_dir / "doc" / "microkit_user_manual.pdf"

    environ["TEXINPUTS"] = "docs/style:"
    r = system(f'pandoc docs/manual.md -o {output}')
    assert r == 0


def build_lib_component(
    component_name: str,
    root_dir: Path,
    build_dir: Path,
    board: BoardInfo,
    config: ConfigInfo,
) -> None:
    """Build a specific library component.

    Right now this is just libsel4.a
    """
    sel4_dir = root_dir / "board" / board.name / config.name
    build_dir = build_dir / board.name / config.name / component_name
    build_dir.mkdir(exist_ok=True, parents=True)

    toolchain = f"{board.arch.c_toolchain()}-"
    defines_str = f" ARCH={board.arch.to_str()} BUILD_DIR={build_dir.absolute()} SEL4_SDK={sel4_dir.absolute()} TOOLCHAIN={toolchain}"

    if board.gcc_cpu is not None:
        defines_str += f" GCC_CPU={board.gcc_cpu}"

    r = system(
        f"{defines_str} make -C {component_name}"
    )
    if r != 0:
        raise Exception(
            f"Error building: {component_name} for board: {board.name} config: {config.name}"
        )
    lib = build_dir / f"{component_name}.a"
    lib_dir = root_dir / "board" / board.name / config.name / "lib"
    dest = lib_dir / f"{component_name}.a"
    dest.unlink(missing_ok=True)
    copy(lib, dest)
    # Make output read-only
    dest.chmod(0o744)

    link_script = Path(component_name) / "microkit.ld"
    dest = lib_dir / "microkit.ld"
    dest.unlink(missing_ok=True)
    copy(link_script, dest)
    # Make output read-only
    dest.chmod(0o744)

    include_dir = root_dir / "board" / board.name / config.name / "include"
    source_dir = Path(component_name) / "include"
    for p in source_dir.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(source_dir)
        dest = include_dir / rel
        dest.parent.mkdir(exist_ok=True, parents=True)
        dest.unlink(missing_ok=True)
        copy(p, dest)
        dest.chmod(0o744)


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--sel4", type=Path, required=True)
    parser.add_argument("--tool-target-triple", default=get_tool_target_triple(), help="Compile the Microkit tool for this target triple")
    parser.add_argument("--boards", metavar="BOARDS", help="Comma-separated list of boards to support. When absent, all boards are supported.")
    parser.add_argument("--configs", metavar="CONFIGS", help="Comma-separated list of configurations to support. When absent, all configurations are supported.")
    parser.add_argument("--skip-tool", action="store_true", help="Tool will not be built")
    parser.add_argument("--skip-sel4", action="store_true", help="seL4 will not be built")
    parser.add_argument("--skip-docs", action="store_true", help="Docs will not be built")
    parser.add_argument("--skip-tar", action="store_true", help="SDK and source tarballs will not be built")
    parser.add_argument("--version", default=VERSION, help="SDK version")
    for arch in KernelArch:
        arch_str = arch.name.lower()
        parser.add_argument(f"--toolchain-prefix-{arch_str}", default=arch.c_toolchain(), help=f"C toolchain prefix when compiling for {arch_str}, e.g {arch_str}-none-elf")

    args = parser.parse_args()

    global TOOLCHAIN_AARCH64
    global TOOLCHAIN_RISCV
    TOOLCHAIN_AARCH64 = args.toolchain_prefix_aarch64
    TOOLCHAIN_RISCV = args.toolchain_prefix_riscv64

    version = args.version

    if args.boards is not None:
        supported_board_names = frozenset(board.name for board in SUPPORTED_BOARDS)
        selected_board_names = frozenset(args.boards.split(","))
        for board_name in selected_board_names:
            if board_name not in supported_board_names:
                raise Exception(f"Trying to build a board: {board_name} that does not exist in supported list.")
        selected_boards = [board for board in SUPPORTED_BOARDS if board.name in selected_board_names]
    else:
        selected_boards = SUPPORTED_BOARDS

    if args.configs is not None:
        supported_config_names = frozenset(config.name for config in SUPPORTED_CONFIGS)
        selected_config_names = frozenset(args.configs.split(","))
        for config_name in selected_config_names:
            if config_name not in supported_config_names:
                raise Exception(f"Trying to build a configuration: {config_name} that does not exist in supported list.")
        selected_configs = [config for config in SUPPORTED_CONFIGS if config.name in selected_config_names]
    else:
        selected_configs = SUPPORTED_CONFIGS

    sel4_dir = args.sel4.expanduser()
    if not sel4_dir.exists():
        raise Exception(f"sel4_dir: {sel4_dir} does not exist")

    root_dir = Path("release") / f"{NAME}-sdk-{version}"
    tar_file = Path("release") / f"{NAME}-sdk-{version}.tar.gz"
    source_tar_file = Path("release") / f"{NAME}-source-{version}.tar.gz"
    dir_structure = [
        root_dir / "bin",
        root_dir / "board",
    ]
    if not args.skip_docs:
        dir_structure.append(root_dir / "doc")
    for board in selected_boards:
        board_dir = root_dir / "board" / board.name
        dir_structure.append(board_dir)
        for config in selected_configs:
            config_dir = board_dir / config.name
            dir_structure.append(config_dir)
            dir_structure += [
                config_dir / "include",
                config_dir / "lib",
                config_dir / "elf",
            ]

    for dr in dir_structure:
        dr.mkdir(exist_ok=True, parents=True)

    copy(Path("LICENSE.md"), root_dir)
    licenses_dir = Path("LICENSES")
    licenses_dest_dir = root_dir / "LICENSES"
    for p in licenses_dir.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(licenses_dir)
        dest = licenses_dest_dir / rel
        dest.parent.mkdir(exist_ok=True, parents=True)
        dest.unlink(missing_ok=True)
        copy(p, dest)
        dest.chmod(0o744)

    if not args.skip_tool:
        tool_target = root_dir / "bin" / "microkit"
        test_tool()
        build_tool(tool_target, args.tool_target_triple)

    if not args.skip_docs:
        build_doc(root_dir)

    build_dir = Path("build")
    for board in selected_boards:
        for config in selected_configs:
            if not args.skip_sel4:
                sel4_gen_config = build_sel4(sel4_dir, root_dir, build_dir, board, config)
            loader_printing = 1 if config.name == "debug" else 0
            loader_defines = [
                ("LINK_ADDRESS", hex(board.loader_link_address)),
                ("PRINTING", loader_printing)
            ]
            # There are some architecture dependent configuration options that the loader
            # needs to know about, so we figure that out here
            if board.arch.is_riscv():
                loader_defines.append(("FIRST_HART_ID", sel4_gen_config["FIRST_HART_ID"]))
            if board.arch.is_arm():
                if sel4_gen_config["ARM_PA_SIZE_BITS_40"]:
                    arm_pa_size_bits = 40
                elif sel4_gen_config["ARM_PA_SIZE_BITS_44"]:
                    arm_pa_size_bits = 44
                else:
                    raise Exception("Unexpected ARM physical address bits defines")
                loader_defines.append(("PHYSICAL_ADDRESS_BITS", arm_pa_size_bits))

            build_elf_component("loader", root_dir, build_dir, board, config, loader_defines)
            build_elf_component("monitor", root_dir, build_dir, board, config, [])
            build_lib_component("libmicrokit", root_dir, build_dir, board, config)
        # Setup the examples
        for example, example_path in board.examples.items():
            include_dir = root_dir / "board" / board.name / "example" / example
            source_dir = example_path
            for p in source_dir.rglob("*"):
                if not p.is_file():
                    continue
                rel = p.relative_to(source_dir)
                dest = include_dir / rel
                dest.parent.mkdir(exist_ok=True, parents=True)
                dest.unlink(missing_ok=True)
                copy(p, dest)
                dest.chmod(0o744)

    if not args.skip_tar:
        # At this point we create a tar.gz file
        with tar_open(tar_file, "w:gz") as tar:
            tar.add(root_dir, arcname=root_dir.name, filter=tar_filter)

        # Build the source tar
        process = popen("git ls-files")
        filenames = [Path(fn.strip()) for fn in process.readlines()]
        process.close()
        source_prefix = Path(f"{NAME}-source-{version}")
        with tar_open(source_tar_file, "w:gz") as tar:
            for filename in filenames:
                tar.add(filename, arcname=source_prefix / filename, filter=tar_filter)


if __name__ == "__main__":
    main()
