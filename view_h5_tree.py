import argparse
import h5py
import numpy as np


def generate_tree_hdf5(hdf5_path, display_metadata=False, truncate_large_folders=False):
    """
    Generate a tree-like representation of the HDF5 file structure.

    Args:
        hdf5_path (str): The path to the HDF5 file.
        display_metadata (bool): Flag to display metadata information.
        truncate_large_folders (bool): Flag to truncate large folders.

    """
    def _print_tree(node, indent="", last=True):
        if isinstance(node, h5py.File):
            name = node.filename
            print(f"{indent}{name}")
            children = [_ for _ in node.values()]
            for i, child in enumerate(children):
                _print_tree(child, indent="", last=(i == len(children) - 1))
        else:
            name = node.name.split("/")[-1]
            if isinstance(node, h5py.Dataset):
                shape = str(node.shape)
                if node.attrs:
                    attrs = " [ATTRS]"
                else:
                    attrs = ""
                if last:
                    print(f"{indent}┗━━ {name} {shape}{attrs}")
                else:
                    print(f"{indent}┣━━ {name} {shape}{attrs}")
                if display_metadata:
                    for key, val in list(node.attrs.items()):
                        if isinstance(val, h5py.Reference):
                            value = h5py.h5r.get_name(val, node.id).decode("utf-8")
                            ref_char = ">"
                        else:
                            value = val
                            ref_char = "─"
                        connector = (
                            f"└─{ref_char}"
                            if key == list(node.attrs.items())[-1][0]
                            else f"├─{ref_char}"
                        )
                        print(
                            f"{indent}{'┃' if not last else ''}   {connector} {key}:"
                            f" {value}"
                        )
            else:
                if node.attrs:
                    attrs = " [ATTRS]"
                else:
                    attrs = ""
                if last:
                    print(f"{indent}┗━━ {name}{attrs}")
                else:
                    print(f"{indent}┣━━ {name}{attrs}")
                if display_metadata:
                    for key, val in list(node.attrs.items()):
                        if isinstance(val, h5py.Reference):
                            value = h5py.h5r.get_name(val, node.id).decode("utf-8")
                            ref_char = ">"
                        else:
                            value = val
                            ref_char = "─"
                        connector = (
                            f"└─{ref_char}"
                            if key == list(node.attrs.items())[-1][0]
                            else f"├─{ref_char}"
                        )
                        print(
                            f"{indent}{'┃' if not last else ''}   {connector} {key}:"
                            f" {value}"
                        )
                children = [_ for _ in node.values()]
                if truncate_large_folders and len(children) > 10:
                    children = children[:10]
                    print(f"{indent}{'┃' if not last else ''}   ... (truncated)")
                for i, child in enumerate(children):
                    _print_tree(
                        child,
                        indent=(indent + ("    " if last else "┃   ")),
                        last=(i == len(children) - 1),
                    )

    with h5py.File(f"{hdf5_path}.h5", "r") as f:
        _print_tree(f)


def main():
    parser = argparse.ArgumentParser(description="HDF5 Tree Generator")
    parser.add_argument("hdf5_path", type=str, help="Path to the HDF5 file")
    parser.add_argument(
        "--display-metadata",
        action="store_true",
        help="Display metadata information",
    )
    parser.add_argument(
        "--truncate-large-folders",
        action="store_true",
        help="Truncate large folders after a certain amount of entries",
    )
    args = parser.parse_args()

    generate_tree_hdf5(
        args.hdf5_path,
        display_metadata=args.display_metadata,
        truncate_large_folders=args.truncate_large_folders,
    )


if __name__ == "__main__":
    main()

