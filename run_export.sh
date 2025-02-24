#!/bin/bash

# Get the environment name if provided, otherwise use active environment
if [ $# -eq 1 ]; then
    env_name="$1"
    # Check if environment exists
    if ! conda env list | grep -q "^$env_name "; then
        echo "Error: Environment '$env_name' not found"
        exit 1
    fi
else
    # Get active environment name
    env_name=$(conda info --envs | grep '*' | awk '{print $1}')
fi

# Create temporary files
conda_tmp=$(mktemp)
pip_tmp=$(mktemp)

# Export conda packages
echo "Exporting conda packages..."
conda env export --from-history -n "$env_name" > "$conda_tmp"

# Export pip packages
echo "Exporting pip packages..."
# Activate the environment to ensure we get the right pip
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$env_name"
pip list --format=freeze --not-required > "$pip_tmp"

# Combine them into final environment.yml
echo "Creating environment.yml..."
(
    # Take conda env export but remove last line (name line)
    head -n -1 "$conda_tmp"
    # Add pip dependencies section
    echo "  - pip:"
    # Add pip packages with proper indentation
    sed 's/^/    - /' "$pip_tmp"
) > environment.yml

# Clean up temporary files
rm "$conda_tmp" "$pip_tmp"

echo "Done! Created environment.yml with both conda and pip packages."
echo "You can create a new environment using: conda env create -f environment.yml"