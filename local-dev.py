import argparse
import sys
from utils.local_dev_setup import LocalDevSetup

def main():
    """
    Main function to run the local development setup wizard.
    """
    parser = argparse.ArgumentParser(
        description="Suna Local Development Setup Wizard.",
        epilog="""
Examples:
  python local-dev.py
    - Run the interactive setup wizard.

  python local-dev.py --skip-optional
    - Run the setup wizard without prompting for optional services.

  python local-dev.py --reset
    - Run the setup wizard and overwrite existing .env files.
""",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--skip-optional',
        action='store_true',
        help='Skip prompts for optional services like Search and Daytona.'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Backup and overwrite existing .env and .env.local files.'
    )

    args = parser.parse_args()

    print("Welcome to the Suna Local Development Setup Wizard!")
    print("="*50)

    try:
        setup = LocalDevSetup(skip_optional=args.skip_optional, reset=args.reset)
        setup.run()
    except KeyboardInterrupt:
        print("\n\nSetup aborted by user. Exiting.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        print("Please check the error message and try again.")
        sys.exit(1)

if __name__ == '__main__':
    main()
