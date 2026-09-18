[CmdletBinding()]
param(
  [string]$Remote = "origin",
  [string]$Branch,
  [string]$Username = "adityakoushik",
  [string]$RepoUrl = "https://github.com/adityakoushik/FastAPIWithVectorDBQdrant.git"
)

$ErrorActionPreference = "Stop"

function Fail($Message) {
  Write-Error $Message
  exit 1
}

$repoRoot = git rev-parse --show-toplevel 2>$null
if ($LASTEXITCODE -ne 0 -or -not $repoRoot) {
  Fail "Run this script inside a Git repository."
}

$remoteUrl = git remote get-url $Remote 2>$null
if ($LASTEXITCODE -ne 0 -or -not $remoteUrl) {
  if ([string]::IsNullOrWhiteSpace($RepoUrl)) {
    Fail "Remote '$Remote' was not found. Provide -RepoUrl or add the remote first."
  }

  Write-Host "Remote '$Remote' was not found. Adding it as $RepoUrl"
  git remote add $Remote $RepoUrl
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }

  $remoteUrl = git remote get-url $Remote
}

if ($remoteUrl -notmatch '^https://github\.com/(?<owner>[^/]+)/(?<repo>[^/]+?)(\.git)?$') {
  Fail "This helper currently supports HTTPS GitHub remotes only."
}

$remoteOwner = $Matches.owner
$remoteRepo = $Matches.repo

if (-not $Branch) {
  $Branch = git branch --show-current 2>$null
  if ($LASTEXITCODE -ne 0 -or -not $Branch) {
    $Branch = "main"
  }
}

if ([string]::IsNullOrWhiteSpace($Username)) {
  $Username = $remoteOwner
}

Write-Host "Preparing one-time push to $remoteOwner/$remoteRepo on branch '$Branch'."
Write-Host "The token will be used only for this push and will not be saved to git config."

$secureToken = Read-Host "Enter GitHub PAT for $Username" -AsSecureString
$tokenBstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)

try {
  $tokenPlain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($tokenBstr)

  if ([string]::IsNullOrWhiteSpace($tokenPlain)) {
    Fail "No token was provided."
  }

  $pair = "${Username}:$tokenPlain"
  $basic = [Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($pair))

  git -c credential.helper= -c "http.https://github.com/.extraheader=AUTHORIZATION: Basic $basic" push -u $Remote $Branch
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }

  Write-Host "Push completed successfully."
}
finally {
  if ($tokenBstr -ne [IntPtr]::Zero) {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenBstr)
  }

  Remove-Variable secureToken -ErrorAction SilentlyContinue
  Remove-Variable tokenPlain -ErrorAction SilentlyContinue
  Remove-Variable pair -ErrorAction SilentlyContinue
  Remove-Variable basic -ErrorAction SilentlyContinue
}
