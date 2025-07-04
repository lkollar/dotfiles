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

# Function to download and install GitHub release binaries
# Usage: download_github_release owner/repo [binary_name] [install_dir] [use_sudo]
# - owner/repo: GitHub repository (required)
# - binary_name: name of binary (optional, defaults to repo name)
# - install_dir: installation directory (optional, defaults to ~/.local/bin)
# - use_sudo: "true" to use sudo for installation (optional, defaults to false)
download_github_release() {
    owner_repo="$1"
    binary_name="$2"
    install_dir="$3"
    use_sudo="$4"

    if [ -z "$owner_repo" ]; then
        echo "Error: Repository name is required"
        echo "Usage: download_github_release owner/repo [binary_name] [install_dir] [use_sudo]"
        return 1
    fi

    # Extract binary name from repo if not provided
    if [ -z "$binary_name" ]; then
        binary_name=$(basename "$owner_repo" | tr '[:upper:]' '[:lower:]')
    fi

    # Set default install directory
    if [ -z "$install_dir" ]; then
        install_dir="$HOME/.local/bin"
    fi

    # Detect OS and architecture
    os_name=$(uname -s)
    case "$os_name" in
        Linux*) os="linux" ;;
        Darwin*) os="darwin" ;;
        MINGW*) os="windows" ;;
        MSYS*) os="windows" ;;
        CYGWIN*) os="windows" ;;
        *)
            echo "Error: Unsupported OS: $os_name"
            return 1
            ;;
    esac

    arch_name=$(uname -m)
    case "$arch_name" in
        x86_64) arch="amd64" ;;
        aarch64) arch="arm64" ;;
        armv7l) arch="armv7" ;;
        i686) arch="i386" ;;
        *)
            echo "Error: Unsupported architecture: $arch_name"
            return 1
            ;;
    esac

    echo "Detected OS: $os, Architecture: $arch"
    echo "Fetching latest release for $owner_repo..."

    # Get the latest release info
    release_info=$(curl -s "https://api.github.com/repos/$owner_repo/releases/latest")

    if echo "$release_info" | grep -q "Not Found"; then
        echo "Error: Repository not found or no releases available"
        return 1
    fi

    # Extract version
    version=$(echo "$release_info" | grep '"tag_name":' | sed -E 's/.*"tag_name": "([^"]+)".*/\1/')
    echo "Latest version: $version"

    # Get assets
    assets=$(echo "$release_info" | grep '"browser_download_url":' | sed -E 's/.*"browser_download_url": "([^"]+)".*/\1/')

    # Try different naming patterns
    download_url=""
    filename=""

    # Pattern 1: fzf style - linux_amd64, darwin_amd64, windows_amd64
    if [ -z "$download_url" ]; then
        download_url=$(echo "$assets" | grep -i "$os[_-]$arch" | head -n 1)
        if [ -n "$download_url" ]; then
            filename=$(basename "$download_url")
            echo "Found asset (os_arch pattern): $filename"
        fi
    fi

    # Pattern 2: zoxide style - x86_64-unknown-linux-musl, aarch64-apple-darwin
    if [ -z "$download_url" ]; then
        # Convert amd64 back to x86_64 for some tools
        alt_arch="$arch"
        if [ "$arch" = "amd64" ]; then
            alt_arch="x86_64"
        fi
        download_url=$(echo "$assets" | grep -i "$alt_arch.*$os" | head -n 1)
        if [ -n "$download_url" ]; then
            filename=$(basename "$download_url")
            echo "Found asset (arch-os pattern): $filename"
        fi
    fi

    # Pattern 3: arch_os - amd64-linux, arm64-darwin
    if [ -z "$download_url" ]; then
        download_url=$(echo "$assets" | grep -i "$arch[_-]$os" | head -n 1)
        if [ -n "$download_url" ]; then
            filename=$(basename "$download_url")
            echo "Found asset (arch_os pattern): $filename"
        fi
    fi

    # Pattern 4: Generic OS match (last resort)
    if [ -z "$download_url" ]; then
        download_url=$(echo "$assets" | grep -i "$os" | head -n 1)
        if [ -n "$download_url" ]; then
            filename=$(basename "$download_url")
            echo "Found asset (generic os pattern): $filename"
        fi
    fi

    if [ -z "$download_url" ]; then
        echo "Error: No suitable release found for $os-$arch"
        echo "Available assets:"
        echo "$assets" | sed 's/^/- /'
        return 1
    fi

    echo "Downloading from: $download_url"

    # Create temporary directory
    temp_dir=$(mktemp -d)
    temp_file="$temp_dir/$filename"

    # Download
    curl -L -o "$temp_file" "$download_url"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to download release"
        rm -rf "$temp_dir"
        return 1
    fi

    # Extract based on file type
    case "$filename" in
        *.tar.gz | *.tgz)
            echo "Extracting tar.gz archive..."
            tar -xzf "$temp_file" -C "$temp_dir"
            bin_file=$(find_binary "$temp_dir" "$binary_name" "$os" "$arch")
            ;;
        *.zip)
            echo "Extracting zip archive..."
            unzip -q "$temp_file" -d "$temp_dir"
            bin_file=$(find_binary "$temp_dir" "$binary_name" "$os" "$arch")
            ;;
        *)
            # Direct binary
            bin_file="$temp_file"
            ;;
    esac

    if [ -z "$bin_file" ] || [ ! -f "$bin_file" ]; then
        echo "Error: Could not find binary $binary_name in downloaded archive"
        rm -rf "$temp_dir"
        return 1
    fi

    # Create install directory if it doesn't exist
    if [ "$use_sudo" = "true" ]; then
        sudo mkdir -p "$install_dir"
        echo "Installing $binary_name to $install_dir (with sudo)..."
        sudo install -m 755 "$bin_file" "$install_dir/$binary_name"
    else
        mkdir -p "$install_dir"
        echo "Installing $binary_name to $install_dir..."
        install -m 755 "$bin_file" "$install_dir/$binary_name"
    fi

    if [ $? -eq 0 ]; then
        echo "Successfully installed $binary_name to $install_dir"
        if [ "$install_dir" = "$HOME/.local/bin" ]; then
            echo "Make sure $install_dir is in your PATH"
        fi
    else
        echo "Error: Failed to install $binary_name"
        rm -rf "$temp_dir"
        return 1
    fi

    # Clean up
    rm -rf "$temp_dir"
    return 0
}
