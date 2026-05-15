$ErrorActionPreference = "Stop"

$RootDir = $PSScriptRoot

function Start-DevWindow {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Title,

        [Parameter(Mandatory = $true)]
        [string] $WorkingDirectory,

        [Parameter(Mandatory = $true)]
        [string] $Command
    )

    Start-Process powershell.exe -WorkingDirectory $WorkingDirectory -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        "`$Host.UI.RawUI.WindowTitle = '$Title'; $Command"
    )
}

Start-DevWindow `
    -Title "Resume Matcher Backend" `
    -WorkingDirectory $RootDir `
    -Command "cd apps/backend; if (-not (Test-Path .env)) { cp .env.example .env }; uv sync; uv run app"

Start-DevWindow `
    -Title "Resume Matcher Frontend" `
    -WorkingDirectory $RootDir `
    -Command "cd apps/frontend; npm install; npm run dev"
