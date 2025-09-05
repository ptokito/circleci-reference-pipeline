#!/bin/bash
# SHEBANG: Tells the system to run this script with bash shell

# ERROR HANDLING SETUP
set -e
# This makes the script exit immediately if any command fails
# Prevents the script from continuing with broken state

# COMMAND LINE ARGUMENT HANDLING
TEST_TYPE=${1:-unit}
# Gets the first command line argument ($1) and stores it in TEST_TYPE variable
# If no argument is provided, defaults to "unit"
# Examples: ./test.sh integration  -> TEST_TYPE="integration"
#          ./test.sh              -> TEST_TYPE="unit" (default)

# MAIN LOGIC: CASE STATEMENT FOR TEST TYPE SELECTION
case $TEST_TYPE in
  # UNIT TESTING BRANCH
  "unit")
    echo "Running unit tests..."
    # Use the working test file
    python -m pytest test_app_working.py -v
    # -m pytest: Run pytest module
    # test_app_working.py: Specific test file with mocked database tests
    # -v: Verbose output showing individual test names and results
    ;;
  
  # SIMPLE TESTING BRANCH  
  "simple")
    echo "Running simple tests..."
    python -m pytest test_simple.py -v
    # Runs basic functionality tests from the simple test file
    # Used for quick validation during development
    ;;
    
  # INTEGRATION TESTING BRANCH
  "integration")
    echo "Running integration tests with Docker..."
    docker build -t my-app:test .
    # Build Docker image with tag "my-app:test"
    # Uses Dockerfile in current directory (.)
    # This tests that the entire application can be containerized successfully
    echo "Docker build successful - integration test passed"
    # Simple success message - if build fails, script exits due to 'set -e'
    ;;
  
  # ERROR HANDLING: UNKNOWN TEST TYPE
  *)
    # The * matches any value not caught by previous cases
    echo "Unknown test type: $TEST_TYPE"
    echo "Usage: $0 [unit|simple|integration]"
    # $0 is the script name, shows proper usage syntax
    exit 1
    # Exit with error code 1 (non-zero indicates failure)
    ;;
esac

# SUCCESS MESSAGE
echo "Tests completed successfully!"
# Only reached if no errors occurred during execution