import os
import argparse
import subprocess
import sys

sys.path.append("scripts/libs")
from configdeode import ConfigDeode


def main():
    parser = argparse.ArgumentParser(
        description=(
            "automation of the main.sh for integration into the deode ",
            "workflow"
        )
    )
    parser.add_argument(
        "--config_file", type=str, help="deode configuration file [.toml]")
    parser.add_argument(
        "--obs", type=str, default="IMERG_pcp",
        help="OBS argument (default: IMERG_pcp)"
    )
    parser.add_argument(
        "--case", type=str, help="Case argument"
    )
    parser.add_argument(
        "--exp", type=str, help="exp argument"
    )
    parser.add_argument(
        "--relative_indexed_path", type=str, default="", help="relative path to store config files and outputs"
    )
    parser.add_argument(
        "--exp_ref", type=str,
        help="reference experiment to be compared with"
    )
    parser.add_argument(
        "--link_obs", action="store_true", help="Launch link_obs.py"
    )
    parser.add_argument(
        "--run_regrid", action="store_true", help="Launch regrid.py"
    )
    parser.add_argument(
        "--run_plot_regrid", action="store_true", help="Launch plot_regrid.py"
    )
    parser.add_argument(
        "--run_verif", action="store_true", help="Launch verification.py"
    )
    parser.add_argument(
        "--run_panels", action="store_true", help="Launch create_panels.py"
    )
    parser.add_argument(
        "--run_comparison", action="store_true",
        help="Launch comparison scripts"
    )
    parser.add_argument(
        "--replace_outputs", action="store_true", help=(
            "The new outputs will replace those that may exist previously. "
            "Only plot_regrid and verification tasks are affected."
        )
    )

    args = parser.parse_args()

    if args.config_file:
        if os.path.exists(args.config_file):
            config_deode = ConfigDeode(
                config_toml=args.config_file,
                yaml_exp_template="config/templates/config_exp.yaml",
                yaml_case_template="config/templates/config_Case.yaml"
            )
            exp = config_deode.write_config_exp()
            if args.case:
                case = args.case
            else:
                case = config_deode.write_config_case()
        else:
            print(f"ERROR: Configuration file {args.config_file} not found")
            sys.exit(1)
    else:
        if not args.case or not args.exp:
            print(
                "ERROR: You must set case and exp arguments if no " \
                + "config_file is specified"
            )
            sys.exit(1)
        exp = args.exp
        case = args.case

    if args.replace_outputs:
        replace = "True"
    else:
        replace = "False"
    print("running set environment now")
    subprocess.run([
        "python3", "scripts/verification/set_environment.py",
        args.obs, case, exp, args.relative_indexed_path
    ])

    if args.link_obs:
        subprocess.run([
            "python3", "scripts/verification/link_obs.py",
            args.obs, case, args.relative_indexed_path
        ])
    if args.run_regrid:
        subprocess.run([
            "python3", "scripts/verification/regrid.py",
            args.obs, case, exp, args.relative_indexed_path
        ])
    if args.run_plot_regrid:
        subprocess.run([
            "python3", "scripts/utils/plot_regrid.py",
            args.obs, case, exp, args.relative_indexed_path, replace
        ])
    if args.run_verif:
        subprocess.run([
            "python3", "scripts/verification/verification.py",
            args.obs, case, exp, args.relative_indexed_path, replace
        ])
    if args.run_panels:
        subprocess.run([
            "python3", "scripts/utils/create_panels.py",
            args.obs, case, exp, args.relative_indexed_path
        ])
    if args.run_comparison and args.exp_ref:
        subprocess.run([
            'python3', 'scripts/verification/compExps_metrics.py',
            args.obs, case, f"{args.exp_ref}-VS-{exp}", args.relative_indexed_path
        ])
        subprocess.run([
            'python3', 'scripts/verification/compExps_maps.py',
            args.obs, case, f"{args.exp_ref}-VS-{exp}", args.relative_indexed_path
        ])


if __name__ == '__main__':
    main()
