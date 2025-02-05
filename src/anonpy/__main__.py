#!/usr/bin/env python3

import json
import sys
from argparse import Namespace
from pathlib import Path

from colorama import Fore, Style, deinit, just_fix_windows_console
from requests.exceptions import HTTPError

from .anonpy import AnonPy
from .cli import build_parser
from .internals import ConfigHandler, RequestHandler, __credits__, __package__, __version__, get_resource_path, read_file, str2bool
from .providers import PixelDrain
from .security import Checksum, MD5

#region commands

def preview(anon: AnonPy, args: Namespace) -> None:
    for resource in args.resource:
        preview = anon.preview(resource)
        print(json.dumps(preview, indent=4) if args.verbose else ",".join(preview.values()))

def upload(anon: AnonPy, args: Namespace) -> None:
    for file in args.file:
        anon.upload(file, progressbar=args.verbose)

        if not args.verbose: continue
        md5 = Checksum.compute(file, MD5)
        print(f"md5\t{Checksum.hash2string(md5)}")

def download(anon: AnonPy, args: Namespace) -> None:
    for resource in (args.resource or read_file(args.batch_file)):
        preview = anon.preview(resource)
        file = preview.get("name")

        if args.check and file is not None and Path(file).exists():
            print(f"Warning: A file with the same name already exists in {str(args.path)!r}.")
            prompt = input("Proceed with download? [Y/n] ")
            if not str2bool(prompt): continue

        anon.download(resource, args.path, progressbar=args.verbose)

        if not args.verbose: continue
        md5 = Checksum.compute(file, MD5)
        print(f"file\t{file}")
        print(f"md5\t{Checksum.hash2string(md5)}")

#endregion

def main() -> None:
    # enable Windows' built-in ANSI support
    just_fix_windows_console()

    description = f"{Fore.WHITE}{Style.DIM}Command line interface for anonymous file sharing.{Style.RESET_ALL}"
    epilog = f"{Fore.WHITE}{Style.DIM}Authors: {','.join(__credits__)}{Style.RESET_ALL}"

    parser = build_parser(__package__, __version__, description, epilog)
    args = parser.parse_args()

    kwargs = {
        "user_agent": RequestHandler.build_user_agent(__package__, __version__),
        "enable_logging": args.logging,
    }

    try:
        log_file = "cli.log"
        module_folder = get_resource_path(__package__)
        # NOTE: Uses the PixelDrain provider by default for now
        provider = PixelDrain(**kwargs)
        provider.logger \
            .set_base_path(module_folder) \
            .add_handler(log_file)

        match args.command:
            case "preview":
                preview(provider, args)
            case "upload":
                upload(provider, args)
            case "download":
                download(provider, args)
            case _:
                raise NotImplementedError()

    except KeyboardInterrupt:
        pass
    except NotImplementedError:
        parser.print_help()
    except HTTPError as http_error:
        print(http_error.response.text, file=sys.stderr)
    except Exception as exception:
        print(exception, file=sys.stderr)
    except:
        print("\n".join([
            "An unhandled exception was thrown. The log file may give you more",
            f"insight into what went wrong: {module_folder!r}.\nAlternatively, file",
            "a bug report on GitHub at https://github.com/advanced-systems/anonpy."
        ]), file=sys.stderr)
    finally:
        deinit()
        provider.logger.shutdown()

if __name__ == "__main__":
    main()
