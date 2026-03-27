#!/usr/bin/env bash
# =============================================================
# RoleFitAI — Azure Deployment Script
# =============================================================
# Uses the Azure CLI and Bicep to deploy infrastructure.
#
# Prerequisites:
#   - az CLI >= 2.50 installed and authenticated (az login)
#   - Bicep CLI installed (az bicep install)
#
# Usage:
#   ./deploy.sh [dev|prod] [eastus]
#
# Examples:
#   ./deploy.sh dev
#   ./deploy.sh prod westus2

set -euo pipefail

# ---------------------
# Arguments & Defaults
# ---------------------

ENVIRONMENT="${1:-dev}"
LOCATION="${2:-eastus}"

if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "prod" ]]; then
  echo "ERROR: environment must be 'dev' or 'prod'. Got: $ENVIRONMENT"
  exit 1
fi

# ---------------------
# Derived Variables
# ---------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BICEP_DIR="$SCRIPT_DIR/../bicep"
TEMPLATE="$BICEP_DIR/main.bicep"
PARAMS="$BICEP_DIR/parameters.${ENVIRONMENT}.json"
DEPLOYMENT_NAME="hireiq-${ENVIRONMENT}-$(date +%Y%m%d%H%M%S)"

echo "============================================="
echo " RoleFitAI Deployment"
echo " Environment : $ENVIRONMENT"
echo " Location    : $LOCATION"
echo " Deployment  : $DEPLOYMENT_NAME"
echo "============================================="

# ---------------------
# Pre-flight Checks
# ---------------------

command -v az &>/dev/null || { echo "ERROR: az CLI not found."; exit 1; }

az account show &>/dev/null || {
  echo "ERROR: Not logged in to Azure. Run 'az login' first."
  exit 1
}

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "Subscription : $SUBSCRIPTION_ID"

# ---------------------
# Ensure Bicep is installed
# ---------------------

az bicep install --only-show-errors || true

# ---------------------
# Lint the template
# ---------------------

echo ""
echo "[1/4] Linting Bicep template…"
az bicep lint --file "$TEMPLATE"

# ---------------------
# What-if (dry run)
# ---------------------

echo ""
echo "[2/4] Running what-if (dry run)…"
az deployment sub what-if \
  --name "$DEPLOYMENT_NAME-whatif" \
  --location "$LOCATION" \
  --template-file "$TEMPLATE" \
  --parameters "@$PARAMS" \
  --no-prompt

# ---------------------
# Confirmation prompt (skip in CI)
# ---------------------

if [[ "${CI:-false}" != "true" ]]; then
  echo ""
  read -rp "Proceed with deployment to '$ENVIRONMENT'? [y/N] " confirm
  if [[ "${confirm,,}" != "y" ]]; then
    echo "Deployment cancelled."
    exit 0
  fi
fi

# ---------------------
# Deploy
# ---------------------

echo ""
echo "[3/4] Deploying to Azure…"
az deployment sub create \
  --name "$DEPLOYMENT_NAME" \
  --location "$LOCATION" \
  --template-file "$TEMPLATE" \
  --parameters "@$PARAMS" \
  --no-prompt \
  --output table

# ---------------------
# Capture Outputs
# ---------------------

echo ""
echo "[4/4] Deployment outputs:"
az deployment sub show \
  --name "$DEPLOYMENT_NAME" \
  --query properties.outputs \
  --output json

echo ""
echo "Deployment complete: $DEPLOYMENT_NAME"
