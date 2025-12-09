#Requires -Version 5.1
<#
.SYNOPSIS
    Creates an Aerospike cluster on GCP using aerolab.

.DESCRIPTION
    This script creates an Aerospike cluster with NVMe SSDs, configures partitions,
    and starts the cluster.

.PARAMETER Name
    Cluster name (default: ags-aerospike)

.PARAMETER NodeCount
    Number of Aerospike nodes (default: 2)

.PARAMETER Zone
    GCP zone (default: us-central1-a)

.PARAMETER InstanceType
    GCP instance type (default: n2d-standard-4)

.PARAMETER AerospikeVersion
    Aerospike version (default: 8.0.*)

.PARAMETER SsdCount
    Number of local SSDs per node (default: 2)

.PARAMETER FeaturesFile
    Path to features.conf file (default: .\features.conf)

.PARAMETER ConfigFile
    Path to custom aerospike config (default: .\aerospike-rf2.conf)

.PARAMETER Destroy
    Destroy the cluster instead of creating it

.EXAMPLE
    .\create-cluster.ps1
    Creates cluster with default settings

.EXAMPLE
    .\create-cluster.ps1 -Name "my-cluster" -NodeCount 3 -Zone "us-west1-a"
    Creates a 3-node cluster named "my-cluster" in us-west1-a

.EXAMPLE
    .\create-cluster.ps1 -Destroy
    Destroys the cluster
#>

param(
    [string]$Name = "ags-aerospike",
    [int]$NodeCount = 2,
    [string]$Zone = "us-central1-a",
    [string]$InstanceType = "n2d-standard-4",
    [string]$AerospikeVersion = "8.0.*",
    [int]$SsdCount = 2,
    [string]$FeaturesFile = "",
    [string]$ConfigFile = "",
    [switch]$Destroy
)

$ErrorActionPreference = "Stop"

# Get script directory for relative paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Set default paths relative to script directory
if (-not $FeaturesFile) {
    $FeaturesFile = Join-Path $ScriptDir "features.conf"
}
if (-not $ConfigFile) {
    $ConfigFile = Join-Path $ScriptDir "aerospike-rf2.conf"
}

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Info($message) {
    Write-Host "[INFO] " -ForegroundColor Cyan -NoNewline
    Write-Host $message
}

function Write-Success($message) {
    Write-Host "[OK] " -ForegroundColor Green -NoNewline
    Write-Host $message
}

function Write-Error($message) {
    Write-Host "[ERROR] " -ForegroundColor Red -NoNewline
    Write-Host $message
}

# Check if aerolab is installed
function Test-Aerolab {
    try {
        $null = Get-Command aerolab -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

# Destroy cluster
if ($Destroy) {
    Write-Info "Destroying cluster: $Name"
    aerolab cluster destroy -n $Name /f
    Write-Success "Cluster destroyed!"
    exit 0
}

# Validate prerequisites
Write-Info "Validating prerequisites..."

if (-not (Test-Aerolab)) {
    Write-Error "aerolab is not installed or not in PATH"
    Write-Host ""
    Write-Host "Install aerolab from: https://github.com/aerospike/aerolab/releases"
    exit 1
}

if (-not (Test-Path $FeaturesFile)) {
    Write-Error "Features file not found: $FeaturesFile"
    Write-Host ""
    Write-Host "Specify the path with -FeaturesFile parameter"
    exit 1
}

if (-not (Test-Path $ConfigFile)) {
    Write-Error "Config file not found: $ConfigFile"
    Write-Host ""
    Write-Host "Specify the path with -ConfigFile parameter"
    exit 1
}

Write-Success "Prerequisites validated"

# Display configuration
Write-Host ""
Write-Host "=== Cluster Configuration ===" -ForegroundColor Yellow
Write-Host "  Name:              $Name"
Write-Host "  Zone:              $Zone"
Write-Host "  Node Count:        $NodeCount"
Write-Host "  Instance Type:     $InstanceType"
Write-Host "  Aerospike Version: $AerospikeVersion"
Write-Host "  SSD Count:         $SsdCount"
Write-Host "  Features File:     $FeaturesFile"
Write-Host "  Config File:       $ConfigFile"
Write-Host ""

# Create cluster
Write-Info "Creating cluster..."

$createArgs = @(
    "cluster", "create",
    "--name", $Name,
    "--zone", $Zone,
    "--count", $NodeCount,
    "--instance", $InstanceType,
    "--aerospike-version", $AerospikeVersion,
    "--featurefile", $FeaturesFile,
    "--customconf", $ConfigFile,
    "--disk", "pd-ssd:20",
    "--disk", "local-ssd@$SsdCount",
    "--start", "n"
)

Write-Host "Running: aerolab $($createArgs -join ' ')" -ForegroundColor DarkGray
& aerolab @createArgs

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to create cluster"
    exit 1
}

Write-Success "Cluster created"

# Configure partitions
Write-Info "Creating partitions..."

aerolab cluster partition create `
    --name $Name `
    --filter-type nvme `
    --partitions 24,24,24,24

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to create partitions"
    exit 1
}

Write-Success "Partitions created"

Write-Info "Configuring partitions for namespace 'test'..."

aerolab cluster partition conf `
    --name $Name `
    --namespace test `
    --filter-type nvme `
    --filter-partitions 1,2,3,4 `
    --configure device

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to configure partitions"
    exit 1
}

Write-Success "Partitions configured"

# Start Aerospike
Write-Info "Starting Aerospike..."

aerolab aerospike start --name $Name

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to start Aerospike"
    exit 1
}

Write-Success "Aerospike started"

# Get cluster info
Write-Host ""
Write-Host "=== Cluster Ready ===" -ForegroundColor Green
Write-Host ""

aerolab cluster list

Write-Host ""
Write-Host "=== Useful Commands ===" -ForegroundColor Yellow
Write-Host "  # SSH to cluster"
Write-Host "  aerolab cluster attach -n $Name"
Write-Host ""
Write-Host "  # View logs (journald)"
Write-Host "  aerolab logs show -n $Name /j"
Write-Host ""
Write-Host "  # Follow logs"
Write-Host "  aerolab logs show -n $Name /j /f"
Write-Host ""
Write-Host "  # Stop Aerospike"
Write-Host "  aerolab aerospike stop -n $Name"
Write-Host ""
Write-Host "  # Destroy cluster"
Write-Host "  .\create-cluster.ps1 -Destroy"
Write-Host "  # or: aerolab cluster destroy -n $Name /f"

