import sys
from utils.status_checker import StatusChecker

def main():
    """
    Main function to run the local development status check.
    """
    print("📊 Suna Local Development Status Check")
    print("="*40)

    try:
        checker = StatusChecker()
        status = checker.check_all()
        checker.display_status_report(status)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        print("Please check the error message and try again.")
        sys.exit(1)

if __name__ == '__main__':
    main()
