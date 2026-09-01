# MathModeling Skills v2 — 一键安装 (Windows PowerShell)
# 用法: 在本目录下运行  .\install.ps1

$ErrorActionPreference = "Stop"
$src = Join-Path $PSScriptRoot "math-modeling-v2"
$dstRoot = Join-Path $HOME ".claude\skills"

if (-not (Test-Path $src)) {
    Write-Host "ERROR: 未找到 $src，请确认脚本位于 skills/ 目录。" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $dstRoot)) {
    New-Item -ItemType Directory -Path $dstRoot -Force | Out-Null
}

$installed = 0
Get-ChildItem -Path $src -Directory | ForEach-Object {
    $skillName = $_.Name
    $target = Join-Path $dstRoot $skillName

    if (Test-Path $target) {
        $backup = "$target.bak-$(Get-Date -Format 'yyyyMMddHHmmss')"
        Move-Item $target $backup
        Write-Host "备份旧目录: $skillName -> $backup" -ForegroundColor Yellow
    }

    Copy-Item $_.FullName $target -Recurse
    $installed++
}

Write-Host "安装完成: 共 $installed 个 skill 已复制到 $dstRoot"
Write-Host "请重启 Claude Code 生效。"
