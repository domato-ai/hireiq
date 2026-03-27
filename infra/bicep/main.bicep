// ============================================================
// RoleFitAI — Main Bicep Deployment Template
// ============================================================
// Deploys the full Azure infrastructure for a given environment.
// Usage:
//   az deployment sub create \
//     --location eastus \
//     --template-file main.bicep \
//     --parameters @parameters.dev.json

targetScope = 'subscription'

// ---------------------
// Parameters
// ---------------------

@description('Environment name: dev or prod')
@allowed(['dev', 'prod'])
param environmentName string = 'dev'

@description('Azure region for all resources')
param location string = 'eastus'

@description('PostgreSQL administrator login')
param postgresAdminLogin string = 'hireiqadmin'

@secure()
@description('PostgreSQL administrator password')
param postgresAdminPassword string

@description('App Service SKU — override for prod')
param appServiceSkuName string = 'B1'

@description('PostgreSQL SKU — override for prod')
param postgresSku string = 'Standard_B1ms'

// ---------------------
// Variables / Naming
// ---------------------

var appName       = 'hireiq'
var rgName        = 'rg-${appName}-${environmentName}'
var swaName       = 'swa-${appName}-${environmentName}'
var apiAppName    = 'app-${appName}-api-${environmentName}'
var aspName       = 'asp-${appName}-${environmentName}'
var pgServerName  = 'pgs-${appName}-${environmentName}'
var storageName   = 'st${appName}${environmentName}'   // no hyphens allowed
var kvName        = 'kv-${appName}-${environmentName}'
var aiName        = 'ai-${appName}-${environmentName}'
var lawName       = 'law-${appName}-${environmentName}'

// ---------------------
// Resource Group
// ---------------------

resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: rgName
  location: location
  tags: {
    environment: environmentName
    project: appName
  }
}

// ---------------------
// Log Analytics Workspace (required by App Insights)
// ---------------------

module logAnalytics 'modules/log-analytics.bicep' = {
  name: 'logAnalytics'
  scope: rg
  params: {
    name: lawName
    location: location
  }
}

// ---------------------
// Application Insights
// ---------------------

module appInsights 'modules/app-insights.bicep' = {
  name: 'appInsights'
  scope: rg
  params: {
    name: aiName
    location: location
    logAnalyticsWorkspaceId: logAnalytics.outputs.workspaceId
  }
}

// ---------------------
// Key Vault
// ---------------------

module keyVault 'modules/key-vault.bicep' = {
  name: 'keyVault'
  scope: rg
  params: {
    name: kvName
    location: location
  }
}

// ---------------------
// Storage Account
// ---------------------

module storage 'modules/storage.bicep' = {
  name: 'storage'
  scope: rg
  params: {
    name: storageName
    location: location
  }
}

// ---------------------
// App Service Plan (Linux)
// ---------------------

module appServicePlan 'modules/app-service-plan.bicep' = {
  name: 'appServicePlan'
  scope: rg
  params: {
    name: aspName
    location: location
    skuName: appServiceSkuName
  }
}

// ---------------------
// App Service — API (FastAPI via Python)
// ---------------------

module apiApp 'modules/app-service.bicep' = {
  name: 'apiApp'
  scope: rg
  params: {
    name: apiAppName
    location: location
    appServicePlanId: appServicePlan.outputs.planId
    appInsightsConnectionString: appInsights.outputs.connectionString
    keyVaultUri: keyVault.outputs.vaultUri
    environmentName: environmentName
  }
}

// ---------------------
// Static Web App — Frontend (Next.js)
// ---------------------

module staticWebApp 'modules/static-web-app.bicep' = {
  name: 'staticWebApp'
  scope: rg
  params: {
    name: swaName
    location: location
  }
}

// ---------------------
// PostgreSQL Flexible Server
// ---------------------

module postgres 'modules/postgres.bicep' = {
  name: 'postgres'
  scope: rg
  params: {
    serverName: pgServerName
    location: location
    administratorLogin: postgresAdminLogin
    administratorLoginPassword: postgresAdminPassword
    skuName: postgresSku
    environmentName: environmentName
  }
}

// ---------------------
// Outputs
// ---------------------

output resourceGroupName string = rg.name
output staticWebAppUrl string = staticWebApp.outputs.defaultHostname
output apiAppUrl string = apiApp.outputs.defaultHostname
output postgresServerFqdn string = postgres.outputs.fqdn
output keyVaultUri string = keyVault.outputs.vaultUri
output storageAccountName string = storage.outputs.accountName
output appInsightsInstrumentationKey string = appInsights.outputs.instrumentationKey
