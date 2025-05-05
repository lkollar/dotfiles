#!/bin/sh


# Function to find a suitable binary in a directory
find_binary() {
    src_dir="$1"
    binary_name="$2"
    os="$3"
    arch="$4"

    # First try to find executable files
    for file in $(find "$src_dir" -type f); do
        if [ -x "$file" ]; then
            echo "$file"
            return 0
        fi
    done

    # If no executable found, try to find something that looks like a binary
    for file in $(find "$src_dir" -type f -name "*$binary_name*" -o -name "*$os*" -o -name "*$arch*"); do
        echo "$file"
        return 0
    done

    # Last resort: just grab the first file that seems reasonably sized for a binary
    for file in $(find "$src_dir" -type f -size +10k -size -100M); do
        echo "$file"
        return 0
    done

    return 1
}

# Function to download the latest release binary from GitHub (POSIX compatible)
# Usage: download_github_release project_name [os_override] [arch_override]

download_github_release() {
    project="$1"
    os_override="$2"
    arch_override="$3"

    if [ -z "$project" ]; then
        echo "Error: Project name is required"
        echo "Usage: download_latest_release project_name [os_override] [arch_override]"
        return 1
    fi

    # Extract owner/repo from project name if it contains a slash
    # Otherwise, assume it's just the repo name without an owner
    case "$project" in
        */*) owner_repo="$project" ;;
        *)
            echo "Warning: No owner specified, assuming it's a project name only"
            echo "For best results, use format: owner/repo"
            owner_repo="$project"
            ;;
    esac

    # Create the target directory if it doesn't exist
    bin_dir="$HOME/.local/bin"
    mkdir -p "$bin_dir"

    # Detect OS and architecture if not provided
    os=""
    arch=""

    if [ -z "$os_override" ]; then
        os_name=$(uname -s)
        case "$os_name" in
            Linux*)     os="linux" ;;
            Darwin*)    os="darwin" ;;
            MINGW*)     os="windows" ;;
            MSYS*)      os="windows" ;;
            CYGWIN*)    os="windows" ;;
            *)          os="unknown" ;;
        esac
    else
        os="$os_override"
    fi

    if [ -z "$arch_override" ]; then
        arch_name=$(uname -m)
        case "$arch_name" in
            x86_64|amd64)  arch="amd64" ;;
            i386|i686)     arch="386" ;;
            arm64|aarch64) arch="arm64" ;;
            armv7*)        arch="arm" ;;
            *)             arch="unknown" ;;
        esac
    else
        arch="$arch_override"
    fi

    if [ "$os" = "unknown" ] || [ "$arch" = "unknown" ]; then
        echo "Error: Could not detect OS ($os) or architecture ($arch)"
        echo "Please provide them as overrides: download_latest_release project_name os_override arch_override"
        return 1
    fi

    echo "Detected OS: $os, Architecture: $arch"
    echo "Checking latest release for $owner_repo..."

    # Get the latest release info
    release_info=$(curl -s "https://api.github.com/repos/$owner_repo/releases/latest")

    if echo "$release_info" | grep -q "Not Found"; then
        echo "Error: Repository not found or no releases available"
        return 1
    fi

    # Extract the tag name for version info
    version=$(echo "$release_info" | grep '"tag_name":' | sed -E 's/.*"tag_name": "([^"]+)".*/\1/')
    echo "Latest version: $version"

    # Get the list of assets
    assets=$(echo "$release_info" | grep '"browser_download_url":' | sed -E 's/.*"browser_download_url": "([^"]+)".*/\1/')

    # Try to find the right asset based on OS and architecture
    download_url=""
    filename=""

    # Try common naming patterns
    for pattern in "$os[-_]$arch" "$os$arch" "$arch[-_]$os" "$arch$os" "$os"; do
        if [ -z "$download_url" ]; then
            download_url=$(echo "$assets" | grep -i "$pattern" | head -n 1)
            if [ -n "$download_url" ]; then
                filename=$(basename "$download_url")
                echo "Found matching asset: $filename"
                break
            fi
        fi
    done

    # If still not found, show available assets and let user choose
    if [ -z "$download_url" ]; then
        echo "Could not automatically find a matching asset for your system ($os-$arch)"
        echo "Available assets:"
        echo "$assets" | sed 's/^/- /'
        echo "Please try again with OS and architecture overrides that match one of these assets"
        return 1
    fi

    echo "Downloading from: $download_url"

    # Create a temporary directory for the download
    temp_dir=$(mktemp -d)
    temp_file="$temp_dir/$filename"

    # Download the file
    curl -L -o "$temp_file" "$download_url"

    if [ $? -ne 0 ]; then
        echo "Error: Failed to download the release"
        rm -rf "$temp_dir"
        return 1
    fi

    # Extract the binary name from the project (assuming it's the repo name)
    binary_name=$(basename "$project" | tr '[:upper:]' '[:lower:]')

    # Handle different file types
    case "$filename" in
        *.tar.gz|*.tgz)
            echo "Extracting tar.gz archive..."
            tar -xzf "$temp_file" -C "$temp_dir"
            bin_file=$(find_binary "$temp_dir" "$binary_name" "$os" "$arch")
            if [ -n "$bin_file" ]; then
                cp "$bin_file" "$bin_dir/$binary_name"
            else
                echo "Warning: Could not find a suitable binary in the archive"
                return 1
            fi
            ;;
        *.zip)
            echo "Extracting zip archive..."
            unzip -q "$temp_file" -d "$temp_dir"
            bin_file=$(find_binary "$temp_dir" "$binary_name" "$os" "$arch")
            if [ -n "$bin_file" ]; then
                cp "$bin_file" "$bin_dir/$binary_name"
            else
                echo "Warning: Could not find a suitable binary in the archive"
                return 1
            fi
            ;;
        *)
            # Assume it's a direct binary
            cp "$temp_file" "$bin_dir/$binary_name"
            ;;
    esac

    # Make it executable
    chmod +x "$bin_dir/$binary_name"

    echo "Installation complete: $binary_name has been installed to $bin_dir"
    echo "Make sure $bin_dir is in your PATH"

    # Clean up
    rm -rf "$temp_dir"
    return 0
}
