#!/bin/bash

# Set default tolerance
TOLERANCE="1e-9"

# Allow optional tolerance argument
if [[ -n "$1" ]]; then
    TOLERANCE="$1"
    echo "Using custom tolerance: $TOLERANCE"
else
    echo "Using default tolerance: $TOLERANCE"
fi

# Check if both files exist
if [[ ! -f "./err.txt" || ! -f "./err.txt.ref" ]]; then
    echo "❌ Error: One or both input files (err.txt, err.txt.ref) not found."
    exit 1
fi

# Read the lines
line1=$(<err.txt)
line2=$(<err.txt.ref)

# Remove spaces and ensure valid formatting
line1=$(echo "$line1" | tr -d '[:space:]')
line2=$(echo "$line2" | tr -d '[:space:]')

# Split the lines into three values
IFS=',' read -r new1 new2 new3 <<< "$line1"  # New values
IFS=',' read -r ref1 ref2 ref3 <<< "$line2"  # Reference values

# Ensure valid floating-point numbers
validate_number() {
    if ! [[ "$1" =~ ^-?[0-9]+(\.[0-9]+)?$ ]]; then
        echo "❌ Error: Invalid number detected: $1"
        exit 1
    fi
}

validate_number "$new1"
validate_number "$new2"
validate_number "$new3"
validate_number "$ref1"
validate_number "$ref2"
validate_number "$ref3"

# Function to compare two values with proper floating-point handling
compare_values() {
    local new="$1"
    local ref="$2"

    # Calculate absolute difference using awk for precision
    diff=$(awk -v n="$new" -v r="$ref" 'BEGIN { print (n > r ? n - r : r - n) }')

    # Check if the difference exceeds tolerance
    if awk -v d="$diff" -v tol="$TOLERANCE" 'BEGIN { exit (d > tol) ? 1 : 0 }'; then
        echo "✅ Within tolerance: NEW=$new vs REF=$ref (abs diff=$diff)"
        return 0
    else
        echo "❌ Absolute Difference exceeds tolerance: NEW=$new vs REF=$ref (abs diff=$diff)"
        return 1
    fi
}

# Perform the comparison
pass=true

compare_values "$new1" "$ref1" || pass=false
compare_values "$new2" "$ref2" || pass=false
compare_values "$new3" "$ref3" || pass=false

# Final result
if $pass; then
    echo "✅ All values are within the tolerance of $TOLERANCE"
    exit 0
else
    echo "❌ Some values exceed the tolerance of $TOLERANCE"
    exit 1
fi
