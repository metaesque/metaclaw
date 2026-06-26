#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# ANSI Terminal Colors
RED = '\033[91m'
GREEN = '\033[92m'
ORANGE = '\033[38;5;208m'
CYAN = '\033[96m'
RESET = '\033[0m'

def get_manifest_files(manifest_path):
    """Reads a MANIFEST.files document and returns a list of tracked relative paths."""
    files = []
    if not os.path.exists(manifest_path):
        return files
    with open(manifest_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                files.append(line)
    return files

def do_push(live_dir, staging_dir, dry_run):
    """Archives existing staging, deletes it, and mirrors live tracked files to a fresh staging dir."""
    load_dotenv(os.path.join(live_dir, '.env'))
    ext_drive = os.environ.get('EXTERNAL_DRIVE_PATH')
    if not ext_drive:
        print(f"{RED}FATAL: EXTERNAL_DRIVE_PATH not defined in .env{RESET}")
        sys.exit(1)

    archive_base = os.path.join(ext_drive, 'metaclaw-archive')

    if os.path.exists(staging_dir):
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        archive_dir = os.path.join(archive_base, timestamp)
        print(f"{CYAN}Archiving existing staging directory to {archive_dir}...{RESET}")
        if not dry_run:
            os.makedirs(archive_dir, exist_ok=True)
            shutil.copytree(staging_dir, os.path.join(archive_dir, 'metaclaw'), dirs_exist_ok=True)

        print(f"{RED}Deleting existing staging directory at {staging_dir}...{RESET}")
        if not dry_run:
            shutil.rmtree(staging_dir)

    print(f"{GREEN}Copying tracked files from live environment to staging...{RESET}")
    manifest_path = os.path.join(live_dir, 'docs', 'MANIFEST.files')
    tracked_files = get_manifest_files(manifest_path)

    for rel_path in tracked_files:
        live_file = os.path.join(live_dir, rel_path)
        staging_file = os.path.join(staging_dir, rel_path)

        if os.path.exists(live_file):
            if not dry_run:
                os.makedirs(os.path.dirname(staging_file), exist_ok=True)
                shutil.copy2(live_file, staging_file)
        else:
            print(f"{ORANGE}Warning: Tracked file {rel_path} missing in live dir.{RESET}")

    staging_env_json = os.path.join(staging_dir, '.env.json')
    print(f"{GREEN}Generating staging .env.json...{RESET}")
    if not dry_run:
        os.makedirs(staging_dir, exist_ok=True)
        with open(staging_env_json, 'w') as f:
            f.write(f'{{\n  "OPENCLAW_ROOT": "{staging_dir}",\n  "EXTERNAL_DRIVE_PATH": "{ext_drive}/staging"\n}}\n')

        print(f"{CYAN}Hydrating staging environment symlinks...{RESET}")
        # Run `make setup` in the staging dir to populate orchestrator routing links
        subprocess.run(['make', 'setup'], cwd=staging_dir)

    print(f"{GREEN}Push complete.{RESET}")

def do_pull(live_dir, staging_dir, dry_run):
    """Compares staging to live and interactively pulls changes down to the host."""
    if not os.path.exists(staging_dir):
        print(f"{RED}FATAL: Staging directory not found at {staging_dir}{RESET}")
        sys.exit(1)

    staging_manifest = os.path.join(staging_dir, 'docs', 'MANIFEST.files')
    live_manifest = os.path.join(live_dir, 'docs', 'MANIFEST.files')

    all_tracked_files = set(get_manifest_files(staging_manifest) + get_manifest_files(live_manifest))

    new_in_staging = []
    deleted_in_staging = []
    modified_files = []

    print(f"{CYAN}Analyzing delta between Live and Staging environments...{RESET}")

    for rel_path in sorted(all_tracked_files):
        live_path = os.path.join(live_dir, rel_path)
        staging_path = os.path.join(staging_dir, rel_path)

        live_exists = os.path.exists(live_path)
        staging_exists = os.path.exists(staging_path)

        if staging_exists and not live_exists:
            new_in_staging.append(rel_path)
        elif live_exists and not staging_exists:
            deleted_in_staging.append(rel_path)
        elif live_exists and staging_exists:
            with open(live_path, 'r') as f1, open(staging_path, 'r') as f2:
                if f1.read() != f2.read():
                    modified_files.append(rel_path)

    if not any([new_in_staging, deleted_in_staging, modified_files]):
        print(f"{GREEN}Live and staging environments are identical. Nothing to apply.{RESET}")
        sys.exit(0)

    print(f"Found {ORANGE}{len(new_in_staging)} new files{RESET}, {RED}{len(deleted_in_staging)} deleted files{RESET}, and {CYAN}{len(modified_files)} modified files{RESET}.")

    # Process Modifications
    for rel_path in modified_files:
        live_path = os.path.join(live_dir, rel_path)
        staging_path = os.path.join(staging_dir, rel_path)

        print(f"\n{CYAN}================================================================================{RESET}")
        print(f"{CYAN}MODIFIED: {rel_path}{RESET}")
        print(f"{CYAN}================================================================================{RESET}")

        try:
            subprocess.run([
                'diff',
                '--width=160',
                '--suppress-common-lines',
                '-y',
                live_path,
                staging_path
            ])
        except FileNotFoundError:
            print(f"{RED}Error: Native 'diff' utility not found on host system.{RESET}")

        if not dry_run:
            resp = input(f"\n{ORANGE}Overwrite live {rel_path} with staging version? [y/N]: {RESET}")
            if resp.lower() in ['y', 'yes']:
                shutil.copy2(staging_path, live_path)
                print(f"{GREEN}Applied {rel_path}.{RESET}")
            else:
                print("Skipped.")
        else:
            print(f"\n{ORANGE}[DRY RUN] Would prompt to overwrite live {rel_path}.{RESET}")

    # Process Additions
    for rel_path in new_in_staging:
        staging_path = os.path.join(staging_dir, rel_path)
        live_path = os.path.join(live_dir, rel_path)
        print(f"\n{GREEN}================================================================================{RESET}")
        print(f"{GREEN}NEW FILE: {rel_path}{RESET}")
        print(f"{GREEN}================================================================================{RESET}")

        if not dry_run:
            resp = input(f"{ORANGE}Copy new file {rel_path} to live environment? [y/N]: {RESET}")
            if resp.lower() in ['y', 'yes']:
                os.makedirs(os.path.dirname(live_path), exist_ok=True)
                shutil.copy2(staging_path, live_path)
                print(f"{GREEN}Copied {rel_path}.{RESET}")
            else:
                print("Skipped.")
        else:
            print(f"{ORANGE}[DRY RUN] Would prompt to copy {rel_path}.{RESET}")

    # Process Deletions
    for rel_path in deleted_in_staging:
        live_path = os.path.join(live_dir, rel_path)
        print(f"\n{RED}================================================================================{RESET}")
        print(f"{RED}DELETED FILE: {rel_path}{RESET}")
        print(f"{RED}================================================================================{RESET}")

        if not dry_run:
            resp = input(f"{ORANGE}File was removed in staging. Delete from live environment? [y/N]: {RESET}")
            if resp.lower() in ['y', 'yes']:
                os.remove(live_path)
                print(f"{GREEN}Deleted {rel_path}.{RESET}")
            else:
                print("Skipped.")
        else:
            print(f"{ORANGE}[DRY RUN] Would prompt to delete {rel_path}.{RESET}")

    print(f"\n{GREEN}Pull process complete.{RESET}")

def main():
    parser = argparse.ArgumentParser(description="Synchronize MetaClaw live and staging environments.")
    parser.add_argument('-n', '--dryrun', action='store_true', help="Do not execute any filesystem operations.")
    parser.add_argument('-s', '--stage', '--push', dest='push', action='store_true', help="Push live codebase to staging directory.")
    parser.add_argument('--pull', action='store_true', help="Pull staging changes into live environment. Default action.")

    args = parser.parse_args()

    bin_dir = os.path.dirname(os.path.abspath(__file__))
    live_dir = os.path.dirname(bin_dir)
    staging_dir = os.path.join(live_dir, 'workspace', 'src', 'metaclaw')

    if args.dryrun:
        print(f"{ORANGE}*** DRY RUN MODE ACTIVE - No files will be modified ***{RESET}\n")

    if args.push:
        do_push(live_dir, staging_dir, args.dryrun)
    else:
        do_pull(live_dir, staging_dir, args.dryrun)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{RED}Process aborted by user.{RESET}")
        sys.exit(1)
